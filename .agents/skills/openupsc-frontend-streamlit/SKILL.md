---
name: openupsc-frontend-streamlit
description: Workflow for developing, styling, and testing modular Streamlit views in streamlit_app/ using the dual-mode OpenUPSCClient (FastAPI + SQLite fallback) and Streamlit AppTest.
---

# OpenUPSC Frontend Streamlit Operations (`frontend_agent`)

Use this skill whenever building or updating OpenUPSC's Streamlit UI (`streamlit_app/`), dual-mode client (`streamlit_app/client.py`), design tokens (`streamlit_app/theme.py`), configuration (`.streamlit/config.toml`), or companion static assets (`frontend/`).

## Owned Files (Strict Boundary)

- `.streamlit/config.toml`
- `streamlit_app/app.py`
- `streamlit_app/dashboard.py`
- `streamlit_app/client.py`
- `streamlit_app/theme.py`
- `streamlit_app/views/*`
- `frontend/*`

Never modify `backend/*`, `UPSC_FREE_RESOURCES_MASTER.md`, `run.py`, `subagents/*`, or `tests/*` under this skill.

## Architectural Guidelines

### 1. Dual-Mode Data Access via `OpenUPSCClient`
- Every Streamlit view must read and mutate state through `streamlit_app/client.py` (`OpenUPSCClient`), **never** via direct `sqlite3` queries or ad-hoc `requests.get` calls scattered in views.
- `OpenUPSCClient` tries FastAPI (`OPENUPSC_API_URL`, default `http://127.0.0.1:8000`) with a short timeout (e.g., `1.5s–2.5s`) and automatically falls back to `backend.database` public functions when FastAPI is offline.
- Clearly display the active mode (`Live API` vs `Direct SQLite Fallback`) in the sidebar/status header so the user always knows the app is functioning smoothly.

### 2. Modular View Design (`streamlit_app/views/`)
- Keep `streamlit_app/app.py` lean: call `st.set_page_config(...)` exactly once, inject CSS via `streamlit_app/theme.py`, instantiate `OpenUPSCClient`, manage navigation/user selection, and dispatch to modular view renderers under `streamlit_app/views/`.
- Keep `streamlit_app/dashboard.py` working cleanly as a backwards-compatible entrypoint/wrapper.
- Prefix widget keys by view name (e.g., `key="pyq_subject_filter"`) to prevent `StreamlitDuplicateElementKey`.
- Guard every chart and metric calculation against empty DataFrames, missing keys, and divide-by-zero (`max(total, 1)`).

### 3. Visual Polish (`streamlit_app/theme.py` & `.streamlit/config.toml`)
- Keep typography legible, spacing airy, and colors aligned with `.streamlit/config.toml`.
- Validate external video/PDF links before rendering `st.video` / link buttons; fall back to clean `st.link_button` or informational notices if a resource is non-embeddable.

## Verification Commands

### 1. Run Frontend Domain Health Probe & Syntax Check
```bash
.venv/bin/python -m subagents.doctor --domain frontend
```

### 2. Headless `AppTest` Verification on an Isolated Temp DB (Offline Fallback Mode)
```bash
.venv/bin/python -c "
import os, tempfile
from pathlib import Path
from streamlit.testing.v1 import AppTest

with tempfile.TemporaryDirectory() as tmp:
    os.environ['OPENUPSC_DB_PATH'] = str(Path(tmp) / 'ui_test.db')
    os.environ['OPENUPSC_API_URL'] = 'http://127.0.0.1:19999'  # force offline SQLite fallback
    entry = 'streamlit_app/app.py' if Path('streamlit_app/app.py').exists() else 'streamlit_app/dashboard.py'
    at = AppTest.from_file(entry, default_timeout=20).run()
    assert not at.exception, f'Unhandled Streamlit exception: {at.exception}'
    print(f'AppTest OK ({entry}) — metrics: {len(at.metric)}, markdown blocks: {len(at.markdown)}')
"
```

### 3. Launch UI Standalone for Interactive QA
```bash
.venv/bin/python run.py --ui-only
```
