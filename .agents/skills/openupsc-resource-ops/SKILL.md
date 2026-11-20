---
name: openupsc-resource-ops
description: Workflow for auditing, synchronizing, validating, and extending OpenUPSC's free UPSC resource catalog in UPSC_FREE_RESOURCES_MASTER.md, backend/resource_engine.py, and backend/data/*.json without breaking IDs or links.
---

# OpenUPSC Resource Operations (`resource_agent`)

Use this skill whenever adding, updating, auditing, or syncing free UPSC links, Class 6–12 NCERT textbooks, roadmaps, PYQs, official question paper archives, or current affairs datasets.

## Owned Files (Strict Boundary)

- `UPSC_FREE_RESOURCES_MASTER.md`
- `backend/resource_engine.py`
- `backend/data/resources.json`
- `backend/data/ncert.json`
- `backend/data/roadmaps.json`
- `backend/data/pyqs.json`
- `backend/data/question_papers.json`
- `backend/data/current_affairs.json`

Never edit `backend/database.py`, `backend/main.py`, `streamlit_app/*`, or `run.py` under this skill.

## Standard Workflow

### 1. Extending `UPSC_FREE_RESOURCES_MASTER.md`
- Preserve the 11-part Markdown table structure (Official UPSC Hub, NCERT Class 6–12 Classic & NEP 2020, Bridge Books, Core Books, Govt Reports, Free News, Free Notes & Toppers' Copies, PYQs/Quizzes, Verified YouTube Playlists, CSAT, Optionals & Interview, Zero-Cost Study Sequence).
- Verify every URL uses `https://` (or `http://` only if official government portal requires it).
- For NCERT official links, use verified `https://ncert.nic.in/textbook.php?<code>=0-<chapters>` URLs.
- For YouTube playlists, use canonical playlist URLs containing `list=PL...` (or valid YouTube playlist ID) so OpenUPSC's in-app player can embed cleanly.

### 2. Idempotent Synchronization via `backend/resource_engine.py`
- Run the resource engine parser/sync after editing `UPSC_FREE_RESOURCES_MASTER.md` so `backend/data/resources.json` stays aligned:
  ```bash
  .venv/bin/python -m backend.resource_engine --sync
  ```
  (Or invoke the exported sync function directly in Python if CLI flags differ.)
- Confirm **idempotency**: running sync twice back-to-back must produce zero extra rows, zero duplicate `id` values, and no unintended diff in `backend/data/resources.json`.

### 3. Validating Catalog Integrity
Run both the engine validator and the Resource domain health probe:
```bash
.venv/bin/python -c "from backend.resource_engine import validate_catalog; import json; print(json.dumps(validate_catalog(), indent=2))"
.venv/bin/python -m subagents.doctor --domain resource
```

### 4. Schema Hygiene Checklist for `backend/data/*.json`
- Valid UTF-8 JSON (`indent=2`, `ensure_ascii=False`).
- Every entry has a stable, non-empty, unique `id` (never rename existing IDs referenced by user bookmarks/progress/notes).
- Every `url` / `pdf_url` / `video_url` starts with `http://` or `https://`.
- Zero `LEGACY_PLACEHOLDER_IDS` reintroduced into `resources.json`.
- Never open or write `data/openupsc.db` directly; `backend/database.py` loads `backend/data/*.json` during `init_db()`.
