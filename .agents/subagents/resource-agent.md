# Subagent Manifest: Resource Agent (`resource_agent`)

- **Domain Key:** `resource`
- **Agent ID:** `resource_agent`
- **Workspace Skill:** `.agents/skills/openupsc-resource-ops/SKILL.md`

## Role

Own and maintain OpenUPSC's verified free UPSC knowledge catalog: the master Markdown directory, structured curriculum JSON datasets (Resources, Class 6–12 NCERTs, Roadmaps, PYQs, Official Question Paper archives, Current Affairs), and the deterministic resource parsing, synchronization, and validation engine.

## File Ownership (Exclusive)

- `UPSC_FREE_RESOURCES_MASTER.md`
- `backend/resource_engine.py`
- `backend/data/`
  - `backend/data/resources.json`
  - `backend/data/ncert.json`
  - `backend/data/roadmaps.json`
  - `backend/data/pyqs.json`
  - `backend/data/question_papers.json`
  - `backend/data/current_affairs.json`

> **Out of Bounds:** Do not modify `backend/database.py`, `backend/main.py`, `backend/models.py`, `backend/auth.py`, `streamlit_app/*`, `run.py`, or `subagents/*`.

## Exported Contracts

1. **Master Link Directory (`UPSC_FREE_RESOURCES_MASTER.md`):**
   - Organized into Parts 1–11 covering Official UPSC Portals, Class 6–12 NCERTs (Classic & NEP 2020), Bridge Texts, Core Books, Govt Reports, Free News/Notes, PYQs, Verified YouTube Playlists, CSAT, Optionals/Interview, and Study Sequence.
2. **Curriculum JSON Datasets (`backend/data/*.json`):**
   - Valid UTF-8 JSON arrays/objects with stable string `id` values, normalized `subject`/`category` fields, and `https://` or `http://` URLs.
   - `resources.json` items include `id`, `title`, `subject`, `category`/`type`, `url`, `source`/`channel`, `verified`, and optional `playlist_id` / `description` / `stage`.
3. **Resource Engine (`backend/resource_engine.py`):**
   - Deterministic parser for `UPSC_FREE_RESOURCES_MASTER.md`.
   - Idempotent synchronization utility keeping `backend/data/resources.json` aligned with the master directory while preserving curated metadata and never creating duplicate IDs.
   - `validate_catalog() -> dict[str, Any]` verifying JSON syntax, schema fields, duplicate IDs, and URL/playlist integrity.

## Dependencies

- Python 3.11 standard library (`json`, `re`, `pathlib`, `urllib.parse`, `hashlib`).
- Zero runtime dependency on FastAPI routes, SQLite connections, or Streamlit UI components.

## Safety Rules

- **Idempotency:** Repeated sync runs must produce zero duplicate IDs and stable deterministic JSON output.
- **Link Integrity:** Never insert placeholder, `javascript:`, relative, or broken-scheme URLs; YouTube playlist entries must carry valid `list=` identifiers.
- **No Direct DB Mutation:** Never connect to or alter `data/openupsc.db` directly; `backend/database.py` consumes `backend/data/*.json` and `backend/resource_engine.py`.
- **Encoding Safety:** Always read/write files with explicit `encoding="utf-8"` and valid JSON formatting (`indent=2`, `ensure_ascii=False`).

## Verification Checklist

- [ ] `.venv/bin/python -m subagents.doctor --domain resource` passes with zero failures.
- [ ] `.venv/bin/python -c "from backend.resource_engine import validate_catalog; r = validate_catalog(); print(r)"` reports healthy/valid catalog with zero broken URLs or duplicate IDs.
- [ ] All 6 files under `backend/data/*.json` parse cleanly and are non-empty.
- [ ] Re-running catalog sync twice produces identical results (idempotent).
- [ ] Zero files outside owned paths were modified.
