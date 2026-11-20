"""Pydantic request and response schemas with strict validation for OpenUPSC."""

from __future__ import annotations

import re
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_HOSTNAME_RE = re.compile(
    r"^(?:localhost|(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}|(?:\d{1,3}\.){3}\d{1,3})$"
)
_FORBIDDEN_URL_CHARS = set(" \t\r\n[]<>\"'`\\{}|")

PREPARATION_STAGES = [
    "Zero Foundation",
    "Foundation (Class 6-12)",
    "Standard Core",
    "Prelims Focused",
    "Mains Focused",
]


def _clean_non_empty(value: str, field_name: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be blank.")
    return cleaned


def _validate_http_url(value: str) -> str:
    """Strictly validate a single clean http(s) URL using urllib.parse.urlparse."""
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError("URL cannot be blank.")

    if any(ch in _FORBIDDEN_URL_CHARS for ch in cleaned):
        raise ValueError("URL must not contain spaces or invalid characters.")

    lower = cleaned.lower()
    if lower.count("http://") + lower.count("https://") != 1:
        raise ValueError("URL must be a single valid http:// or https:// address.")

    try:
        parsed = urlparse(cleaned)
    except ValueError as exc:
        raise ValueError("URL is malformed.") from exc

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("URL must start with https:// or http://")

    if not parsed.netloc or "@" in parsed.netloc or "&" in parsed.netloc:
        raise ValueError("URL must contain a valid host without composite '&' or credentials.")

    if "&" in parsed.path:
        raise ValueError("URL path must not contain composite '&' characters.")

    if parsed.query and ("http://" in parsed.query.lower() or "https://" in parsed.query.lower()):
        raise ValueError("Composite URLs are not allowed.")

    host = parsed.hostname or ""
    if not host or not _HOSTNAME_RE.match(host):
        raise ValueError("URL must contain a valid hostname.")

    return cleaned


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=6, max_length=128)
    preparation_stage: str = "Foundation (Class 6-12)"
    target_attempt_year: str = "2028"
    daily_target_hours: int = Field(default=4, ge=1, le=16)

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: str) -> str:
        return _clean_non_empty(v, "Full name")

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_RE.match(cleaned):
            raise ValueError("Please enter a valid email address.")
        return cleaned


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    preparation_stage: Optional[str] = None
    target_attempt_year: Optional[str] = None
    daily_target_hours: Optional[int] = Field(default=None, ge=1, le=16)
    preferred_language: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def check_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _clean_non_empty(v, "Full name")


class PasswordUpdateRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class ProgressUpdateRequest(BaseModel):
    progress_percentage: int = Field(..., ge=0, le=100)


class NoteUpdateRequest(BaseModel):
    content: str = ""
    item_title: Optional[str] = None
    item_category: Optional[str] = None


class AdminNoteUpdateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    item_id: str = Field(..., min_length=1)
    content: str = ""

    @field_validator("user_id", "item_id")
    @classmethod
    def check_ids(cls, v: str) -> str:
        return _clean_non_empty(v, "Identifier")


class StudySessionCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(default="", max_length=250)
    resource_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: int = Field(..., ge=1, le=600)
    session_type: str = "Focus"
    completed: bool = True
    notes: Optional[str] = None

    @field_validator("subject")
    @classmethod
    def check_subject(cls, v: str) -> str:
        return _clean_non_empty(v, "Subject")


class PyqAttemptCreate(BaseModel):
    pyq_id: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    selected_option: str = Field(..., min_length=1)
    is_correct: Optional[bool] = None

    @field_validator("pyq_id", "subject", "selected_option")
    @classmethod
    def check_pyq_fields(cls, v: str) -> str:
        return _clean_non_empty(v, "Field")


class TimetableCreate(BaseModel):
    day_of_week: str = "Daily"
    start_time: str = "06:30"
    end_time: str = "07:30"
    subject: str
    topic: str
    resource_id: Optional[str] = None
    resource_title: Optional[str] = None
    completed: bool = False

    @field_validator("day_of_week")
    @classmethod
    def check_day(cls, v: str) -> str:
        return _clean_non_empty(v, "Day of week")

    @field_validator("subject")
    @classmethod
    def check_subject(cls, v: str) -> str:
        return _clean_non_empty(v, "Subject")

    @field_validator("topic")
    @classmethod
    def check_topic(cls, v: str) -> str:
        return _clean_non_empty(v, "Topic")

    @field_validator("start_time", "end_time")
    @classmethod
    def check_time(cls, v: str) -> str:
        cleaned = (v or "").strip()
        if not TIME_RE.match(cleaned):
            raise ValueError("Time must be in HH:MM 24-hour format.")
        return cleaned

    @model_validator(mode="after")
    def check_order(self) -> "TimetableCreate":
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time.")
        return self


class TimetableUpdate(BaseModel):
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    resource_id: Optional[str] = None
    resource_title: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("day_of_week", "subject", "topic")
    @classmethod
    def check_non_empty_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _clean_non_empty(v, "Field")

    @field_validator("start_time", "end_time")
    @classmethod
    def check_time_opt(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not TIME_RE.match(cleaned):
            raise ValueError("Time must be in HH:MM 24-hour format.")
        return cleaned

    @model_validator(mode="after")
    def check_order(self) -> "TimetableUpdate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after start time.")
        return self


class ResourceCreate(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=250)
    subject: str = "General"
    category: str = "NCERT Foundation"
    level: str = "Foundation"
    class_level: Optional[str] = None
    language: str = "English/Hinglish"
    type: str = "YouTube"
    provider: str = "Independent Educator"
    url: str = Field(..., min_length=8)
    description: str = ""
    senior_tip: Optional[str] = None
    views: Optional[str] = None
    likes: Optional[str] = None
    channel_subscribers: Optional[str] = None
    playlist_length: Optional[str] = None
    estimated_hours: int = Field(default=0, ge=0)
    free: bool = True
    verified: bool = True
    verification_status: str = "Verified"
    next_resource_title: Optional[str] = None
    tags: list[str] = Field(default_factory=lambda: ["UPSC"])
    master_part: Optional[int] = Field(default=None, ge=1, le=11)

    @field_validator("id")
    @classmethod
    def check_opt_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned or None

    @field_validator("title", "subject", "provider")
    @classmethod
    def check_required_str(cls, v: str) -> str:
        return _clean_non_empty(v, "Field")

    @field_validator("url")
    @classmethod
    def check_url(cls, v: str) -> str:
        return _validate_http_url(v)


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    class_level: Optional[str] = None
    language: Optional[str] = None
    type: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    senior_tip: Optional[str] = None
    views: Optional[str] = None
    playlist_length: Optional[str] = None
    estimated_hours: Optional[int] = Field(default=None, ge=0)
    verified: Optional[bool] = None
    verification_status: Optional[str] = None
    next_resource_title: Optional[str] = None
    tags: Optional[list[str]] = None
    master_part: Optional[int] = Field(default=None, ge=1, le=11)

    @field_validator("title", "subject", "provider")
    @classmethod
    def check_opt_non_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _clean_non_empty(v, "Field")

    @field_validator("url")
    @classmethod
    def check_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return _validate_http_url(v)


class SuggestionCreate(BaseModel):
    subject: str
    chapter_title: str
    chapter_num: int = 0
    url: str
    channel: Optional[str] = ""

    @field_validator("subject", "chapter_title")
    @classmethod
    def check_fields(cls, v: str) -> str:
        return _clean_non_empty(v, "Field")

    @field_validator("url")
    @classmethod
    def check_url(cls, v: str) -> str:
        return _validate_http_url(v)


class SuggestionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|dismissed)$")


class JourneyPlanSave(BaseModel):
    plan: dict[str, Any]
