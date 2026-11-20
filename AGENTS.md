# OpenUPSC — Multi-Subagent Architecture & Governance (`AGENTS.md`)

OpenUPSC is structured into **4 strictly independent, non-overlapping subagent domains** so Resource data curation, Backend API/persistence, Frontend Streamlit UI, and System supervision/testing can evolve, fail-isolate, and be verified independently without breaking the platform.

---

## 1. The 4 Independent Subagents

| Domain Key | Agent ID | Manifest | Workspace Skill | Primary Responsibility |
| :--- | :--- | :--- | :--- | :--- |
| `resource` | `resource_agent` | `.agents/subagents/resource-agent.md` | `.agents/skills/openupsc-resource-ops/SKILL.md` | Master free UPSC link directory, Class 6–12 NCERT & PYQ JSON datasets, idempotent resource parser/sync & catalog validation. |
| `backend` | `backend_agent` | `.agents/subagents/backend-agent.md` | `.agents/skills/openupsc-backend-ops/SKILL.md` | FastAPI REST API, PBKDF2 authentication & sessions, SQLite WAL persistence, schema migrations, backups, and UPSC Readiness analytics. |
| `frontend` | `frontend_agent` | `.agents/subagents/frontend-agent.md` | `.agents/skills/openupsc-frontend-streamlit/SKILL.md` | Modular Python Streamlit app (`streamlit_app/`), dual-mode `OpenUPSCClient` (API + SQLite fallback), visual theme, and companion static assets (`frontend/`). |
| `system` | `system_agent` | `.agents/subagents/system-agent.md` | `.agents/skills/openupsc-system-ops/SKILL.md` | Self-healing process supervisor (`run.py`), programmatic subagent registry & health doctor (`subagents/`), governance docs, and isolated automated tests (`tests/`). |

---

## 2. Strict Non-Overlapping File Ownership Boundaries

No two subagents may own or edit the same file. Ownership is programmatically enforced by `subagents.registry.check_ownership_boundaries()`.

| Domain | Owned Paths (Exclusive) |
| :--- | :--- |
| **`resource`** | `UPSC_FREE_RESOURCES_MASTER.md`, `backend/resource_engine.py`, `backend/data/` (`resources.json`, `master_guide.json`, `ncert.json`, `roadmaps.json`, `pyqs.json`, `question_papers.json`, `current_affairs.json`) |
| **`backend`** | `backend/__init__.py`, `backend/auth.py`, `backend/models.py`, `backend/database.py`, `backend/main.py` |
| **`frontend`** | `.streamlit/config.toml`, `streamlit_app/` (`app.py`, `dashboard.py`, `client.py`, `theme.py`, `views/`), `frontend/` |
| **`system`** | `run.py`, `subagents/` (`__init__.py`, `registry.py`, `doctor.py`), `AGENTS.md`, `.agents/`, `tests/`, `requirements.txt`, `README.md` |

> **Runtime Data Note:** `data/openupsc.db` and `data/backups/` are runtime artifacts created/maintained by `backend/database.py` (and backed up pre-flight by `run.py`). They are never checked in as test fixtures and must **never** be mutated by automated tests.

> **Cross-Domain Defect Protocol:** If an agent discovers a defect outside its ownership boundary, it must **not** patch foreign files directly. Instead, document the exact file path, line number, minimal reproduction command, and expected contract behavior and hand it back to the coordinator / owning subagent.

---

## 3. Domain Interface Contracts

Data and control flow follow a clean acyclic layering supervised horizontally by `system_agent`:

```text
  [resource_agent] ──(JSON datasets + resource_engine.py)──▶ [backend_agent]
                                                                    │
                                                  (FastAPI /api/* + database.py fallback)
                                                                    ▼
                                                             [frontend_agent]

  [system_agent] ══(supervises, health-probes, verifies all 4 domains)══▶ ALL
```

### 3.1 Resource ──▶ Backend
- **Master Directory:** `UPSC_FREE_RESOURCES_MASTER.md` is the human-curated source of truth for verified free UPSC links.
- **Structured Datasets:** `backend/data/*.json` provide schema-validated collections (`resources.json`, `ncert.json`, `roadmaps.json`, `pyqs.json`, `question_papers.json`, `current_affairs.json`).
- **Engine API (`backend/resource_engine.py`):**
  - Parses `UPSC_FREE_RESOURCES_MASTER.md` deterministically.
  - Synchronizes verified entries idempotently into `backend/data/resources.json` without duplicating IDs or wiping curated metadata.
  - Exports `validate_catalog() -> dict[str, Any]` returning validation status, counts, and any URL/schema/duplicate-ID findings.

### 3.2 Backend ──▶ Frontend
- **Primary HTTP Contract (`backend/main.py`):** RESTful JSON endpoints under `/api/*` (`/api/health`, `/api/auth/*`, `/api/workspace`, `/api/resources`, `/api/ncert`, `/api/roadmaps`, `/api/pyqs`, `/api/question-papers`, `/api/current-affairs`, `/api/search`, `/api/progress/*`, `/api/notes/*`, `/api/bookmarks/*`, `/api/study-sessions`, `/api/timetable`, `/api/pyq-attempts`, `/api/suggestions`, `/api/analytics/overview`, `/api/admin/*`).
- **Fallback Python Contract (`backend/database.py`):** Public, connection-safe data functions (`init_db`, `get_connection`, `get_db_path`, `list_resources`, `create_resource`, `update_resource`, `delete_resource`, `compute_user_analytics`, `get_ncert_data`, `get_roadmaps_data`, `get_pyqs_data`, `get_question_papers_data`, `get_current_affairs_data`, `serialize_user`, `check_db_integrity`, `backup_database`).
- **Dual-Mode Client (`streamlit_app/client.py`):** `OpenUPSCClient` routes reads/writes to FastAPI (`OPENUPSC_API_URL`) when available and falls back seamlessly to `backend.database` SQLite calls when the API server is offline.

### 3.3 System ◀══▶ All Domains
- **Registry (`subagents/registry.py`):** Programmatic source of truth for `SubagentSpec`, `SUBAGENTS`, `list_subagents()`, `get_subagent(domain)`, and `check_ownership_boundaries()`.
- **Health Doctor (`subagents/doctor.py`):** Independent, lazy-imported health probes (`probe_resource`, `probe_backend`, `probe_frontend`, `probe_system`, `run_diagnostics`) runnable via CLI (`python -m subagents.doctor`) or callable by Backend/Frontend status views.
- **Supervisor (`run.py`):** Executes pre-flight integrity checks, rolling backups, catalog sync verification, port checks (`--auto-port`), and self-healing supervision for both FastAPI and Streamlit with clean `SIGINT`/`SIGTERM` teardown.

---

## 4. Non-Negotiable Unbreakability Rules

1. **Temp DB Isolation for Tests:** Every automated test **must** set `OPENUPSC_DB_PATH` to a fresh temporary file (`tempfile.TemporaryDirectory`) before calling `init_db()` or instantiating `TestClient` / `AppTest`. Never read-write mutate `data/openupsc.db` in tests.
2. **Dual-Mode SQLite Fallback in Streamlit:** Every Streamlit view must access data exclusively via `OpenUPSCClient` and work cleanly whether FastAPI is online (`http://127.0.0.1:8000`) or completely offline.
3. **Idempotent Resource Sync & DB Init:** Running `init_db()` or catalog sync 1 time or 100 times must yield identical row counts, zero duplicate IDs, and preserve user progress, notes, bookmarks, sessions, and custom admin resources.
4. **Zero Unhandled Exceptions:** Every API endpoint validates inputs via Pydantic v2 and returns structured HTTP errors; every Streamlit view handles empty states and backend faults gracefully; every doctor probe catches exceptions per check so one broken domain never blinds diagnostics for the others.
5. **Zero Broken Links or Invalid Schemas:** Every URL in `UPSC_FREE_RESOURCES_MASTER.md` and `backend/data/*.json` must use `http://` or `https://` with non-empty titles, unique IDs, and valid YouTube `list=` IDs where playlist playback is enabled.
6. **Zero Unapproved Dependencies:** All runtime, diagnostics, and tests run strictly inside `.venv/bin/python` using installed packages from `requirements.txt` plus Python 3.11 standard library (`unittest`, `sqlite3`, `tomllib`, `urllib`, `py_compile`).

---

## 5. Exact Verification Commands (`.venv/bin/python`)

Always execute commands using the workspace virtual environment `.venv/bin/python`:

```bash
# 1. Inspect subagent registry & verify strict non-overlapping ownership boundaries
.venv/bin/python -c "from subagents.registry import list_subagents, check_ownership_boundaries; import json; print(json.dumps(check_ownership_boundaries(), indent=2))"

# 2. Run domain-specific or full system health diagnostics
.venv/bin/python -m subagents.doctor --domain system
.venv/bin/python -m subagents.doctor --domain resource
.venv/bin/python -m subagents.doctor --domain backend
.venv/bin/python -m subagents.doctor --domain frontend
.venv/bin/python -m subagents.doctor --domain all
.venv/bin/python -m subagents.doctor --domain all --json

# 3. Validate resource catalog directly
.venv/bin/python -c "from backend.resource_engine import validate_catalog; import json; print(json.dumps(validate_catalog(), indent=2))"

# 4. Run full isolated automated test suite
.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v

# 5. Supervisor pre-flight doctor & launch modes
.venv/bin/python run.py --doctor
.venv/bin/python run.py --auto-port
.venv/bin/python run.py --api-only
.venv/bin/python run.py --ui-only
```
