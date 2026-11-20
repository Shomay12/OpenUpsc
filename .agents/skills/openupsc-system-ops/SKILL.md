---
name: openupsc-system-ops
description: Workflow for running OpenUPSC's self-healing supervisor (run.py), programmatic subagent registry, cross-domain health doctor (python -m subagents.doctor), and isolated automated test suite.
---

# OpenUPSC System Operations (`system_agent`)

Use this skill for launching/supervising the OpenUPSC stack, inspecting subagent ownership boundaries, running cross-domain health diagnostics, and executing the isolated automated test suite.

## Owned Files (Strict Boundary)

- `run.py`
- `subagents/__init__.py`
- `subagents/registry.py`
- `subagents/doctor.py`
- `AGENTS.md`
- `.agents/subagents/*.md`
- `.agents/skills/*/SKILL.md`
- `tests/*.py`
- `requirements.txt`
- `README.md`

Never edit business logic inside `backend/*`, `streamlit_app/*`, or `UPSC_FREE_RESOURCES_MASTER.md` under this skill. If a test or probe exposes a defect in another domain, report the exact file, line number, and minimal repro back to the coordinator.

## Operational Commands (`.venv/bin/python`)

### 1. Subagent Health Doctor (`subagents.doctor`)
Run health checks for a single independent domain or the entire platform:
```bash
# Check individual subsystems independently
.venv/bin/python -m subagents.doctor --domain resource
.venv/bin/python -m subagents.doctor --domain backend
.venv/bin/python -m subagents.doctor --domain frontend
.venv/bin/python -m subagents.doctor --domain system

# Full platform diagnostic report (human-readable or JSON)
.venv/bin/python -m subagents.doctor --domain all
.venv/bin/python -m subagents.doctor --domain all --json

# Strict CI mode (non-zero exit code on degraded OR error)
.venv/bin/python -m subagents.doctor --domain all --strict
```

### 2. Ownership Boundary Audit (`subagents.registry`)
Verify all 4 subagents have strictly disjoint file ownership and inspect declared paths:
```bash
.venv/bin/python -c "
import json
from subagents.registry import list_subagents, check_ownership_boundaries
print('Registered domains:', [s['domain'] for s in list_subagents()])
report = check_ownership_boundaries()
print(json.dumps(report, indent=2))
assert report['ok'], f'Ownership overlap detected: {report[\"overlaps\"]}'
"
```

### 3. Self-Healing Process Supervisor (`run.py`)
```bash
# Run pre-flight checks only (DB integrity + backup + catalog + doctor) without starting servers
.venv/bin/python run.py --doctor

# Start full supervised stack (FastAPI + Streamlit) with auto-restart & graceful Ctrl+C cleanup
.venv/bin/python run.py

# Automatically select free ports if 8000 / 8501 are busy
.venv/bin/python run.py --auto-port

# Run individual layers independently
.venv/bin/python run.py --api-only
.venv/bin/python run.py --ui-only
```

### 4. Automated Test Suite (`tests/`)
All tests enforce `OPENUPSC_DB_PATH` isolation in temporary directories and verify `data/openupsc.db` is never modified:
```bash
.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
```
