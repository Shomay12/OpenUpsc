"""FastAPI application for OpenUPSC — hardened v3.0 REST API powering the Streamlit Main UI."""

from __future__ import annotations

import html
import importlib
import logging
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.auth import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_DAYS,
)
from backend.database import (
    BASE_DIR,
    DEMO_USER_ID,
    admin_update_user_note,
    authenticate_user,
    backup_database,
    check_db_integrity,
    cleanup_expired_sessions,
    compute_user_analytics,
    create_demo_session,
    create_resource,
    create_resource_suggestion,
    create_user_study_session,
    create_user_timetable_event,
    delete_resource,
    delete_user_account,
    delete_user_study_session,
    delete_user_timetable_event,
    get_admin_user_details,
    get_connection,
    get_current_affairs_data,
    get_master_guide_data,
    get_ncert_data,
    get_pyqs_data,
    get_question_papers_data,
    get_resource_facets,
    get_roadmaps_data,
    get_study_sequence_data,
    get_user_note,
    get_workspace_bundle,
    global_search,
    init_db,
    list_admin_users,
    list_backups,
    list_resource_suggestions,
    list_resources,
    list_user_notes,
    list_user_study_sessions,
    list_user_timetable,
    logout_session,
    record_user_pyq_attempt,
    register_user,
    reset_user_pyq_attempts,
    resolve_session_context,
    save_user_journey_plan,
    save_user_note_item,
    sync_resources_from_master,
    toggle_user_bookmark,
    update_resource,
    update_resource_suggestion_status,
    update_user_password,
    update_user_profile,
    update_user_progress,
    update_user_timetable_event,
)
from backend.models import (
    AdminNoteUpdateRequest,
    JourneyPlanSave,
    LoginRequest,
    NoteUpdateRequest,
    PasswordUpdateRequest,
    ProfileUpdateRequest,
    ProgressUpdateRequest,
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

logger = logging.getLogger("openupsc.api")

APP_VERSION = "3.0.0"
FRONTEND_DIR = BASE_DIR / "frontend"
_STARTED_AT = time.monotonic()


def _get_streamlit_url() -> str:
    return os.environ.get("OPENUPSC_STREAMLIT_URL", "http://localhost:8501").strip() or "http://localhost:8501"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    cleanup_expired_sessions()
    yield


app = FastAPI(
    title="OpenUPSC API",
    description="Hardened Python FastAPI + SQLite WAL backend powering the OpenUPSC Streamlit preparation platform.",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/auth"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


# =========================================================================
# GLOBAL EXCEPTION HANDLERS (ZERO RAW 500 TRACEBACK LEAKS)
# =========================================================================


@app.exception_handler(sqlite3.Error)
async def handle_sqlite_error(_request: Request, exc: sqlite3.Error) -> JSONResponse:
    logger.exception("SQLite error during API request: %s", exc)
    msg = str(exc).lower()
    if "locked" in msg or "busy" in msg:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database is temporarily busy. Please retry in a moment."},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "A database error occurred while processing your request."},
    )


@app.exception_handler(ValueError)
async def handle_value_error(_request: Request, exc: ValueError) -> JSONResponse:
    detail = str(exc) or "Invalid request parameter."
    status_code = 409 if "already exists" in detail.lower() else 400
    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."},
    )


# =========================================================================
# SESSION & COOKIE HELPERS
# =========================================================================


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return request.cookies.get(SESSION_COOKIE_NAME)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )


def get_active_context(request: Request) -> dict[str, Any]:
    """Return active user context. Uses logged-in session or falls back cleanly to Demo workspace."""
    return resolve_session_context(_extract_token(request))


# =========================================================================
# HEALTH CHECK & SYSTEM TELEMETRY / BACKUPS
# =========================================================================


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    db_ok = False
    resources_count = 0
    try:
        with get_connection() as conn:
            resources_count = int(conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0])
            db_ok = True
    except Exception:
        db_ok = False

    master_guide_links = 0
    try:
        mg = get_master_guide_data()
        master_guide_links = int(mg.get("meta", {}).get("total_links", 0))
    except Exception:
        master_guide_links = 0

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "OpenUPSC FastAPI",
        "version": APP_VERSION,
        "uptime_seconds": round(max(0.0, time.monotonic() - _STARTED_AT), 2),
        "db_ok": db_ok,
        "resources_count": resources_count,
        "master_guide_links": master_guide_links,
        "streamlit_url": _get_streamlit_url(),
    }


@app.get("/api/system/diagnostics")
def api_system_diagnostics(
    include_doctor: bool = Query(default=True),
) -> dict[str, Any]:
    db_report = check_db_integrity()
    backups = list_backups()

    catalog_validation: dict[str, Any]
    try:
        engine_mod = importlib.import_module("backend.resource_engine")
        catalog_validation = engine_mod.validate_catalog()
    except Exception as exc:
        catalog_validation = {"valid": False, "errors": [f"Catalog validation unavailable: {exc}"]}

    doctor_summary: Optional[dict[str, Any]] = None
    if include_doctor:
        try:
            doctor_mod = importlib.import_module("subagents.doctor")
            raw_doc = doctor_mod.run_diagnostics(domain="all")
            doctor_summary = {
                "status": raw_doc.get("status"),
                "checked_at": raw_doc.get("checked_at"),
                "summary": raw_doc.get("summary"),
                "domains": {
                    dom: {
                        "status": rep.get("status"),
                        "summary": rep.get("summary"),
                        "duration_ms": rep.get("duration_ms"),
                    }
                    for dom, rep in (raw_doc.get("domains") or {}).items()
                },
            }
        except Exception as exc:
            doctor_summary = {"status": "unavailable", "detail": str(exc)}

    overall_ok = bool(db_report.get("ok")) and bool(catalog_validation.get("valid", True))
    return {
        "status": "healthy" if overall_ok else "degraded",
        "service": "OpenUPSC FastAPI",
        "version": APP_VERSION,
        "uptime_seconds": round(max(0.0, time.monotonic() - _STARTED_AT), 2),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "database": db_report,
        "backups": {
            "count": len(backups),
            "latest": backups[0] if backups else None,
            "items": backups,
        },
        "catalog_validation": catalog_validation,
        "subagents_doctor": doctor_summary,
    }


@app.post("/api/system/backup")
def api_system_backup(
    max_backups: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    result = backup_database(max_backups=max_backups)
    return {
        **result,
        "backup": result,
        "backups": list_backups(),
    }


# =========================================================================
# AUTHENTICATION & PROFILE
# =========================================================================


@app.get("/api/auth/me")
def auth_me(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return {
        "authenticated": ctx["authenticated"],
        "is_demo": ctx["is_demo"],
        "user": ctx["user"],
    }


@app.post("/api/auth/signup")
def auth_signup(payload: SignupRequest, response: Response) -> dict[str, Any]:
    try:
        result = register_user(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            preparation_stage=payload.preparation_stage,
            target_attempt_year=payload.target_attempt_year,
            daily_target_hours=payload.daily_target_hours,
        )
    except ValueError as exc:
        status_code = 409 if "already exists" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    _set_session_cookie(response, result["token"])
    return result


@app.post("/api/auth/login")
def auth_login(payload: LoginRequest, response: Response) -> dict[str, Any]:
    result = authenticate_user(payload.email, payload.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _set_session_cookie(response, result["token"])
    return result


@app.post("/api/auth/demo")
def auth_demo_login(response: Response) -> dict[str, Any]:
    result = create_demo_session()
    _set_session_cookie(response, result["token"])
    return result


@app.post("/api/auth/logout")
def auth_logout(request: Request, response: Response) -> dict[str, str]:
    token = _extract_token(request)
    if token:
        logout_session(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully."}


@app.put("/api/profile")
def update_profile(
    payload: ProfileUpdateRequest, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    patch = payload.model_dump(exclude_unset=True)
    updated = update_user_profile(ctx["user_id"], patch)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"user": updated}


@app.put("/api/auth/password")
def update_password(
    payload: PasswordUpdateRequest, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, str]:
    if not ctx["authenticated"]:
        raise HTTPException(status_code=401, detail="Please log in to change your password.")
    updated = update_user_password(ctx["user_id"], payload.new_password)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "Password updated successfully."}


@app.delete("/api/auth/account")
def delete_account(
    response: Response, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, str]:
    if not ctx["authenticated"]:
        raise HTTPException(status_code=401, detail="Please log in to delete an account.")
    if ctx["user_id"] == DEMO_USER_ID:
        raise HTTPException(
            status_code=400,
            detail="The default demo account cannot be deleted. Sign up for a personal account to test deletion.",
        )
    try:
        deleted = delete_user_account(ctx["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"message": "Account permanently deleted."}


# =========================================================================
# WORKSPACE BOOTSTRAP
# =========================================================================


@app.get("/api/workspace")
def get_workspace(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return get_workspace_bundle(
        user_id=ctx["user_id"],
        authenticated=ctx["authenticated"],
        is_demo=ctx["is_demo"],
    )


# =========================================================================
# MASTER GUIDE, STUDY SEQUENCE & CURRICULUM DATA
# =========================================================================


def _item_matches_query(obj: Any, q_low: str) -> bool:
    if isinstance(obj, str):
        return q_low in obj.lower()
    if isinstance(obj, dict):
        return any(_item_matches_query(v, q_low) for v in obj.values())
    if isinstance(obj, list):
        return any(_item_matches_query(v, q_low) for v in obj)
    return False


@app.get("/api/master-guide")
def api_master_guide(
    part: Optional[int] = Query(default=None, ge=1, le=11),
    q: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    guide = get_master_guide_data()
    q_clean = (q or "").strip()

    if part is None and not q_clean:
        return guide

    parts = list(guide.get("parts", []))
    if part is not None:
        parts = [p for p in parts if int(p.get("part_number", 0)) == part]
        if not parts:
            raise HTTPException(status_code=404, detail=f"Master Guide Part {part} not found.")

    matched_items_count = 0
    if q_clean:
        q_low = q_clean.lower()
        filtered_parts: list[dict[str, Any]] = []
        for p in parts:
            part_matches = q_low in str(p.get("title", "")).lower() or q_low in str(p.get("summary", "")).lower()
            filtered_sections: list[dict[str, Any]] = []
            for sec in p.get("sections", []):
                sec_items = [it for it in sec.get("items", []) if _item_matches_query(it, q_low)]
                sec_title_match = q_low in str(sec.get("title", "")).lower()
                if sec_items or sec_title_match:
                    chosen_items = sec_items if sec_items else list(sec.get("items", []))
                    matched_items_count += len(chosen_items)
                    filtered_sections.append({**sec, "items": chosen_items})
            if filtered_sections or part_matches:
                filtered_parts.append({**p, "sections": filtered_sections})
        parts = filtered_parts
    else:
        matched_items_count = sum(
            len(sec.get("items", [])) for p in parts for sec in p.get("sections", [])
        )

    payload: dict[str, Any] = {
        "meta": guide.get("meta", {}),
        "part_filter": part,
        "query": q_clean or None,
        "matched_items_count": matched_items_count,
        "parts": parts,
    }
    if part is not None and parts:
        payload["part"] = parts[0]
    return payload


@app.get("/api/study-sequence")
def api_study_sequence() -> dict[str, Any]:
    phases = get_study_sequence_data()
    return {
        "phases": phases,
        "study_sequence": phases,
        "total_phases": len(phases),
    }


@app.get("/api/ncert")
def api_ncert(class_num: Optional[int] = Query(default=None)) -> dict[str, Any]:
    books = get_ncert_data()
    if class_num is not None:
        books = [b for b in books if b["classNum"] == class_num]
    return {"classes": [6, 7, 8, 9, 10, 11, 12], "books": books}


@app.get("/api/roadmaps")
def api_roadmaps() -> dict[str, Any]:
    return {"roadmaps": get_roadmaps_data()}


@app.get("/api/roadmaps/{subject_id}")
def api_roadmap_detail(subject_id: str) -> dict[str, Any]:
    for rm in get_roadmaps_data():
        if rm["subjectId"] == subject_id:
            return {"roadmap": rm}
    raise HTTPException(status_code=404, detail="Roadmap not found.")


@app.get("/api/pyqs")
def api_pyqs(
    exam_type: Optional[str] = Query(default=None, alias="type"),
    subject: Optional[str] = Query(default=None),
    year: Optional[int] = Query(default=None),
) -> dict[str, Any]:
    items = get_pyqs_data()
    if exam_type and exam_type != "All":
        items = [i for i in items if i["type"].lower() == exam_type.lower()]
    if subject and subject != "All":
        items = [i for i in items if i["subject"].lower() == subject.lower()]
    if year:
        items = [i for i in items if i["year"] == year]
    return {"pyqs": items, "questionPapers": get_question_papers_data()}


@app.get("/api/question-papers")
def api_question_papers() -> dict[str, Any]:
    return {"questionPapers": get_question_papers_data()}


@app.post("/api/pyq-attempts")
def api_record_pyq_attempt(
    payload: PyqAttemptCreate, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return record_user_pyq_attempt(
        user_id=ctx["user_id"],
        pyq_id=payload.pyq_id,
        subject=payload.subject,
        selected_option=payload.selected_option,
        is_correct=payload.is_correct,
    )


@app.delete("/api/pyq-attempts")
def api_reset_pyq_attempts(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return reset_user_pyq_attempts(ctx["user_id"])


@app.get("/api/current-affairs")
def api_current_affairs() -> dict[str, Any]:
    return {"categories": get_current_affairs_data()}


@app.get("/api/search")
def api_global_search(
    q: str = Query(default=""),
    limit: int = Query(default=40, ge=1, le=100),
) -> dict[str, Any]:
    results = global_search(q, limit=limit)
    return {"query": q.strip(), "count": len(results), "results": results}


# =========================================================================
# RESOURCES CATALOG (PUBLIC READ, FACETS, VALIDATION, RESYNC & ADMIN CRUD)
# =========================================================================


@app.get("/api/resources")
def api_list_resources(
    search: Optional[str] = None,
    pill: Optional[str] = None,
    subject: Optional[str] = None,
    level: Optional[str] = None,
    res_type: Optional[str] = Query(default=None, alias="type"),
    language: Optional[str] = None,
    master_part: Optional[int] = Query(default=None, ge=1, le=11),
    has_playlist: Optional[bool] = None,
    verified_only: bool = False,
) -> dict[str, Any]:
    items = list_resources(
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
    return {"count": len(items), "resources": items}


@app.get("/api/resources/facets")
def api_resource_facets() -> dict[str, Any]:
    return get_resource_facets()


@app.get("/api/resources/validate")
def api_validate_resources() -> dict[str, Any]:
    engine_mod = importlib.import_module("backend.resource_engine")
    report = engine_mod.validate_catalog()
    with get_connection() as conn:
        db_count = int(conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0])
    return {
        **report,
        "db_resources_count": db_count,
    }


@app.post("/api/resources/resync")
def api_resync_resources(
    write_json: bool = Query(default=True),
    force_refresh: bool = Query(default=False),
) -> dict[str, Any]:
    return sync_resources_from_master(write_json=write_json, force_refresh=force_refresh)


@app.post("/api/resources")
def api_create_resource(payload: ResourceCreate) -> dict[str, Any]:
    try:
        saved = create_resource(payload.model_dump())
    except ValueError as exc:
        status_code = 409 if "already exists" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return {"resource": saved}


@app.put("/api/resources/{resource_id}")
def api_update_resource(resource_id: str, payload: ResourceUpdate) -> dict[str, Any]:
    patch = payload.model_dump(exclude_unset=True)
    updated = update_resource(resource_id, patch)
    if not updated:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return {"resource": updated}


@app.delete("/api/resources/{resource_id}")
def api_delete_resource(resource_id: str) -> dict[str, Any]:
    deleted = delete_resource(resource_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resource not found.")
    return {"deleted": True, "id": resource_id}


# =========================================================================
# PROGRESS, NOTES & BOOKMARKS
# =========================================================================


@app.put("/api/progress/{item_id}")
def api_update_progress(
    item_id: str,
    payload: ProgressUpdateRequest,
    ctx: dict[str, Any] = Depends(get_active_context),
) -> dict[str, Any]:
    return update_user_progress(ctx["user_id"], item_id, payload.progress_percentage)


@app.get("/api/notes")
def api_list_notes(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return {"notes": list_user_notes(ctx["user_id"])}


@app.get("/api/notes/{item_id}")
def api_get_note(
    item_id: str, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return get_user_note(ctx["user_id"], item_id)


@app.put("/api/notes/{item_id}")
def api_save_note(
    item_id: str,
    payload: NoteUpdateRequest,
    ctx: dict[str, Any] = Depends(get_active_context),
) -> dict[str, Any]:
    return save_user_note_item(
        user_id=ctx["user_id"],
        item_id=item_id,
        content=payload.content,
        item_title=payload.item_title,
        item_category=payload.item_category,
    )


@app.post("/api/bookmarks/{resource_id}/toggle")
def api_toggle_bookmark(
    resource_id: str, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return toggle_user_bookmark(ctx["user_id"], resource_id)


# =========================================================================
# STUDY SESSIONS, TIMETABLE & JOURNEY PLAN
# =========================================================================


@app.get("/api/study-sessions")
def api_list_sessions(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return {"sessions": list_user_study_sessions(ctx["user_id"])}


@app.post("/api/study-sessions")
def api_create_session(
    payload: StudySessionCreate, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return create_user_study_session(ctx["user_id"], payload.model_dump())


@app.delete("/api/study-sessions/{session_id}")
def api_delete_session(
    session_id: str, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    deleted = delete_user_study_session(ctx["user_id"], session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Study session not found.")
    return {"deleted": True, "id": session_id}


@app.get("/api/timetable")
def api_list_timetable(ctx: dict[str, Any] = Depends(get_active_context)) -> dict[str, Any]:
    return {"timetable": list_user_timetable(ctx["user_id"])}


@app.post("/api/timetable")
def api_create_timetable(
    payload: TimetableCreate, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    event = create_user_timetable_event(ctx["user_id"], payload.model_dump())
    return {"event": event}


@app.put("/api/timetable/{event_id}")
def api_update_timetable(
    event_id: str,
    payload: TimetableUpdate,
    ctx: dict[str, Any] = Depends(get_active_context),
) -> dict[str, Any]:
    patch = payload.model_dump(exclude_unset=True)
    if not patch:
        raise HTTPException(status_code=400, detail="No fields provided for update.")
    try:
        updated = update_user_timetable_event(ctx["user_id"], event_id, patch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Timetable block not found.")
    return {"event": updated}


@app.delete("/api/timetable/{event_id}")
def api_delete_timetable(
    event_id: str, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    deleted = delete_user_timetable_event(ctx["user_id"], event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Timetable block not found.")
    return {"deleted": True, "id": event_id}


@app.put("/api/journey-plan")
def api_save_journey_plan(
    payload: JourneyPlanSave, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return save_user_journey_plan(ctx["user_id"], payload.plan)


# =========================================================================
# RESOURCE SUGGESTIONS, ANALYTICS & ADMIN ENDPOINTS
# =========================================================================


@app.get("/api/suggestions")
def api_list_suggestions() -> dict[str, Any]:
    return {"suggestions": list_resource_suggestions()}


@app.post("/api/suggestions")
def api_create_suggestion(
    payload: SuggestionCreate, ctx: dict[str, Any] = Depends(get_active_context)
) -> dict[str, Any]:
    return create_resource_suggestion(ctx["user_id"], payload.model_dump())


@app.put("/api/suggestions/{suggestion_id}")
def api_update_suggestion(
    suggestion_id: str, payload: SuggestionStatusUpdate
) -> dict[str, Any]:
    updated = update_resource_suggestion_status(suggestion_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Suggestion not found.")
    return {"id": suggestion_id, "status": payload.status}


@app.get("/api/analytics/overview")
def api_analytics_overview(
    user_id: Optional[str] = Query(default=None),
    ctx: dict[str, Any] = Depends(get_active_context),
) -> dict[str, Any]:
    target_uid = user_id or ctx["user_id"]
    analytics = compute_user_analytics(target_uid)
    return {"user_id": target_uid, "analytics": analytics}


@app.get("/api/admin/users")
def api_admin_users() -> dict[str, Any]:
    return {"users": list_admin_users()}


@app.get("/api/admin/user-details")
def api_admin_user_details(user_id: str = Query(...)) -> dict[str, Any]:
    return get_admin_user_details(user_id)


@app.put("/api/admin/notes")
def api_admin_update_note(payload: AdminNoteUpdateRequest) -> dict[str, Any]:
    result = admin_update_user_note(payload.user_id, payload.item_id, payload.content)
    if not result:
        raise HTTPException(status_code=404, detail="Note not found.")
    return result


# =========================================================================
# ROOT LAUNCH CARD, LEGACY FRONTEND & STATIC ASSETS
# =========================================================================


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def _render_status_page(title_suffix: str = "API Gateway", status_code: int = 200) -> HTMLResponse:
    streamlit_url = _get_streamlit_url()
    safe_st_url = html.escape(streamlit_url, quote=True)
    health = health_check()
    res_count = health.get("resources_count", 0)
    mg_links = health.get("master_guide_links", 0)
    db_badge = "SQLite WAL Online" if health.get("db_ok") else "Database Initializing"
    legacy_link = (
        '<a class="link-btn" href="/legacy">Legacy Static View</a>'
        if (FRONTEND_DIR / "index.html").is_file()
        else ""
    )

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>OpenUPSC — {html.escape(title_suffix)}</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --card: #ffffff;
      --ink: #0f172a;
      --muted: #475569;
      --accent: #1d4ed8;
      --accent-hover: #1e40af;
      --border: #e2e8f0;
      --ok-bg: #ecfdf5;
      --ok-ink: #065f46;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: radial-gradient(circle at top right, #eff6ff, var(--bg) 55%);
      color: var(--ink);
    }}
    .card {{
      width: 100%;
      max-width: 580px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 32px;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 999px;
      background: var(--ok-bg);
      color: var(--ok-ink);
      margin-bottom: 14px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 26px; letter-spacing: -0.02em; }}
    p {{ margin: 0 0 22px; color: var(--muted); line-height: 1.55; font-size: 15px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-bottom: 24px;
    }}
    .stat {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
    }}
    .stat strong {{ display: block; font-size: 20px; color: var(--ink); }}
    .stat span {{ font-size: 12px; color: var(--muted); }}
    .cta {{
      display: inline-block;
      width: 100%;
      text-align: center;
      padding: 13px 18px;
      border-radius: 12px;
      background: var(--accent);
      color: #ffffff;
      text-decoration: none;
      font-weight: 600;
      font-size: 15px;
      transition: background 0.15s ease;
    }}
    .cta:hover {{ background: var(--accent-hover); }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 16px;
    }}
    .link-btn {{
      flex: 1 1 auto;
      text-align: center;
      padding: 9px 12px;
      border-radius: 10px;
      border: 1px solid var(--border);
      color: var(--ink);
      text-decoration: none;
      font-size: 13px;
      font-weight: 500;
      background: #ffffff;
    }}
    .link-btn:hover {{ background: #f1f5f9; }}
    .foot {{ margin-top: 18px; font-size: 12px; color: var(--muted); }}
  </style>
</head>
<body>
  <main class="card">
    <span class="pill">&#9679; OpenUPSC API v{APP_VERSION} &middot; {html.escape(db_badge)}</span>
    <h1>OpenUPSC Preparation Platform</h1>
    <p>
      The FastAPI REST backend is live and serving verified Class 6&ndash;12 NCERTs,
      11-part Master Guide links, 8 Subject Roadmaps, PYQs, and UPSC Readiness Analytics.
      Open the redesigned Streamlit Main Application below to study.
    </p>
    <div class="stats">
      <div class="stat"><strong>{res_count}</strong><span>Verified Resources</span></div>
      <div class="stat"><strong>{mg_links}</strong><span>Master Guide Links</span></div>
      <div class="stat"><strong>8</strong><span>Subject Roadmaps</span></div>
    </div>
    <a class="cta" href="{safe_st_url}">Launch OpenUPSC Streamlit Main App &rarr;</a>
    <div class="links">
      <a class="link-btn" href="/docs">Swagger API Docs</a>
      <a class="link-btn" href="/api/health">Health JSON</a>
      <a class="link-btn" href="/api/system/diagnostics">System Diagnostics</a>
      {legacy_link}
    </div>
    <div class="foot">Streamlit target: <code>{safe_st_url}</code></div>
  </main>
</body>
</html>"""
    return HTMLResponse(content=page_html, status_code=status_code)


@app.get("/", include_in_schema=False)
def root_status_page() -> HTMLResponse:
    return _render_status_page("Main Launchpad", status_code=200)


@app.get("/legacy", include_in_schema=False)
@app.get("/legacy/{_subpath:path}", include_in_schema=False)
def serve_legacy_frontend(_subpath: str = ""):
    index_file = FRONTEND_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(str(index_file))
    return JSONResponse({"detail": "Legacy static frontend is not available."}, status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    ico = FRONTEND_DIR / "assets" / "favicon.ico"
    if ico.is_file():
        return FileResponse(str(ico))
    return JSONResponse({"detail": "Not found"}, status_code=404)


@app.get("/{full_path:path}", include_in_schema=False)
def catch_all(full_path: str):
    if full_path == "api" or full_path.startswith("api/"):
        return JSONResponse({"detail": "API route not found."}, status_code=404)
    return _render_status_page("Page Not Found", status_code=404)
