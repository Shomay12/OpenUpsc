"""Programmatic subagent registry and file-ownership boundary enforcer for OpenUPSC.

Defines the 4 strictly independent domains:
- resource: Master free UPSC resource guide, JSON curriculum datasets, and resource engine.
- backend:  FastAPI REST API, PBKDF2 auth, SQLite WAL persistence, backups, and analytics.
- frontend: Modular Streamlit application, dual-mode client, theme, and companion web assets.
- system:   Process supervisor, subagent registry/doctor, workspace governance, and test suite.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

CANONICAL_DOMAINS: tuple[str, ...] = ("resource", "backend", "frontend", "system")

_IGNORED_PATH_PARTS = {"__pycache__", ".DS_Store", ".pytest_cache", ".mypy_cache"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


@dataclass
class SubagentSpec:
    """Declarative specification for an independent OpenUPSC subagent domain."""

    id: str
    name: str
    domain: str
    role: str
    owned_paths: list[str]
    contracts: list[str]
    entrypoint_hint: str
    description: str
    manifest_path: str = ""
    skill_path: str = ""
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable copy of this subagent specification."""
        data = asdict(self)
        data["owned_paths"] = list(self.owned_paths)
        data["contracts"] = list(self.contracts)
        data["dependencies"] = list(self.dependencies)
        return data


SUBAGENTS: dict[str, SubagentSpec] = {
    "resource": SubagentSpec(
        id="resource_agent",
        name="Resource & Curriculum Agent",
        domain="resource",
        role="Curate, parse, synchronize, and validate OpenUPSC's 100% free UPSC resource catalog and curriculum JSON datasets.",
        owned_paths=[
            "UPSC_FREE_RESOURCES_MASTER.md",
            "backend/resource_engine.py",
            "backend/data/",
        ],
        contracts=[
            "UPSC_FREE_RESOURCES_MASTER.md: 11-part verified free UPSC directory (Official UPSC, Class 6-12 NCERTs, YouTube playlists, PYQs, CSAT, Interview).",
            "backend/data/*.json: Schema-valid UTF-8 JSON datasets (resources, ncert, roadmaps, pyqs, question_papers, current_affairs).",
            "backend.resource_engine: Deterministic master Markdown parser, idempotent catalog sync, and validate_catalog() -> dict[str, Any].",
        ],
        entrypoint_hint="backend/resource_engine.py",
        description=(
            "Single source of truth for verified free UPSC video playlists, official NCERT direct PDFs, "
            "roadmaps, PYQs, question paper archives, and current affairs links."
        ),
        manifest_path=".agents/subagents/resource-agent.md",
        skill_path=".agents/skills/openupsc-resource-ops/SKILL.md",
        dependencies=[],
    ),
    "backend": SubagentSpec(
        id="backend_agent",
        name="Backend API & Persistence Agent",
        domain="backend",
        role="Own FastAPI REST endpoints, PBKDF2 authentication/sessions, SQLite WAL persistence, migrations, backups, and readiness analytics.",
        owned_paths=[
            "backend/__init__.py",
            "backend/auth.py",
            "backend/models.py",
            "backend/database.py",
            "backend/main.py",
        ],
        contracts=[
            "backend.main: FastAPI ASGI app exposing /api/health, /api/auth/*, /api/workspace, /api/resources, /api/ncert, /api/pyqs, /api/roadmaps, /api/analytics/overview, /api/admin/*.",
            "backend.database: Dynamic OPENUPSC_DB_PATH resolution, WAL+FK get_connection(), idempotent init_db(), check_db_integrity(), rolling SQLite backup_database(), CRUD & analytics helpers.",
            "backend.auth & backend.models: PBKDF2-HMAC-SHA256 password hashing, secure session tokens, and strict Pydantic v2 validation schemas.",
        ],
        entrypoint_hint="backend/main.py",
        description=(
            "Provides hardened REST APIs, user isolation, study/PYQ analytics, and thread-safe SQLite "
            "persistence used by both HTTP clients and Streamlit's direct offline fallback."
        ),
        manifest_path=".agents/subagents/backend-agent.md",
        skill_path=".agents/skills/openupsc-backend-ops/SKILL.md",
        dependencies=["resource"],
    ),
    "frontend": SubagentSpec(
        id="frontend_agent",
        name="Frontend Streamlit & UI Agent",
        domain="frontend",
        role="Own the modular Python Streamlit student/analytics/admin UI, dual-mode OpenUPSCClient, theme system, and companion static assets.",
        owned_paths=[
            ".streamlit/config.toml",
            "streamlit_app/",
            "frontend/",
        ],
        contracts=[
            "streamlit_app/app.py & streamlit_app/dashboard.py: Modular multi-view Streamlit entrypoints runnable via streamlit run and testable via AppTest.",
            "streamlit_app/client.py: OpenUPSCClient with FastAPI HTTP primary path and automatic direct backend.database SQLite fallback.",
            "streamlit_app/theme.py & .streamlit/config.toml: Centralized visual styling tokens, cards, and headless server config.",
        ],
        entrypoint_hint="streamlit_app/app.py",
        description=(
            "Delivers a distraction-free UPSC preparation workspace and analytics studio that remains "
            "fully operational whether the FastAPI server is online or offline."
        ),
        manifest_path=".agents/subagents/frontend-agent.md",
        skill_path=".agents/skills/openupsc-frontend-streamlit/SKILL.md",
        dependencies=["backend"],
    ),
    "system": SubagentSpec(
        id="system_agent",
        name="System Supervision & Verification Agent",
        domain="system",
        role="Own the self-healing process supervisor, subagent registry, cross-domain health doctor, governance docs, and isolated automated test suite.",
        owned_paths=[
            "run.py",
            "subagents/",
            "AGENTS.md",
            ".agents/",
            "tests/",
            "requirements.txt",
            "README.md",
        ],
        contracts=[
            "run.py: Pre-flight DB integrity & backup, port conflict detection (--auto-port), exponential-backoff supervisor, --api-only / --ui-only / --doctor modes, clean signal teardown.",
            "subagents.registry: SubagentSpec, SUBAGENTS, list_subagents(), get_subagent(domain), check_ownership_boundaries().",
            "subagents.doctor: Lazy, fault-isolated probe_resource/backend/frontend/system(), run_diagnostics(domain), CLI python -m subagents.doctor.",
            "tests/: Isolated unittest + FastAPI TestClient + Streamlit AppTest suite using temporary OPENUPSC_DB_PATH.",
        ],
        entrypoint_hint="run.py",
        description=(
            "Enforces architectural boundaries, monitors subsystem health independently, supervises "
            "runtime processes, and verifies end-to-end unbreakability."
        ),
        manifest_path=".agents/subagents/system-agent.md",
        skill_path=".agents/skills/openupsc-system-ops/SKILL.md",
        dependencies=["resource", "backend", "frontend"],
    ),
}


def list_subagents() -> list[dict[str, Any]]:
    """Return all registered subagent specifications as JSON-serializable dicts."""
    return [SUBAGENTS[domain].to_dict() for domain in CANONICAL_DOMAINS]


def get_subagent(domain: str) -> SubagentSpec:
    """Look up a subagent specification by domain key (e.g. 'backend') or agent id (e.g. 'backend_agent')."""
    if not isinstance(domain, str) or not domain.strip():
        raise KeyError("Subagent domain must be a non-empty string.")
    normalized = domain.strip().lower()
    if normalized in SUBAGENTS:
        return SUBAGENTS[normalized]
    for spec in SUBAGENTS.values():
        if spec.id.lower() == normalized:
            return spec
    valid = ", ".join(CANONICAL_DOMAINS)
    raise KeyError(f"Unknown subagent domain {domain!r}. Valid domains: {valid}")


def _normalize_pattern(pattern: str) -> tuple[str, bool]:
    """Return (clean_posix_path, is_directory_hint) while preserving dotfile prefixes."""
    raw = pattern.strip().replace("\\", "/")
    is_dir = raw.endswith("/")
    cleaned = raw
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    cleaned = cleaned.rstrip("/")
    return cleaned, is_dir


def _has_glob_magic(pattern: str) -> bool:
    return any(ch in pattern for ch in ("*", "?", "["))


def _patterns_overlap(pat_a: str, pat_b: str) -> str | None:
    """Return an overlap reason string if two declared ownership patterns overlap, else None."""
    norm_a, dir_a = _normalize_pattern(pat_a)
    norm_b, dir_b = _normalize_pattern(pat_b)

    if norm_a == norm_b:
        return "exact_duplicate"

    parts_a = PurePosixPath(norm_a).parts
    parts_b = PurePosixPath(norm_b).parts

    # Directory containment check (e.g., 'backend/' contains 'backend/main.py' or 'backend/data/')
    if not _has_glob_magic(norm_a) and not _has_glob_magic(norm_b):
        if len(parts_a) < len(parts_b) and parts_b[: len(parts_a)] == parts_a:
            return "directory_containment"
        if len(parts_b) < len(parts_a) and parts_a[: len(parts_b)] == parts_b:
            return "directory_containment"
    else:
        # Check glob match against concrete path or prefix containment
        p_a = PurePosixPath(norm_a)
        p_b = PurePosixPath(norm_b)
        if not _has_glob_magic(norm_b) and p_b.match(norm_a):
            return "glob_match"
        if not _has_glob_magic(norm_a) and p_a.match(norm_b):
            return "glob_match"
        if dir_a and norm_b.startswith(norm_a + "/"):
            return "directory_glob_containment"
        if dir_b and norm_a.startswith(norm_b + "/"):
            return "directory_glob_containment"

    return None


def _is_ignored_file(rel_path: Path) -> bool:
    if any(part in _IGNORED_PATH_PARTS for part in rel_path.parts):
        return True
    if rel_path.suffix in _IGNORED_SUFFIXES:
        return True
    return False


def _resolve_pattern_files(root: Path, pattern: str) -> tuple[bool, set[str]]:
    """Check whether a declared ownership pattern exists on disk and resolve concrete files."""
    norm, _ = _normalize_pattern(pattern)
    resolved: set[str] = set()

    if _has_glob_magic(norm):
        matches = list(root.glob(norm))
        exists = len(matches) > 0
        for match in matches:
            if match.is_file():
                rel = match.relative_to(root)
                if not _is_ignored_file(rel):
                    resolved.add(rel.as_posix())
            elif match.is_dir():
                for child in match.rglob("*"):
                    if child.is_file():
                        rel = child.relative_to(root)
                        if not _is_ignored_file(rel):
                            resolved.add(rel.as_posix())
        return exists, resolved

    target = root / norm
    if not target.exists():
        return False, resolved

    if target.is_file():
        rel = target.relative_to(root)
        if not _is_ignored_file(rel):
            resolved.add(rel.as_posix())
        return True, resolved

    if target.is_dir():
        for child in target.rglob("*"):
            if child.is_file():
                rel = child.relative_to(root)
                if not _is_ignored_file(rel):
                    resolved.add(rel.as_posix())
        return True, resolved

    return False, resolved


def find_owner(rel_path: str) -> str | None:
    """Return the owning domain key for a repository-relative path, or None if unowned."""
    norm_target, _ = _normalize_pattern(rel_path)
    target_parts = PurePosixPath(norm_target).parts
    for domain in CANONICAL_DOMAINS:
        spec = SUBAGENTS[domain]
        for pattern in spec.owned_paths:
            norm_pat, is_dir = _normalize_pattern(pattern)
            if norm_target == norm_pat:
                return domain
            if _has_glob_magic(norm_pat):
                if PurePosixPath(norm_target).match(norm_pat):
                    return domain
            else:
                pat_parts = PurePosixPath(norm_pat).parts
                if (is_dir or len(target_parts) > len(pat_parts)) and target_parts[: len(pat_parts)] == pat_parts:
                    return domain
    return None


def check_ownership_boundaries(root: Path | None = None) -> dict[str, Any]:
    """Verify strictly non-overlapping ownership patterns across all 4 subagents and check path existence.

    Returns a structured report with:
      - ok: True iff zero pattern or resolved-file overlaps exist.
      - all_paths_exist: True iff every declared owned_path exists on disk.
      - overlaps: List of any detected cross-domain ownership conflicts.
      - missing_paths: Mapping of domain -> list of declared paths not found on disk.
      - per_domain: Detailed breakdown per domain.
    """
    repo_root = (root or REPO_ROOT).resolve()
    overlaps: list[dict[str, Any]] = []
    missing_paths: dict[str, list[str]] = {}
    per_domain: dict[str, dict[str, Any]] = {}

    # 1. Pairwise static pattern overlap detection
    domains = list(CANONICAL_DOMAINS)
    for i in range(len(domains)):
        d_a = domains[i]
        for j in range(i + 1, len(domains)):
            d_b = domains[j]
            for pat_a in SUBAGENTS[d_a].owned_paths:
                for pat_b in SUBAGENTS[d_b].owned_paths:
                    reason = _patterns_overlap(pat_a, pat_b)
                    if reason is not None:
                        overlaps.append(
                            {
                                "type": "pattern_overlap",
                                "reason": reason,
                                "domains": [d_a, d_b],
                                "paths": [pat_a, pat_b],
                            }
                        )

    # 2. On-disk existence & concrete resolved file intersection check
    file_to_domains: dict[str, list[str]] = {}
    total_declared_paths = 0
    all_resolved_files: set[str] = set()

    for domain in domains:
        spec = SUBAGENTS[domain]
        existing_list: list[str] = []
        missing_list: list[str] = []
        domain_files: set[str] = set()

        for pattern in spec.owned_paths:
            total_declared_paths += 1
            exists, files = _resolve_pattern_files(repo_root, pattern)
            if exists:
                existing_list.append(pattern)
            else:
                missing_list.append(pattern)
            domain_files.update(files)

        for rel_file in sorted(domain_files):
            file_to_domains.setdefault(rel_file, []).append(domain)
            all_resolved_files.add(rel_file)

        if missing_list:
            missing_paths[domain] = missing_list

        per_domain[domain] = {
            "id": spec.id,
            "owned_paths": list(spec.owned_paths),
            "existing_paths": existing_list,
            "missing_paths": missing_list,
            "resolved_file_count": len(domain_files),
        }

    for rel_file, owners in sorted(file_to_domains.items()):
        if len(owners) > 1:
            overlaps.append(
                {
                    "type": "resolved_file_overlap",
                    "reason": "multiple_owners",
                    "domains": owners,
                    "paths": [rel_file],
                }
            )

    return {
        "ok": len(overlaps) == 0,
        "all_paths_exist": len(missing_paths) == 0,
        "overlaps": overlaps,
        "missing_paths": missing_paths,
        "per_domain": per_domain,
        "checked_root": str(repo_root),
        "total_declared_paths": total_declared_paths,
        "total_resolved_files": len(all_resolved_files),
    }
