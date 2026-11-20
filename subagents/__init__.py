"""OpenUPSC 4-domain subagent registry and fault-isolated health diagnostics package."""

from __future__ import annotations

import importlib
from typing import Any

from subagents.registry import (
    CANONICAL_DOMAINS,
    SUBAGENTS,
    SubagentSpec,
    check_ownership_boundaries,
    find_owner,
    get_subagent,
    list_subagents,
)

_DOCTOR_EXPORTS = frozenset(
    {
        "probe_backend",
        "probe_frontend",
        "probe_resource",
        "probe_system",
        "run_diagnostics",
    }
)

__all__ = [
    "CANONICAL_DOMAINS",
    "SUBAGENTS",
    "SubagentSpec",
    "check_ownership_boundaries",
    "find_owner",
    "get_subagent",
    "list_subagents",
    "probe_backend",
    "probe_frontend",
    "probe_resource",
    "probe_system",
    "run_diagnostics",
]


def __getattr__(name: str) -> Any:
    """Lazily expose subagents.doctor helpers so `python -m subagents.doctor` emits no RuntimeWarning."""
    if name in _DOCTOR_EXPORTS:
        doctor_mod = importlib.import_module("subagents.doctor")
        return getattr(doctor_mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
