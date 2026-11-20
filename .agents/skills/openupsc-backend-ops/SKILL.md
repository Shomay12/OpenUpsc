---
name: openupsc-backend-ops
description: Workflow for safely developing, migrating, backing up, and testing OpenUPSC's FastAPI REST API, PBKDF2 authentication, SQLite WAL database, and UPSC Readiness analytics in backend/.
---

# OpenUPSC Backend Operations (`backend_agent`)

Use this skill whenever modifying REST endpoints, Pydantic request/response schemas, authentication/session cookies, SQLite schema/migrations, rolling backups, or analytics logic.

## Owned Files (Strict Boundary)

- `backend/__init__.py`
- `backend/auth.py`
- `backend/models.py`
- `backend/database.py`
- `backend/main.py`

Never modify `backend/resource_engine.py`, `backend/data/*`, `UPSC_FREE_RESOURCES_MASTER.md`, `streamlit_app/*`, `run.py`, or `subagents/*` under this skill.

## Core Safety Rules

1. **Dynamic Temp DB Isolation (`OPENUPSC_DB_PATH`):**
   - `get_db_path()` in `backend/database.py` must always read `os.environ.get("OPENUPSC_DB_PATH")` at call time so tests can point to a temporary SQLite file without touching `data/openupsc.db`.
2. **Additive, Idempotent Migrations:**
   - Use `CREATE TABLE IF NOT EXISTS` and inspect `PRAGMA table_info(<table>)` before running `ALTER TABLE ADD COLUMN`.
   - Never drop existing user tables (`users`, `sessions`, `progress`, `notes`, `bookmarks`, `study_sessions`, `timetable`, `pyq_attempts`, `suggestions`, `journey_plans`).
3. **Safe Online SQLite Backups & Integrity Checks:**
   - Always enable `PRAGMA foreign_keys = ON;` and `PRAGMA journal_mode = WAL;`.
   - Implement backups using SQLite's native `source_conn.backup(dest_conn)` into `data/backups/` with rolling retention (never raw `shutil.copy` of an active WAL file).
   - Provide `check_db_integrity()` running `PRAGMA integrity_check;`.
4. **Strict Validation & Clean Error Responses:**
   - Validate all payloads via Pydantic v2 models in `backend/models.py`.
   - Return clear `400`/`401`/`404`/`422` JSON responses; never expose unhandled `500` tracebacks.
   - Always use parameterized SQL queries (`?`).

## Development & Verification Commands

### 1. Run Backend Domain Health Probe
```bash
.venv/bin/python -m subagents.doctor --domain backend
```

### 2. Smoke-Test DB Init, Integrity & Backup on an Isolated Temp DB
```bash
.venv/bin/python -c "
import os, tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    os.environ['OPENUPSC_DB_PATH'] = str(Path(tmp) / 'test.db')
    from backend import database as db
    db.init_db()
    db.init_db()  # verify idempotency
    if hasattr(db, 'check_db_integrity'):
        print('Integrity:', db.check_db_integrity())
    print('Resources:', len(db.list_resources()))
"
```

### 3. Smoke-Test FastAPI Routes via `TestClient` (Temp DB)
```bash
.venv/bin/python -c "
import os, tempfile
from pathlib import Path
from fastapi.testclient import TestClient
with tempfile.TemporaryDirectory() as tmp:
    os.environ['OPENUPSC_DB_PATH'] = str(Path(tmp) / 'api_test.db')
    from backend.main import app
    with TestClient(app) as client:
        r = client.get('/api/health')
        assert r.status_code == 200, r.text
        print('Health:', r.json())
"
```

### 4. Run Backend Unit Tests (Phase 2+)
```bash
.venv/bin/python -m unittest discover -s tests -p "test_backend*.py" -v
```
