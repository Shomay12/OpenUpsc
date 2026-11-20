"""Fault-tolerant Dual-Mode Data Client for OpenUPSC Streamlit Flagship.

Routes reads and mutations to the live FastAPI server (`OPENUPSC_API_URL`) when
reachable, attaching the active session Bearer token, and automatically falls back
to `backend.database` SQLite calls via a 15-second circuit breaker whenever the
API server is offline or restarting. HTTP 4xx validation errors are surfaced
faithfully rather than silently swallowed.
"""

from __future__ import annotations

import importlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import streamlit as st
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend import database as db  # noqa: E402
from backend.models import (  # noqa: E402
    PasswordUpdateRequest,
    ProfileUpdateRequest,
    PyqAttemptCreate,
    ResourceCreate,
    ResourceUpdate,
    SignupRequest,
    StudySessionCreate,
    SuggestionCreate,
    SuggestionStatusUpdate,
    TimetableCreate,
    TimetableUpdate,
)

CIRCUIT_TTL_SECONDS = 15.0
DEFAULT_API_TIMEOUT = 2.5
HEALTH_TIMEOUT = 0.65
SQLITE_ONLY_TRUTHY = {"1", "true", "yes", "on"}
SQLITE_ONLY_API_SENTINELS = {"", "none", "off", "sqlite", "direct"}


def _read_config_value(key: str) -> Optional[str]:
    """Read a config value from os.environ first, then st.secrets safely without ever raising."""
    if key in os.environ:
        return os.environ[key]
    try:
        secrets = getattr(st, "secrets", None)
        if secrets is not None and key in secrets:
            val = secrets[key]
            return None if val is None else str(val)
    except Exception:
        return None
    return None


def _is_cloud_runtime() -> bool:
    """Detect Streamlit Community Cloud runtime cleanly."""
    if Path("/mount/src").exists():
        return True
    if os.environ.get("STREAMLIT_SHARING_MODE"):
        return True
    if (os.environ.get("STREAMLIT_RUNTIME_ENV") or "").strip().lower() == "cloud":
        return True
    return False


def _format_pydantic_error(exc: ValidationError) -> str:
    msgs: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "__root__")
        msg = str(err.get("msg", "Invalid value")).replace("Value error, ", "")
        msgs.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(msgs) if msgs else "Validation failed."


def _extract_http_error(resp: requests.Response) -> str:
    try:
        body = resp.json()
        detail = body.get("detail", resp.text)
        if isinstance(detail, list):
            parts = []
            for item in detail:
                if isinstance(item, dict):
                    loc = ".".join(str(x) for x in item.get("loc", []) if x not in ("body", "__root__"))
                    msg = str(item.get("msg", "Invalid input")).replace("Value error, ", "")
                    parts.append(f"{loc}: {msg}" if loc else msg)
                else:
                    parts.append(str(item))
            return "; ".join(parts)
        return str(detail)
    except Exception:
        return f"Request failed (HTTP {resp.status_code})."


class OpenUPSCClient:
    """Unified Dual-Mode Client (FastAPI Live HTTP + Direct SQLite Fallback)."""

    def __init__(self, api_base: Optional[str] = None) -> None:
        self._explicit_api_base = api_base.rstrip("/") if api_base else None
        self._api_online: Optional[bool] = None
        self._last_health_check: float = 0.0
        self._last_health_payload: dict[str, Any] = {}
        self._initialized_db_path: Optional[str] = None
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}

        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Configuration, Session State & Circuit Breaker
    # ------------------------------------------------------------------

    @property
    def cloud_mode(self) -> bool:
        return _is_cloud_runtime()

    def _raw_api_url_setting(self) -> Optional[str]:
        if self._explicit_api_base is not None:
            return self._explicit_api_base
        return _read_config_value("OPENUPSC_API_URL")

    def is_sqlite_only_mode(self) -> bool:
        """Return True when HTTP API probing must be bypassed completely (zero latency)."""
        flag = (_read_config_value("OPENUPSC_SQLITE_ONLY") or "").strip().lower()
        if flag in SQLITE_ONLY_TRUTHY:
            return True

        raw_api = self._raw_api_url_setting()
        if raw_api is not None:
            cleaned = raw_api.strip().lower()
            if cleaned in SQLITE_ONLY_API_SENTINELS:
                return True

        if self.cloud_mode:
            if not raw_api:
                return True
            parsed = urlparse(raw_api.strip())
            host = (parsed.hostname or "").lower()
            if parsed.scheme.lower() not in ("http", "https") or host in ("", "127.0.0.1", "localhost", "::1"):
                return True

        return False

    @property
    def api_base_url(self) -> str:
        if self.is_sqlite_only_mode():
            return ""
        raw = self._raw_api_url_setting()
        if raw is not None and raw.strip():
            return raw.strip().rstrip("/")
        return "http://127.0.0.1:8000"

    @property
    def mode_label(self) -> str:
        if self.is_api_online():
            return "FastAPI Live"
        if self.cloud_mode:
            return "Cloud SQLite Mode"
        return "Direct SQLite Mode"

    def _is_local_api(self) -> bool:
        host = (urlparse(self.api_base_url).hostname or "").lower()
        return host in ("127.0.0.1", "localhost", "::1")

    def _req_kwargs(self, timeout: float = DEFAULT_API_TIMEOUT) -> dict[str, Any]:
        headers: dict[str, str] = {"Accept": "application/json"}
        token = self.auth_token
        if token:
            headers["Authorization"] = f"Bearer {token}"
        kwargs: dict[str, Any] = {"headers": headers, "timeout": timeout}
        if self._is_local_api():
            kwargs["proxies"] = {"http": None, "https": None}
        return kwargs

    def _ss_get(self, key: str, default: Any = None) -> Any:
        try:
            return st.session_state.get(key, default)
        except Exception:
            return default

    def _ss_set(self, key: str, value: Any) -> None:
        try:
            st.session_state[key] = value
        except Exception:
            pass

    @property
    def auth_token(self) -> Optional[str]:
        tok = self._ss_get("auth_token", None)
        return str(tok) if tok else None

    @property
    def active_user_id(self) -> str:
        uid = self._ss_get("active_user_id", None)
        return str(uid) if uid else db.DEMO_USER_ID

    @property
    def is_authenticated(self) -> bool:
        return bool(self._ss_get("authenticated", False))

    @property
    def is_demo(self) -> bool:
        return bool(self._ss_get("is_demo", True))

    def set_auth_state(
        self,
        *,
        token: Optional[str],
        user_id: str,
        authenticated: bool,
        is_demo: bool,
    ) -> None:
        self._ss_set("auth_token", token)
        self._ss_set("active_user_id", user_id or db.DEMO_USER_ID)
        self._ss_set("authenticated", bool(authenticated))
        self._ss_set("is_demo", bool(is_demo))
        self.clear_caches()

    def ensure_db(self) -> None:
        """Ensure SQLite schema and curated seed catalog exist for the active OPENUPSC_DB_PATH."""
        current_path = str(db.get_db_path())
        if self._initialized_db_path != current_path or not Path(current_path).exists():
            db.init_db()
            self._initialized_db_path = current_path
            self._cache.clear()

    def _trip_circuit(self) -> None:
        self._api_online = False
        self._last_health_check = time.monotonic()

    def is_api_online(self, force: bool = False) -> bool:
        """Check FastAPI availability with zero-latency SQLite-only bypass and 15s circuit breaker."""
        if self.is_sqlite_only_mode():
            self._api_online = False
            return False

        now = time.monotonic()
        if (
            not force
            and self._api_online is not None
            and (now - self._last_health_check) < CIRCUIT_TTL_SECONDS
        ):
            return self._api_online

        url = f"{self.api_base_url}/api/health"
        try:
            resp = self._session.get(url, **self._req_kwargs(timeout=HEALTH_TIMEOUT))
            if resp.status_code == 200:
                self._api_online = True
                self._last_health_check = now
                try:
                    self._last_health_payload = resp.json()
                except Exception:
                    self._last_health_payload = {"status": "ok"}
                return True
            self._api_online = False
            self._last_health_check = now
            return False
        except requests.RequestException:
            self._trip_circuit()
            return False

    def connection_mode_label(self) -> str:
        return self.mode_label

    def clear_caches(self) -> None:
        self._cache.clear()

    def _cache_key(self, name: str, *parts: Any) -> tuple[Any, ...]:
        return (str(db.get_db_path()), self.active_user_id, name, *parts)

    def _cache_get(self, key: tuple[Any, ...], ttl: float = 20.0) -> tuple[bool, Any]:
        entry = self._cache.get(key)
        if not entry:
            return False, None
        ts, val = entry
        if (time.monotonic() - ts) <= ttl:
            return True, val
        self._cache.pop(key, None)
        return False, None

    def _cache_set(self, key: tuple[Any, ...], val: Any) -> Any:
        self._cache[key] = (time.monotonic(), val)
        return val

    def _http_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
        timeout: float = DEFAULT_API_TIMEOUT,
    ) -> tuple[Optional[requests.Response], bool]:
        """Execute an HTTP call if API is online.

        Returns `(response, fallback_needed)`.
        - If `fallback_needed` is True, caller must run Direct SQLite Fallback.
        - If `fallback_needed` is False, `response` is a real HTTP response (2xx or 4xx).
        """
        if not self.is_api_online():
            return None, True
        url = f"{self.api_base_url}{path}"
        kwargs = self._req_kwargs(timeout=timeout)
        if params:
            clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
            if clean_params:
                kwargs["params"] = clean_params
        if json_body is not None:
            kwargs["json"] = json_body
        try:
            resp = self._session.request(method, url, **kwargs)
            if resp.status_code >= 500:
                self._trip_circuit()
                return None, True
            return resp, False
        except requests.RequestException:
            self._trip_circuit()
            return None, True

    # ------------------------------------------------------------------
    # Workspace & Analytics
    # ------------------------------------------------------------------

    def get_workspace(self, force_refresh: bool = False) -> dict[str, Any]:
        self.ensure_db()
        ck = self._cache_key("workspace", bool(self.auth_token))
        if not force_refresh:
            hit, cached = self._cache_get(ck, ttl=12.0)
            if hit:
                return cached

        resp, fallback = self._http_request("GET", "/api/workspace")
        if not fallback and resp is not None and resp.ok:
            data = resp.json()
            prof = data.get("profile") or {}
            if prof.get("id"):
                self._ss_set("active_user_id", prof["id"])
                self._ss_set("authenticated", bool(data.get("authenticated", False)))
                self._ss_set("is_demo", bool(data.get("is_demo", True)))
            return self._cache_set(ck, data)

        # Direct SQLite Fallback
        ctx = db.resolve_session_context(self.auth_token)
        uid = ctx["user_id"] if self.auth_token else self.active_user_id
        try:
            bundle = db.get_workspace_bundle(
                user_id=uid,
                authenticated=ctx["authenticated"] if self.auth_token else self.is_authenticated,
                is_demo=ctx["is_demo"] if self.auth_token else (uid == db.DEMO_USER_ID),
            )
        except ValueError:
            self.set_auth_state(token=None, user_id=db.DEMO_USER_ID, authenticated=False, is_demo=True)
            bundle = db.get_workspace_bundle(db.DEMO_USER_ID, authenticated=False, is_demo=True)
        return self._cache_set(ck, bundle)

    def get_analytics(self, user_id: Optional[str] = None, force_refresh: bool = False) -> dict[str, Any]:
        self.ensure_db()
        target_uid = user_id or self.active_user_id
        ck = self._cache_key("analytics", target_uid)
        if not force_refresh:
            hit, cached = self._cache_get(ck, ttl=15.0)
            if hit:
                return cached

        resp, fallback = self._http_request("GET", "/api/analytics/overview", params={"user_id": target_uid})
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("analytics", {}))

        return self._cache_set(ck, db.compute_user_analytics(target_uid))

    # ------------------------------------------------------------------
    # Authentication & Profile
    # ------------------------------------------------------------------

    def login(self, email: str, password: str) -> tuple[bool, str]:
        self.ensure_db()
        clean_email = (email or "").strip().lower()
        if not clean_email or not password:
            return False, "Please enter both email and password."

        resp, fallback = self._http_request(
            "POST", "/api/auth/login", json_body={"email": clean_email, "password": password}
        )
        if not fallback and resp is not None:
            if resp.ok:
                data = resp.json()
                user = data.get("user") or {}
                self.set_auth_state(
                    token=data.get("token"),
                    user_id=user.get("id", db.DEMO_USER_ID),
                    authenticated=True,
                    is_demo=bool(data.get("is_demo", False)),
                )
                return True, f"Welcome back, {user.get('full_name', 'Aspirant')}!"
            return False, _extract_http_error(resp)

        res = db.authenticate_user(clean_email, password)
        if not res:
            return False, "Invalid email or password."
        user = res["user"]
        self.set_auth_state(
            token=res["token"],
            user_id=user["id"],
            authenticated=True,
            is_demo=bool(res["is_demo"]),
        )
        return True, f"Welcome back, {user.get('full_name', 'Aspirant')}!"

    def signup(
        self,
        full_name: str,
        email: str,
        password: str,
        preparation_stage: str = "Foundation (Class 6-12)",
        target_attempt_year: str = "2028",
        daily_target_hours: int = 4,
    ) -> tuple[bool, str]:
        self.ensure_db()
        raw_payload = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "preparation_stage": preparation_stage,
            "target_attempt_year": str(target_attempt_year),
            "daily_target_hours": int(daily_target_hours),
        }
        try:
            validated = SignupRequest(**raw_payload)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc)

        resp, fallback = self._http_request("POST", "/api/auth/signup", json_body=validated.model_dump())
        if not fallback and resp is not None:
            if resp.ok:
                data = resp.json()
                user = data.get("user") or {}
                self.set_auth_state(
                    token=data.get("token"),
                    user_id=user.get("id", db.DEMO_USER_ID),
                    authenticated=True,
                    is_demo=False,
                )
                return True, f"Account created for {user.get('full_name', full_name)}!"
            return False, _extract_http_error(resp)

        try:
            res = db.register_user(**validated.model_dump())
        except ValueError as exc:
            return False, str(exc)
        user = res["user"]
        self.set_auth_state(
            token=res["token"],
            user_id=user["id"],
            authenticated=True,
            is_demo=False,
        )
        return True, f"Account created for {user.get('full_name', full_name)}!"

    def demo_login(self) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request("POST", "/api/auth/demo")
        if not fallback and resp is not None and resp.ok:
            data = resp.json()
            user = data.get("user") or {}
            self.set_auth_state(
                token=data.get("token"),
                user_id=user.get("id", db.DEMO_USER_ID),
                authenticated=True,
                is_demo=True,
            )
            return True, "Signed into Demo Aspirant Workspace."

        res = db.create_demo_session()
        user = res["user"]
        self.set_auth_state(
            token=res["token"],
            user_id=user["id"],
            authenticated=True,
            is_demo=True,
        )
        return True, "Signed into Demo Aspirant Workspace."

    def logout(self) -> tuple[bool, str]:
        self.ensure_db()
        tok = self.auth_token
        resp, fallback = self._http_request("POST", "/api/auth/logout")
        if fallback and tok:
            db.logout_session(tok)
        self.set_auth_state(token=None, user_id=db.DEMO_USER_ID, authenticated=False, is_demo=True)
        return True, "Signed out cleanly. Switched to Demo preview workspace."

    def update_profile(self, patch: dict[str, Any]) -> tuple[bool, str]:
        self.ensure_db()
        try:
            validated = ProfileUpdateRequest(**patch).model_dump(exclude_unset=True)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc)

        resp, fallback = self._http_request("PUT", "/api/profile", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Profile and study targets updated!"
            return False, _extract_http_error(resp)

        updated = db.update_user_profile(self.active_user_id, validated)
        if not updated:
            return False, "Active user record not found."
        self.clear_caches()
        return True, "Profile and study targets updated!"

    def change_password(self, new_password: str) -> tuple[bool, str]:
        self.ensure_db()
        if not self.is_authenticated:
            return False, "Please sign in first to change your password."
        try:
            validated = PasswordUpdateRequest(new_password=new_password)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc)

        resp, fallback = self._http_request("PUT", "/api/auth/password", json_body=validated.model_dump())
        if not fallback and resp is not None:
            if resp.ok:
                return True, "Password updated securely."
            return False, _extract_http_error(resp)

        ok = db.update_user_password(self.active_user_id, validated.new_password)
        return (True, "Password updated securely.") if ok else (False, "User not found.")

    def delete_account(self) -> tuple[bool, str]:
        self.ensure_db()
        if not self.is_authenticated:
            return False, "Please sign in to delete a personal account."
        if self.active_user_id == db.DEMO_USER_ID:
            return False, "The default demo account cannot be deleted. Create a personal account first."

        resp, fallback = self._http_request("DELETE", "/api/auth/account")
        if not fallback and resp is not None:
            if resp.ok:
                self.set_auth_state(token=None, user_id=db.DEMO_USER_ID, authenticated=False, is_demo=True)
                return True, "Personal account permanently deleted."
            return False, _extract_http_error(resp)

        try:
            ok = db.delete_user_account(self.active_user_id)
        except ValueError as exc:
            return False, str(exc)
        if ok:
            self.set_auth_state(token=None, user_id=db.DEMO_USER_ID, authenticated=False, is_demo=True)
            return True, "Personal account permanently deleted."
        return False, "Account not found."

    # ------------------------------------------------------------------
    # Resources Catalog, Facets, Validation & Sync
    # ------------------------------------------------------------------

    def get_resources(
        self,
        *,
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
        self.ensure_db()
        ck = self._cache_key(
            "resources", search, pill, subject, level, res_type, language, master_part, has_playlist, verified_only
        )
        hit, cached = self._cache_get(ck, ttl=25.0)
        if hit:
            return cached

        params = {
            "search": search,
            "pill": pill,
            "subject": subject,
            "level": level,
            "type": res_type,
            "language": language,
            "master_part": master_part,
            "has_playlist": has_playlist,
            "verified_only": True if verified_only else None,
        }
        resp, fallback = self._http_request("GET", "/api/resources", params=params)
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("resources", []))

        items = db.list_resources(
            search=search,
            pill=pill,
            subject=subject,
            level=level,
            res_type=res_type,
            language=language,
            master_part=master_part,
            has_playlist=has_playlist,
            verified_only=verified_only,
        )
        return self._cache_set(ck, items)

    def get_resource_facets(self) -> dict[str, Any]:
        self.ensure_db()
        ck = self._cache_key("resource_facets")
        hit, cached = self._cache_get(ck, ttl=30.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/resources/facets")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json())

        return self._cache_set(ck, db.get_resource_facets())

    def create_resource(self, payload: dict[str, Any]) -> tuple[bool, str, Optional[dict[str, Any]]]:
        self.ensure_db()
        try:
            validated = ResourceCreate(**payload).model_dump()
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), None

        resp, fallback = self._http_request("POST", "/api/resources", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Resource added to catalog!", resp.json().get("resource")
            return False, _extract_http_error(resp), None

        try:
            saved = db.create_resource(validated)
        except ValueError as exc:
            return False, str(exc), None
        self.clear_caches()
        return True, "Resource added to catalog!", saved

    def update_resource(
        self, resource_id: str, payload: dict[str, Any]
    ) -> tuple[bool, str, Optional[dict[str, Any]]]:
        self.ensure_db()
        try:
            validated = ResourceUpdate(**payload).model_dump(exclude_unset=True)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), None

        resp, fallback = self._http_request("PUT", f"/api/resources/{resource_id}", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Resource updated!", resp.json().get("resource")
            return False, _extract_http_error(resp), None

        updated = db.update_resource(resource_id, validated)
        if not updated:
            return False, "Resource not found.", None
        self.clear_caches()
        return True, "Resource updated!", updated

    def delete_resource(self, resource_id: str) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request("DELETE", f"/api/resources/{resource_id}")
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Resource deleted from catalog."
            return False, _extract_http_error(resp)

        ok = db.delete_resource(resource_id)
        if ok:
            self.clear_caches()
            return True, "Resource deleted from catalog."
        return False, "Resource not found."

    def resync_resources(self, write_json: bool = True) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        resp, fallback = self._http_request(
            "POST", "/api/resources/resync", params={"write_json": write_json}, timeout=15.0
        )
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                data = resp.json()
                return True, "Master Guide catalog synchronized cleanly!", data
            return False, _extract_http_error(resp), {}

        data = db.sync_resources_from_master(write_json=write_json)
        self.clear_caches()
        return bool(data.get("ok", True)), "Master Guide catalog synchronized cleanly!", data

    def validate_catalog(self) -> dict[str, Any]:
        self.ensure_db()
        resp, fallback = self._http_request("GET", "/api/resources/validate", timeout=10.0)
        if not fallback and resp is not None and resp.ok:
            return resp.json()

        engine_mod = importlib.import_module("backend.resource_engine")
        report = engine_mod.validate_catalog()
        with db.get_connection() as conn:
            db_count = int(conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0])
        return {**report, "db_resources_count": db_count}

    # ------------------------------------------------------------------
    # Curriculum, Master Guide & Global Search
    # ------------------------------------------------------------------

    def get_master_guide(self, part: Optional[int] = None, q: Optional[str] = None) -> dict[str, Any]:
        ck = self._cache_key("master_guide", part, q)
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/master-guide", params={"part": part, "q": q})
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json())

        guide = db.get_master_guide_data()
        if part is None and not (q or "").strip():
            return self._cache_set(ck, guide)

        parts = list(guide.get("parts", []))
        if part is not None:
            parts = [p for p in parts if int(p.get("part_number", 0)) == part]
        q_low = (q or "").strip().lower()
        if q_low:
            filtered_parts = []
            for p in parts:
                secs = []
                for sec in p.get("sections", []):
                    items = [it for it in sec.get("items", []) if q_low in str(it).lower()]
                    if items or q_low in str(sec.get("title", "")).lower():
                        secs.append({**sec, "items": items or list(sec.get("items", []))})
                if secs or q_low in str(p.get("title", "")).lower():
                    filtered_parts.append({**p, "sections": secs})
            parts = filtered_parts
        payload = {"meta": guide.get("meta", {}), "parts": parts}
        if part is not None and parts:
            payload["part"] = parts[0]
        return self._cache_set(ck, payload)

    def get_study_sequence(self) -> list[dict[str, Any]]:
        ck = self._cache_key("study_sequence")
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/study-sequence")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("phases", []))
        return self._cache_set(ck, db.get_study_sequence_data())

    def get_ncert(self, class_num: Optional[int] = None) -> list[dict[str, Any]]:
        ck = self._cache_key("ncert", class_num)
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/ncert", params={"class_num": class_num})
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("books", []))

        books = db.get_ncert_data()
        if class_num is not None:
            books = [b for b in books if b.get("classNum") == class_num]
        return self._cache_set(ck, books)

    def get_roadmaps(self) -> list[dict[str, Any]]:
        ck = self._cache_key("roadmaps")
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/roadmaps")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("roadmaps", []))
        return self._cache_set(ck, db.get_roadmaps_data())

    def get_pyqs(
        self,
        *,
        exam_type: Optional[str] = None,
        subject: Optional[str] = None,
        year: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        ck = self._cache_key("pyqs", exam_type, subject, year)
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request(
            "GET", "/api/pyqs", params={"type": exam_type, "subject": subject, "year": year}
        )
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("pyqs", []))

        items = db.get_pyqs_data()
        if exam_type and exam_type != "All":
            items = [i for i in items if str(i.get("type", "")).lower() == exam_type.lower()]
        if subject and subject != "All":
            items = [i for i in items if str(i.get("subject", "")).lower() == subject.lower()]
        if year:
            items = [i for i in items if i.get("year") == year]
        return self._cache_set(ck, items)

    def get_question_papers(self) -> list[dict[str, Any]]:
        ck = self._cache_key("question_papers")
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/question-papers")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("questionPapers", []))
        return self._cache_set(ck, db.get_question_papers_data())

    def get_current_affairs(self) -> list[dict[str, Any]]:
        ck = self._cache_key("current_affairs")
        hit, cached = self._cache_get(ck, ttl=60.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/current-affairs")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("categories", []))
        return self._cache_set(ck, db.get_current_affairs_data())

    def global_search(self, query: str, limit: int = 40) -> list[dict[str, Any]]:
        self.ensure_db()
        cleaned = (query or "").strip()
        if not cleaned:
            return []
        resp, fallback = self._http_request("GET", "/api/search", params={"q": cleaned, "limit": limit})
        if not fallback and resp is not None and resp.ok:
            return resp.json().get("results", [])
        return db.global_search(cleaned, limit=limit)

    # ------------------------------------------------------------------
    # Progress, Bookmarks, Notes & PYQ Attempts
    # ------------------------------------------------------------------

    def update_progress(self, item_id: str, pct: int) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        pct_val = max(0, min(100, int(pct)))
        resp, fallback = self._http_request(
            "PUT", f"/api/progress/{item_id}", json_body={"progress_percentage": pct_val}
        )
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, f"Progress saved ({pct_val}%).", resp.json()
            return False, _extract_http_error(resp), {}

        res = db.update_user_progress(self.active_user_id, item_id, pct_val)
        self.clear_caches()
        return True, f"Progress saved ({pct_val}%).", res

    def toggle_bookmark(self, resource_id: str) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        resp, fallback = self._http_request("POST", f"/api/bookmarks/{resource_id}/toggle")
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                data = resp.json()
                msg = "Saved to Bookmarks." if data.get("bookmarked") else "Removed from Bookmarks."
                return True, msg, data
            return False, _extract_http_error(resp), {}

        data = db.toggle_user_bookmark(self.active_user_id, resource_id)
        self.clear_caches()
        msg = "Saved to Bookmarks." if data.get("bookmarked") else "Removed from Bookmarks."
        return True, msg, data

    def get_notes(self) -> list[dict[str, Any]]:
        self.ensure_db()
        resp, fallback = self._http_request("GET", "/api/notes")
        if not fallback and resp is not None and resp.ok:
            return resp.json().get("notes", [])
        return db.list_user_notes(self.active_user_id)

    def save_note(
        self,
        item_id: str,
        content: str,
        item_title: Optional[str] = None,
        item_category: Optional[str] = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        payload = {
            "content": content or "",
            "item_title": item_title,
            "item_category": item_category,
        }
        resp, fallback = self._http_request("PUT", f"/api/notes/{item_id}", json_body=payload)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Personal note saved!", resp.json()
            return False, _extract_http_error(resp), {}

        res = db.save_user_note_item(
            user_id=self.active_user_id,
            item_id=item_id,
            content=content or "",
            item_title=item_title,
            item_category=item_category,
        )
        self.clear_caches()
        return True, "Personal note saved!", res

    def admin_update_note(self, user_id: str, item_id: str, content: str) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request(
            "PUT",
            "/api/admin/notes",
            json_body={"user_id": user_id, "item_id": item_id, "content": content},
        )
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Aspirant note updated!"
            return False, _extract_http_error(resp)

        res = db.admin_update_user_note(user_id, item_id, content)
        if not res:
            return False, "Note not found."
        self.clear_caches()
        return True, "Aspirant note updated!"

    def record_pyq_attempt(
        self,
        pyq_id: str,
        subject: str,
        selected_option: str,
        is_correct: Optional[bool] = None,
    ) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        try:
            validated = PyqAttemptCreate(
                pyq_id=pyq_id,
                subject=subject,
                selected_option=selected_option,
                is_correct=is_correct,
            ).model_dump()
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), {}

        resp, fallback = self._http_request("POST", "/api/pyq-attempts", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Attempt recorded!", resp.json()
            return False, _extract_http_error(resp), {}

        res = db.record_user_pyq_attempt(
            user_id=self.active_user_id,
            pyq_id=validated["pyq_id"],
            subject=validated["subject"],
            selected_option=validated["selected_option"],
            is_correct=validated["is_correct"],
        )
        self.clear_caches()
        return True, "Attempt recorded!", res

    def reset_pyq_attempts(self) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request("DELETE", "/api/pyq-attempts")
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "All PYQ attempts reset."
            return False, _extract_http_error(resp)

        db.reset_user_pyq_attempts(self.active_user_id)
        self.clear_caches()
        return True, "All PYQ attempts reset."

    # ------------------------------------------------------------------
    # Study Sessions & Timetable
    # ------------------------------------------------------------------

    def create_study_session(self, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        try:
            validated = StudySessionCreate(**payload).model_dump()
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), {}

        resp, fallback = self._http_request("POST", "/api/study-sessions", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Study session logged!", resp.json()
            return False, _extract_http_error(resp), {}

        res = db.create_user_study_session(self.active_user_id, validated)
        self.clear_caches()
        return True, "Study session logged!", res

    def delete_study_session(self, session_id: str) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request("DELETE", f"/api/study-sessions/{session_id}")
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Study session deleted."
            return False, _extract_http_error(resp)

        ok = db.delete_user_study_session(self.active_user_id, session_id)
        if ok:
            self.clear_caches()
            return True, "Study session deleted."
        return False, "Study session not found."

    def create_timetable_event(self, payload: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        try:
            validated = TimetableCreate(**payload).model_dump()
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), {}

        resp, fallback = self._http_request("POST", "/api/timetable", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Timetable block added!", resp.json().get("event", {})
            return False, _extract_http_error(resp), {}

        ev = db.create_user_timetable_event(self.active_user_id, validated)
        self.clear_caches()
        return True, "Timetable block added!", ev

    def update_timetable_event(self, event_id: str, patch: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        try:
            validated = TimetableUpdate(**patch).model_dump(exclude_unset=True)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc), {}

        resp, fallback = self._http_request("PUT", f"/api/timetable/{event_id}", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Timetable block updated!", resp.json().get("event", {})
            return False, _extract_http_error(resp), {}

        try:
            ev = db.update_user_timetable_event(self.active_user_id, event_id, validated)
        except ValueError as exc:
            return False, str(exc), {}
        if not ev:
            return False, "Timetable block not found.", {}
        self.clear_caches()
        return True, "Timetable block updated!", ev

    def delete_timetable_event(self, event_id: str) -> tuple[bool, str]:
        self.ensure_db()
        resp, fallback = self._http_request("DELETE", f"/api/timetable/{event_id}")
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Timetable block removed."
            return False, _extract_http_error(resp)

        ok = db.delete_user_timetable_event(self.active_user_id, event_id)
        if ok:
            self.clear_caches()
            return True, "Timetable block removed."
        return False, "Timetable block not found."

    # ------------------------------------------------------------------
    # Community Suggestions & Admin Insights
    # ------------------------------------------------------------------

    def get_suggestions(self) -> list[dict[str, Any]]:
        self.ensure_db()
        resp, fallback = self._http_request("GET", "/api/suggestions")
        if not fallback and resp is not None and resp.ok:
            return resp.json().get("suggestions", [])
        return db.list_resource_suggestions()

    def create_suggestion(self, payload: dict[str, Any]) -> tuple[bool, str]:
        self.ensure_db()
        try:
            validated = SuggestionCreate(**payload).model_dump()
        except ValidationError as exc:
            return False, _format_pydantic_error(exc)

        resp, fallback = self._http_request("POST", "/api/suggestions", json_body=validated)
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, "Thank you! Your free resource suggestion was submitted for review."
            return False, _extract_http_error(resp)

        db.create_resource_suggestion(self.active_user_id, validated)
        self.clear_caches()
        return True, "Thank you! Your free resource suggestion was submitted for review."

    def update_suggestion_status(self, sug_id: str, status: str) -> tuple[bool, str]:
        self.ensure_db()
        try:
            validated = SuggestionStatusUpdate(status=status)
        except ValidationError as exc:
            return False, _format_pydantic_error(exc)

        resp, fallback = self._http_request(
            "PUT", f"/api/suggestions/{sug_id}", json_body=validated.model_dump()
        )
        if not fallback and resp is not None:
            if resp.ok:
                self.clear_caches()
                return True, f"Suggestion marked {validated.status}."
            return False, _extract_http_error(resp)

        ok = db.update_resource_suggestion_status(sug_id, validated.status)
        if ok:
            self.clear_caches()
            return True, f"Suggestion marked {validated.status}."
        return False, "Suggestion not found."

    def get_admin_users(self) -> list[dict[str, Any]]:
        self.ensure_db()
        ck = self._cache_key("admin_users")
        hit, cached = self._cache_get(ck, ttl=15.0)
        if hit:
            return cached

        resp, fallback = self._http_request("GET", "/api/admin/users")
        if not fallback and resp is not None and resp.ok:
            return self._cache_set(ck, resp.json().get("users", []))
        return self._cache_set(ck, db.list_admin_users())

    def get_admin_user_details(self, user_id: str) -> dict[str, Any]:
        self.ensure_db()
        resp, fallback = self._http_request("GET", "/api/admin/user-details", params={"user_id": user_id})
        if not fallback and resp is not None and resp.ok:
            return resp.json()
        return db.get_admin_user_details(user_id)

    # ------------------------------------------------------------------
    # System Diagnostics, Backups & 4-Subagent Console
    # ------------------------------------------------------------------

    def get_system_diagnostics(self, include_doctor: bool = False) -> dict[str, Any]:
        self.ensure_db()
        resp, fallback = self._http_request(
            "GET",
            "/api/system/diagnostics",
            params={"include_doctor": include_doctor},
            timeout=10.0,
        )
        if not fallback and resp is not None and resp.ok:
            return resp.json()

        db_report = db.check_db_integrity()
        backups = db.list_backups()
        try:
            engine_mod = importlib.import_module("backend.resource_engine")
            catalog_val = engine_mod.validate_catalog()
        except Exception as exc:
            catalog_val = {"valid": False, "errors": [str(exc)]}

        doctor_summary = self.run_subagents_doctor("all") if include_doctor else None
        overall_ok = bool(db_report.get("ok")) and bool(catalog_val.get("valid", True))
        return {
            "status": "healthy" if overall_ok else "degraded",
            "service": "OpenUPSC Direct SQLite Fallback",
            "version": "3.0.0",
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "database": db_report,
            "backups": {
                "count": len(backups),
                "latest": backups[0] if backups else None,
                "items": backups,
            },
            "catalog_validation": catalog_val,
            "subagents_doctor": doctor_summary,
        }

    def create_backup(self, max_backups: int = 10) -> tuple[bool, str, dict[str, Any]]:
        self.ensure_db()
        resp, fallback = self._http_request(
            "POST", "/api/system/backup", params={"max_backups": max_backups}, timeout=10.0
        )
        if not fallback and resp is not None:
            if resp.ok:
                data = resp.json()
                return True, f"Backup created: {data.get('filename', 'snapshot.db')}", data
            return False, _extract_http_error(resp), {}

        res = db.backup_database(max_backups=max_backups)
        return bool(res.get("ok")), f"Backup created: {res.get('filename', 'snapshot.db')}", {
            **res,
            "backups": db.list_backups(),
        }

    def list_backups(self) -> list[dict[str, Any]]:
        self.ensure_db()
        return db.list_backups()

    def get_subagents_registry(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        try:
            reg_mod = importlib.import_module("subagents.registry")
            return reg_mod.list_subagents(), reg_mod.check_ownership_boundaries()
        except Exception as exc:
            return [], {"ok": False, "error": str(exc)}

    def run_subagents_doctor(self, domain: str = "all") -> dict[str, Any]:
        try:
            doc_mod = importlib.import_module("subagents.doctor")
            return doc_mod.run_diagnostics(domain=domain)
        except Exception as exc:
            return {"status": "error", "error": str(exc), "domains": {}}


def get_client() -> OpenUPSCClient:
    """Return a session-scoped OpenUPSCClient singleton, auto-reinitializing on env changes."""
    try:
        client = st.session_state.get("_openupsc_client")
        probe = OpenUPSCClient()
        if not isinstance(client, OpenUPSCClient) or (
            client.api_base_url != probe.api_base_url
            or client.is_sqlite_only_mode() != probe.is_sqlite_only_mode()
        ):
            client = probe
            st.session_state["_openupsc_client"] = client
        client.ensure_db()
        return client
    except Exception:
        client = OpenUPSCClient()
        client.ensure_db()
        return client
