"""Backend Subsystem Unit, Migration, Auth, API & Backup Tests (backend_agent).

Every test runs against a fresh isolated SQLite database inside
`tempfile.TemporaryDirectory()` via `OPENUPSC_DB_PATH` and NEVER touches
production `data/openupsc.db` or `data/backups/`.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend import database as db
from backend.main import app


class TestBackendSubsystem(unittest.TestCase):
    """Comprehensive isolated verification of FastAPI v3.0 & SQLite WAL persistence."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="openupsc_backend_test_")
        self.tmp_path = Path(self._tmpdir.name)
        self.db_path = self.tmp_path / "isolated_backend.db"

        self._prev_db_env = os.environ.get("OPENUPSC_DB_PATH")
        self._prev_st_url = os.environ.get("OPENUPSC_STREAMLIT_URL")
        os.environ["OPENUPSC_DB_PATH"] = str(self.db_path)
        os.environ["OPENUPSC_STREAMLIT_URL"] = "http://localhost:8599"

        db.init_db()
        self._client_cm = TestClient(app)
        self.client = self._client_cm.__enter__()

    def tearDown(self) -> None:
        self._client_cm.__exit__(None, None, None)
        if self._prev_db_env is None:
            os.environ.pop("OPENUPSC_DB_PATH", None)
        else:
            os.environ["OPENUPSC_DB_PATH"] = self._prev_db_env

        if self._prev_st_url is None:
            os.environ.pop("OPENUPSC_STREAMLIT_URL", None)
        else:
            os.environ["OPENUPSC_STREAMLIT_URL"] = self._prev_st_url

        self._tmpdir.cleanup()

    def test_init_db_idempotency_and_custom_resource_preservation(self) -> None:
        initial = db.list_resources()
        self.assertEqual(len(initial), 334, f"Expected 334 seeded resources, got {len(initial)}.")

        custom = db.create_resource(
            {
                "id": "res-custom-test-preserve",
                "title": "Custom Aspirant Notes Archive",
                "subject": "Indian Polity",
                "category": "Notes",
                "level": "Core",
                "language": "English",
                "type": "Notes",
                "provider": "Aspirant Collective",
                "url": "https://example.org/custom-polity-notes",
                "description": "Custom admin resource that must survive init_db() re-runs.",
                "tags": ["Polity", "Custom"],
            }
        )
        self.assertEqual(custom["id"], "res-custom-test-preserve")

        # Run init_db() twice more — seeded count must stay identical and custom row preserved
        db.init_db()
        db.init_db()
        after = db.list_resources()
        self.assertEqual(len(after), 335)
        ids = {r["id"] for r in after}
        self.assertIn("res-custom-test-preserve", ids)

    def test_additive_migration_from_legacy_db_without_master_part(self) -> None:
        legacy_db = self.tmp_path / "legacy_v1.db"
        conn = sqlite3.connect(str(legacy_db))
        try:
            conn.executescript(
                """
                CREATE TABLE resources (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    category TEXT NOT NULL,
                    level TEXT NOT NULL,
                    class_level TEXT,
                    language TEXT NOT NULL,
                    type TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT NOT NULL,
                    senior_tip TEXT,
                    views TEXT,
                    likes TEXT,
                    channel_subscribers TEXT,
                    playlist_length TEXT,
                    estimated_hours INTEGER DEFAULT 0,
                    free INTEGER DEFAULT 1,
                    verified INTEGER DEFAULT 1,
                    verification_status TEXT DEFAULT 'Verified',
                    last_verified TEXT,
                    verification_signals_json TEXT,
                    prerequisites_json TEXT,
                    next_resource_id TEXT,
                    next_resource_title TEXT,
                    tags_json TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                INSERT INTO resources (
                    id, title, subject, category, level, language, type, provider, url, description, created_at
                ) VALUES (
                    'res-custom-legacy-row', 'Legacy Row', 'History', 'Notes', 'Core',
                    'English', 'Notes', 'Legacy Provider', 'https://example.org/legacy',
                    'Row created before master_part column existed', '2025-01-01T00:00:00Z'
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

        prev = os.environ["OPENUPSC_DB_PATH"]
        try:
            os.environ["OPENUPSC_DB_PATH"] = str(legacy_db)
            db.init_db()
            integrity = db.check_db_integrity()
            self.assertTrue(integrity["ok"], integrity)

            with db.get_connection() as c:
                cols = {row[1] for row in c.execute("PRAGMA table_info(resources)").fetchall()}
                self.assertIn("master_part", cols, "Additive migration failed to add master_part column.")
                row = c.execute(
                    "SELECT id, title FROM resources WHERE id = ?", ("res-custom-legacy-row",)
                ).fetchone()
                self.assertIsNotNone(row, "Legacy custom resource was lost during migration.")
        finally:
            os.environ["OPENUPSC_DB_PATH"] = prev

    def test_auth_full_lifecycle(self) -> None:
        # 1. Signup
        signup_payload = {
            "full_name": "Aarav Sharma",
            "email": "aarav.test@openupsc.in",
            "password": "strongpassword123",
            "preparation_stage": "Standard Core",
            "target_attempt_year": "2027",
            "daily_target_hours": 6,
        }
        r = self.client.post("/api/auth/signup", json=signup_payload)
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        token = body["token"]
        self.assertTrue(token)
        self.assertEqual(body["user"]["email"], "aarav.test@openupsc.in")

        # 2. Duplicate email -> 409
        r_dup = self.client.post("/api/auth/signup", json=signup_payload)
        self.assertEqual(r_dup.status_code, 409, r_dup.text)

        # 3. Bad password login -> 401
        r_bad = self.client.post(
            "/api/auth/login",
            json={"email": "aarav.test@openupsc.in", "password": "wrongpassword"},
        )
        self.assertEqual(r_bad.status_code, 401)

        # 4. Good login -> 200
        r_login = self.client.post(
            "/api/auth/login",
            json={"email": "aarav.test@openupsc.in", "password": "strongpassword123"},
        )
        self.assertEqual(r_login.status_code, 200, r_login.text)
        auth_headers = {"Authorization": f"Bearer {r_login.json()['token']}"}

        # 5. Update password & verify new password works
        r_pw = self.client.put(
            "/api/auth/password",
            json={"new_password": "newstrongpassword456"},
            headers=auth_headers,
        )
        self.assertEqual(r_pw.status_code, 200, r_pw.text)
        r_login2 = self.client.post(
            "/api/auth/login",
            json={"email": "aarav.test@openupsc.in", "password": "newstrongpassword456"},
        )
        self.assertEqual(r_login2.status_code, 200, r_login2.text)
        auth_headers2 = {"Authorization": f"Bearer {r_login2.json()['token']}"}

        # 6. Demo login & demo account delete blocked with 400
        r_demo = self.client.post("/api/auth/demo")
        self.assertEqual(r_demo.status_code, 200, r_demo.text)
        demo_headers = {"Authorization": f"Bearer {r_demo.json()['token']}"}
        r_del_demo = self.client.delete("/api/auth/account", headers=demo_headers)
        self.assertEqual(r_del_demo.status_code, 400, r_del_demo.text)

        # 7. Logout demo session
        r_logout = self.client.post("/api/auth/logout", headers=demo_headers)
        self.assertEqual(r_logout.status_code, 200)

        # 8. Delete personal account -> 200 and subsequent login fails with 401
        r_del_user = self.client.delete("/api/auth/account", headers=auth_headers2)
        self.assertEqual(r_del_user.status_code, 200, r_del_user.text)
        r_after_del = self.client.post(
            "/api/auth/login",
            json={"email": "aarav.test@openupsc.in", "password": "newstrongpassword456"},
        )
        self.assertEqual(r_after_del.status_code, 401)

    def test_resources_crud_validation_facets_and_resync(self) -> None:
        # Bad URL -> 422
        bad_payload = {
            "title": "XSS Attempt",
            "subject": "History",
            "provider": "Evil",
            "url": "javascript:alert(1)",
        }
        r_bad = self.client.post("/api/resources", json=bad_payload)
        self.assertEqual(r_bad.status_code, 422)

        composite_payload = {
            "title": "Composite URL",
            "subject": "History",
            "provider": "Test",
            "url": "https://a.example.org & https://b.example.org",
        }
        r_comp = self.client.post("/api/resources", json=composite_payload)
        self.assertEqual(r_comp.status_code, 422)

        # Create
        good_payload = {
            "id": "res-custom-crud-test",
            "title": "OpenUPSC Test Polity Lecture Series",
            "subject": "Indian Polity",
            "category": "Standard Core",
            "level": "Core",
            "type": "YouTube",
            "provider": "Test Educator",
            "url": "https://www.youtube.com/playlist?list=PLTWYSxOsBjqH2xjccBt1sxN3X9HwmI8VK",
            "master_part": 8,
        }
        r_create = self.client.post("/api/resources", json=good_payload)
        self.assertEqual(r_create.status_code, 200, r_create.text)
        created = r_create.json()["resource"]
        self.assertEqual(created["id"], "res-custom-crud-test")

        # Duplicate ID -> 409
        r_dup = self.client.post("/api/resources", json=good_payload)
        self.assertEqual(r_dup.status_code, 409, r_dup.text)

        # Update
        r_upd = self.client.put(
            "/api/resources/res-custom-crud-test",
            json={"title": "Updated Test Polity Lecture Series", "estimated_hours": 18},
        )
        self.assertEqual(r_upd.status_code, 200, r_upd.text)
        self.assertEqual(r_upd.json()["resource"]["title"], "Updated Test Polity Lecture Series")

        # Facets
        r_facets = self.client.get("/api/resources/facets")
        self.assertEqual(r_facets.status_code, 200)
        facets = r_facets.json()
        self.assertGreaterEqual(facets["total"], 335)
        subject_names = {s["name"] for s in facets["subjects"]}
        self.assertIn("Indian Polity", subject_names)
        self.assertIn("Indian Polity", facets["subject_counts"])

        # Validate
        r_val = self.client.get("/api/resources/validate")
        self.assertEqual(r_val.status_code, 200)
        self.assertTrue(r_val.json()["valid"])

        # Resync without modifying repo JSON files
        r_sync = self.client.post("/api/resources/resync?write_json=false")
        self.assertEqual(r_sync.status_code, 200, r_sync.text)

        # Delete
        r_del = self.client.delete("/api/resources/res-custom-crud-test")
        self.assertEqual(r_del.status_code, 200)
        self.assertTrue(r_del.json()["deleted"])

    def test_curriculum_endpoints_master_guide_and_global_search(self) -> None:
        r_mg_part = self.client.get("/api/master-guide?part=2")
        self.assertEqual(r_mg_part.status_code, 200)
        mg_part = r_mg_part.json()
        self.assertEqual(len(mg_part["parts"]), 1)
        self.assertEqual(mg_part["parts"][0]["part_number"], 2)

        r_mg_q = self.client.get("/api/master-guide?q=NCERT")
        self.assertEqual(r_mg_q.status_code, 200)
        self.assertGreater(r_mg_q.json()["matched_items_count"], 10)

        r_seq = self.client.get("/api/study-sequence")
        self.assertEqual(r_seq.status_code, 200)
        self.assertGreaterEqual(r_seq.json()["total_phases"], 5)

        r_roadmaps = self.client.get("/api/roadmaps")
        self.assertEqual(r_roadmaps.status_code, 200)
        roadmaps = r_roadmaps.json()["roadmaps"]
        self.assertEqual(len(roadmaps), 8)
        first_rm_id = roadmaps[0]["subjectId"]
        r_rm_one = self.client.get(f"/api/roadmaps/{first_rm_id}")
        self.assertEqual(r_rm_one.status_code, 200)

        r_ncert = self.client.get("/api/ncert")
        self.assertEqual(r_ncert.status_code, 200)
        self.assertGreaterEqual(len(r_ncert.json()["books"]), 36)

        r_qp = self.client.get("/api/question-papers")
        self.assertEqual(r_qp.status_code, 200)
        self.assertGreaterEqual(len(r_qp.json()["questionPapers"]), 8)

        r_ca = self.client.get("/api/current-affairs")
        self.assertEqual(r_ca.status_code, 200)
        self.assertGreaterEqual(len(r_ca.json()["categories"]), 4)

        r_search = self.client.get("/api/search?q=Polity")
        self.assertEqual(r_search.status_code, 200)
        self.assertGreater(len(r_search.json()["results"]), 0)

    def test_authoritative_server_side_pyq_grading_and_reset(self) -> None:
        pyqs = self.client.get("/api/pyqs").json()["pyqs"]
        prelims = [p for p in pyqs if p.get("options") and p.get("correctAnswer")]
        self.assertGreater(len(prelims), 0)
        q = prelims[0]
        correct_opt = q["correctAnswer"]
        wrong_opt = next(opt for opt in q["options"] if opt != correct_opt)

        # Spoof is_correct=True on a WRONG option — backend MUST enforce False!
        r_spoof = self.client.post(
            "/api/pyq-attempts",
            json={
                "pyq_id": q["id"],
                "subject": q["subject"],
                "selected_option": wrong_opt,
                "is_correct": True,
            },
        )
        self.assertEqual(r_spoof.status_code, 200, r_spoof.text)
        attempt_data = r_spoof.json().get("attempt") or r_spoof.json()
        self.assertFalse(
            attempt_data["is_correct"],
            f"Backend accepted spoofed is_correct=True for wrong answer! Response: {r_spoof.json()}",
        )

        # Submit the CORRECT option — backend MUST grade True!
        r_right = self.client.post(
            "/api/pyq-attempts",
            json={
                "pyq_id": q["id"],
                "subject": q["subject"],
                "selected_option": correct_opt,
                "is_correct": False,
            },
        )
        self.assertEqual(r_right.status_code, 200, r_right.text)
        right_data = r_right.json().get("attempt") or r_right.json()
        self.assertTrue(
            right_data["is_correct"],
            f"Backend failed to grade correct option as True! Response: {r_right.json()}",
        )

        # Reset PYQ attempts
        r_reset = self.client.delete("/api/pyq-attempts")
        self.assertEqual(r_reset.status_code, 200)
        analytics = self.client.get("/api/analytics/overview").json()["analytics"]
        self.assertEqual(analytics["pyq_total_attempted"], 0)

    def test_study_session_timetable_autocomplete_streak_and_analytics(self) -> None:
        # Create a Daily timetable event for Indian Polity
        r_tt = self.client.post(
            "/api/timetable",
            json={
                "day_of_week": "Daily",
                "start_time": "06:00",
                "end_time": "07:00",
                "subject": "Indian Polity",
                "topic": "Fundamental Rights Revision",
                "completed": False,
            },
        )
        self.assertEqual(r_tt.status_code, 200, r_tt.text)
        ev_id = r_tt.json()["event"]["id"]

        # Log a completed study session for Indian Polity -> auto-completes matching timetable block
        r_sess = self.client.post(
            "/api/study-sessions",
            json={
                "subject": "Indian Polity",
                "topic": "Fundamental Rights Revision",
                "duration_minutes": 45,
                "session_type": "Focus",
                "completed": True,
            },
        )
        self.assertEqual(r_sess.status_code, 200, r_sess.text)

        tt_events = self.client.get("/api/timetable").json()["timetable"]
        matched = next(e for e in tt_events if e["id"] == ev_id)
        self.assertTrue(
            matched["completed"],
            "Expected matching Daily timetable event to auto-complete after study session.",
        )

        analytics = self.client.get("/api/analytics/overview").json()["analytics"]
        self.assertGreaterEqual(analytics["study_streak_days"], 1)
        self.assertGreaterEqual(analytics["today_minutes"], 45)

        subject_mastery = analytics["subject_mastery"]
        self.assertEqual(len(subject_mastery), 9, f"Expected 9 subject mastery buckets, got {len(subject_mastery)}.")
        subjects = [s["subject"] for s in subject_mastery]
        self.assertEqual(len(subjects), len(set(subjects)), f"Duplicate subject mastery entries: {subjects}")

    def test_online_rolling_sqlite_backup_and_pruning(self) -> None:
        backup_dir = self.tmp_path / "custom_backups"
        last_result = None
        for _ in range(5):
            last_result = db.backup_database(backup_dir=backup_dir, max_backups=3)
            self.assertTrue(last_result["ok"], last_result)

        assert last_result is not None
        self.assertEqual(last_result["retained_count"], 3)
        snapshots = db.list_backups(backup_dir=backup_dir)
        self.assertEqual(len(snapshots), 3)

        # Verify actual SQLite integrity of the backup copy
        snap_path = Path(snapshots[0]["path"])
        self.assertTrue(snap_path.is_file())
        conn = sqlite3.connect(f"file:{snap_path.resolve().as_posix()}?mode=ro", uri=True)
        try:
            rows = conn.execute("PRAGMA integrity_check;").fetchall()
            self.assertEqual(rows, [("ok",)])
        finally:
            conn.close()

    def test_security_headers_and_root_points_to_streamlit(self) -> None:
        r_root = self.client.get("/")
        self.assertEqual(r_root.status_code, 200)
        self.assertIn("http://localhost:8599", r_root.text)
        self.assertIn("Streamlit", r_root.text)

        # Security headers on normal endpoint
        self.assertEqual(r_root.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(r_root.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(r_root.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertIn("camera=()", r_root.headers.get("Permissions-Policy", ""))

        # Cache-Control: no-store on /api/auth/*
        r_me = self.client.get("/api/auth/me")
        self.assertEqual(r_me.status_code, 200)
        self.assertEqual(r_me.headers.get("Cache-Control"), "no-store")


if __name__ == "__main__":
    unittest.main()
