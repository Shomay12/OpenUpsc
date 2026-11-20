"""Frontend Subsystem Dual-Mode Fallback & Streamlit AppTest Suite (frontend_agent).

Tests OpenUPSCClient in strict Offline Direct SQLite Fallback mode
(`OPENUPSC_API_URL=http://127.0.0.1:19999`) on an isolated temporary DB, plus
headless `streamlit.testing.v1.AppTest` verification for `app.py`, `dashboard.py`,
and all 10 modular views asserting zero exceptions and zero `st.error` elements.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from backend import database as db
from streamlit_app.client import OpenUPSCClient

REPO_ROOT = Path(__file__).resolve().parent.parent

ALL_MODULAR_VIEWS: tuple[tuple[str, str], ...] = (
    ("home", "render_home"),
    ("library", "render_library"),
    ("ncert", "render_ncert"),
    ("pyqs", "render_pyqs"),
    ("roadmaps", "render_roadmaps"),
    ("current_affairs", "render_current_affairs"),
    ("csat_optionals", "render_csat_optionals"),
    ("study_workspace", "render_study_workspace"),
    ("analytics", "render_analytics"),
    ("admin_system", "render_admin_system"),
)


class TestFrontendSubsystem(unittest.TestCase):
    """Independent verification of Streamlit Main App, views, and offline SQLite fallback."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="openupsc_frontend_test_")
        self.tmp_path = Path(self._tmpdir.name)
        self.db_path = self.tmp_path / "isolated_frontend.db"

        self._prev_db_env = os.environ.get("OPENUPSC_DB_PATH")
        self._prev_api_env = os.environ.get("OPENUPSC_API_URL")

        os.environ["OPENUPSC_DB_PATH"] = str(self.db_path)
        # Unused local port guarantees FastAPI is offline -> forces Direct SQLite Fallback
        os.environ["OPENUPSC_API_URL"] = "http://127.0.0.1:19999"
        db.init_db()

    def tearDown(self) -> None:
        if self._prev_db_env is None:
            os.environ.pop("OPENUPSC_DB_PATH", None)
        else:
            os.environ["OPENUPSC_DB_PATH"] = self._prev_db_env

        if self._prev_api_env is None:
            os.environ.pop("OPENUPSC_API_URL", None)
        else:
            os.environ["OPENUPSC_API_URL"] = self._prev_api_env

        self._tmpdir.cleanup()

    def test_client_offline_direct_sqlite_fallback_end_to_end(self) -> None:
        client = OpenUPSCClient(api_base="http://127.0.0.1:19999")
        self.assertFalse(client.is_api_online(force=True))
        self.assertIn("SQLite", client.connection_mode_label())

        # Workspace & Search
        ws = client.get_workspace(force_refresh=True)
        self.assertIn("profile", ws)
        self.assertIn("analytics", ws)
        results = client.global_search("NCERT")
        self.assertGreater(len(results), 0)

        # Progress, Bookmark & Note mutations
        ok, _, prog = client.update_progress("ncert-c6-hist", 75)
        self.assertTrue(ok)
        self.assertEqual(prog.get("progress_percentage"), 75)

        resources = client.get_resources()
        self.assertEqual(len(resources), 334)
        sample_res_id = resources[0]["id"]
        ok, _, bm = client.toggle_bookmark(sample_res_id)
        self.assertTrue(ok)
        self.assertIn("bookmarked", bm)

        ok, _, note = client.save_note(
            "ncert-c6-hist",
            "Key Indus Valley notes saved offline.",
            item_title="Class 6 History",
            item_category="NCERT",
        )
        self.assertTrue(ok)
        self.assertIn("Indus Valley", note.get("content", ""))

        # Authoritative PYQ grading even in offline SQLite mode
        pyqs = client.get_pyqs()
        prelims = next(p for p in pyqs if p.get("options") and p.get("correctAnswer"))
        wrong_opt = next(o for o in prelims["options"] if o != prelims["correctAnswer"])
        ok, _, attempt = client.record_pyq_attempt(
            prelims["id"], prelims["subject"], wrong_opt, is_correct=True
        )
        self.assertTrue(ok)
        attempt_obj = attempt.get("attempt") or attempt
        self.assertFalse(
            attempt_obj.get("is_correct"),
            "Offline fallback PYQ grading must reject spoofed is_correct=True.",
        )

        # Study session + timetable CRUD
        ok, _, sess = client.create_study_session(
            {
                "subject": "Geography",
                "topic": "Monsoon Mechanism",
                "duration_minutes": 40,
                "session_type": "Focus",
                "completed": True,
            }
        )
        self.assertTrue(ok, sess)

        ok, _, tt = client.create_timetable_event(
            {
                "day_of_week": "Daily",
                "start_time": "08:00",
                "end_time": "09:00",
                "subject": "Geography",
                "topic": "Indian Drainage System",
            }
        )
        self.assertTrue(ok, tt)
        ev_id = (tt.get("event") or tt)["id"]
        ok, _, upd_tt = client.update_timetable_event(ev_id, {"completed": True})
        self.assertTrue(ok, upd_tt)
        ok, _ = client.delete_timetable_event(ev_id)
        self.assertTrue(ok)

        # Resource CRUD + invalid URL rejection
        ok, msg, bad_res = client.create_resource(
            {
                "title": "Bad JS URL",
                "subject": "History",
                "provider": "Test",
                "url": "javascript:alert(1)",
            }
        )
        self.assertFalse(ok)
        self.assertIsNone(bad_res)
        self.assertTrue(msg)

        ok, msg, created = client.create_resource(
            {
                "id": "res-custom-offline-client",
                "title": "Offline Created Resource",
                "subject": "Economy",
                "category": "Notes",
                "level": "Core",
                "type": "Notes",
                "provider": "Offline Test",
                "url": "https://example.org/offline-economy",
            }
        )
        self.assertTrue(ok, msg)
        assert created is not None
        ok, msg, updated = client.update_resource(
            "res-custom-offline-client", {"title": "Offline Updated Resource"}
        )
        self.assertTrue(ok, msg)
        assert updated is not None
        self.assertEqual(updated["title"], "Offline Updated Resource")
        ok, msg = client.delete_resource("res-custom-offline-client")
        self.assertTrue(ok, msg)

        # System diagnostics & rolling backup inside isolated temp dir
        diag = client.get_system_diagnostics(include_doctor=False)
        self.assertEqual(diag.get("status"), "healthy", diag)
        ok, msg, bkp = client.create_backup(max_backups=3)
        self.assertTrue(ok, msg)
        self.assertTrue(bkp.get("ok"))
        self.assertTrue(Path(bkp["path"]).resolve().is_relative_to(self.tmp_path.resolve()))

    def test_apptest_main_app_and_dashboard_wrapper(self) -> None:
        for entry in ("streamlit_app/app.py", "streamlit_app/dashboard.py"):
            with self.subTest(entry=entry):
                at = AppTest.from_file(str(REPO_ROOT / entry), default_timeout=25).run()
                self.assertEqual(
                    len(at.exception),
                    0,
                    f"{entry} raised exception(s): {[e.message for e in at.exception]}",
                )
                self.assertEqual(
                    len(at.error),
                    0,
                    f"{entry} rendered st.error: {[e.value for e in at.error]}",
                )

    def test_apptest_all_10_modular_views_zero_errors(self) -> None:
        for module_name, func_name in ALL_MODULAR_VIEWS:
            with self.subTest(view=module_name):
                script = (
                    "import sys\n"
                    f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
                    "from streamlit_app.theme import inject_theme\n"
                    f"from streamlit_app.views.{module_name} import {func_name}\n"
                    "inject_theme()\n"
                    f"{func_name}()\n"
                )
                at = AppTest.from_string(script, default_timeout=25).run()
                self.assertEqual(
                    len(at.exception),
                    0,
                    f"View {module_name} raised exception(s): {[e.message for e in at.exception]}",
                )
                self.assertEqual(
                    len(at.error),
                    0,
                    f"View {module_name} rendered st.error: {[e.value for e in at.error]}",
                )


if __name__ == "__main__":
    unittest.main()
