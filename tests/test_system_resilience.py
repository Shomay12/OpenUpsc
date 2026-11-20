"""System Subsystem, Ownership Boundary, Doctor & Supervisor Resilience Tests (system_agent).

Verifies subagents.registry, subagents.doctor across all 4 domains,
run.py port/backoff/CLI helpers, and production DB isolation safety.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import run as supervisor
from backend import database as db
from subagents.doctor import run_diagnostics
from subagents.registry import (
    CANONICAL_DOMAINS,
    SUBAGENTS,
    check_ownership_boundaries,
    find_owner,
    get_subagent,
    list_subagents,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestSystemResilience(unittest.TestCase):
    """Independent verification of subagent registry, doctor diagnostics, and supervisor."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="openupsc_system_test_")
        self.tmp_path = Path(self._tmpdir.name)
        self.db_path = self.tmp_path / "isolated_system.db"

        self._prev_db_env = os.environ.get("OPENUPSC_DB_PATH")
        os.environ["OPENUPSC_DB_PATH"] = str(self.db_path)
        db.init_db()

    def tearDown(self) -> None:
        if self._prev_db_env is None:
            os.environ.pop("OPENUPSC_DB_PATH", None)
        else:
            os.environ["OPENUPSC_DB_PATH"] = self._prev_db_env
        self._tmpdir.cleanup()

    def test_registry_specs_and_ownership_boundaries(self) -> None:
        self.assertEqual(tuple(SUBAGENTS.keys()), CANONICAL_DOMAINS)
        self.assertEqual(len(list_subagents()), 4)
        for dom in CANONICAL_DOMAINS:
            spec = get_subagent(dom)
            self.assertEqual(spec.domain, dom)
            self.assertEqual(get_subagent(spec.id), spec)

        self.assertEqual(find_owner("UPSC_FREE_RESOURCES_MASTER.md"), "resource")
        self.assertEqual(find_owner("backend/resource_engine.py"), "resource")
        self.assertEqual(find_owner("backend/data/resources.json"), "resource")
        self.assertEqual(find_owner("backend/main.py"), "backend")
        self.assertEqual(find_owner("streamlit_app/app.py"), "frontend")
        self.assertEqual(find_owner(".streamlit/config.toml"), "frontend")
        self.assertEqual(find_owner("run.py"), "system")
        self.assertEqual(find_owner("subagents/doctor.py"), "system")
        self.assertEqual(find_owner("tests/test_system_resilience.py"), "system")

        bounds = check_ownership_boundaries()
        self.assertTrue(bounds["ok"], f"Ownership overlap detected: {bounds['overlaps']}")
        self.assertEqual(bounds["overlaps"], [])
        self.assertTrue(
            bounds["all_paths_exist"],
            f"Missing owned paths across domains: {bounds['missing_paths']}",
        )

    def test_doctor_all_four_domains_healthy(self) -> None:
        report = run_diagnostics("all")
        self.assertEqual(
            report["status"],
            "healthy",
            f"Expected all 4 domains healthy, got:\n{json.dumps(report, indent=2)}",
        )
        self.assertEqual(set(report["domains"].keys()), set(CANONICAL_DOMAINS))
        self.assertEqual(report["summary"]["fail_checks"], 0)
        self.assertEqual(report["summary"]["warn_checks"], 0)
        for dom in CANONICAL_DOMAINS:
            self.assertEqual(
                report["domains"][dom]["status"],
                "healthy",
                f"Domain {dom!r} was not healthy: {report['domains'][dom]}",
            )

    def test_supervisor_find_free_port_and_backoff_helpers(self) -> None:
        # Hold an ephemeral port open to simulate port conflict
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            busy_port = occupied.getsockname()[1]

            self.assertFalse(supervisor._is_port_free(busy_port))
            free_port = supervisor._find_free_port(busy_port)
            self.assertNotEqual(free_port, busy_port)
            self.assertGreater(free_port, busy_port)
            self.assertTrue(supervisor._is_port_free(free_port))

            # Verify exclusion set is respected
            next_free = supervisor._find_free_port(busy_port, exclude={free_port})
            self.assertNotIn(next_free, {busy_port, free_port})

        # Verify bounded exponential backoff schedule: 1 -> 2 -> 4 -> 8 -> 15 -> 15
        self.assertEqual(
            [supervisor._backoff_delay(i) for i in range(1, 7)],
            [1, 2, 4, 8, 15, 15],
        )

    def test_supervisor_cli_parser_modes(self) -> None:
        parser = supervisor.build_parser()
        args = parser.parse_args(["--auto-port", "--ui-only", "--no-backup", "--no-reload", "--max-restarts", "3"])
        self.assertTrue(args.auto_port)
        self.assertTrue(args.ui_only)
        self.assertFalse(args.api_only)
        self.assertTrue(args.no_backup)
        self.assertTrue(args.no_reload)
        self.assertEqual(args.max_restarts, 3)

    def test_supervisor_preflight_isolated_backup_and_catalog(self) -> None:
        result = supervisor.run_preflight(skip_backup=False)
        self.assertTrue(result["database"]["ok"])
        self.assertTrue(result["catalog"]["valid"])
        self.assertEqual(result["catalog"]["stats"]["resources_count"], 334)
        self.assertIsNotNone(result["backup"])
        self.assertTrue(result["backup"]["ok"])
        # Confirm rolling backup stayed strictly inside temporary directory
        self.assertTrue(Path(result["backup"]["path"]).resolve().is_relative_to(self.tmp_path.resolve()))

        no_bkp = supervisor.run_preflight(skip_backup=True)
        self.assertIsNone(no_bkp["backup"])
        self.assertTrue(no_bkp["database"]["ok"])

    def test_managed_service_restart_backoff_and_exhaustion(self) -> None:
        svc = supervisor.ManagedService(
            key="api",
            name="Test API",
            command=[sys.executable, "-c", "pass"],
            env=os.environ.copy(),
            cwd=REPO_ROOT,
            max_restarts=2,
        )
        self.assertTrue(svc.schedule_restart(1, peer_running=True))
        self.assertFalse(svc.exhausted)
        self.assertIsNotNone(svc.next_restart_at)
        self.assertTrue(svc.schedule_restart(1, peer_running=True))
        self.assertFalse(svc.exhausted)
        # 3rd crash exceeds max_restarts=2
        self.assertFalse(svc.schedule_restart(1, peer_running=True))
        self.assertTrue(svc.exhausted)

    def test_run_py_doctor_cli_exits_zero(self) -> None:
        env = os.environ.copy()
        env["OPENUPSC_DB_PATH"] = str(self.db_path)

        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "run.py"), "--doctor", "--json"],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            f"run.py --doctor --json failed (rc={proc.returncode}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
        )
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertTrue(payload["database"]["ok"])
        self.assertTrue(payload["catalog"]["valid"])
        self.assertEqual(payload["diagnostics"]["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
