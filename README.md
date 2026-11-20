# OpenUPSC

A 100% free, distraction-free **UPSC Civil Services (CSE)** preparation platform built with a **Flagship Python Streamlit Main UI**, a **Hardened FastAPI v3.0.0 + SQLite WAL Backend**, a **334-Resource Live-Verified Free Directory**, and an **Unbreakable Self-Healing Supervisor** governed by a **4-Subagent Independent Architecture**.

---

## Architecture Overview

| Layer | Primary URL / Entrypoint | Technology |
| :--- | :--- | :--- |
| **OpenUPSC Main App (Flagship UI)** | `http://localhost:8501` (`streamlit_app/app.py`) | Python Streamlit + Pandas + Plotly + Dual-Mode `OpenUPSCClient` |
| **FastAPI Backend & REST API** | `http://localhost:8000` (`backend/main.py`) | FastAPI v3.0.0 + Uvicorn + Pydantic v2 + SQLite WAL |
| **Swagger API Docs** | `http://localhost:8000/docs` | OpenAPI 3.1 interactive documentation |
| **Master Resource Engine** | `UPSC_FREE_RESOURCES_MASTER.md` + `backend/resource_engine.py` | Zero-dependency deterministic parser, idempotent sync & validator |
| **Supervisor & Health Doctor** | `run.py` + `subagents/doctor.py` | Pre-flight integrity/backup, auto-port, exponential-backoff self-healing |

> **Dual-Mode Unbreakability:** `streamlit_app/client.py` (`OpenUPSCClient`) routes traffic to FastAPI when online and seamlessly switches to **Direct SQLite Fallback Mode** via a 15-second circuit breaker if FastAPI is offline or restarting — so aspirants never lose study flow.

---

## Key Features

### 1. Redesigned Flagship Streamlit Main App (`http://localhost:8501`) — 10 Modular Views
1. **Home & Search (`home`)**: Global instant search across all 334 resources, NCERTs, roadmaps, and PYQs; readiness snapshot; daily streak; and quick launchpad.
2. **Study Workspace (`study_workspace`)**: Focus timer, session logger, daily/weekly timetable with automatic block completion, and personal study notes.
3. **Free Resource Library (`library`)**: Browse & filter **334 verified free resources across all 11 parts** of `UPSC_FREE_RESOURCES_MASTER.md` (129 YouTube playlists/channels, 107 official PDFs, 65 websites, 22 curated notes, 11 PYQ archives) with inline playlist viewer and bookmarking.
4. **NCERT Class 6–12 (`ncert`)**: **36 core NCERT textbooks** (`315` chapters) + **86 official Class 6–12 Classic & NEP 2020 links** direct from `ncert.nic.in`, with chapter progress tracking and notes.
5. **Subject Roadmaps (`roadmaps`)**: **8 structured UPSC Subject Roadmaps** (34 guided steps) plus the 5-phase Zero-Cost Study Sequence (Part 11).
6. **PYQs & Official Hub (`pyqs`)**: **18 official UPSC Question Paper & QCAB archives** (`upsc.gov.in`) + **24 interactive Prelims & Mains PYQs** with authoritative server-side grading synced to analytics.
7. **Current Affairs & Reports (`current_affairs`)**: Official PIB, PRS India, Sansad TV, AIR Spotlight, Economic Survey, Union Budget, and free think-tank reading hubs.
8. **CSAT, Optionals & Interview (`csat_optionals`)**: Complete CSAT Paper-II resource kit (16 split clean entries), 6 Optional subjects with IGNOU/YouTube links, and Personality Test (DAF/Interview) prep.
9. **Readiness Analytics (`analytics`)**: UPSC Readiness Score gauge, 14-day focus trend, 9-subject syllabus mastery matrix, PYQ accuracy breakdown, weak-subject guidance, and CSV export.
10. **Account, Admin & Health (`admin_system`)**: PBKDF2 account signup/login/profile management, full Resource CRUD catalog admin, student suggestion approvals, rolling SQLite backups, and live 4-domain Subagent Doctor panel.

### 2. Hardened FastAPI v3.0.0 Backend (`http://localhost:8000`)
- **42 `/api/*` REST endpoints** covering Auth, Workspace, Master Guide (`/api/master-guide`), Study Sequence (`/api/study-sequence`), Resources CRUD + Facets + Validation + Resync, NCERT, 8 Roadmaps, PYQs (with tamper-proof server-side grading), Study Sessions, Timetable, Analytics, Admin, and System Diagnostics/Backups (`/api/system/diagnostics`, `/api/system/backup`).
- **SQLite WAL Persistence & Safety**: Dynamic `OPENUPSC_DB_PATH` isolation, `PRAGMA foreign_keys = ON`, idempotent additive schema migrations, `check_db_integrity()`, and atomic online rolling backups via `sqlite3.Connection.backup()` in `data/backups/`.
- **Security Headers & Clean Launchpad**: Hardened HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` on `/api/auth/*`) and a clean root `/` launchpad pointing to the Streamlit Main App.

### 3. 4-Subagent Independent Architecture (`AGENTS.md`)
OpenUPSC is partitioned into **4 strictly non-overlapping subagent domains** enforced programmatically by `subagents/registry.py` and audited lazily by `subagents/doctor.py`:

| Domain | Agent ID | Exclusive Ownership | Manifest & Skill |
| :--- | :--- | :--- | :--- |
| `resource` | `resource_agent` | `UPSC_FREE_RESOURCES_MASTER.md`, `backend/resource_engine.py`, `backend/data/` | `.agents/subagents/resource-agent.md` · `.agents/skills/openupsc-resource-ops/SKILL.md` |
| `backend` | `backend_agent` | `backend/__init__.py`, `backend/auth.py`, `backend/models.py`, `backend/database.py`, `backend/main.py` | `.agents/subagents/backend-agent.md` · `.agents/skills/openupsc-backend-ops/SKILL.md` |
| `frontend` | `frontend_agent` | `.streamlit/config.toml`, `streamlit_app/`, `frontend/` | `.agents/subagents/frontend-agent.md` · `.agents/skills/openupsc-frontend-streamlit/SKILL.md` |
| `system` | `system_agent` | `run.py`, `subagents/`, `AGENTS.md`, `.agents/`, `tests/`, `requirements.txt`, `README.md` | `.agents/subagents/system-agent.md` · `.agents/skills/openupsc-system-ops/SKILL.md` |

---

## Quick Start

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python run.py
```

Open **http://localhost:8501** for the **OpenUPSC Main App (Streamlit)**.

### Demo Workspace Credentials
Works immediately out of the box with a pre-seeded demo workspace, or sign up for your own isolated aspirant account in **Account, Admin & Health**:
- **Email:** `student@upschub.in`
- **Password:** `openupsc123`

---

## Unbreakable Supervisor Modes (`run.py`)

Before starting servers, `run.py` automatically runs pre-flight SQLite initialization, `PRAGMA integrity_check`, an atomic rolling backup in `data/backups/`, and Master Guide catalog validation. If either service crashes, only the failed process restarts with bounded exponential backoff (`1s -> 2s -> 4s -> 8s -> 15s`) while Streamlit continues operating smoothly in Direct SQLite Fallback mode.

```bash
# Default: Dual-stack supervised launch (Streamlit Main App :8501 + FastAPI :8000, stable mode)
.venv/bin/python run.py

# Pre-flight DB integrity + Resource Catalog + 4-domain Subagent Doctor (no servers started)
.venv/bin/python run.py --doctor
.venv/bin/python run.py --doctor --json

# Auto-select free ports if 8000 or 8501 are busy and wire URLs together automatically
.venv/bin/python run.py --auto-port

# Run ONLY the Streamlit Main App (works seamlessly via Direct SQLite Fallback)
.venv/bin/python run.py --ui-only

# Run ONLY the FastAPI REST Backend
.venv/bin/python run.py --api-only

# Additional options
.venv/bin/python run.py --reload          # Enable Uvicorn dev auto-reload
.venv/bin/python run.py --no-reload       # Force stable non-reloading mode (default)
.venv/bin/python run.py --no-backup       # Skip pre-flight SQLite backup
.venv/bin/python run.py --max-restarts 5  # Restart cap per service in 5-min window
```

---

## Verification & Automated Testing

All automated tests run against isolated temporary SQLite databases (`OPENUPSC_DB_PATH` inside `tempfile.TemporaryDirectory`) and **never mutate** `data/openupsc.db` or `data/backups/`.

```bash
# 1. Run full isolated automated test suite (Resource + Backend + Frontend AppTest + System)
.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v

# 2. Run 4-domain Subagent Health Doctor (human-readable or JSON)
.venv/bin/python -m subagents.doctor --domain all
.venv/bin/python -m subagents.doctor --domain all --json
.venv/bin/python -m subagents.doctor --domain resource|backend|frontend|system

# 3. Verify strict non-overlapping ownership boundaries
.venv/bin/python -c "from subagents.registry import check_ownership_boundaries; import json; print(json.dumps(check_ownership_boundaries(), indent=2))"

# 4. Run supervisor pre-flight doctor
.venv/bin/python run.py --doctor
```
