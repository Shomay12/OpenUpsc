"""SQLite database setup, hardened persistence layer, curriculum loaders, and UPSC Readiness analytics.

Serves as the Single Source of Truth for BOTH FastAPI (`backend/main.py`) and
Streamlit's direct SQLite offline fallback (`streamlit_app/client.py`).
"""

from __future__ import annotations

import copy
import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Generator, Optional
from urllib.parse import quote_plus

from backend.auth import (
    generate_session_token,
    hash_password,
    verify_password,
)

try:
    from backend.resource_engine import (
        extract_youtube_playlist_id as _engine_extract_youtube_playlist_id,
    )
except Exception:  # pragma: no cover - defensive fallback if engine unavailable
    _engine_extract_youtube_playlist_id = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_JSON_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DB_PATH = BASE_DIR / "data" / "openupsc.db"

# Indian Standard Time (UTC+5:30) for authentic UPSC daily study buckets & streaks
IST = timezone(timedelta(hours=5, minutes=30))

DEMO_USER_ID = "usr-default-student"
DEMO_USER_EMAIL = "student@upschub.in"
DEMO_USER_PASSWORD = "openupsc123"

LEGACY_PLACEHOLDER_IDS = {
    "res-ncert-history-mega",
    "res-ncert-geo-mega",
    "res-ncert-polity-strategy",
    "res-ncert-economy-ied",
    "res-spectrum-modern",
    "res-laxmikanth-master",
    "res-world-mapping",
    "res-csat-quant-reasoning",
}

STALE_SEEDED_URLS = {
    "https://www.youtube.com/@SansadTV",
    "https://prsindia.org",
    "https://pib.gov.in",
}

LEGACY_SUBJECT_NAMES = {
    "Optional & Bridge",
    "International Relations",
    "Internal Security",
}

ROADMAP_SUBJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "history": ("history", "art"),
    "geography": ("geography",),
    "polity": ("polity", "governance"),
    "economy": ("economy",),
    "environment": ("environment", "ecology"),
    "ethics": ("ethics",),
    "csat": ("csat",),
    "scitech": ("science", "tech", "security"),
}


# =========================================================================
# SAFE HELPERS (JSON, YOUTUBE, IST TIME & STREAK)
# =========================================================================


def _safe_json_loads(raw: Any, default: Any) -> Any:
    """Safely deserialize JSON from SQLite columns without ever crashing on malformed data."""
    fallback = copy.deepcopy(default)
    if raw is None:
        return fallback
    if isinstance(raw, (dict, list)):
        if isinstance(default, dict) and not isinstance(raw, dict):
            return fallback
        if isinstance(default, list) and not isinstance(raw, list):
            return fallback
        return copy.deepcopy(raw)
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    if not isinstance(raw, str):
        return fallback
    stripped = raw.strip()
    if not stripped:
        return fallback
    try:
        parsed = json.loads(stripped)
    except (ValueError, TypeError):
        return fallback
    if parsed is None:
        return fallback
    if isinstance(default, dict) and not isinstance(parsed, dict):
        return fallback
    if isinstance(default, list) and not isinstance(parsed, list):
        return fallback
    return parsed


def extract_youtube_playlist_id(url: Optional[str]) -> Optional[str]:
    """Extract a YouTube playlist ID (`list=...`) cleanly using resource_engine when available."""
    if not url:
        return None
    if _engine_extract_youtube_playlist_id is not None:
        return _engine_extract_youtube_playlist_id(url)
    m = re.search(r"[?&]list=([A-Za-z0-9_-]{8,})", url)
    return m.group(1) if m else None


def _now_ist() -> datetime:
    return datetime.now(IST)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_str() -> str:
    return _now_ist().strftime("%Y-%m-%d")


def _today_weekday() -> str:
    return _now_ist().strftime("%A")


def _to_ist_date_str(ts: Optional[str]) -> Optional[str]:
    """Parse an ISO-8601 timestamp or YYYY-MM-DD date string and return YYYY-MM-DD in IST."""
    if not ts or not isinstance(ts, str):
        return None
    cleaned = ts.strip()
    if not cleaned:
        return None

    # Exact date-only string (e.g. "2026-11-20")
    if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
        try:
            return date.fromisoformat(cleaned).isoformat()
        except ValueError:
            return None

    iso_candidate = cleaned[:-1] + "+00:00" if cleaned.endswith(("Z", "z")) else cleaned
    try:
        dt = datetime.fromisoformat(iso_candidate)
        if dt.tzinfo is not None:
            dt = dt.astimezone(IST)
        return dt.date().isoformat()
    except ValueError:
        # Final safe attempt on leading date prefix
        prefix = cleaned[:10]
        try:
            return date.fromisoformat(prefix).isoformat()
        except ValueError:
            return None


def _compute_effective_streak(
    stored_streak: Any,
    last_study_date: Optional[str],
    today_date: Optional[date] = None,
) -> int:
    """Compute live displayed streak in IST without mutating the database on read."""
    try:
        streak = int(stored_streak or 0)
    except (ValueError, TypeError):
        return 0
    if streak <= 0 or not last_study_date:
        return 0
    last_date_str = _to_ist_date_str(last_study_date)
    if not last_date_str:
        return 0
    today = today_date or _now_ist().date()
    yesterday = today - timedelta(days=1)
    if last_date_str in (today.isoformat(), yesterday.isoformat()):
        return streak
    return 0


# =========================================================================
# CONNECTION, INTEGRITY, BACKUP & SESSION CLEANUP
# =========================================================================


def get_db_path() -> Path:
    """Dynamically resolve OPENUPSC_DB_PATH so tests always stay isolated from production."""
    env_path = os.environ.get("OPENUPSC_DB_PATH")
    path = Path(env_path) if env_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Open a hardened SQLite WAL connection with foreign keys and busy timeout enabled."""
    conn = sqlite3.connect(
        str(get_db_path()),
        timeout=30.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_db_integrity() -> dict[str, Any]:
    """Run non-mutating PRAGMA integrity_check, table counts, and DB file telemetry."""
    db_path = get_db_path()
    if not db_path.exists():
        return {
            "ok": False,
            "healthy": False,
            "status": "missing",
            "integrity": "missing",
            "integrity_messages": ["Database file does not exist yet."],
            "foreign_key_violations": 0,
            "journal_mode": None,
            "db_path": str(db_path),
            "size_bytes": 0,
            "table_count": 0,
            "tables": {},
            "total_rows": 0,
            "checked_at": _utc_now(),
        }

    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=10.0)
    except sqlite3.OperationalError:
        conn = sqlite3.connect(str(db_path), timeout=10.0)

    try:
        integrity_rows = [r[0] for r in conn.execute("PRAGMA integrity_check;").fetchall()]
        integrity_ok = integrity_rows == ["ok"]
        fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
        jm_row = conn.execute("PRAGMA journal_mode;").fetchone()
        journal_mode = jm_row[0] if jm_row else None

        table_names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
            ).fetchall()
        ]
        table_counts: dict[str, int] = {}
        for tbl in table_names:
            quoted = '"' + tbl.replace('"', '""') + '"'
            cnt = conn.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
            table_counts[tbl] = int(cnt)
    finally:
        conn.close()

    size_bytes = db_path.stat().st_size
    wal_path = Path(f"{db_path}-wal")
    wal_size_bytes = wal_path.stat().st_size if wal_path.exists() else 0

    return {
        "ok": integrity_ok,
        "healthy": integrity_ok,
        "status": "ok" if integrity_ok else "error",
        "integrity": integrity_rows[0] if len(integrity_rows) == 1 else "; ".join(integrity_rows),
        "integrity_messages": integrity_rows,
        "foreign_key_violations": len(fk_violations),
        "journal_mode": journal_mode,
        "db_path": str(db_path),
        "size_bytes": size_bytes,
        "wal_size_bytes": wal_size_bytes,
        "table_count": len(table_counts),
        "tables": table_counts,
        "total_rows": sum(table_counts.values()),
        "checked_at": _utc_now(),
    }


def _resolve_backup_dir(backup_dir: Optional[Path] = None) -> Path:
    if backup_dir is not None:
        return Path(backup_dir)
    return get_db_path().parent / "backups"


def list_backups(backup_dir: Optional[Path] = None) -> list[dict[str, Any]]:
    """List available rolling SQLite backup snapshots sorted newest first."""
    target_dir = _resolve_backup_dir(backup_dir)
    if not target_dir.exists() or not target_dir.is_dir():
        return []
    files = sorted(
        (p for p in target_dir.glob("*.db") if p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    items: list[dict[str, Any]] = []
    for p in files:
        st = p.stat()
        items.append(
            {
                "filename": p.name,
                "path": str(p),
                "size_bytes": st.st_size,
                "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return items


def backup_database(
    backup_dir: Optional[Path] = None,
    max_backups: int = 10,
) -> dict[str, Any]:
    """Create an atomic online SQLite backup via conn.backup() with rolling retention."""
    db_path = get_db_path()
    if not db_path.exists():
        init_db()

    target_dir = _resolve_backup_dir(backup_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    backup_path = target_dir / f"{db_path.stem}_{stamp}.db"

    src = sqlite3.connect(str(db_path), timeout=30.0)
    dest = sqlite3.connect(str(backup_path), timeout=30.0)
    try:
        src.execute("PRAGMA busy_timeout = 10000;")
        src.backup(dest)
        integrity_rows = [r[0] for r in dest.execute("PRAGMA integrity_check;").fetchall()]
        backup_ok = integrity_rows == ["ok"]
    finally:
        dest.close()
        src.close()

    pruned = 0
    keep_n = max(1, int(max_backups))
    existing = sorted(
        (p for p in target_dir.glob(f"{db_path.stem}_*.db") if p.is_file()),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
    for stale in existing[keep_n:]:
        try:
            stale.unlink()
            pruned += 1
        except OSError:
            pass

    remaining = list_backups(target_dir)
    return {
        "ok": backup_ok,
        "filename": backup_path.name,
        "path": str(backup_path),
        "backup_dir": str(target_dir),
        "size_bytes": backup_path.stat().st_size if backup_path.exists() else 0,
        "created_at": _utc_now(),
        "retained_count": len(remaining),
        "pruned_count": pruned,
        "integrity": integrity_rows[0] if integrity_rows else "unknown",
    }


def cleanup_expired_sessions(conn: Optional[sqlite3.Connection] = None) -> int:
    """Purge expired session rows and return the number of deleted tokens."""
    now_iso = _utc_now()
    if conn is not None:
        cur = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso,))
        return int(cur.rowcount or 0)
    with get_connection() as managed_conn:
        cur = managed_conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now_iso,))
        return int(cur.rowcount or 0)


# =========================================================================
# CURRICULUM & MASTER GUIDE LOADERS
# =========================================================================


@lru_cache(maxsize=16)
def load_curriculum_json(filename: str) -> Any:
    path = DATA_JSON_DIR / filename
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def clear_curriculum_cache() -> None:
    """Clear cached JSON datasets after a catalog resync."""
    load_curriculum_json.cache_clear()


def get_master_guide_data() -> dict[str, Any]:
    """Load structured 11-part Master Guide JSON, falling back to live Markdown parse if missing."""
    try:
        data = load_curriculum_json("master_guide.json")
        if isinstance(data, dict) and data.get("parts"):
            return data
    except (FileNotFoundError, ValueError, OSError):
        pass
    from backend.resource_engine import parse_master_guide

    return parse_master_guide()


def get_study_sequence_data() -> list[dict[str, Any]]:
    """Return the Part 11 zero-cost step-by-step study sequence phases."""
    mg = get_master_guide_data()
    return list(mg.get("study_sequence", []))


def get_ncert_data() -> list[dict[str, Any]]:
    return load_curriculum_json("ncert.json")


def get_roadmaps_data() -> list[dict[str, Any]]:
    return load_curriculum_json("roadmaps.json")


def get_pyqs_data() -> list[dict[str, Any]]:
    return load_curriculum_json("pyqs.json")


def get_question_papers_data() -> list[dict[str, Any]]:
    return load_curriculum_json("question_papers.json")


def get_current_affairs_data() -> list[dict[str, Any]]:
    return load_curriculum_json("current_affairs.json")


# =========================================================================
# SCHEMA INITIALIZATION, SAFE MIGRATIONS & IDEMPOTENT SYNC
# =========================================================================


def _apply_schema_migrations(conn: sqlite3.Connection) -> None:
    """Apply strictly additive, idempotent migrations for existing user databases."""
    res_cols = {row["name"] for row in conn.execute("PRAGMA table_info(resources)").fetchall()}
    if "master_part" not in res_cols:
        conn.execute("ALTER TABLE resources ADD COLUMN master_part INTEGER")

    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_sessions_user_expires
            ON sessions(user_id, expires_at);
        CREATE INDEX IF NOT EXISTS idx_study_sessions_user_start
            ON study_sessions(user_id, start_time);
        CREATE INDEX IF NOT EXISTS idx_user_progress_user
            ON user_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_saved_resources_user
            ON saved_resources(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_notes_user
            ON user_notes(user_id);
        CREATE INDEX IF NOT EXISTS idx_timetable_events_user_day
            ON timetable_events(user_id, day_of_week);
        CREATE INDEX IF NOT EXISTS idx_pyq_attempts_user_subject
            ON pyq_attempts(user_id, subject);
        CREATE INDEX IF NOT EXISTS idx_resources_subject_type_level
            ON resources(subject, type, level);
        CREATE INDEX IF NOT EXISTS idx_resources_master_part
            ON resources(master_part);
        """
    )


def init_db() -> None:
    """Create all SQLite tables, run safe additive migrations, and sync resources & demo workspace."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                preparation_stage TEXT NOT NULL DEFAULT 'Foundation (Class 6-12)',
                target_attempt_year TEXT NOT NULL DEFAULT '2028',
                daily_target_hours INTEGER NOT NULL DEFAULT 4,
                preferred_language TEXT NOT NULL DEFAULT 'Hinglish',
                study_streak_days INTEGER NOT NULL DEFAULT 1,
                last_study_date TEXT,
                active_plan_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT NOT NULL,
                level TEXT NOT NULL DEFAULT 'Foundation',
                class_level TEXT,
                language TEXT NOT NULL DEFAULT 'English/Hinglish',
                type TEXT NOT NULL DEFAULT 'YouTube',
                provider TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                senior_tip TEXT,
                views TEXT,
                likes TEXT,
                channel_subscribers TEXT,
                playlist_length TEXT,
                estimated_hours INTEGER NOT NULL DEFAULT 0,
                free INTEGER NOT NULL DEFAULT 1,
                verified INTEGER NOT NULL DEFAULT 1,
                verification_status TEXT NOT NULL DEFAULT 'Verified',
                last_verified TEXT,
                verification_signals_json TEXT,
                prerequisites_json TEXT,
                next_resource_id TEXT,
                next_resource_title TEXT,
                tags_json TEXT NOT NULL DEFAULT '[]',
                master_part INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                progress_percentage INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'not_started',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, item_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_notes (
                user_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_title TEXT,
                item_category TEXT,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, item_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS saved_resources (
                user_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, resource_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                resource_id TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                session_type TEXT NOT NULL DEFAULT 'Focus',
                completed INTEGER NOT NULL DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pyq_attempts (
                user_id TEXT NOT NULL,
                pyq_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                selected_option TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                attempted_at TEXT NOT NULL,
                PRIMARY KEY (user_id, pyq_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS timetable_events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL DEFAULT 'Daily',
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                resource_id TEXT,
                resource_title TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS resource_suggestions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                subject TEXT NOT NULL,
                chapter_title TEXT NOT NULL,
                chapter_num INTEGER NOT NULL DEFAULT 0,
                url TEXT NOT NULL,
                channel TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
            """
        )

        _apply_schema_migrations(conn)
        _sync_verified_resources(conn)

        demo_exists = conn.execute(
            "SELECT 1 FROM users WHERE id = ?", (DEMO_USER_ID,)
        ).fetchone()
        if not demo_exists:
            _seed_demo_user(conn)


def _sync_verified_resources(
    conn: sqlite3.Connection,
    resources_override: Optional[list[dict[str, Any]]] = None,
) -> dict[str, int]:
    """Idempotently sync all verified resources into SQLite without clobbering custom resources."""
    now = _utc_now()
    for bad_id in LEGACY_PLACEHOLDER_IDS:
        conn.execute("DELETE FROM resources WHERE id = ?", (bad_id,))
        conn.execute("DELETE FROM saved_resources WHERE resource_id = ?", (bad_id,))

    initial_resources = (
        resources_override
        if resources_override is not None
        else load_curriculum_json("resources.json")
    )

    inserted = 0
    updated = 0
    unchanged = 0

    for res in initial_resources:
        rid = res["id"]
        if str(rid).startswith("res-custom-"):
            continue
        master_part = (
            res.get("masterPart")
            if res.get("masterPart") is not None
            else res.get("master_part")
        )
        if master_part is not None:
            try:
                master_part = int(master_part)
            except (ValueError, TypeError):
                master_part = None

        existing = conn.execute(
            "SELECT id, url, master_part, subject, type FROM resources WHERE id = ?",
            (rid,),
        ).fetchone()

        if not existing:
            conn.execute(
                """
                INSERT INTO resources (
                    id, title, subject, category, level, class_level, language, type,
                    provider, url, description, senior_tip, views, likes,
                    channel_subscribers, playlist_length, estimated_hours, free,
                    verified, verification_status, last_verified,
                    verification_signals_json, prerequisites_json,
                    next_resource_id, next_resource_title, tags_json, master_part, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rid,
                    res["title"],
                    res["subject"],
                    res.get("category", "General"),
                    res.get("level", "Foundation"),
                    res.get("classLevel"),
                    res.get("language", "English/Hinglish"),
                    res.get("type", "YouTube"),
                    res.get("provider", "Independent"),
                    res["url"],
                    res.get("description", ""),
                    res.get("seniorTip"),
                    res.get("views"),
                    res.get("likes"),
                    res.get("channelSubscribers"),
                    res.get("playlistLength"),
                    int(res.get("estimatedHours", 0) or 0),
                    1 if res.get("free", True) else 0,
                    1 if res.get("verified", True) else 0,
                    res.get("verificationStatus", "Verified"),
                    res.get("lastVerified", _today_str()),
                    json.dumps(res.get("verificationSignals", {})),
                    json.dumps(res.get("prerequisites", [])),
                    res.get("nextResourceId"),
                    res.get("nextResourceTitle"),
                    json.dumps(res.get("tags", [])),
                    master_part,
                    now,
                ),
            )
            inserted += 1
        elif existing["url"] in STALE_SEEDED_URLS:
            conn.execute(
                """
                UPDATE resources
                SET url = ?, title = ?, description = ?, senior_tip = ?,
                    subject = ?, type = ?, master_part = ?, last_verified = ?
                WHERE id = ?
                """,
                (
                    res["url"],
                    res["title"],
                    res.get("description", ""),
                    res.get("seniorTip"),
                    res["subject"],
                    res.get("type", "YouTube"),
                    master_part,
                    res.get("lastVerified", _today_str()),
                    rid,
                ),
            )
            updated += 1
        elif (
            (existing["master_part"] is None and master_part is not None)
            or (existing["subject"] in LEGACY_SUBJECT_NAMES and existing["subject"] != res["subject"])
        ):
            conn.execute(
                """
                UPDATE resources
                SET master_part = COALESCE(?, master_part),
                    subject = ?,
                    type = ?,
                    last_verified = ?
                WHERE id = ?
                """,
                (
                    master_part,
                    res["subject"],
                    res.get("type", existing["type"]),
                    res.get("lastVerified", _today_str()),
                    rid,
                ),
            )
            updated += 1
        else:
            unchanged += 1

    return {
        "inserted": inserted,
        "updated": updated,
        "unchanged": unchanged,
        "total_in_json": len(initial_resources),
    }


def sync_resources_from_master(write_json: bool = True) -> dict[str, Any]:
    """Run resource_engine master sync, refresh caches, and idempotently sync SQLite catalog."""
    from backend.resource_engine import (
        MASTER_GUIDE_PATH,
        build_enriched_resources,
        parse_master_guide,
        sync_master_files,
    )

    engine_summary = sync_master_files(write_files=write_json)
    clear_curriculum_cache()

    resources_override: Optional[list[dict[str, Any]]] = None
    if not write_json:
        mg = parse_master_guide(MASTER_GUIDE_PATH)
        existing_json = load_curriculum_json("resources.json")
        resources_override = build_enriched_resources(existing_json, mg)

    with get_connection() as conn:
        _apply_schema_migrations(conn)
        db_sync = _sync_verified_resources(conn, resources_override=resources_override)
        db_total = int(conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0])

    validation = engine_summary.get("validation", {})
    return {
        "ok": bool(validation.get("valid", True)),
        "written": write_json,
        "engine": engine_summary,
        "db_sync": db_sync,
        "db_total_resources": db_total,
        "validation": validation,
    }


# =========================================================================
# DEMO SEEDING & STREAK TRACKING
# =========================================================================


def _seed_demo_user(conn: sqlite3.Connection) -> None:
    now = _utc_now()
    today = _today_str()
    conn.execute(
        """
        INSERT INTO users (
            id, email, password_hash, full_name, role, preparation_stage,
            target_attempt_year, daily_target_hours, preferred_language,
            study_streak_days, last_study_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            DEMO_USER_ID,
            DEMO_USER_EMAIL,
            hash_password(DEMO_USER_PASSWORD),
            "Khushi",
            "admin",
            "Foundation (Class 6-12)",
            "2028",
            4,
            "Hinglish",
            7,
            today,
            now,
            now,
        ),
    )
    seed_user_defaults(conn, DEMO_USER_ID, with_demo_history=True)


def seed_user_defaults(
    conn: sqlite3.Connection, user_id: str, with_demo_history: bool = False
) -> None:
    """Populate starter timetable and optionally demo progress/sessions/PYQ attempts."""
    now = _utc_now()
    default_timetable = [
        (
            "History",
            "Modern Indian History (Spectrum + Bookstawa)",
            "Daily",
            "06:30",
            "07:30",
            "res-bookstawa-modern",
            "Modern Indian History Complete Animated Series",
            1 if with_demo_history else 0,
        ),
        (
            "Indian Polity",
            "Indian Constitution at Work & Magna Carta Polity",
            "Daily",
            "08:00",
            "09:00",
            "res-atish-magna-carta",
            "Magna Carta — Complete Free Indian Polity Course",
            0,
        ),
        (
            "Current Affairs",
            "Daily PIB, PRS Bill Track & Sansad TV Perspective",
            "Daily",
            "18:00",
            "19:00",
            "res-pib-portal",
            "Press Information Bureau (PIB)",
            0,
        ),
        (
            "Geography",
            "Class 11 Physical Geography & Indian Mapping",
            "Daily",
            "20:00",
            "21:00",
            "res-amit-c11-phys-geo",
            "Class 11 Fundamentals of Physical Geography",
            0,
        ),
    ]
    for item in default_timetable:
        conn.execute(
            """
            INSERT INTO timetable_events (
                id, user_id, day_of_week, start_time, end_time,
                subject, topic, resource_id, resource_title, completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"tt-{uuid.uuid4().hex[:10]}",
                user_id,
                item[2],
                item[3],
                item[4],
                item[0],
                item[1],
                item[5],
                item[6],
                item[7],
                now,
                now,
            ),
        )

    if not with_demo_history:
        return

    default_progress = {
        "res-sleepy-ncert-all": 100,
        "res-amit-c11-phys-geo": 100,
        "res-hd-c11-polity": 75,
        "res-atish-magna-carta": 50,
        "res-bookstawa-modern": 75,
        "res-mrunal-economy-beginners": 50,
        "res-pmf-environment-video": 25,
        "res-ungist-csat-full": 25,
        "ncert-c6-history": 100,
        "ncert-c6-geography": 100,
        "ncert-c6-civics": 100,
        "ncert-c11-polity-constitution": 75,
        "ncert-c11-geography-physical": 100,
        "ncert-c11-fine-arts": 50,
        "hist-s1": 100,
        "hist-s2": 75,
        "pol-s1": 100,
        "pol-s2": 50,
        "geo-s1": 100,
        "geo-s2": 75,
        "eco-s1": 50,
    }
    for item_id, pct in default_progress.items():
        status = "completed" if pct >= 100 else ("in_progress" if pct > 0 else "not_started")
        conn.execute(
            """
            INSERT OR REPLACE INTO user_progress (user_id, item_id, progress_percentage, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, item_id, pct, status, now),
        )

    for res_id in [
        "res-upsc-official-pyqs",
        "res-atish-magna-carta",
        "res-mrunal-economy-beginners",
        "res-bookstawa-modern",
        "res-vision-free-resources",
    ]:
        conn.execute(
            "INSERT OR IGNORE INTO saved_resources (user_id, resource_id, created_at) VALUES (?, ?, ?)",
            (user_id, res_id, now),
        )

    conn.execute(
        """
        INSERT OR REPLACE INTO user_notes (user_id, item_id, item_title, item_category, content, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "ncert-c11-polity-constitution",
            "Indian Constitution at Work",
            "Polity",
            (
                "## Article 32 Writs Summary\n"
                "- **Habeas Corpus**: To produce the body (unlawful detention).\n"
                "- **Mandamus**: We command (public duty enforcement).\n"
                "- **Prohibition**: Higher court to lower court preventing excess jurisdiction.\n"
                "- **Certiorari**: Quashing illegal orders.\n"
                "- **Quo-Warranto**: By what authority (preventing illegal usurpation of public office)."
            ),
            now,
        ),
    )

    demo_pyq_attempts = [
        ("pyq-pol-2024-1", "Indian Polity", "1, 2 and 3", 1),
        ("pyq-pol-2024-2", "Indian Polity", "Article 21", 1),
        ("pyq-pol-2023-1", "Indian Polity", "Fair application of law", 1),
        ("pyq-hist-2024-1", "History", "1 only", 1),
        ("pyq-env-2024-1", "Environment", "Statement-I is correct, but Statement-II is incorrect", 1),
        ("pyq-eco-2023-1", "Economy", "Conducting 'Open Market Operations'", 1),
        ("pyq-geo-2023-1", "Geography", "Only one", 0),
    ]
    for pyq_id, subj, sel_opt, is_ok in demo_pyq_attempts:
        conn.execute(
            """
            INSERT OR REPLACE INTO pyq_attempts (user_id, pyq_id, subject, selected_option, is_correct, attempted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, pyq_id, subj, sel_opt, is_ok, now),
        )

    base = _now_ist()
    demo_sessions = [
        (0, 3, "History", "Bookstawa Modern History (1857 & Acts)", 60, "Focus"),
        (0, 2, "Indian Polity", "Atish Mathur Magna Carta — Fundamental Rights", 50, "Focus"),
        (0, 1, "Current Affairs", "Sansad TV Perspective + PIB Summary", 35, "Focus"),
        (1, 5, "Geography", "Amit Sengupta Class 11 Physical Geo", 75, "Focus"),
        (1, 2, "Economy", "Mrunal Patel — RBI Monetary Policy", 50, "Focus"),
        (2, 6, "History", "Class 12 Themes in Indian History Part II", 90, "Focus"),
        (2, 3, "Indian Polity", "Atish Mathur 10-Year Polity PYQs", 60, "Focus"),
        (3, 4, "Environment", "PMF IAS Ecology & Wildlife Protection Act", 55, "Focus"),
        (3, 1, "CSAT", "UNGIST Reading Comprehension & Number System", 45, "Focus"),
        (4, 5, "Economy", "Class 12 Macroeconomics — Money Multiplier", 80, "Focus"),
        (5, 4, "History", "HD Education Spectrum Freedom Struggle", 100, "Focus"),
        (5, 2, "Current Affairs", "Vision IAS Monthly Current Affairs Notes", 40, "Focus"),
        (6, 3, "Indian Polity", "PRS Bill Track & Parliamentary Committees", 65, "Focus"),
        (7, 4, "Geography", "Sudarshan Gurjar Indian Rivers Mapping", 70, "Focus"),
        (8, 3, "Ethics", "Atish Mathur Ethics GS-4 Case Studies", 50, "Focus"),
        (9, 4, "CSAT", "UNGIST Topic-Wise CSAT PYQs", 60, "Focus"),
    ]
    for idx, (days_ago, hrs_ago, subject, topic, mins, s_type) in enumerate(demo_sessions, start=1):
        start_dt = base - timedelta(days=days_ago, hours=hrs_ago)
        end_dt = start_dt + timedelta(minutes=mins)
        conn.execute(
            """
            INSERT INTO study_sessions (
                id, user_id, subject, topic, start_time, end_time,
                duration_minutes, session_type, completed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                f"sess-seed-{idx}",
                user_id,
                subject,
                topic,
                start_dt.isoformat(),
                end_dt.isoformat(),
                mins,
                s_type,
                end_dt.isoformat(),
            ),
        )


def touch_study_streak(conn: sqlite3.Connection, user_id: str) -> int:
    """Update a user's consecutive daily study streak accurately in IST."""
    user_row = conn.execute(
        "SELECT study_streak_days, last_study_date FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user_row:
        return 1
    today_dt = _now_ist().date()
    today = today_dt.isoformat()
    yesterday = (today_dt - timedelta(days=1)).isoformat()
    last_date = _to_ist_date_str(user_row["last_study_date"])
    streak = int(user_row["study_streak_days"] or 0)

    if last_date == today:
        streak = max(1, streak)
    elif last_date == yesterday:
        streak += 1
    else:
        streak = 1

    conn.execute(
        "UPDATE users SET study_streak_days = ?, last_study_date = ?, updated_at = ? WHERE id = ?",
        (streak, today, _utc_now(), user_id),
    )
    return streak


# =========================================================================
# SERIALIZERS
# =========================================================================


def serialize_user(row: sqlite3.Row) -> dict[str, Any]:
    effective_streak = _compute_effective_streak(
        row["study_streak_days"], row["last_study_date"]
    )
    return {
        "id": row["id"],
        "email": row["email"],
        "full_name": row["full_name"],
        "name": row["full_name"],
        "role": row["role"],
        "preparation_stage": row["preparation_stage"],
        "preparationStage": row["preparation_stage"],
        "target_attempt_year": row["target_attempt_year"],
        "targetAttemptYear": row["target_attempt_year"],
        "daily_target_hours": row["daily_target_hours"],
        "dailyTargetHours": row["daily_target_hours"],
        "preferred_language": row["preferred_language"],
        "study_streak_days": effective_streak,
        "last_study_date": row["last_study_date"],
        "active_plan": _safe_json_loads(row["active_plan_json"], None),
        "created_at": row["created_at"],
    }


def serialize_resource(row: sqlite3.Row) -> dict[str, Any]:
    url = row["url"]
    keys = row.keys()
    master_part = row["master_part"] if "master_part" in keys else None
    return {
        "id": row["id"],
        "title": row["title"],
        "subject": row["subject"],
        "category": row["category"],
        "level": row["level"],
        "classLevel": row["class_level"],
        "class_level": row["class_level"],
        "language": row["language"],
        "type": row["type"],
        "provider": row["provider"],
        "url": url,
        "youtubePlaylistId": extract_youtube_playlist_id(url),
        "description": row["description"],
        "seniorTip": row["senior_tip"],
        "senior_tip": row["senior_tip"],
        "views": row["views"],
        "likes": row["likes"],
        "channelSubscribers": row["channel_subscribers"],
        "playlistLength": row["playlist_length"],
        "playlist_length": row["playlist_length"],
        "estimatedHours": row["estimated_hours"],
        "estimated_hours": row["estimated_hours"],
        "free": bool(row["free"]),
        "verified": bool(row["verified"]),
        "verificationStatus": row["verification_status"],
        "verification_status": row["verification_status"],
        "lastVerified": row["last_verified"],
        "verificationSignals": _safe_json_loads(row["verification_signals_json"], {}),
        "prerequisites": _safe_json_loads(row["prerequisites_json"], []),
        "nextResourceId": row["next_resource_id"],
        "nextResourceTitle": row["next_resource_title"],
        "tags": _safe_json_loads(row["tags_json"], []),
        "masterPart": master_part,
        "master_part": master_part,
        "created_at": row["created_at"],
    }


def _serialize_timetable_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "dayOfWeek": row["day_of_week"],
        "startTime": row["start_time"],
        "endTime": row["end_time"],
        "subject": row["subject"],
        "topic": row["topic"],
        "resourceId": row["resource_id"],
        "resourceTitle": row["resource_title"],
        "completed": bool(row["completed"]),
    }


def _serialize_session_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "subject": row["subject"],
        "topic": row["topic"],
        "resourceId": row["resource_id"],
        "startTime": row["start_time"],
        "endTime": row["end_time"],
        "durationMinutes": row["duration_minutes"],
        "sessionType": row["session_type"],
        "completed": bool(row["completed"]),
        "notes": row["notes"],
        "createdAt": row["created_at"],
    }


# =========================================================================
# RESOURCES CATALOG (QUERY, FACETS & ADMIN CRUD)
# =========================================================================


def list_resources(
    search: Optional[str] = None,
    pill: Optional[str] = None,
    subject: Optional[str] = None,
    level: Optional[str] = None,
    res_type: Optional[str] = None,
    language: Optional[str] = None,
    master_part: Optional[int] = None,
    has_playlist: Optional[bool] = None,
    verified_only: bool = False,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM resources ORDER BY subject ASC, level ASC, title ASC"
        ).fetchall()
    items = [serialize_resource(r) for r in rows]

    if search and search.strip():
        q = search.strip().lower()
        items = [
            r
            for r in items
            if q in r["title"].lower()
            or q in (r["description"] or "").lower()
            or q in r["subject"].lower()
            or q in r["provider"].lower()
            or q in r["category"].lower()
            or q in (r.get("language") or "").lower()
            or q in (r.get("class_level") or "").lower()
            or q in (r.get("url") or "").lower()
            or any(q in str(t).lower() for t in r["tags"])
        ]

    if pill and pill != "All":
        p = pill.lower()
        items = [
            r
            for r in items
            if p in r["subject"].lower()
            or p in r["level"].lower()
            or p in r["category"].lower()
            or p in r["type"].lower()
            or any(p in str(t).lower() for t in r["tags"])
        ]

    if subject and subject != "All":
        s = subject.lower()
        items = [r for r in items if s in r["subject"].lower()]

    if level and level != "All":
        lv = level.lower()
        items = [r for r in items if lv in r["level"].lower()]

    if res_type and res_type != "All":
        rt = res_type.lower()
        items = [r for r in items if rt in r["type"].lower()]

    if language and language != "All":
        lg = language.lower()
        items = [r for r in items if lg in (r.get("language") or "").lower()]

    if master_part is not None:
        mp = int(master_part)
        items = [r for r in items if r.get("master_part") == mp]

    if has_playlist is True:
        items = [r for r in items if bool(r.get("youtubePlaylistId"))]
    elif has_playlist is False:
        items = [r for r in items if not r.get("youtubePlaylistId")]

    if verified_only:
        items = [r for r in items if bool(r.get("verified"))]

    return items


def get_resource_facets() -> dict[str, Any]:
    """Return structured facet counts across subjects, types, levels, languages, and master parts."""
    items = list_resources()
    subject_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    level_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    part_counts: dict[int, int] = {}
    providers: set[str] = set()
    verified_count = 0
    playlist_count = 0

    for r in items:
        s = r.get("subject") or "General"
        t = r.get("type") or "Other"
        lv = r.get("level") or "Foundation"
        lg = r.get("language") or "English"
        subject_counts[s] = subject_counts.get(s, 0) + 1
        type_counts[t] = type_counts.get(t, 0) + 1
        level_counts[lv] = level_counts.get(lv, 0) + 1
        language_counts[lg] = language_counts.get(lg, 0) + 1
        if r.get("provider"):
            providers.add(r["provider"])
        if r.get("verified"):
            verified_count += 1
        if r.get("youtubePlaylistId"):
            playlist_count += 1
        mp = r.get("master_part")
        if mp is not None:
            part_counts[int(mp)] = part_counts.get(int(mp), 0) + 1

    part_titles: dict[int, str] = {}
    try:
        for p in get_master_guide_data().get("parts", []):
            pnum = p.get("part_number")
            if pnum is not None:
                part_titles[int(pnum)] = p.get("title", f"Part {pnum}")
    except Exception:
        pass

    return {
        "total": len(items),
        "verified_count": verified_count,
        "playlist_count": playlist_count,
        "providers_count": len(providers),
        "subjects": [
            {"name": k, "count": v} for k, v in sorted(subject_counts.items(), key=lambda x: (-x[1], x[0]))
        ],
        "types": [
            {"name": k, "count": v} for k, v in sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))
        ],
        "levels": [
            {"name": k, "count": v} for k, v in sorted(level_counts.items(), key=lambda x: (-x[1], x[0]))
        ],
        "languages": [
            {"name": k, "count": v} for k, v in sorted(language_counts.items(), key=lambda x: (-x[1], x[0]))
        ],
        "master_parts": [
            {
                "part_number": p,
                "title": part_titles.get(p, f"Part {p}"),
                "count": c,
            }
            for p, c in sorted(part_counts.items())
        ],
        "subject_counts": dict(sorted(subject_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
        "level_counts": dict(sorted(level_counts.items())),
        "language_counts": dict(sorted(language_counts.items())),
    }


def create_resource(data: dict[str, Any]) -> dict[str, Any]:
    raw_id = data.get("id")
    rid = raw_id.strip() if isinstance(raw_id, str) and raw_id.strip() else f"res-custom-{uuid.uuid4().hex[:8]}"
    now = _utc_now()
    today = _today_str()
    verification_status = data.get("verification_status", "Verified")
    verified = data.get("verified")
    if verified is None:
        verified = verification_status == "Verified"

    master_part = (
        data.get("master_part")
        if data.get("master_part") is not None
        else data.get("masterPart")
    )
    if master_part is not None:
        master_part = int(master_part)

    signals = {
        "views": data.get("views") or "",
        "completeness": data.get("playlist_length") or "Verified Free Resource",
        "uploadYear": str(datetime.now().year),
        "channelName": data.get("provider") or "",
    }

    with get_connection() as conn:
        exists = conn.execute("SELECT 1 FROM resources WHERE id = ?", (rid,)).fetchone()
        if exists:
            raise ValueError("Resource with this ID already exists.")
        try:
            conn.execute(
                """
                INSERT INTO resources (
                    id, title, subject, category, level, class_level, language, type,
                    provider, url, description, senior_tip, views, likes,
                    channel_subscribers, playlist_length, estimated_hours, free,
                    verified, verification_status, last_verified,
                    verification_signals_json, prerequisites_json,
                    next_resource_id, next_resource_title, tags_json, master_part, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rid,
                    data["title"],
                    data.get("subject", "General"),
                    data.get("category", "NCERT Foundation"),
                    data.get("level", "Foundation"),
                    data.get("class_level"),
                    data.get("language", "English/Hinglish"),
                    data.get("type", "YouTube"),
                    data.get("provider", "Independent Educator"),
                    data["url"],
                    data.get("description", ""),
                    data.get("senior_tip"),
                    data.get("views"),
                    data.get("likes"),
                    data.get("channel_subscribers"),
                    data.get("playlist_length"),
                    int(data.get("estimated_hours", 0) or 0),
                    1 if data.get("free", True) else 0,
                    1 if verified else 0,
                    verification_status,
                    today,
                    json.dumps(signals),
                    json.dumps([]),
                    None,
                    data.get("next_resource_title"),
                    json.dumps(data.get("tags", ["UPSC"])),
                    master_part,
                    now,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Resource with this ID already exists.") from exc
        row = conn.execute("SELECT * FROM resources WHERE id = ?", (rid,)).fetchone()
    return serialize_resource(row)


def update_resource(resource_id: str, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Partially update an existing resource without wiping untouched metadata; returns None if missing."""
    today = _today_str()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM resources WHERE id = ?", (resource_id,)
        ).fetchone()
        if not existing:
            return None

        merged = serialize_resource(existing)
        signals = dict(merged["verificationSignals"] or {})
        if "views" in patch and patch["views"] is not None:
            signals["views"] = patch["views"]
        if "playlist_length" in patch and patch["playlist_length"] is not None:
            signals["completeness"] = patch["playlist_length"]
        if "provider" in patch and patch["provider"]:
            signals["channelName"] = patch["provider"]

        new_status = (
            patch["verification_status"]
            if "verification_status" in patch and patch["verification_status"] is not None
            else merged["verification_status"]
        )
        if "verified" in patch and patch["verified"] is not None:
            new_verified = bool(patch["verified"])
        elif "verification_status" in patch:
            new_verified = new_status == "Verified"
        else:
            new_verified = merged["verified"]

        def _val(key: str, current: Any) -> Any:
            return patch[key] if key in patch else current

        if "master_part" in patch:
            new_master_part = patch["master_part"]
        elif "masterPart" in patch:
            new_master_part = patch["masterPart"]
        else:
            new_master_part = merged["master_part"]

        conn.execute(
            """
            UPDATE resources SET
                title = ?, subject = ?, category = ?, level = ?, class_level = ?,
                language = ?, type = ?, provider = ?, url = ?, description = ?,
                senior_tip = ?, views = ?, playlist_length = ?, estimated_hours = ?,
                verified = ?, verification_status = ?, last_verified = ?,
                verification_signals_json = ?, next_resource_title = ?, tags_json = ?,
                master_part = ?
            WHERE id = ?
            """,
            (
                _val("title", merged["title"]),
                _val("subject", merged["subject"]),
                _val("category", merged["category"]),
                _val("level", merged["level"]),
                _val("class_level", merged["class_level"]),
                _val("language", merged["language"]),
                _val("type", merged["type"]),
                _val("provider", merged["provider"]),
                _val("url", merged["url"]),
                _val("description", merged["description"]),
                _val("senior_tip", merged["senior_tip"]),
                _val("views", merged["views"]),
                _val("playlist_length", merged["playlist_length"]),
                int(_val("estimated_hours", merged["estimated_hours"]) or 0),
                1 if new_verified else 0,
                new_status,
                today,
                json.dumps(signals),
                _val("next_resource_title", merged["nextResourceTitle"]),
                json.dumps(_val("tags", merged["tags"]) or []),
                new_master_part,
                resource_id,
            ),
        )
        row = conn.execute("SELECT * FROM resources WHERE id = ?", (resource_id,)).fetchone()
    return serialize_resource(row)


def upsert_resource(data: dict[str, Any], resource_id: Optional[str] = None) -> dict[str, Any]:
    """Convenience helper for Streamlit fallback."""
    if resource_id:
        updated = update_resource(resource_id, data)
        if updated:
            return updated
    return create_resource(data)


def delete_resource(resource_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
        return cur.rowcount > 0


# =========================================================================
# UNIFIED DATA SERVICE LAYER (SHARED BY FASTAPI & STREAMLIT FALLBACK)
# =========================================================================


def resolve_session_context(token: Optional[str]) -> dict[str, Any]:
    """Resolve active user context from session token, falling back cleanly to Demo workspace."""
    now_iso = _utc_now()
    with get_connection() as conn:
        if token:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, now_iso),
            ).fetchone()
            if row:
                return {
                    "authenticated": True,
                    "is_demo": row["id"] == DEMO_USER_ID,
                    "user": serialize_user(row),
                    "user_id": row["id"],
                }

        demo_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (DEMO_USER_ID,)
        ).fetchone()
        if demo_row:
            return {
                "authenticated": False,
                "is_demo": True,
                "user": serialize_user(demo_row),
                "user_id": demo_row["id"],
            }

    init_db()
    with get_connection() as conn:
        demo_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (DEMO_USER_ID,)
        ).fetchone()
        return {
            "authenticated": False,
            "is_demo": True,
            "user": serialize_user(demo_row),
            "user_id": demo_row["id"],
        }


def authenticate_user(email: str, password: str) -> Optional[dict[str, Any]]:
    """Verify credentials and create a persistent session token."""
    cleaned_email = (email or "").strip().lower()
    now = _utc_now()
    with get_connection() as conn:
        user_row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (cleaned_email,)
        ).fetchone()
        if not user_row or not verify_password(password, user_row["password_hash"]):
            return None

        token, expires_at = generate_session_token()
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_row["id"], expires_at, now),
        )
        return {
            "authenticated": True,
            "is_demo": user_row["id"] == DEMO_USER_ID,
            "token": token,
            "user": serialize_user(user_row),
        }


def register_user(
    full_name: str,
    email: str,
    password: str,
    preparation_stage: str = "Foundation (Class 6-12)",
    target_attempt_year: str = "2028",
    daily_target_hours: int = 4,
) -> dict[str, Any]:
    """Register a new personal student account, seed starter timetable, and start a session."""
    cleaned_email = (email or "").strip().lower()
    cleaned_name = (full_name or "").strip()
    if not cleaned_name:
        raise ValueError("Full name cannot be blank.")
    if not cleaned_email:
        raise ValueError("Email cannot be blank.")

    now = _utc_now()
    user_id = f"usr-{uuid.uuid4().hex[:12]}"

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT 1 FROM users WHERE email = ?", (cleaned_email,)
        ).fetchone()
        if existing:
            raise ValueError("An account with this email already exists.")

        conn.execute(
            """
            INSERT INTO users (
                id, email, password_hash, full_name, role, preparation_stage,
                target_attempt_year, daily_target_hours, preferred_language,
                study_streak_days, last_study_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'student', ?, ?, ?, 'Hinglish', 0, NULL, ?, ?)
            """,
            (
                user_id,
                cleaned_email,
                hash_password(password),
                cleaned_name,
                preparation_stage,
                target_attempt_year,
                int(daily_target_hours),
                now,
                now,
            ),
        )
        seed_user_defaults(conn, user_id, with_demo_history=False)

        token, expires_at = generate_session_token()
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, expires_at, now),
        )
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    return {
        "authenticated": True,
        "is_demo": False,
        "token": token,
        "user": serialize_user(user_row),
    }


def create_demo_session() -> dict[str, Any]:
    """Ensure demo user exists and issue a fresh authenticated session token for it."""
    now = _utc_now()
    with get_connection() as conn:
        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (DEMO_USER_ID,)
        ).fetchone()

    if not user_row:
        init_db()

    with get_connection() as conn:
        user_row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (DEMO_USER_ID,)
        ).fetchone()
        token, expires_at = generate_session_token()
        conn.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_row["id"], expires_at, now),
        )
        serialized = serialize_user(user_row)

    return {
        "authenticated": True,
        "is_demo": True,
        "token": token,
        "user": serialized,
    }


def logout_session(token: str) -> None:
    """Delete a session token from SQLite."""
    if not token:
        return
    with get_connection() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))


def update_user_profile(user_id: str, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Update allowed profile fields for a user; returns None if user does not exist."""
    allowed_fields = (
        "full_name",
        "preparation_stage",
        "target_attempt_year",
        "daily_target_hours",
        "preferred_language",
    )
    updates: list[str] = []
    params: list[Any] = []
    for col in allowed_fields:
        if col in patch and patch[col] is not None:
            updates.append(f"{col} = ?")
            params.append(patch[col])

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        if updates:
            updates.append("updated_at = ?")
            params.append(_utc_now())
            params.append(user_id)
            conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return serialize_user(row)


def update_user_password(user_id: str, new_password: str) -> bool:
    """Update a user's PBKDF2 password hash."""
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (hash_password(new_password), _utc_now(), user_id),
        )
        return cur.rowcount > 0


def delete_user_account(user_id: str) -> bool:
    """Permanently delete a non-demo user account and cascade owned workspace data."""
    if user_id == DEMO_USER_ID:
        raise ValueError(
            "The default demo account cannot be deleted. Sign up for a personal account to test deletion."
        )
    with get_connection() as conn:
        conn.execute(
            "UPDATE resource_suggestions SET user_id = NULL WHERE user_id = ?",
            (user_id,),
        )
        cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cur.rowcount > 0


def get_workspace_bundle(
    user_id: str,
    authenticated: bool = False,
    is_demo: bool = True,
) -> dict[str, Any]:
    """Return the complete hydrated workspace payload for a user."""
    with get_connection() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user_row and user_id == DEMO_USER_ID:
        init_db()
        with get_connection() as conn:
            user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user_row:
        raise ValueError("User not found.")

    with get_connection() as conn:
        prog_rows = conn.execute(
            "SELECT item_id, progress_percentage FROM user_progress WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        bm_rows = conn.execute(
            "SELECT resource_id FROM saved_resources WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        note_rows = conn.execute(
            "SELECT item_id, item_title, item_category, content, updated_at FROM user_notes WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
        tt_rows = conn.execute(
            "SELECT * FROM timetable_events WHERE user_id = ? ORDER BY start_time ASC",
            (user_id,),
        ).fetchall()
        sess_rows = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY start_time DESC LIMIT 200",
            (user_id,),
        ).fetchall()
        pyq_rows = conn.execute(
            "SELECT pyq_id, subject, selected_option, is_correct, attempted_at FROM pyq_attempts WHERE user_id = ?",
            (user_id,),
        ).fetchall()

    return {
        "authenticated": authenticated,
        "is_demo": is_demo,
        "profile": serialize_user(user_row),
        "progressMap": {r["item_id"]: r["progress_percentage"] for r in prog_rows},
        "bookmarkedIds": [r["resource_id"] for r in bm_rows],
        "notes": {r["item_id"]: r["content"] for r in note_rows},
        "notesList": [dict(r) for r in note_rows],
        "pyqAttempts": {
            r["pyq_id"]: {
                "selectedOption": r["selected_option"],
                "isCorrect": bool(r["is_correct"]),
                "attemptedAt": r["attempted_at"],
            }
            for r in pyq_rows
        },
        "timetable": [_serialize_timetable_row(r) for r in tt_rows],
        "studySessions": [_serialize_session_row(r) for r in sess_rows],
        "analytics": compute_user_analytics(user_id),
    }


def update_user_progress(user_id: str, item_id: str, pct: int) -> dict[str, Any]:
    """Upsert completion percentage (0..100) for any syllabus/NCERT/roadmap/resource item."""
    pct_val = max(0, min(100, int(pct)))
    status = "completed" if pct_val >= 100 else ("in_progress" if pct_val > 0 else "not_started")
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_progress (user_id, item_id, progress_percentage, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                progress_percentage = excluded.progress_percentage,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (user_id, item_id, pct_val, status, now),
        )
    return {
        "item_id": item_id,
        "progress_percentage": pct_val,
        "status": status,
        "analytics": compute_user_analytics(user_id),
    }


def list_user_notes(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM user_notes WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_user_note(user_id: str, item_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM user_notes WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone()
    return {
        "item_id": item_id,
        "content": row["content"] if row else "",
        "item_title": row["item_title"] if row else None,
        "item_category": row["item_category"] if row else None,
        "updated_at": row["updated_at"] if row else None,
    }


def save_user_note_item(
    user_id: str,
    item_id: str,
    content: str,
    item_title: Optional[str] = None,
    item_category: Optional[str] = None,
) -> dict[str, Any]:
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_notes (user_id, item_id, item_title, item_category, content, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET
                item_title = COALESCE(excluded.item_title, user_notes.item_title),
                item_category = COALESCE(excluded.item_category, user_notes.item_category),
                content = excluded.content,
                updated_at = excluded.updated_at
            """,
            (user_id, item_id, item_title, item_category, content, now),
        )
        row = conn.execute(
            "SELECT item_title, item_category FROM user_notes WHERE user_id = ? AND item_id = ?",
            (user_id, item_id),
        ).fetchone()
    return {
        "item_id": item_id,
        "content": content,
        "item_title": row["item_title"] if row else item_title,
        "item_category": row["item_category"] if row else item_category,
        "updated_at": now,
    }


def admin_update_user_note(
    user_id: str, item_id: str, content: str
) -> Optional[dict[str, Any]]:
    now = _utc_now()
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE user_notes SET content = ?, updated_at = ? WHERE user_id = ? AND item_id = ?",
            (content, now, user_id, item_id),
        )
        if cur.rowcount == 0:
            return None
    return {"saved": True, "user_id": user_id, "item_id": item_id, "updated_at": now}


def toggle_user_bookmark(user_id: str, resource_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM saved_resources WHERE user_id = ? AND resource_id = ?",
            (user_id, resource_id),
        ).fetchone()
        if exists:
            conn.execute(
                "DELETE FROM saved_resources WHERE user_id = ? AND resource_id = ?",
                (user_id, resource_id),
            )
            bookmarked = False
        else:
            conn.execute(
                "INSERT INTO saved_resources (user_id, resource_id, created_at) VALUES (?, ?, ?)",
                (user_id, resource_id, _utc_now()),
            )
            bookmarked = True
        all_rows = conn.execute(
            "SELECT resource_id FROM saved_resources WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    return {
        "resource_id": resource_id,
        "bookmarked": bookmarked,
        "bookmarkedIds": [r["resource_id"] for r in all_rows],
    }


def record_user_pyq_attempt(
    user_id: str,
    pyq_id: str,
    subject: str,
    selected_option: str,
    is_correct: Optional[bool] = None,
) -> dict[str, Any]:
    """Record a PYQ attempt with authoritative server-side answer verification for known MCQs."""
    matched_pyq: Optional[dict[str, Any]] = None
    for q in get_pyqs_data():
        if q.get("id") == pyq_id:
            matched_pyq = q
            break

    canonical_answer: Optional[str] = None
    server_verified = False
    resolved_subject = subject

    if matched_pyq is not None:
        resolved_subject = matched_pyq.get("subject") or subject
        if matched_pyq.get("correctAnswer") is not None:
            canonical_answer = str(matched_pyq["correctAnswer"]).strip()
            verified_correct = str(selected_option).strip() == canonical_answer
            server_verified = True
        else:
            verified_correct = bool(is_correct) if is_correct is not None else False
    else:
        verified_correct = bool(is_correct) if is_correct is not None else False

    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO pyq_attempts (user_id, pyq_id, subject, selected_option, is_correct, attempted_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, pyq_id) DO UPDATE SET
                subject = excluded.subject,
                selected_option = excluded.selected_option,
                is_correct = excluded.is_correct,
                attempted_at = excluded.attempted_at
            """,
            (
                user_id,
                pyq_id,
                resolved_subject,
                selected_option,
                1 if verified_correct else 0,
                now,
            ),
        )

    return {
        "saved": True,
        "pyq_id": pyq_id,
        "subject": resolved_subject,
        "selected_option": selected_option,
        "is_correct": verified_correct,
        "correct_answer": canonical_answer,
        "server_verified": server_verified,
        "analytics": compute_user_analytics(user_id),
    }


def reset_user_pyq_attempts(user_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute("DELETE FROM pyq_attempts WHERE user_id = ?", (user_id,))
    return {"reset": True, "analytics": compute_user_analytics(user_id)}


def list_user_study_sessions(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY start_time DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_user_study_session(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    now_dt = _now_ist()
    duration_minutes = int(payload["duration_minutes"])
    end_iso = payload.get("end_time") or now_dt.isoformat()
    start_iso = payload.get("start_time") or (
        now_dt - timedelta(minutes=duration_minutes)
    ).isoformat()
    sess_id = f"sess-{uuid.uuid4().hex[:10]}"
    session_type = payload.get("session_type") or "Focus"
    completed = bool(payload.get("completed", True))
    subject = str(payload["subject"]).strip()
    topic = str(payload.get("topic") or "")
    resource_id = payload.get("resource_id")
    notes = payload.get("notes")
    is_focus = "break" not in session_type.lower()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO study_sessions (
                id, user_id, subject, topic, resource_id, start_time, end_time,
                duration_minutes, session_type, completed, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sess_id,
                user_id,
                subject,
                topic,
                resource_id,
                start_iso,
                end_iso,
                duration_minutes,
                session_type,
                1 if completed else 0,
                notes,
                now_dt.isoformat(),
            ),
        )

        # Auto-complete today's first matching uncompleted timetable block for completed Focus sessions
        if is_focus and completed:
            today_name = now_dt.strftime("%A")
            match = conn.execute(
                """
                SELECT id FROM timetable_events
                WHERE user_id = ? AND completed = 0
                  AND day_of_week IN ('Daily', ?)
                  AND LOWER(subject) = LOWER(?)
                ORDER BY start_time ASC
                LIMIT 1
                """,
                (user_id, today_name, subject),
            ).fetchone()
            if match:
                conn.execute(
                    "UPDATE timetable_events SET completed = 1, updated_at = ? WHERE id = ?",
                    (_utc_now(), match["id"]),
                )
            touch_study_streak(conn, user_id)

    return {
        "session": {
            "id": sess_id,
            "subject": subject,
            "topic": topic,
            "resourceId": resource_id,
            "durationMinutes": duration_minutes,
            "sessionType": session_type,
            "startTime": start_iso,
            "endTime": end_iso,
            "completed": completed,
            "notes": notes,
            "createdAt": now_dt.isoformat(),
        },
        "analytics": compute_user_analytics(user_id),
    }


def delete_user_study_session(user_id: str, session_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM study_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        )
        return cur.rowcount > 0


def list_user_timetable(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM timetable_events WHERE user_id = ? ORDER BY start_time ASC",
            (user_id,),
        ).fetchall()
    return [_serialize_timetable_row(r) for r in rows]


def create_user_timetable_event(user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    now = _utc_now()
    event_id = f"tt-{uuid.uuid4().hex[:10]}"
    day_of_week = payload.get("day_of_week") or payload.get("dayOfWeek") or "Daily"
    start_time = payload.get("start_time") or payload.get("startTime") or "06:30"
    end_time = payload.get("end_time") or payload.get("endTime") or "07:30"
    subject = str(payload["subject"]).strip()
    topic = str(payload["topic"]).strip()
    resource_id = payload.get("resource_id") if "resource_id" in payload else payload.get("resourceId")
    resource_title = (
        payload.get("resource_title") if "resource_title" in payload else payload.get("resourceTitle")
    )
    completed = bool(payload.get("completed", False))

    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO timetable_events (
                id, user_id, day_of_week, start_time, end_time,
                subject, topic, resource_id, resource_title, completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                user_id,
                day_of_week,
                start_time,
                end_time,
                subject,
                topic,
                resource_id,
                resource_title,
                1 if completed else 0,
                now,
                now,
            ),
        )
        row = conn.execute("SELECT * FROM timetable_events WHERE id = ?", (event_id,)).fetchone()
    return _serialize_timetable_row(row)


def update_user_timetable_event(
    user_id: str, event_id: str, patch: dict[str, Any]
) -> Optional[dict[str, Any]]:
    key_aliases = {
        "day_of_week": ("day_of_week", "dayOfWeek"),
        "start_time": ("start_time", "startTime"),
        "end_time": ("end_time", "endTime"),
        "subject": ("subject",),
        "topic": ("topic",),
        "resource_id": ("resource_id", "resourceId"),
        "resource_title": ("resource_title", "resourceTitle"),
    }

    normalized: dict[str, Any] = {}
    for col, aliases in key_aliases.items():
        for alias in aliases:
            if alias in patch and patch[alias] is not None:
                normalized[col] = patch[alias]
                break

    if "completed" in patch and patch["completed"] is not None:
        normalized["completed"] = 1 if bool(patch["completed"]) else 0

    if not normalized:
        raise ValueError("No fields provided for update.")

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM timetable_events WHERE id = ? AND user_id = ?",
            (event_id, user_id),
        ).fetchone()
        if not existing:
            return None

        eff_start = normalized.get("start_time", existing["start_time"])
        eff_end = normalized.get("end_time", existing["end_time"])
        if eff_end <= eff_start:
            raise ValueError("End time must be after start time.")

        fields = [f"{col} = ?" for col in normalized]
        params = list(normalized.values())
        fields.append("updated_at = ?")
        params.append(_utc_now())
        params.extend([event_id, user_id])

        conn.execute(
            f"UPDATE timetable_events SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        row = conn.execute("SELECT * FROM timetable_events WHERE id = ?", (event_id,)).fetchone()
    return _serialize_timetable_row(row)


def delete_user_timetable_event(user_id: str, event_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM timetable_events WHERE id = ? AND user_id = ?",
            (event_id, user_id),
        )
        return cur.rowcount > 0


def save_user_journey_plan(user_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET active_plan_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(plan), _utc_now(), user_id),
        )
    return {"saved": True, "plan": plan}


def list_resource_suggestions() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM resource_suggestions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def create_resource_suggestion(
    user_id: Optional[str], payload: dict[str, Any]
) -> dict[str, Any]:
    sug_id = f"sug-{uuid.uuid4().hex[:10]}"
    now = _utc_now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO resource_suggestions (
                id, user_id, subject, chapter_title, chapter_num, url, channel, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                sug_id,
                user_id,
                str(payload["subject"]).strip(),
                str(payload["chapter_title"]).strip(),
                int(payload.get("chapter_num", 0) or 0),
                str(payload["url"]).strip(),
                str(payload.get("channel") or "").strip(),
                now,
            ),
        )
    return {"id": sug_id, "status": "pending", "message": "Suggestion submitted for review."}


def update_resource_suggestion_status(sug_id: str, status: str) -> bool:
    if status not in ("pending", "approved", "dismissed"):
        raise ValueError("Status must be one of: pending, approved, dismissed.")
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE resource_suggestions SET status = ? WHERE id = ?",
            (status, sug_id),
        )
        return cur.rowcount > 0


def list_admin_users() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT u.*,
                (SELECT COUNT(*) FROM study_sessions s WHERE s.user_id = u.id AND s.completed = 1 AND LOWER(s.session_type) NOT LIKE '%break%') AS session_count,
                (SELECT COALESCE(SUM(s.duration_minutes), 0) FROM study_sessions s WHERE s.user_id = u.id AND s.completed = 1 AND LOWER(s.session_type) NOT LIKE '%break%') AS total_minutes,
                (SELECT COUNT(*) FROM saved_resources b WHERE b.user_id = u.id) AS bookmark_count
            FROM users u
            ORDER BY u.created_at ASC
            """
        ).fetchall()
    users: list[dict[str, Any]] = []
    for r in rows:
        item = serialize_user(r)
        item["session_count"] = r["session_count"]
        item["total_minutes"] = r["total_minutes"]
        item["bookmark_count"] = r["bookmark_count"]
        users.append(item)
    return users


def get_admin_user_details(user_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        sessions = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY start_time DESC",
                (user_id,),
            ).fetchall()
        ]
        notes = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM user_notes WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            ).fetchall()
        ]
        timetable = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM timetable_events WHERE user_id = ? ORDER BY start_time ASC",
                (user_id,),
            ).fetchall()
        ]
    return {"sessions": sessions, "notes": notes, "timetable": timetable}


# =========================================================================
# GLOBAL CROSS-CATALOG SEARCH
# =========================================================================


def global_search(query: str, limit: int = 40) -> list[dict[str, Any]]:
    """Search across all 334 resources, 11-part Master Guide, NCERTs, PYQs, papers, roadmaps & CA."""
    q = (query or "").strip().lower()
    if not q:
        return []
    max_items = max(1, min(100, int(limit)))

    results: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    def _add(entry: dict[str, Any], score: int = 50) -> None:
        dedup_key = (entry["kind"].lower(), entry["title"].lower())
        if dedup_key in seen_keys:
            return
        seen_keys.add(dedup_key)
        results.append({**entry, "_score": score})

    # 1. All verified resources in SQLite (334+)
    for res in list_resources(search=q):
        title_low = res["title"].lower()
        score = 100 if title_low.startswith(q) else (90 if q in title_low else 75)
        _add(
            {
                "kind": f"{res['type']} · {res['subject']}",
                "title": res["title"],
                "subtitle": f"{res['provider']} · {res['level']}",
                "href": f"/resources?search={quote_plus(res['title'])}",
                "url": res["url"],
                "source": "resource",
                "id": res["id"],
            },
            score=score,
        )

    # 2. Master Guide (all 11 parts, bridge textbooks, standard books, govt reports, optionals, interview, sequence)
    try:
        mg = get_master_guide_data()
    except Exception:
        mg = {}

    for part in mg.get("parts", []):
        pnum = part.get("part_number")
        ptitle = part.get("title", "")
        psummary = part.get("summary", "")
        if q in ptitle.lower() or q in psummary.lower() or f"part {pnum}" == q:
            _add(
                {
                    "kind": f"Master Guide · Part {pnum}",
                    "title": ptitle,
                    "subtitle": psummary[:120] or f"Part {pnum} of UPSC Free Resources Master Guide",
                    "href": f"/master-guide?part={pnum}",
                    "source": "master_guide",
                },
                score=88,
            )

    for item in mg.get("bridge_textbooks", []):
        if q in item.get("title", "").lower() or q in item.get("best_used_for", "").lower():
            _add(
                {
                    "kind": "Bridge Textbook",
                    "title": item["title"],
                    "subtitle": item.get("best_used_for", ""),
                    "href": "/master-guide?part=2",
                    "url": item.get("url"),
                    "source": "master_guide",
                },
                score=82,
            )

    for item in mg.get("standard_books", []):
        subj = item.get("subject", "")
        book = item.get("standard_book", "")
        if q in subj.lower() or q in book.lower():
            first_url = item["companions"][0]["url"] if item.get("companions") else None
            _add(
                {
                    "kind": "Standard Core Book",
                    "title": book,
                    "subtitle": f"{subj} · {len(item.get('companions', []))} free legal companion(s)",
                    "href": "/master-guide?part=3",
                    "url": first_url,
                    "source": "master_guide",
                },
                score=85,
            )

    for item in mg.get("govt_reports", []):
        if (
            q in item.get("title", "").lower()
            or q in item.get("utility", "").lower()
            or q in item.get("subsection", "").lower()
        ):
            _add(
                {
                    "kind": "Govt Report & Data",
                    "title": item["title"],
                    "subtitle": item.get("utility", ""),
                    "href": "/master-guide?part=4",
                    "url": item.get("url"),
                    "source": "master_guide",
                },
                score=78,
            )

    for opt in mg.get("optionals", []):
        subj = opt.get("subject", "")
        links = list(opt.get("academic_links", [])) + list(opt.get("video_links", []))
        if q in subj.lower() or "optional" in q or any(q in l.get("title", "").lower() for l in links):
            first_url = links[0]["url"] if links else None
            _add(
                {
                    "kind": "Optional Subject",
                    "title": f"{subj} Optional (Free Academic + Video Kit)",
                    "subtitle": f"{len(opt.get('academic_links', []))} academic & {len(opt.get('video_links', []))} video resource(s)",
                    "href": "/master-guide?part=10",
                    "url": first_url,
                    "source": "master_guide",
                },
                score=84 if q in subj.lower() else 72,
            )

    for item in mg.get("interview_prep", []):
        if q in item.get("title", "").lower() or q in item.get("purpose", "").lower() or "interview" in q or "daf" in q:
            _add(
                {
                    "kind": "Interview & DAF",
                    "title": item["title"],
                    "subtitle": item.get("purpose", ""),
                    "href": "/master-guide?part=10",
                    "url": item.get("url"),
                    "source": "master_guide",
                },
                score=76,
            )

    for phase in mg.get("study_sequence", []):
        if (
            q in phase.get("title", "").lower()
            or q in phase.get("timeframe", "").lower()
            or any(q in t.lower() for t in phase.get("tasks", []))
        ):
            _add(
                {
                    "kind": f"Study Sequence · Phase {phase.get('phase_number')}",
                    "title": phase.get("title", ""),
                    "subtitle": phase.get("timeframe", ""),
                    "href": "/master-guide?part=11",
                    "source": "master_guide",
                },
                score=80,
            )

    # 3. NCERT books & chapters
    for book in get_ncert_data():
        if (
            q in book["bookTitle"].lower()
            or q in book["subjectName"].lower()
            or f"class {book['classNum']}" in q
        ):
            _add(
                {
                    "kind": f"NCERT Class {book['classNum']}",
                    "title": f"{book['subjectName']} — {book['bookTitle']}",
                    "subtitle": f"{len(book.get('chapters', []))} chapters · Official PDF + Video",
                    "href": f"/ncert?class={book['classNum']}&book={quote_plus(book['id'])}",
                    "url": book.get("officialPdfUrl"),
                    "source": "ncert",
                },
                score=89,
            )
        for ch in book.get("chapters", []):
            if q in ch["title"].lower() or any(q in k.lower() for k in ch.get("keyThemes", [])):
                _add(
                    {
                        "kind": "NCERT Chapter",
                        "title": f"Ch {ch['number']}: {ch['title']}",
                        "subtitle": f"Class {book['classNum']} {book['subjectName']} ({book['bookTitle']})",
                        "href": f"/ncert?class={book['classNum']}&book={quote_plus(book['id'])}",
                        "url": book.get("officialPdfUrl"),
                        "source": "ncert",
                    },
                    score=80,
                )

    # 4. Question Papers
    for qp in get_question_papers_data():
        if (
            q in qp["title"].lower()
            or q in qp["stage"].lower()
            or q in (qp.get("provider") or "").lower()
            or "paper" in q
            or "pyq" in q
        ):
            _add(
                {
                    "kind": "Question Paper",
                    "title": qp["title"],
                    "subtitle": f"{qp['stage']} · {qp['years']}",
                    "href": "/pyqs",
                    "url": qp.get("url"),
                    "source": "question_paper",
                },
                score=77,
            )

    # 5. PYQs
    for pyq in get_pyqs_data():
        if (
            q in pyq["topic"].lower()
            or q in pyq["question"].lower()
            or q in pyq["subject"].lower()
            or q == str(pyq.get("year", ""))
        ):
            _add(
                {
                    "kind": f"PYQ {pyq['year']}",
                    "title": pyq["topic"],
                    "subtitle": f"{pyq['type']} {pyq['year']} · {pyq['subject']}",
                    "href": f"/pyqs?type={quote_plus(pyq['type'])}",
                    "source": "pyq",
                },
                score=83,
            )

    # 6. All 8 Roadmaps & Steps
    for rm in get_roadmaps_data():
        if (
            q in rm["subjectName"].lower()
            or q in rm["description"].lower()
            or q in rm["subjectId"].lower()
        ):
            _add(
                {
                    "kind": "Roadmap",
                    "title": rm["subjectName"],
                    "subtitle": f"{len(rm['steps'])} structured milestones",
                    "href": f"/roadmaps/{quote_plus(rm['subjectId'])}",
                    "source": "roadmap",
                },
                score=92,
            )
        for st in rm.get("steps", []):
            if q in st.get("title", "").lower() or q in st.get("tagline", "").lower():
                _add(
                    {
                        "kind": f"Roadmap Step · {rm['subjectName']}",
                        "title": st["title"],
                        "subtitle": st.get("tagline", ""),
                        "href": f"/roadmaps/{quote_plus(rm['subjectId'])}",
                        "source": "roadmap",
                    },
                    score=79,
                )

    # 7. Current Affairs categories & sources
    for cat in get_current_affairs_data():
        if (
            q in cat.get("title", "").lower()
            or q in cat.get("description", "").lower()
            or any(q in t.lower() for t in cat.get("highYieldTopics", []))
        ):
            _add(
                {
                    "kind": f"Current Affairs · {cat.get('gsPaper', 'GS')}",
                    "title": cat["title"],
                    "subtitle": f"{len(cat.get('keySources', []))} official/free sources",
                    "href": "/current-affairs",
                    "source": "current_affairs",
                },
                score=81,
            )
        for src in cat.get("keySources", []):
            if q in src.get("name", "").lower() or q in src.get("howToUse", "").lower():
                _add(
                    {
                        "kind": "Current Affairs Source",
                        "title": src["name"],
                        "subtitle": f"{cat.get('title', '')} · {src.get('type', '')}",
                        "href": "/current-affairs",
                        "url": src.get("url"),
                        "source": "current_affairs",
                    },
                    score=74,
                )

    results.sort(key=lambda item: (-item["_score"], item["title"].lower()))
    cleaned_results = []
    for item in results[:max_items]:
        item.pop("_score", None)
        cleaned_results.append(item)
    return cleaned_results


# =========================================================================
# DEEP UPSC READINESS & STUDY ANALYTICS ENGINE
# =========================================================================


def _roadmap_matches_resource_subject(subject_id: str, res_subject: str) -> bool:
    sid = (subject_id or "").strip().lower()
    rsub = (res_subject or "").strip().lower()
    keywords = ROADMAP_SUBJECT_KEYWORDS.get(sid, (sid,))
    return any(kw in rsub for kw in keywords)


def compute_user_analytics(user_id: str) -> dict[str, Any]:
    """Compute deep study, progress, PYQ accuracy, resource, master guide, and readiness analytics."""
    with get_connection() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        sessions = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY start_time DESC",
            (user_id,),
        ).fetchall()
        progress_rows = conn.execute(
            "SELECT item_id, progress_percentage FROM user_progress WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        bookmarks_count = conn.execute(
            "SELECT COUNT(*) FROM saved_resources WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        notes_count = conn.execute(
            "SELECT COUNT(*) FROM user_notes WHERE user_id = ? AND TRIM(content) != ''",
            (user_id,),
        ).fetchone()[0]
        timetable_rows = conn.execute(
            "SELECT * FROM timetable_events WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        pyq_rows = conn.execute(
            "SELECT * FROM pyq_attempts WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        all_resources = conn.execute(
            "SELECT id, subject, level, type, estimated_hours FROM resources"
        ).fetchall()

    progress_map = {r["item_id"]: r["progress_percentage"] for r in progress_rows}
    today_date = _now_ist().date()
    today_str = today_date.isoformat()

    daily_buckets: dict[str, int] = {}
    for offset in range(13, -1, -1):
        day_key = (today_date - timedelta(days=offset)).isoformat()
        daily_buckets[day_key] = 0

    subject_minutes: dict[str, int] = {}
    session_type_counts: dict[str, int] = {}
    today_minutes = 0
    weekly_minutes = 0
    total_minutes = 0
    focus_session_count = 0
    active_days_14: set[str] = set()
    week_cutoff = today_date - timedelta(days=6)

    for s in sessions:
        s_type = s["session_type"] or "Focus"
        session_type_counts[s_type] = session_type_counts.get(s_type, 0) + 1
        # Only count completed Focus study sessions toward focus minutes (exclude Short/Long Breaks)
        if not s["completed"] or "break" in s_type.lower():
            continue

        mins = int(s["duration_minutes"] or 0)
        focus_session_count += 1
        total_minutes += mins
        subj = s["subject"] or "General"
        subject_minutes[subj] = subject_minutes.get(subj, 0) + mins

        day_part = _to_ist_date_str(s["start_time"] or s["created_at"])
        if day_part:
            if day_part in daily_buckets:
                daily_buckets[day_part] += mins
                if mins > 0:
                    active_days_14.add(day_part)
            if day_part == today_str:
                today_minutes += mins
            try:
                s_date = date.fromisoformat(day_part)
                if week_cutoff <= s_date <= today_date:
                    weekly_minutes += mins
            except ValueError:
                pass

    ncert_books = get_ncert_data()
    roadmaps = get_roadmaps_data()

    def _avg_progress(item_ids: list[str]) -> int:
        unique_ids = list(dict.fromkeys(item_ids))
        if not unique_ids:
            return 0
        vals = [progress_map.get(i, 0) for i in unique_ids]
        return round(sum(vals) / len(vals))

    ncert_ids = [b["id"] for b in ncert_books]
    subject_mastery = [
        {
            "subject": "NCERT Foundation (Class 6–12)",
            "percent": _avg_progress(ncert_ids),
            "href": "/ncert",
        }
    ]

    covered_roadmap_ids: set[str] = set()
    for rm in roadmaps:
        sid = rm["subjectId"]
        covered_roadmap_ids.add(sid.lower())
        step_ids = [st["id"] for st in rm.get("steps", [])]
        matching_res = [
            r["id"]
            for r in all_resources
            if _roadmap_matches_resource_subject(sid, r["subject"])
        ]
        subject_mastery.append(
            {
                "subject": rm["subjectName"],
                "percent": _avg_progress(step_ids + matching_res),
                "href": f"/roadmaps/{sid}",
            }
        )

    # Guard against missing roadmaps without EVER duplicating existing 8 roadmaps
    for fallback_id, extra_subj, pill_key in [
        ("environment", "Environment", "Environment"),
        ("ethics", "Ethics", "Ethics"),
        ("csat", "CSAT", "CSAT"),
        ("scitech", "Science & Tech", "Science & Tech"),
    ]:
        if fallback_id in covered_roadmap_ids:
            continue
        ids = [r["id"] for r in all_resources if extra_subj.lower() in r["subject"].lower()]
        if ids:
            subject_mastery.append(
                {
                    "subject": extra_subj,
                    "percent": _avg_progress(ids),
                    "href": f"/resources?pill={pill_key}",
                }
            )

    overall_percent = (
        round(sum(s["percent"] for s in subject_mastery) / len(subject_mastery))
        if subject_mastery
        else 0
    )

    pyq_total = len(pyq_rows)
    pyq_correct = sum(1 for r in pyq_rows if r["is_correct"])
    pyq_accuracy = round((pyq_correct / pyq_total) * 100) if pyq_total else 0
    pyq_by_subject: dict[str, dict[str, int]] = {}
    for r in pyq_rows:
        sb = r["subject"]
        bucket = pyq_by_subject.setdefault(sb, {"attempted": 0, "correct": 0})
        bucket["attempted"] += 1
        bucket["correct"] += int(bool(r["is_correct"]))
    pyq_subject_list = [
        {
            "subject": sb,
            "attempted": b["attempted"],
            "correct": b["correct"],
            "accuracy": round((b["correct"] / b["attempted"]) * 100) if b["attempted"] else 0,
        }
        for sb, b in sorted(pyq_by_subject.items())
    ]

    type_counts: dict[str, int] = {}
    subject_res_counts: dict[str, int] = {}
    completed_resources = 0
    in_progress_resources = 0
    total_catalog_hours = 0
    completed_catalog_hours = 0.0

    for r in all_resources:
        rt = r["type"] or "Other"
        type_counts[rt] = type_counts.get(rt, 0) + 1
        sb = r["subject"] or "General"
        subject_res_counts[sb] = subject_res_counts.get(sb, 0) + 1
        hrs = int(r["estimated_hours"] or 0)
        total_catalog_hours += hrs
        pct = progress_map.get(r["id"], 0)
        completed_catalog_hours += hrs * (pct / 100.0)
        if pct >= 100:
            completed_resources += 1
        elif pct > 0:
            in_progress_resources += 1

    ncert_audit = []
    for cls in [6, 7, 8, 9, 10, 11, 12]:
        cls_books = [b for b in ncert_books if b["classNum"] == cls]
        distinct_subjects = len({b["subjectName"] for b in cls_books})
        total_ch = sum(len(b.get("chapters", [])) for b in cls_books)
        covered_ch = sum(
            sum(1 for c in b.get("chapters", []) if c.get("hasResources", True) is not False)
            for b in cls_books
        )
        cov_pct = round((covered_ch / total_ch) * 100) if total_ch > 0 else 0
        user_cls_pct = _avg_progress([b["id"] for b in cls_books])
        ncert_audit.append(
            {
                "class_num": cls,
                "subjects": distinct_subjects,
                "books": len(cls_books),
                "total_chapters": total_ch,
                "covered_chapters": covered_ch,
                "coverage_percent": cov_pct,
                "user_completion_percent": user_cls_pct,
                "status": "Complete Coverage" if cov_pct == 100 else "Active Curation",
            }
        )

    daily_target_mins = (user_row["daily_target_hours"] if user_row else 4) * 60
    today_target_percent = (
        min(100, round((today_minutes / daily_target_mins) * 100)) if daily_target_mins else 0
    )
    top_subject = (
        max(subject_minutes.items(), key=lambda kv: kv[1])[0] if subject_minutes else "None yet"
    )

    consistency_score = min(100, round((len(active_days_14) / 10) * 100))
    readiness_score = round(
        0.40 * consistency_score + 0.35 * overall_percent + 0.25 * pyq_accuracy
    )

    today_day_name = _today_weekday()
    today_blocks = [
        t for t in timetable_rows if t["day_of_week"] in ("Daily", today_day_name)
    ]
    tt_total = len(today_blocks)
    tt_done = sum(1 for t in today_blocks if t["completed"])

    weak_subjects = sorted(subject_mastery, key=lambda x: x["percent"])[:3]

    effective_streak = (
        _compute_effective_streak(
            user_row["study_streak_days"], user_row["last_study_date"], today_date
        )
        if user_row
        else 0
    )

    try:
        mg_data = get_master_guide_data()
        mg_meta = mg_data.get("meta", {})
        master_guide_total_links = int(mg_meta.get("total_links", 0))
        master_guide_parts = int(mg_meta.get("parts_count", len(mg_data.get("parts", []))))
    except Exception:
        master_guide_total_links = 0
        master_guide_parts = 0

    return {
        "today_minutes": today_minutes,
        "daily_target_minutes": daily_target_mins,
        "today_target_percent": today_target_percent,
        "weekly_minutes": weekly_minutes,
        "total_minutes": total_minutes,
        "total_sessions": focus_session_count,
        "all_logged_sessions": len(sessions),
        "active_days_last_14": len(active_days_14),
        "study_streak_days": effective_streak,
        "top_subject": top_subject,
        "overall_progress_percent": overall_percent,
        "readiness_score": readiness_score,
        "consistency_score": consistency_score,
        "bookmarks_count": bookmarks_count,
        "notes_count": notes_count,
        "timetable_total": tt_total,
        "timetable_completed": tt_done,
        "pyq_total_attempted": pyq_total,
        "pyq_total_correct": pyq_correct,
        "pyq_accuracy_percent": pyq_accuracy,
        "pyq_by_subject": pyq_subject_list,
        "catalog_total_resources": len(all_resources),
        "catalog_completed": completed_resources,
        "catalog_in_progress": in_progress_resources,
        "catalog_type_counts": type_counts,
        "catalog_subject_counts": subject_res_counts,
        "catalog_total_hours": total_catalog_hours,
        "catalog_completed_hours": round(completed_catalog_hours, 1),
        "master_guide_total_links": master_guide_total_links,
        "master_guide_parts": master_guide_parts,
        "weak_subjects": weak_subjects,
        "daily_series": [
            {"date": d, "label": datetime.strptime(d, "%Y-%m-%d").strftime("%a %d"), "minutes": m}
            for d, m in daily_buckets.items()
        ],
        "subject_minutes": [
            {"subject": subj, "minutes": mins}
            for subj, mins in sorted(subject_minutes.items(), key=lambda x: -x[1])
        ],
        "session_types": session_type_counts,
        "subject_mastery": subject_mastery,
        "ncert_audit": ncert_audit,
    }
