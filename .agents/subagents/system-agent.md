# Subagent Manifest: System Agent (`system_agent`)

- **Domain Key:** `system`
- **Agent ID:** `system_agent`
- **Workspace Skill:** `.agents/skills/openupsc-system-ops/SKILL.md`

## Role

Own OpenUPSC's platform reliability, self-healing process supervisor, programmatic 4-domain subagent registry, cross-domain health doctor, persistent Antigravity agent/skill governance documentation, and isolated end-to-end automated test suite.

## File Ownership (Exclusive)

- `run.py`
- `subagents/`
  - `subagents/__init__.py`
  - `subagents/registry.py`
  - `subagents/doctor.py`
- `AGENTS.md`
- `.agents/`
  - `.agents/subagents/*.md`
  - `.agents/skills/*/SKILL.md`
- `tests/` (`tests/*.py`)
- `requirements.txt`
- `README.md`

> **Out of Bounds:** Do not rewrite business logic inside `backend/*` or `streamlit_app/*` or `UPSC_FREE_RESOURCES_MASTER.md`. Audit and test them rigorously, reporting defects with exact file, line, and reproduction steps back to the coordinator.

## Exported Contracts

1. **Subagent Registry (`subagents/registry.py`):**
   - `SubagentSpec` dataclass (`id`, `name`, `domain`, `role`, `owned_paths`, `contracts`, `entrypoint_hint`, `description`)
   - `SUBAGENTS: dict[str, SubagentSpec]` (`"resource"`, `"backend"`, `"frontend"`, `"system"`)
   - `list_subagents() -> list[dict[str, Any]]`
   - `get_subagent(domain: str) -> SubagentSpec`
   - `check_ownership_boundaries() -> dict[str, Any]`
2. **Health Doctor (`subagents/doctor.py`):**
   - `probe_resource() -> dict[str, Any]`
   - `probe_backend() -> dict[str, Any]`
   - `probe_frontend() -> dict[str, Any]`
   - `probe_system() -> dict[str, Any]`
   - `run_diagnostics(domain: str = "all") -> dict[str, Any]`
   - CLI: `.venv/bin/python -m subagents.doctor --domain all|resource|backend|frontend|system [--json] [--strict]`
3. **Self-Healing Process Supervisor (`run.py`):**
   - Pre-flight DB integrity check, rolling SQLite backup, and resource catalog sync verification.
   - Port conflict detection with optional `--auto-port` fallback.
   - Exponential backoff auto-restart supervision for FastAPI and Streamlit child processes.
   - Modes: default (dual stack), `--api-only`, `--ui-only`, `--doctor`.
   - Clean `SIGINT`/`SIGTERM` process-group shutdown leaving zero orphan processes.
4. **Automated Test Suite (`tests/*.py`):**
   - Domain-isolated unit tests (Resource, Backend, Frontend, System), dual-mode resilience tests, and end-to-end integration tests runnable via `.venv/bin/python -m unittest discover -s tests -v`.

## Dependencies

- Lazily imports and audits `backend.*`, `streamlit_app.*`, and `UPSC_FREE_RESOURCES_MASTER.md` inside fault-tolerant `try/except` wrappers.
- Uses only `.venv/bin/python` installed dependencies (`requirements.txt`) plus Python 3.11 standard library (`unittest`, `sqlite3`, `tomllib`, `socket`, `subprocess`, `signal`).

## Safety Rules

- **Zero Production DB Mutation:** All tests must isolate SQLite state via `OPENUPSC_DB_PATH` inside a temporary directory and verify `data/openupsc.db` is untouched.
- **Fault-Isolated Probes:** A syntax error or missing module in one domain must never crash `subagents.doctor` when checking another domain.
- **Read-Only Diagnostics:** Running `subagents.doctor` must never perform destructive writes or leave stray temporary files in the workspace.
- **Process Hygiene:** `run.py` must always reap child process groups on exit and cap restart storms via bounded exponential backoff.

## Verification Checklist

- [ ] `.venv/bin/python -m subagents.doctor --domain system` exits `0` with zero failures.
- [ ] `check_ownership_boundaries()` confirms zero overlapping ownership patterns across all 4 subagents.
- [ ] `.venv/bin/python -m subagents.doctor --domain all --json` emits valid JSON with all 4 domains.
- [ ] `.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v` passes 100% (Phase 2+).
- [ ] `run.py --doctor` runs cleanly and verifies pre-flight readiness (Phase 2+).
