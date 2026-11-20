"""Independent, fault-tolerant health diagnostics for all 4 OpenUPSC subagent domains.

Each domain probe imports target modules lazily inside try/except blocks so an issue or
in-progress edit in one domain never prevents diagnosing the other three.

CLI Usage:
    .venv/bin/python -m subagents.doctor --domain all
    .venv/bin/python -m subagents.doctor --domain system --json
    .venv/bin/python -m subagents.doctor --domain backend --strict
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sqlite3
import sys
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from subagents.registry import CANONICAL_DOMAINS, check_ownership_boundaries  # noqa: E402

CORE_DATA_JSON_FILES: tuple[str, ...] = (
    "resources.json",
    "ncert.json",
    "roadmaps.json",
    "pyqs.json",
    "question_papers.json",
    "current_affairs.json",
)

CORE_BACKEND_ROUTES: tuple[str, ...] = (
    "/api/health",
    "/api/auth/login",
    "/api/workspace",
    "/api/resources",
    "/api/ncert",
    "/api/pyqs",
    "/api/roadmaps",
    "/api/analytics/overview",
)

EXPECTED_SUBAGENT_MANIFESTS: tuple[str, ...] = (
    "resource-agent.md",
    "backend-agent.md",
    "frontend-agent.md",
    "system-agent.md",
)

EXPECTED_SKILLS: tuple[str, ...] = (
    "openupsc-resource-ops",
    "openupsc-backend-ops",
    "openupsc-frontend-streamlit",
    "openupsc-system-ops",
)

_HTTP_URL_RE = re.compile(r"https?://[^\s<>)\"']+")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_check(
    name: str,
    status: str,
    detail: str,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if status not in ("ok", "warn", "fail"):
        raise ValueError(f"Invalid check status: {status!r}")
    entry: dict[str, Any] = {
        "name": name,
        "status": status,
        "detail": detail,
    }
    if metrics is not None:
        entry["metrics"] = metrics
    return entry


def _build_domain_report(
    domain: str,
    checks: list[dict[str, Any]],
    started_at: float,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ok_count = sum(1 for c in checks if c["status"] == "ok")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    fail_count = sum(1 for c in checks if c["status"] == "fail")

    if fail_count > 0:
        status = "error"
    elif warn_count > 0:
        status = "degraded"
    else:
        status = "healthy"

    return {
        "domain": domain,
        "status": status,
        "checked_at": _utc_now(),
        "duration_ms": round((time.perf_counter() - started_at) * 1000.0, 2),
        "checks": checks,
        "summary": {
            "total": len(checks),
            "ok": ok_count,
            "warn": warn_count,
            "fail": fail_count,
        },
        "metrics": metrics or {},
    }


def _compile_python_file(path: Path) -> tuple[bool, str]:
    """Syntax-check a Python file in memory without writing bytecode artifacts."""
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        return True, "ok"
    except SyntaxError as exc:
        return False, f"SyntaxError at line {exc.lineno}: {exc.msg}"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _parse_yaml_frontmatter(text: str) -> dict[str, str]:
    """Minimal stdlib parser for simple YAML frontmatter (key: value) in SKILL.md files."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return meta
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return {}


# ---------------------------------------------------------------------------
# 1. Resource Domain Probe
# ---------------------------------------------------------------------------
def probe_resource() -> dict[str, Any]:
    """Audit UPSC_FREE_RESOURCES_MASTER.md, backend/data/*.json, and backend.resource_engine."""
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    domain_metrics: dict[str, Any] = {}

    # Check 1: Master Markdown guide
    master_md = REPO_ROOT / "UPSC_FREE_RESOURCES_MASTER.md"
    try:
        if not master_md.exists():
            checks.append(_make_check("master_markdown", "fail", "UPSC_FREE_RESOURCES_MASTER.md is missing."))
        else:
            content = master_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            urls = _HTTP_URL_RE.findall(content)
            parts = re.findall(r"^##\s+Part\s+\d+", content, flags=re.MULTILINE)
            if not content.strip() or not urls:
                checks.append(
                    _make_check(
                        "master_markdown",
                        "fail",
                        "UPSC_FREE_RESOURCES_MASTER.md is empty or contains no HTTP(S) links.",
                        {"lines": len(lines), "urls": len(urls), "parts": len(parts)},
                    )
                )
            else:
                checks.append(
                    _make_check(
                        "master_markdown",
                        "ok",
                        f"Present and readable ({len(lines)} lines, {len(parts)} parts, {len(urls)} links).",
                        {"lines": len(lines), "parts": len(parts), "urls": len(urls)},
                    )
                )
                domain_metrics["master_markdown_urls"] = len(urls)
    except Exception as exc:
        checks.append(_make_check("master_markdown", "fail", f"Failed reading master guide: {exc}"))

    # Check 2: All backend/data/*.json files exist and parse cleanly
    data_dir = REPO_ROOT / "backend" / "data"
    parsed_counts: dict[str, int] = {}
    parse_errors: list[str] = []
    missing_core: list[str] = []
    resources_payload: list[dict[str, Any]] | None = None

    try:
        if not data_dir.is_dir():
            checks.append(_make_check("curriculum_json_files", "fail", "backend/data/ directory is missing."))
        else:
            found_json = sorted(p.name for p in data_dir.glob("*.json"))
            for fname in CORE_DATA_JSON_FILES:
                if fname not in found_json:
                    missing_core.append(fname)

            for fname in found_json:
                fpath = data_dir / fname
                try:
                    payload = json.loads(fpath.read_text(encoding="utf-8"))
                    if isinstance(payload, list):
                        parsed_counts[fname] = len(payload)
                        if fname == "resources.json":
                            resources_payload = payload
                    elif isinstance(payload, dict):
                        parsed_counts[fname] = len(payload)
                    else:
                        parse_errors.append(f"{fname}: unexpected JSON root type {type(payload).__name__}")
                except Exception as exc:
                    parse_errors.append(f"{fname}: {type(exc).__name__}: {exc}")

            if missing_core or parse_errors:
                detail_parts = []
                if missing_core:
                    detail_parts.append(f"missing core JSONs: {', '.join(missing_core)}")
                if parse_errors:
                    detail_parts.append(f"parse errors: {'; '.join(parse_errors)}")
                checks.append(
                    _make_check(
                        "curriculum_json_files",
                        "fail",
                        "; ".join(detail_parts),
                        {
                            "parsed_counts": parsed_counts,
                            "missing_core": missing_core,
                            "parse_errors": parse_errors,
                        },
                    )
                )
            else:
                checks.append(
                    _make_check(
                        "curriculum_json_files",
                        "ok",
                        f"All {len(parsed_counts)} JSON files under backend/data/ parsed cleanly.",
                        {"parsed_counts": parsed_counts},
                    )
                )
                domain_metrics["json_files"] = parsed_counts
    except Exception as exc:
        checks.append(_make_check("curriculum_json_files", "fail", f"Error scanning backend/data/: {exc}"))

    # Check 3: Direct resources.json schema & URL hygiene
    if resources_payload is not None:
        seen_ids: set[str] = set()
        duplicate_ids: list[str] = []
        invalid_urls: list[str] = []
        missing_titles: int = 0

        for idx, item in enumerate(resources_payload):
            if not isinstance(item, dict):
                invalid_urls.append(f"index:{idx}:not-a-dict")
                continue
            rid = str(item.get("id") or "").strip()
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            if not rid:
                duplicate_ids.append(f"index:{idx}:missing-id")
            elif rid in seen_ids:
                duplicate_ids.append(rid)
            else:
                seen_ids.add(rid)
            if not title:
                missing_titles += 1
            if not (url.startswith("https://") or url.startswith("http://")):
                invalid_urls.append(rid or f"index:{idx}")

        if duplicate_ids or invalid_urls or missing_titles:
            checks.append(
                _make_check(
                    "resources_catalog_hygiene",
                    "fail",
                    (
                        f"Catalog hygiene issues: {len(duplicate_ids)} duplicate/missing IDs, "
                        f"{len(invalid_urls)} invalid URLs, {missing_titles} blank titles."
                    ),
                    {
                        "total": len(resources_payload),
                        "duplicate_ids": duplicate_ids[:10],
                        "invalid_urls": invalid_urls[:10],
                        "missing_titles": missing_titles,
                    },
                )
            )
        else:
            checks.append(
                _make_check(
                    "resources_catalog_hygiene",
                    "ok",
                    f"{len(resources_payload)} resources verified with unique IDs, titles, and valid HTTP(S) URLs.",
                    {"total": len(resources_payload)},
                )
            )
            domain_metrics["resource_count"] = len(resources_payload)

    # Check 4: Lazy import of backend.resource_engine & validate_catalog()
    engine_file = REPO_ROOT / "backend" / "resource_engine.py"
    if not engine_file.exists():
        checks.append(
            _make_check(
                "resource_engine_validate_catalog",
                "warn",
                "backend/resource_engine.py not present yet.",
                {"exists": False},
            )
        )
    else:
        try:
            engine_mod = importlib.import_module("backend.resource_engine")
            validate_fn = getattr(engine_mod, "validate_catalog", None)
            if not callable(validate_fn):
                checks.append(
                    _make_check(
                        "resource_engine_validate_catalog",
                        "warn",
                        "backend.resource_engine imported, but validate_catalog() callable is missing.",
                        {"exists": True, "has_validate_catalog": False},
                    )
                )
            else:
                result = validate_fn()
                if isinstance(result, bool):
                    st = "ok" if result else "fail"
                    checks.append(
                        _make_check(
                            "resource_engine_validate_catalog",
                            st,
                            f"validate_catalog() returned {result}.",
                            {"result": result},
                        )
                    )
                elif isinstance(result, dict):
                    raw_errors = result.get("errors") or result.get("issues") or result.get("broken_links") or []
                    raw_warnings = result.get("warnings") or []
                    explicit_ok = result.get("ok")
                    if explicit_ok is None and "valid" in result:
                        explicit_ok = result.get("valid")
                    status_str = str(result.get("status", "")).lower()

                    if explicit_ok is False or status_str in ("error", "fail", "invalid") or (
                        isinstance(raw_errors, list) and len(raw_errors) > 0
                    ):
                        checks.append(
                            _make_check(
                                "resource_engine_validate_catalog",
                                "fail",
                                f"validate_catalog() reported errors ({len(raw_errors) if isinstance(raw_errors, list) else raw_errors}).",
                                {"catalog_report": result},
                            )
                        )
                    elif status_str in ("degraded", "warn", "warning") or (
                        isinstance(raw_warnings, list) and len(raw_warnings) > 0
                    ):
                        checks.append(
                            _make_check(
                                "resource_engine_validate_catalog",
                                "warn",
                                f"validate_catalog() succeeded with {len(raw_warnings)} warning(s).",
                                {"catalog_report": result},
                            )
                        )
                    else:
                        checks.append(
                            _make_check(
                                "resource_engine_validate_catalog",
                                "ok",
                                "backend.resource_engine.validate_catalog() passed cleanly.",
                                {"catalog_report": result},
                            )
                        )
                else:
                    checks.append(
                        _make_check(
                            "resource_engine_validate_catalog",
                            "ok",
                            f"validate_catalog() executed (returned {type(result).__name__}).",
                        )
                    )
        except Exception as exc:
            checks.append(
                _make_check(
                    "resource_engine_validate_catalog",
                    "fail",
                    f"backend.resource_engine failed: {type(exc).__name__}: {exc}",
                )
            )

    return _build_domain_report("resource", checks, started, domain_metrics)


# ---------------------------------------------------------------------------
# 2. Backend Domain Probe
# ---------------------------------------------------------------------------
def probe_backend() -> dict[str, Any]:
    """Audit backend modules, SQLite DB integrity, FastAPI routes, and live API reachability."""
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    domain_metrics: dict[str, Any] = {}

    imported: dict[str, Any] = {}
    import_failures: dict[str, str] = {}

    # Check 1: Lazy imports of core backend modules
    for mod_name in ("backend.auth", "backend.models", "backend.database", "backend.main"):
        try:
            imported[mod_name] = importlib.import_module(mod_name)
        except Exception as exc:
            import_failures[mod_name] = f"{type(exc).__name__}: {exc}"

    if import_failures:
        checks.append(
            _make_check(
                "backend_module_imports",
                "fail",
                f"Failed to import: {', '.join(import_failures.keys())}",
                {"loaded": sorted(imported.keys()), "failures": import_failures},
            )
        )
    else:
        checks.append(
            _make_check(
                "backend_module_imports",
                "ok",
                "All core backend modules imported cleanly (auth, models, database, main).",
                {"loaded": sorted(imported.keys())},
            )
        )

    # Check 2: SQLite DB integrity (prefers backend.database.check_db_integrity() if present)
    db_mod = imported.get("backend.database")
    try:
        if db_mod is not None and callable(getattr(db_mod, "get_db_path", None)):
            db_path = Path(db_mod.get_db_path())
        else:
            env_db = os.environ.get("OPENUPSC_DB_PATH")
            db_path = Path(env_db) if env_db else (REPO_ROOT / "data" / "openupsc.db")

        check_fn = getattr(db_mod, "check_db_integrity", None) if db_mod is not None else None

        if not db_path.exists():
            checks.append(
                _make_check(
                    "sqlite_db_integrity",
                    "warn",
                    f"Database file does not exist yet at {db_path} (will initialize on first run).",
                    {"db_path": str(db_path), "exists": False},
                )
            )
        elif callable(check_fn):
            result = check_fn()
            if isinstance(result, bool):
                ok = result
                detail = "check_db_integrity() passed." if ok else "check_db_integrity() returned False."
                metrics = {"db_path": str(db_path), "method": "backend.database.check_db_integrity", "result": result}
            elif isinstance(result, dict):
                raw_ok = result.get("ok")
                if raw_ok is None and "healthy" in result:
                    raw_ok = result.get("healthy")
                if raw_ok is None and "integrity" in result:
                    raw_ok = str(result.get("integrity")).lower() == "ok"
                if raw_ok is None and "status" in result:
                    raw_ok = str(result.get("status")).lower() in ("ok", "healthy")
                ok = bool(raw_ok)
                detail = (
                    "SQLite integrity verified via backend.database.check_db_integrity()."
                    if ok
                    else f"check_db_integrity() reported failure: {result}"
                )
                metrics = {"db_path": str(db_path), "method": "backend.database.check_db_integrity", "report": result}
            else:
                ok = str(result).strip().lower() == "ok"
                detail = f"check_db_integrity() returned {result!r}."
                metrics = {"db_path": str(db_path), "method": "backend.database.check_db_integrity", "result": str(result)}

            checks.append(_make_check("sqlite_db_integrity", "ok" if ok else "fail", detail, metrics))
            domain_metrics["db_path"] = str(db_path)
        else:
            # Read-only direct SQLite PRAGMA integrity_check fallback (never mutates DB)
            uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=3.0)
            try:
                rows = conn.execute("PRAGMA integrity_check;").fetchall()
                tables = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
                    ).fetchall()
                ]
            finally:
                conn.close()
            integrity_ok = rows == [("ok",)]
            checks.append(
                _make_check(
                    "sqlite_db_integrity",
                    "ok" if integrity_ok else "fail",
                    (
                        f"PRAGMA integrity_check passed ({len(tables)} tables, read-only probe)."
                        if integrity_ok
                        else f"PRAGMA integrity_check failed: {rows}"
                    ),
                    {
                        "db_path": str(db_path),
                        "method": "sqlite3_pragma_readonly",
                        "table_count": len(tables),
                        "tables": tables,
                    },
                )
            )
            domain_metrics["db_path"] = str(db_path)
            domain_metrics["table_count"] = len(tables)
    except Exception as exc:
        checks.append(_make_check("sqlite_db_integrity", "fail", f"DB integrity probe failed: {type(exc).__name__}: {exc}"))

    # Check 3: FastAPI routes registered
    main_mod = imported.get("backend.main")
    if main_mod is None:
        checks.append(_make_check("fastapi_routes", "fail", "Skipped because backend.main failed to import."))
    else:
        try:
            app = getattr(main_mod, "app", None)
            if app is None or not hasattr(app, "routes"):
                checks.append(_make_check("fastapi_routes", "fail", "backend.main.app is missing or invalid."))
            else:
                route_paths = {getattr(r, "path", "") for r in app.routes if getattr(r, "path", "")}
                api_routes = sorted(p for p in route_paths if p.startswith("/api/"))
                missing_core = [r for r in CORE_BACKEND_ROUTES if r not in route_paths]
                system_routes = sorted(p for p in api_routes if p.startswith("/api/system"))
                if missing_core:
                    checks.append(
                        _make_check(
                            "fastapi_routes",
                            "fail",
                            f"Missing core FastAPI routes: {', '.join(missing_core)}",
                            {"api_route_count": len(api_routes), "missing_core": missing_core},
                        )
                    )
                else:
                    checks.append(
                        _make_check(
                            "fastapi_routes",
                            "ok",
                            f"{len(api_routes)} /api/* routes registered (all {len(CORE_BACKEND_ROUTES)} core routes verified).",
                            {
                                "api_route_count": len(api_routes),
                                "total_routes": len(app.routes),
                                "system_routes": system_routes,
                            },
                        )
                    )
                    domain_metrics["api_route_count"] = len(api_routes)
        except Exception as exc:
            checks.append(_make_check("fastapi_routes", "fail", f"Failed inspecting FastAPI routes: {exc}"))

    # Check 4: Live FastAPI health endpoint (reports live vs offline cleanly without failing if stopped)
    api_base = os.environ.get("OPENUPSC_API_URL")
    if not api_base:
        port = os.environ.get("OPENUPSC_PORT", "8000")
        api_base = f"http://127.0.0.1:{port}"
    health_url = f"{api_base.rstrip('/')}/api/health"

    try:
        req = Request(health_url, headers={"Accept": "application/json"})
        host = (urlparse(health_url).hostname or "").lower()
        opener = build_opener(ProxyHandler({})) if host in ("127.0.0.1", "localhost", "::1") else None
        open_fn = opener.open if opener is not None else urlopen
        with open_fn(req, timeout=1.0) as resp:
            status_code = getattr(resp, "status", 200)
            raw_body = resp.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw_body)
            except Exception:
                payload = raw_body[:200]
            if status_code == 200:
                checks.append(
                    _make_check(
                        "live_api_health",
                        "ok",
                        f"FastAPI server is LIVE at {health_url} (HTTP 200).",
                        {"live": True, "url": health_url, "status_code": status_code, "payload": payload},
                    )
                )
            else:
                checks.append(
                    _make_check(
                        "live_api_health",
                        "warn",
                        f"FastAPI server at {health_url} returned HTTP {status_code}.",
                        {"live": True, "url": health_url, "status_code": status_code},
                    )
                )
            domain_metrics["api_live"] = True
    except HTTPError as exc:
        checks.append(
            _make_check(
                "live_api_health",
                "warn",
                f"FastAPI server responded with HTTP {exc.code} at {health_url}.",
                {"live": True, "url": health_url, "status_code": exc.code},
            )
        )
        domain_metrics["api_live"] = True
    except (URLError, TimeoutError, OSError):
        checks.append(
            _make_check(
                "live_api_health",
                "ok",
                f"FastAPI server is currently offline ({health_url} not listening).",
                {"live": False, "url": health_url},
            )
        )
        domain_metrics["api_live"] = False
    except Exception as exc:
        checks.append(
            _make_check(
                "live_api_health",
                "warn",
                f"Unexpected error probing live API at {health_url}: {type(exc).__name__}: {exc}",
                {"live": False, "url": health_url},
            )
        )
        domain_metrics["api_live"] = False

    return _build_domain_report("backend", checks, started, domain_metrics)


# ---------------------------------------------------------------------------
# 3. Frontend Domain Probe
# ---------------------------------------------------------------------------
def probe_frontend() -> dict[str, Any]:
    """Audit .streamlit/config.toml, streamlit_app modules/syntax, and UI dependencies."""
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    domain_metrics: dict[str, Any] = {}

    # Check 1: .streamlit/config.toml
    config_path = REPO_ROOT / ".streamlit" / "config.toml"
    try:
        if not config_path.exists():
            checks.append(_make_check("streamlit_config", "fail", ".streamlit/config.toml is missing."))
        else:
            parsed_cfg = tomllib.loads(config_path.read_text(encoding="utf-8"))
            checks.append(
                _make_check(
                    "streamlit_config",
                    "ok",
                    ".streamlit/config.toml parsed cleanly.",
                    {
                        "sections": sorted(parsed_cfg.keys()),
                        "port": parsed_cfg.get("server", {}).get("port"),
                        "headless": parsed_cfg.get("server", {}).get("headless"),
                    },
                )
            )
    except Exception as exc:
        checks.append(_make_check("streamlit_config", "fail", f"Invalid .streamlit/config.toml: {exc}"))

    # Check 2: Core UI Python packages (streamlit, pandas, plotly)
    pkg_versions: dict[str, str] = {}
    pkg_failures: dict[str, str] = {}
    for pkg in ("streamlit", "pandas", "plotly"):
        try:
            mod = importlib.import_module(pkg)
            pkg_versions[pkg] = getattr(mod, "__version__", "unknown")
        except Exception as exc:
            pkg_failures[pkg] = f"{type(exc).__name__}: {exc}"

    if pkg_failures:
        checks.append(
            _make_check(
                "frontend_dependencies",
                "fail",
                f"Failed to import required UI packages: {', '.join(pkg_failures.keys())}",
                {"versions": pkg_versions, "failures": pkg_failures},
            )
        )
    else:
        checks.append(
            _make_check(
                "frontend_dependencies",
                "ok",
                "Required UI packages available: " + ", ".join(f"{k}=={v}" for k, v in pkg_versions.items()),
                {"versions": pkg_versions},
            )
        )
        domain_metrics["packages"] = pkg_versions

    # Check 3: Streamlit module layout (app.py, dashboard.py, client.py, theme.py)
    st_dir = REPO_ROOT / "streamlit_app"
    expected_files = ("app.py", "dashboard.py", "client.py", "theme.py")
    present_files = [f for f in expected_files if (st_dir / f).is_file()]
    missing_files = [f for f in expected_files if f not in present_files]
    views_dir = st_dir / "views"
    view_files = sorted(p.name for p in views_dir.glob("*.py")) if views_dir.is_dir() else []

    if "app.py" not in present_files and "dashboard.py" not in present_files:
        checks.append(
            _make_check(
                "streamlit_modules",
                "fail",
                "Neither streamlit_app/app.py nor streamlit_app/dashboard.py exists.",
                {"present": present_files, "missing": missing_files},
            )
        )
    elif missing_files:
        checks.append(
            _make_check(
                "streamlit_modules",
                "warn",
                f"Fallback entrypoint present, but modular files not yet created: {', '.join(missing_files)}",
                {"present": present_files, "missing": missing_files, "views": view_files},
            )
        )
    else:
        checks.append(
            _make_check(
                "streamlit_modules",
                "ok",
                f"All 4 core Streamlit modules present ({len(view_files)} view module(s) in streamlit_app/views/).",
                {"present": present_files, "views": view_files},
            )
        )

    # Check 4: Syntax-compile all .py files under streamlit_app/
    if not st_dir.is_dir():
        checks.append(_make_check("streamlit_syntax_compile", "fail", "streamlit_app/ directory is missing."))
    else:
        py_files = sorted(
            p for p in st_dir.rglob("*.py") if "__pycache__" not in p.parts
        )
        syntax_errors: dict[str, str] = {}
        for py_file in py_files:
            ok, msg = _compile_python_file(py_file)
            if not ok:
                syntax_errors[py_file.relative_to(REPO_ROOT).as_posix()] = msg

        if not py_files:
            checks.append(_make_check("streamlit_syntax_compile", "fail", "No .py files found in streamlit_app/."))
        elif syntax_errors:
            checks.append(
                _make_check(
                    "streamlit_syntax_compile",
                    "fail",
                    f"Syntax error in {len(syntax_errors)}/{len(py_files)} Streamlit file(s).",
                    {"compiled": len(py_files) - len(syntax_errors), "total": len(py_files), "errors": syntax_errors},
                )
            )
        else:
            checks.append(
                _make_check(
                    "streamlit_syntax_compile",
                    "ok",
                    f"All {len(py_files)} Python file(s) under streamlit_app/ compiled with zero syntax errors.",
                    {
                        "total": len(py_files),
                        "files": [p.relative_to(REPO_ROOT).as_posix() for p in py_files],
                    },
                )
            )
            domain_metrics["streamlit_py_files"] = len(py_files)

    # Check 5: Companion static web frontend presence
    static_index = REPO_ROOT / "frontend" / "index.html"
    if static_index.is_file():
        checks.append(
            _make_check(
                "companion_static_frontend",
                "ok",
                "Companion static web app frontend/index.html is present.",
                {"path": "frontend/index.html"},
            )
        )
    else:
        checks.append(
            _make_check(
                "companion_static_frontend",
                "warn",
                "Companion static web app frontend/index.html not found.",
            )
        )

    return _build_domain_report("frontend", checks, started, domain_metrics)


# ---------------------------------------------------------------------------
# 4. System Domain Probe
# ---------------------------------------------------------------------------
def probe_system() -> dict[str, Any]:
    """Audit Python runtime, run.py, governance docs, ownership boundaries, backups, and tests/."""
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    domain_metrics: dict[str, Any] = {}

    # Check 1: Python runtime version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        checks.append(
            _make_check(
                "python_runtime",
                "ok",
                f"Python {py_ver} ({sys.executable}).",
                {"version": py_ver, "executable": sys.executable},
            )
        )
    else:
        checks.append(
            _make_check(
                "python_runtime",
                "fail",
                f"Python {py_ver} is below required 3.10+.",
                {"version": py_ver, "executable": sys.executable},
            )
        )
    domain_metrics["python_version"] = py_ver

    # Check 2: run.py presence & syntax
    run_py = REPO_ROOT / "run.py"
    if not run_py.is_file():
        checks.append(_make_check("run_py_syntax", "fail", "run.py is missing."))
    else:
        ok, msg = _compile_python_file(run_py)
        checks.append(
            _make_check(
                "run_py_syntax",
                "ok" if ok else "fail",
                "run.py exists and compiles cleanly." if ok else f"run.py syntax check failed: {msg}",
                {"path": "run.py"},
            )
        )

    # Check 3: AGENTS.md completeness
    agents_md = REPO_ROOT / "AGENTS.md"
    if not agents_md.is_file():
        checks.append(_make_check("agents_md", "fail", "AGENTS.md is missing at repo root."))
    else:
        text = agents_md.read_text(encoding="utf-8")
        expected_ids = ("resource_agent", "backend_agent", "frontend_agent", "system_agent")
        missing_ids = [aid for aid in expected_ids if aid not in text]
        if missing_ids:
            checks.append(
                _make_check(
                    "agents_md",
                    "fail",
                    f"AGENTS.md is missing references to: {', '.join(missing_ids)}",
                    {"missing_agent_ids": missing_ids},
                )
            )
        else:
            checks.append(
                _make_check(
                    "agents_md",
                    "ok",
                    f"AGENTS.md present and documents all 4 subagents ({len(text.splitlines())} lines).",
                    {"lines": len(text.splitlines())},
                )
            )

    # Check 4: .agents/subagents/*.md completeness
    subagents_dir = REPO_ROOT / ".agents" / "subagents"
    missing_manifests: list[str] = []
    empty_manifests: list[str] = []
    for fname in EXPECTED_SUBAGENT_MANIFESTS:
        fpath = subagents_dir / fname
        if not fpath.is_file():
            missing_manifests.append(fname)
        elif not fpath.read_text(encoding="utf-8").strip():
            empty_manifests.append(fname)

    if missing_manifests or empty_manifests:
        checks.append(
            _make_check(
                "subagent_manifests",
                "fail",
                f"Incomplete .agents/subagents/: missing={missing_manifests}, empty={empty_manifests}",
                {"missing": missing_manifests, "empty": empty_manifests},
            )
        )
    else:
        checks.append(
            _make_check(
                "subagent_manifests",
                "ok",
                f"All {len(EXPECTED_SUBAGENT_MANIFESTS)} subagent manifests present in .agents/subagents/.",
                {"manifests": list(EXPECTED_SUBAGENT_MANIFESTS)},
            )
        )

    # Check 5: .agents/skills/*/SKILL.md completeness & frontmatter validation
    skills_dir = REPO_ROOT / ".agents" / "skills"
    missing_skills: list[str] = []
    invalid_frontmatter: list[str] = []
    for skill_name in EXPECTED_SKILLS:
        skill_file = skills_dir / skill_name / "SKILL.md"
        if not skill_file.is_file():
            missing_skills.append(skill_name)
            continue
        meta = _parse_yaml_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not meta.get("name") or not meta.get("description"):
            invalid_frontmatter.append(skill_name)

    if missing_skills or invalid_frontmatter:
        checks.append(
            _make_check(
                "workspace_skills",
                "fail",
                f"Incomplete .agents/skills/: missing={missing_skills}, invalid_frontmatter={invalid_frontmatter}",
                {"missing": missing_skills, "invalid_frontmatter": invalid_frontmatter},
            )
        )
    else:
        checks.append(
            _make_check(
                "workspace_skills",
                "ok",
                f"All {len(EXPECTED_SKILLS)} workspace skills present with valid YAML frontmatter.",
                {"skills": list(EXPECTED_SKILLS)},
            )
        )

    # Check 6: Ownership boundaries via subagents.registry
    try:
        boundary_report = check_ownership_boundaries(REPO_ROOT)
        domain_metrics["ownership_resolved_files"] = boundary_report["total_resolved_files"]
        if not boundary_report["ok"]:
            checks.append(
                _make_check(
                    "ownership_boundaries",
                    "fail",
                    f"Detected {len(boundary_report['overlaps'])} ownership overlap(s) across subagents.",
                    boundary_report,
                )
            )
        else:
            missing_map = boundary_report["missing_paths"]
            system_core_missing = [p for p in missing_map.get("system", []) if p.rstrip("/") != "tests"]
            if system_core_missing:
                checks.append(
                    _make_check(
                        "ownership_boundaries",
                        "fail",
                        f"Zero overlaps, but core system paths are missing: {', '.join(system_core_missing)}",
                        boundary_report,
                    )
                )
            else:
                missing_note = (
                    f" ({sum(len(v) for v in missing_map.values())} pending path(s) across domains)"
                    if missing_map
                    else " (all declared paths exist on disk)"
                )
                checks.append(
                    _make_check(
                        "ownership_boundaries",
                        "ok",
                        f"Strict non-overlapping ownership verified across all 4 domains{missing_note}.",
                        {
                            "overlaps": 0,
                            "all_paths_exist": boundary_report["all_paths_exist"],
                            "missing_paths": missing_map,
                            "total_resolved_files": boundary_report["total_resolved_files"],
                        },
                    )
                )
    except Exception as exc:
        checks.append(_make_check("ownership_boundaries", "fail", f"Boundary audit raised {type(exc).__name__}: {exc}"))

    # Check 7: Backup directory readiness (read-only check; does not mutate disk)
    data_dir = REPO_ROOT / "data"
    backups_dir = data_dir / "backups"
    if backups_dir.exists():
        if not backups_dir.is_dir():
            checks.append(
                _make_check(
                    "backup_directory_readiness",
                    "fail",
                    "data/backups exists but is not a directory.",
                )
            )
        elif not os.access(backups_dir, os.W_OK):
            checks.append(
                _make_check(
                    "backup_directory_readiness",
                    "fail",
                    "data/backups directory is not writable.",
                )
            )
        else:
            backup_files = sorted(p.name for p in backups_dir.glob("*.db"))
            checks.append(
                _make_check(
                    "backup_directory_readiness",
                    "ok",
                    f"data/backups/ exists and is writable ({len(backup_files)} backup file(s)).",
                    {"exists": True, "writable": True, "backup_count": len(backup_files)},
                )
            )
    elif data_dir.is_dir() and os.access(data_dir, os.W_OK):
        checks.append(
            _make_check(
                "backup_directory_readiness",
                "ok",
                "data/ is writable; data/backups/ is ready to be created automatically on first backup.",
                {"exists": False, "parent_writable": True},
            )
        )
    elif os.access(REPO_ROOT, os.W_OK):
        checks.append(
            _make_check(
                "backup_directory_readiness",
                "warn",
                "data/ directory does not exist yet (workspace root is writable).",
                {"exists": False, "root_writable": True},
            )
        )
    else:
        checks.append(
            _make_check(
                "backup_directory_readiness",
                "fail",
                "Neither data/backups/ nor data/ is writable for rolling backups.",
            )
        )

    # Check 8: tests/ suite presence & syntax
    tests_dir = REPO_ROOT / "tests"
    if not tests_dir.is_dir():
        checks.append(
            _make_check(
                "tests_suite",
                "warn",
                "tests/ directory not yet created (scheduled for Phase 2 test suite).",
                {"exists": False, "test_files": []},
            )
        )
    else:
        test_files = sorted(p for p in tests_dir.glob("test_*.py") if p.is_file())
        if not test_files:
            checks.append(
                _make_check(
                    "tests_suite",
                    "warn",
                    "tests/ directory exists but contains no test_*.py files yet.",
                    {"exists": True, "test_files": []},
                )
            )
        else:
            syntax_errors: dict[str, str] = {}
            for tf in test_files:
                ok, msg = _compile_python_file(tf)
                if not ok:
                    syntax_errors[tf.name] = msg
            if syntax_errors:
                checks.append(
                    _make_check(
                        "tests_suite",
                        "fail",
                        f"Syntax errors in test files: {', '.join(syntax_errors.keys())}",
                        {"test_files": [p.name for p in test_files], "errors": syntax_errors},
                    )
                )
            else:
                checks.append(
                    _make_check(
                        "tests_suite",
                        "ok",
                        f"{len(test_files)} test module(s) present and compile cleanly.",
                        {"test_files": [p.name for p in test_files]},
                    )
                )
                domain_metrics["test_file_count"] = len(test_files)

    return _build_domain_report("system", checks, started, domain_metrics)


# ---------------------------------------------------------------------------
# Aggregated Diagnostics & CLI
# ---------------------------------------------------------------------------
DOMAIN_PROBES: dict[str, Callable[[], dict[str, Any]]] = {
    "resource": probe_resource,
    "backend": probe_backend,
    "frontend": probe_frontend,
    "system": probe_system,
}


def run_diagnostics(domain: str = "all") -> dict[str, Any]:
    """Run independent health probes for one domain or all 4 domains.

    Returns:
        {
            "status": "healthy" | "degraded" | "error",
            "checked_at": ISO-8601 UTC timestamp,
            "domains": {domain: report, ...},
            "summary": {...},
        }
    """
    normalized = (domain or "all").strip().lower()
    if normalized != "all" and normalized not in DOMAIN_PROBES:
        valid = ", ".join(("all",) + CANONICAL_DOMAINS)
        raise ValueError(f"Unknown diagnostics domain {domain!r}. Choose one of: {valid}")

    selected = list(CANONICAL_DOMAINS) if normalized == "all" else [normalized]
    started = time.perf_counter()
    checked_at = _utc_now()
    domains_report: dict[str, dict[str, Any]] = {}

    for dom in selected:
        probe_started = time.perf_counter()
        try:
            domains_report[dom] = DOMAIN_PROBES[dom]()
        except Exception as exc:
            domains_report[dom] = _build_domain_report(
                dom,
                [
                    _make_check(
                        "probe_execution",
                        "fail",
                        f"Unhandled exception inside probe_{dom}: {type(exc).__name__}: {exc}",
                    )
                ],
                probe_started,
            )

    statuses = [rep["status"] for rep in domains_report.values()]
    if "error" in statuses:
        overall_status = "error"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    total_checks = sum(rep["summary"]["total"] for rep in domains_report.values())
    ok_checks = sum(rep["summary"]["ok"] for rep in domains_report.values())
    warn_checks = sum(rep["summary"]["warn"] for rep in domains_report.values())
    fail_checks = sum(rep["summary"]["fail"] for rep in domains_report.values())

    return {
        "status": overall_status,
        "checked_at": checked_at,
        "domains": domains_report,
        "summary": {
            "requested_domain": normalized,
            "domains_checked": len(selected),
            "healthy_domains": [d for d, r in domains_report.items() if r["status"] == "healthy"],
            "degraded_domains": [d for d, r in domains_report.items() if r["status"] == "degraded"],
            "error_domains": [d for d, r in domains_report.items() if r["status"] == "error"],
            "total_checks": total_checks,
            "ok_checks": ok_checks,
            "warn_checks": warn_checks,
            "fail_checks": fail_checks,
            "duration_ms": round((time.perf_counter() - started) * 1000.0, 2),
        },
    }


def _format_human_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    overall = report["status"].upper()
    summary = report["summary"]
    lines.append("=" * 72)
    lines.append(f"OpenUPSC Subagent Health Doctor  |  Overall Status: {overall}")
    lines.append(
        f"Checked: {report['checked_at']}  |  Domain(s): {summary['requested_domain']}  "
        f"|  Duration: {summary['duration_ms']} ms"
    )
    lines.append("=" * 72)

    badge_map = {"ok": "[ OK ]", "warn": "[WARN]", "fail": "[FAIL]"}
    for dom, dom_report in report["domains"].items():
        dom_sum = dom_report["summary"]
        lines.append(
            f"\n[{dom.upper()}] status={dom_report['status']} "
            f"(ok={dom_sum['ok']}, warn={dom_sum['warn']}, fail={dom_sum['fail']}, {dom_report['duration_ms']} ms)"
        )
        for chk in dom_report["checks"]:
            badge = badge_map.get(chk["status"], "[????]")
            lines.append(f"  {badge} {chk['name']}: {chk['detail']}")

    lines.append("\n" + "-" * 72)
    lines.append(
        f"Summary: {summary['ok_checks']}/{summary['total_checks']} checks ok, "
        f"{summary['warn_checks']} warn, {summary['fail_checks']} fail"
    )
    lines.append("-" * 72)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m subagents.doctor",
        description="Run independent health diagnostics across OpenUPSC's 4 subagent domains.",
    )
    parser.add_argument(
        "--domain",
        choices=["all", "resource", "backend", "frontend", "system"],
        default="all",
        help="Target subagent domain to diagnose (default: all).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on 'degraded' status as well as 'error' status.",
    )
    args = parser.parse_args(argv)

    report = run_diagnostics(args.domain)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(_format_human_report(report))

    if report["status"] == "error":
        return 1
    if args.strict and report["status"] == "degraded":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
