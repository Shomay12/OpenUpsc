"""Unbreakable Self-Healing Process Supervisor for OpenUPSC.

Launches and supervises:
  - OpenUPSC Main App (Python Streamlit):  streamlit_app/app.py (default port 8501)
  - FastAPI Backend & REST API:            backend.main:app     (default port 8000)

Features:
  - Pre-flight SQLite initialization, integrity verification, rolling atomic backup,
    and Master Guide resource catalog validation.
  - Port conflict detection with optional `--auto-port` dynamic binding and
    cross-service URL wiring (`OPENUPSC_API_URL` <-> `OPENUPSC_STREAMLIT_URL`).
  - Independent self-healing process supervision with bounded exponential backoff
    (1s -> 2s -> 4s -> 8s -> 15s) inside a sliding restart window.
  - Graceful POSIX process-group cleanup on SIGINT / SIGTERM with zero orphan children.
  - Operational modes: default (dual stack), `--doctor`, `--api-only`, `--ui-only`.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_API_PORT = 8000
DEFAULT_STREAMLIT_PORT = 8501
BACKOFF_SCHEDULE: tuple[int, ...] = (1, 2, 4, 8, 15)
RESTART_WINDOW_SECONDS: float = 300.0
POLL_INTERVAL_SECONDS: float = 0.4


# =========================================================================
# NETWORK & BACKOFF HELPERS
# =========================================================================


def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return True if TCP `host:port` can be bound right now."""
    if not (1 <= int(port) <= 65535):
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, int(port)))
            return True
        except OSError:
            return False


def _find_free_port(
    start_port: int,
    *,
    host: str = "127.0.0.1",
    exclude: Optional[set[int]] = None,
    max_attempts: int = 100,
) -> int:
    """Find the first free TCP port at or above `start_port` not in `exclude`."""
    blocked = set(exclude or ())
    port = max(1024, int(start_port))
    for offset in range(max(1, int(max_attempts))):
        candidate = port + offset
        if candidate > 65535:
            break
        if candidate in blocked:
            continue
        if _is_port_free(candidate, host=host):
            return candidate
    raise RuntimeError(
        f"Unable to find a free port starting from {start_port} after {max_attempts} attempts."
    )


def _backoff_delay(attempt: int) -> int:
    """Return bounded exponential backoff delay in seconds (1 -> 2 -> 4 -> 8 -> 15)."""
    idx = max(0, min(int(attempt) - 1, len(BACKOFF_SCHEDULE) - 1))
    return BACKOFF_SCHEDULE[idx]


def _wait_for_http(url: str, timeout_s: float = 8.0) -> bool:
    """Poll an HTTP endpoint until HTTP 200 or timeout, bypassing proxies for localhost."""
    deadline = time.monotonic() + max(0.5, float(timeout_s))
    host = (urlparse(url).hostname or "").lower()
    opener = (
        build_opener(ProxyHandler({}))
        if host in ("127.0.0.1", "localhost", "::1")
        else None
    )
    open_fn = opener.open if opener is not None else urlopen

    while time.monotonic() < deadline:
        try:
            req = Request(url, headers={"Accept": "application/json"})
            with open_fn(req, timeout=0.9) as resp:
                if getattr(resp, "status", 200) == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False


# =========================================================================
# PRE-FLIGHT & DOCTOR MODES
# =========================================================================


def run_doctor_mode(as_json: bool = False) -> int:
    """Run non-mutating pre-flight checks + full 4-domain subagent health diagnostics."""
    from backend.database import check_db_integrity
    from backend.resource_engine import validate_catalog
    from subagents.doctor import _format_human_report, run_diagnostics

    db_report = check_db_integrity()
    catalog_report = validate_catalog()
    diag_report = run_diagnostics("all")

    db_ok = bool(db_report.get("ok")) or db_report.get("status") == "missing"
    catalog_ok = bool(catalog_report.get("valid"))
    doctor_ok = diag_report.get("status") != "error"
    overall_ok = db_ok and catalog_ok and doctor_ok

    if as_json:
        payload = {
            "ok": overall_ok,
            "database": db_report,
            "catalog": catalog_report,
            "diagnostics": diag_report,
        }
        print(json.dumps(payload, indent=2))
        return 0 if overall_ok else 1

    stats = catalog_report.get("stats") or {}
    print("\n" + "=" * 72)
    print("  OpenUPSC Pre-Flight Doctor Report")
    print("=" * 72)
    print(
        f"  Database Integrity : {db_report.get('status', 'unknown').upper()} "
        f"(tables={db_report.get('table_count', 0)}, rows={db_report.get('total_rows', 0)}, "
        f"mode={db_report.get('journal_mode') or 'n/a'})"
    )
    print(
        f"  Resource Catalog   : {'VALID' if catalog_ok else 'INVALID'} "
        f"({stats.get('resources_count', 0)} verified free resources across "
        f"{stats.get('master_guide_parts', 0)} parts, "
        f"{stats.get('total_urls_checked', 0)} URLs checked)"
    )
    print(
        f"  Subagent Doctor    : {str(diag_report.get('status', 'unknown')).upper()} "
        f"({diag_report['summary']['ok_checks']}/{diag_report['summary']['total_checks']} checks ok, "
        f"{diag_report['summary']['warn_checks']} warn, "
        f"{diag_report['summary']['fail_checks']} fail)"
    )
    print("=" * 72 + "\n")
    print(_format_human_report(diag_report))

    if not db_ok:
        print(
            "\n[ERROR] Database integrity check failed. Inspect data/backups/ to restore a clean snapshot.",
            file=sys.stderr,
        )
    if not catalog_ok:
        print(
            f"\n[ERROR] Resource catalog validation found {len(catalog_report.get('errors') or [])} error(s).",
            file=sys.stderr,
        )
    return 0 if overall_ok else 1


def run_preflight(*, skip_backup: bool = False) -> dict[str, Any]:
    """Execute pre-flight DB init, integrity audit, rolling backup, and catalog validation."""
    from backend.database import backup_database, check_db_integrity, init_db
    from backend.resource_engine import validate_catalog

    print("[PRE-FLIGHT] Initializing SQLite database & verifying schema...")
    init_db()

    db_report = check_db_integrity()
    if not db_report.get("ok"):
        print(
            "\n[FATAL] SQLite database integrity check FAILED!",
            file=sys.stderr,
        )
        print(f"        Database path : {db_report.get('db_path')}", file=sys.stderr)
        print(f"        Messages      : {db_report.get('integrity_messages')}", file=sys.stderr)
        print(
            "        Recovery hint : Restore the latest clean snapshot from data/backups/ "
            "or move the corrupt file aside before restarting.",
            file=sys.stderr,
        )
        raise RuntimeError("Database integrity check failed.")

    print(
        f"[PRE-FLIGHT] SQLite integrity OK "
        f"({db_report.get('table_count', 0)} tables, {db_report.get('total_rows', 0)} rows, "
        f"WAL={db_report.get('journal_mode')})."
    )

    backup_report: Optional[dict[str, Any]] = None
    if skip_backup:
        print("[PRE-FLIGHT] Skipping rolling backup (--no-backup).")
    else:
        backup_report = backup_database()
        if not backup_report.get("ok"):
            print(
                f"[WARN] Pre-flight backup completed with warning: {backup_report}",
                file=sys.stderr,
            )
        else:
            size_kb = round(int(backup_report.get("size_bytes", 0)) / 1024.0, 1)
            print(
                f"[PRE-FLIGHT] Atomic backup created: {backup_report['filename']} "
                f"({size_kb} KB, {backup_report['retained_count']} retained)."
            )

    catalog_report = validate_catalog()
    stats = catalog_report.get("stats") or {}
    res_count = stats.get("resources_count", 0)
    parts_count = stats.get("master_guide_parts", 11)
    urls_checked = stats.get("total_urls_checked", 0)
    if catalog_report.get("valid"):
        print(
            f"[PRE-FLIGHT] Catalog verified: {res_count} verified free resources across "
            f"{parts_count} parts ({urls_checked} URLs checked, 0 errors)."
        )
    else:
        err_count = len(catalog_report.get("errors") or [])
        print(
            f"[WARN] Resource catalog reported {err_count} error(s) across {res_count} resources. "
            "Run `.venv/bin/python run.py --doctor` for full diagnostics.",
            file=sys.stderr,
        )

    return {
        "database": db_report,
        "backup": backup_report,
        "catalog": catalog_report,
    }


# =========================================================================
# SELF-HEALING PROCESS SUPERVISOR
# =========================================================================


@dataclass
class ManagedService:
    """Tracked child service with process-group teardown and bounded exponential backoff."""

    key: str
    name: str
    command: list[str]
    env: dict[str, str]
    cwd: Path
    max_restarts: int = 5
    proc: Optional[subprocess.Popen[Any]] = None
    restart_timestamps: list[float] = field(default_factory=list)
    next_restart_at: Optional[float] = None
    exhausted: bool = False

    def start(self) -> None:
        self.next_restart_at = None
        popen_kwargs: dict[str, Any] = {
            "cwd": str(self.cwd),
            "env": self.env,
        }
        if os.name == "posix":
            popen_kwargs["start_new_session"] = True
        self.proc = subprocess.Popen(self.command, **popen_kwargs)

    def poll(self) -> Optional[int]:
        if self.proc is None:
            return None
        return self.proc.poll()

    def is_running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def schedule_restart(self, exit_code: int, *, peer_running: bool = False) -> bool:
        """Schedule a restart with exponential backoff if within max_restarts window."""
        now = time.monotonic()
        self.restart_timestamps = [
            ts for ts in self.restart_timestamps if (now - ts) <= RESTART_WINDOW_SECONDS
        ]
        attempt = len(self.restart_timestamps) + 1
        if attempt > self.max_restarts:
            self.exhausted = True
            self.proc = None
            print(
                f"[SUPERVISOR] {self.name} exited (code={exit_code}) and exceeded "
                f"max restarts ({self.max_restarts} within {int(RESTART_WINDOW_SECONDS)}s).",
                file=sys.stderr,
            )
            return False

        delay = _backoff_delay(attempt)
        self.restart_timestamps.append(now)
        self.next_restart_at = now + delay
        self.proc = None

        extra = ""
        if self.key == "api" and peer_running:
            extra = " Streamlit Main App remains live in Direct SQLite Fallback mode."
        print(
            f"[SUPERVISOR] {self.name} exited unexpectedly (code={exit_code}). "
            f"Auto-restarting in {delay}s (attempt {attempt}/{self.max_restarts})...{extra}",
            file=sys.stderr,
        )
        return True

    def terminate_gracefully(self, timeout_s: float = 5.0) -> None:
        """Terminate this service's process group cleanly (SIGTERM -> wait -> SIGKILL)."""
        proc = self.proc
        if proc is None:
            return
        if proc.poll() is not None:
            self.proc = None
            return

        try:
            if os.name == "posix":
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                proc.terminate()
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass

        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    proc.kill()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass
        finally:
            self.proc = None


def _build_api_command(python_exe: str, api_port: int, enable_reload: bool) -> list[str]:
    cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(api_port),
    ]
    if enable_reload:
        cmd.extend(["--reload", "--reload-dir", str(ROOT / "backend")])
    return cmd


def _build_streamlit_command(python_exe: str, ui_port: int) -> list[str]:
    entry = "streamlit_app/app.py" if (ROOT / "streamlit_app" / "app.py").is_file() else "streamlit_app/dashboard.py"
    return [
        python_exe,
        "-m",
        "streamlit",
        "run",
        entry,
        "--server.port",
        str(ui_port),
        "--server.headless",
        "true",
    ]


def _resolve_ports(
    *,
    run_api: bool,
    run_ui: bool,
    requested_api_port: int,
    requested_ui_port: int,
    auto_port: bool,
) -> tuple[int, int]:
    """Validate or auto-allocate free ports for FastAPI and Streamlit."""
    api_port = requested_api_port
    ui_port = requested_ui_port
    reserved: set[int] = set()

    if run_api:
        if not _is_port_free(api_port):
            if not auto_port:
                raise RuntimeError(
                    f"Port {api_port} required for FastAPI Backend is already in use. "
                    "Stop the conflicting process, set OPENUPSC_PORT, or pass --auto-port."
                )
            api_port = _find_free_port(api_port + 1, exclude=reserved)
            print(f"[PORT] Port {requested_api_port} busy; auto-selected port {api_port} for FastAPI Backend.")
        reserved.add(api_port)

    if run_ui:
        if ui_port in reserved or not _is_port_free(ui_port):
            if not auto_port:
                raise RuntimeError(
                    f"Port {ui_port} required for OpenUPSC Streamlit Main App is already in use. "
                    "Stop the conflicting process, set OPENUPSC_STREAMLIT_PORT, or pass --auto-port."
                )
            ui_port = _find_free_port(ui_port + 1, exclude=reserved)
            print(
                f"[PORT] Port {requested_ui_port} busy; auto-selected port {ui_port} for Streamlit Main App."
            )
        reserved.add(ui_port)

    return api_port, ui_port


def _print_banner(
    *,
    run_api: bool,
    run_ui: bool,
    api_port: int,
    ui_port: int,
    enable_reload: bool,
    max_restarts: int,
) -> None:
    print("\n" + "=" * 72)
    print("  OpenUPSC — Unbreakable Self-Healing Platform Supervisor")
    print("=" * 72)
    if run_ui:
        mode_note = "" if run_api else "  [Direct SQLite Fallback Mode]"
        print(f"  OpenUPSC Main App (Streamlit) : http://localhost:{ui_port}{mode_note}")
    if run_api:
        reload_note = " (reload=ON)" if enable_reload else " (stable mode)"
        print(f"  FastAPI Backend & REST API    : http://localhost:{api_port}{reload_note}")
        print(f"  FastAPI Swagger API Docs      : http://localhost:{api_port}/docs")
        print(f"  Health & System Diagnostics   : http://localhost:{api_port}/api/system/diagnostics")
    print(f"  Self-Healing Supervision      : Auto-restart up to {max_restarts}x (backoff 1-15s)")
    print("  Press Ctrl+C to shut down cleanly.")
    print("=" * 72 + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python run.py",
        description="Unbreakable self-healing launcher & supervisor for OpenUPSC (Streamlit Main App + FastAPI Backend).",
    )
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run pre-flight DB integrity, resource catalog validation, and 4-domain subagent diagnostics, then exit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit JSON output when used with --doctor.",
    )
    parser.add_argument(
        "--auto-port",
        action="store_true",
        help="Automatically select free ports if 8000/8501 are occupied and wire service URLs together.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--api-only",
        action="store_true",
        help="Run only the FastAPI backend server.",
    )
    mode_group.add_argument(
        "--ui-only",
        action="store_true",
        help="Run only the Streamlit Main App (works seamlessly via Direct SQLite Fallback).",
    )
    reload_group = parser.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable Uvicorn auto-reload on backend/ changes (development mode).",
    )
    reload_group.add_argument(
        "--no-reload",
        action="store_true",
        default=False,
        help="Disable Uvicorn auto-reload for maximum production stability (default).",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip the pre-flight atomic SQLite backup.",
    )
    parser.add_argument(
        "--max-restarts",
        type=int,
        default=5,
        help="Maximum automatic restarts per service within a 5-minute sliding window (default: 5).",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=int(os.environ.get("OPENUPSC_PORT", str(DEFAULT_API_PORT))),
        help=f"FastAPI backend port (default: env OPENUPSC_PORT or {DEFAULT_API_PORT}).",
    )
    parser.add_argument(
        "--ui-port",
        type=int,
        default=int(os.environ.get("OPENUPSC_STREAMLIT_PORT", str(DEFAULT_STREAMLIT_PORT))),
        help=f"Streamlit Main App port (default: env OPENUPSC_STREAMLIT_PORT or {DEFAULT_STREAMLIT_PORT}).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.max_restarts < 0:
        parser.error("--max-restarts must be >= 0.")

    if args.doctor:
        return run_doctor_mode(as_json=args.as_json)

    run_api = not args.ui_only
    run_ui = not args.api_only
    enable_reload = bool(args.reload and not args.no_reload)

    # 1. Pre-flight DB init, integrity audit, rolling backup, and catalog check
    try:
        run_preflight(skip_backup=args.no_backup)
    except Exception as exc:
        print(f"[ERROR] Pre-flight check failed: {exc}", file=sys.stderr)
        return 1

    # 2. Port validation / auto-selection
    try:
        api_port, ui_port = _resolve_ports(
            run_api=run_api,
            run_ui=run_ui,
            requested_api_port=args.api_port,
            requested_ui_port=args.ui_port,
            auto_port=args.auto_port,
        )
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    # 3. Cross-service environment wiring
    base_env = os.environ.copy()
    base_env["OPENUPSC_PORT"] = str(api_port)
    base_env["OPENUPSC_STREAMLIT_PORT"] = str(ui_port)
    base_env["OPENUPSC_STREAMLIT_URL"] = f"http://localhost:{ui_port}"
    if run_api:
        base_env["OPENUPSC_API_URL"] = f"http://127.0.0.1:{api_port}"
    else:
        # In --ui-only mode, preserve any explicitly supplied OPENUPSC_API_URL, else keep default
        base_env.setdefault("OPENUPSC_API_URL", f"http://127.0.0.1:{api_port}")

    python_exe = sys.executable
    services: list[ManagedService] = []

    if run_api:
        services.append(
            ManagedService(
                key="api",
                name="FastAPI Backend",
                command=_build_api_command(python_exe, api_port, enable_reload),
                env=base_env.copy(),
                cwd=ROOT,
                max_restarts=args.max_restarts,
            )
        )

    if run_ui:
        services.append(
            ManagedService(
                key="ui",
                name="Streamlit Main App",
                command=_build_streamlit_command(python_exe, ui_port),
                env=base_env.copy(),
                cwd=ROOT,
                max_restarts=args.max_restarts,
            )
        )

    _print_banner(
        run_api=run_api,
        run_ui=run_ui,
        api_port=api_port,
        ui_port=ui_port,
        enable_reload=enable_reload,
        max_restarts=args.max_restarts,
    )

    stop_requested = False

    def _request_shutdown(signum: int, _frame: Any) -> None:
        nonlocal stop_requested
        if not stop_requested:
            sig_name = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else str(signum)
            print(f"\n[SUPERVISOR] Received {sig_name}; shutting down OpenUPSC services cleanly...")
        stop_requested = True

    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    # 4. Initial service startup (start FastAPI first so Streamlit sees live API immediately)
    try:
        for svc in services:
            if stop_requested:
                break
            svc.start()
            if svc.key == "api" and run_ui:
                ready = _wait_for_http(f"http://127.0.0.1:{api_port}/api/health", timeout_s=8.0)
                if not ready and not stop_requested:
                    print(
                        "[WARN] FastAPI health endpoint took longer than expected; "
                        "starting Streamlit Main App (Direct SQLite Fallback keeps UI live)..."
                    )

        # 5. Self-healing supervision loop
        exit_code = 0
        while not stop_requested:
            now = time.monotonic()

            for svc in services:
                if svc.exhausted:
                    continue

                if svc.proc is not None:
                    rc = svc.poll()
                    if rc is not None:
                        peer_running = any(other is not svc and other.is_running() for other in services)
                        svc.schedule_restart(rc, peer_running=peer_running)
                elif svc.next_restart_at is not None and now >= svc.next_restart_at:
                    print(f"[SUPERVISOR] Restarting {svc.name}...")
                    svc.start()

            if all(svc.exhausted for svc in services):
                print(
                    "[FATAL] All supervised OpenUPSC services exhausted their restart budget. Exiting.",
                    file=sys.stderr,
                )
                exit_code = 1
                break

            time.sleep(POLL_INTERVAL_SECONDS)

        return exit_code
    except KeyboardInterrupt:
        print("\n[SUPERVISOR] KeyboardInterrupt received; shutting down cleanly...")
        return 0
    finally:
        # Shut down UI first, then Backend, using process-group termination
        for svc in reversed(services):
            svc.terminate_gracefully(timeout_s=5.0)
        print("[SUPERVISOR] All OpenUPSC child processes terminated cleanly.")


if __name__ == "__main__":
    raise SystemExit(main())
