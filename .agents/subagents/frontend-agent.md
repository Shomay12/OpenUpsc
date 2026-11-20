# Subagent Manifest: Frontend Agent (`frontend_agent`)

- **Domain Key:** `frontend`
- **Agent ID:** `frontend_agent`
- **Workspace Skill:** `.agents/skills/openupsc-frontend-streamlit/SKILL.md`

## Role

Own OpenUPSC's modular Python Streamlit web application (student preparation workspace, video/NCERT/PYQ/roadmap views, readiness analytics, and admin studio), its dual-mode `OpenUPSCClient` data layer, theme/design system, and companion vanilla static web assets.

## File Ownership (Exclusive)

- `.streamlit/config.toml`
- `streamlit_app/`
  - `streamlit_app/app.py` (primary modular entrypoint)
  - `streamlit_app/dashboard.py` (compatibility entrypoint / wrapper)
  - `streamlit_app/client.py` (`OpenUPSCClient` dual-mode API + SQLite fallback)
  - `streamlit_app/theme.py` (centralized CSS styling & UI primitives)
  - `streamlit_app/views/` (independent modular page/tab renderers)
- `frontend/` (companion vanilla HTML/CSS/JS static assets)

> **Out of Bounds:** Do not modify `backend/*`, `UPSC_FREE_RESOURCES_MASTER.md`, `run.py`, `subagents/*`, or `tests/*`.

## Exported Contracts

1. **Primary Streamlit Entrypoint (`streamlit_app/app.py` & `streamlit_app/dashboard.py`):**
   - Launchable directly via `streamlit run streamlit_app/app.py` or `streamlit run streamlit_app/dashboard.py` on port `OPENUPSC_STREAMLIT_PORT` (default `8501`).
   - Testable headlessly via `streamlit.testing.v1.AppTest`.
2. **Dual-Mode Client (`streamlit_app/client.py`):**
   - `OpenUPSCClient`: attempts FastAPI HTTP requests against `OPENUPSC_API_URL` (default `http://127.0.0.1:8000`) with short bounded timeouts, and transparently falls back to direct `backend.database` SQLite calls if FastAPI is unreachable.
   - Exposes connection mode indicator (`api` vs `sqlite_fallback`) so the UI clearly surfaces live sync status without blocking user workflows.
3. **Theme & Design System (`streamlit_app/theme.py`):**
   - Consistent typography, light/accessible palette matching `.streamlit/config.toml`, metric cards, badges, and empty-state components.
4. **Modular Views (`streamlit_app/views/*.py`):**
   - Self-contained render functions accepting the client and user/workspace context, decoupled from raw SQL and HTTP plumbing.

## Dependencies

- Consumes Backend REST API (`/api/*`) over HTTP (`requests`) and falls back to `backend.database` public functions.
- Optionally queries `subagents.doctor` / `subagents.registry` (via API or lazy import) to render system health diagnostics in Admin/System view.
- Packages: `streamlit`, `pandas`, `plotly`, `requests` (from `requirements.txt`).

## Safety Rules

- **Dual-Mode Unbreakability:** Every view must render with zero exceptions both when FastAPI is running AND when FastAPI is offline (SQLite fallback).
- **No Raw SQL in Views:** Views must never call `sqlite3.connect` directly; all persistence/reads go through `OpenUPSCClient`.
- **Graceful Empty States:** Guard all DataFrame operations, Plotly charts, and percentage divisions against empty lists, `None`, and zero denominators.
- **Safe Session State & Keys:** Always namespace widget keys cleanly across modular views to avoid `StreamlitDuplicateElementKey` errors.
- **Single `set_page_config`:** Call `st.set_page_config(...)` once at the top-level app entrypoint only.

## Verification Checklist

- [ ] `.venv/bin/python -m subagents.doctor --domain frontend` passes with zero failures.
- [ ] All `.py` files under `streamlit_app/` compile cleanly with zero syntax errors.
- [ ] `.streamlit/config.toml` parses cleanly with `tomllib`.
- [ ] `AppTest.from_file("streamlit_app/app.py").run()` renders with zero uncaught exceptions (`not at.exception`) on an isolated temp DB (both with API offline and online).
- [ ] Zero files outside owned paths were modified.
