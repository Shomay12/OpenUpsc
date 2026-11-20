"""Editorial design system, safe HTML components, YouTube Theater & Focus Timer for OpenUPSC."""

from __future__ import annotations

import html
import json
import logging
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse

import streamlit as st
import streamlit.components.v1 as components

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from backend.resource_engine import (
        extract_youtube_playlist_id,
        extract_youtube_video_id,
    )
except Exception:  # pragma: no cover - defensive fallback
    import re

    def extract_youtube_playlist_id(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        m = re.search(r"[?&]list=([A-Za-z0-9_-]{8,})", url)
        return m.group(1) if m else None

    def extract_youtube_video_id(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?.*v=|embed/|shorts/))([A-Za-z0-9_-]{11})", url)
        return m.group(1) if m else None


logger = logging.getLogger("openupsc.ui")
IST = timezone(timedelta(hours=5, minutes=30))

# Refined Editorial Palette
INK_PRIMARY = "#0F172A"
INK_SECONDARY = "#475569"
INK_MUTED = "#64748B"
CANVAS_BG = "#F8FAFC"
SURFACE_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
EMERALD = "#059669"
INDIGO = "#1D4ED8"
AMBER = "#D97706"
ROSE = "#DC2626"

CHART_PALETTE = [
    "#0F172A",
    "#1D4ED8",
    "#059669",
    "#D97706",
    "#7C3AED",
    "#0891B2",
    "#DC2626",
    "#475569",
]


# =========================================================================
# GLOBAL CSS THEME INJECTION
# =========================================================================


def inject_theme() -> None:
    """Inject refined light editorial CSS styling across OpenUPSC."""
    st.markdown(
        """
        <style>
          /* Main Workspace Layout */
          .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1320px !important;
          }

          /* Refined Sidebar */
          section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
          }
          section[data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem !important;
          }

          /* Metric Cards */
          div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
          }
          div[data-testid="stMetric"]:hover {
            border-color: #CBD5E1;
            box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
          }
          div[data-testid="stMetric"] label {
            font-size: 11.5px !important;
            color: #64748B !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
          }
          div[data-testid="stMetricValue"] {
            font-size: 1.65rem !important;
            font-weight: 700 !important;
            color: #0F172A !important;
            letter-spacing: -0.02em;
          }

          /* Bordered Card Containers */
          div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #FFFFFF;
            border-color: #E2E8F0 !important;
            border-radius: 14px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.025);
          }

          /* Tabs Polish */
          button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            color: #475569 !important;
            padding-bottom: 10px !important;
          }
          button[data-baseweb="tab"][aria-selected="true"] {
            color: #0F172A !important;
          }

          /* Buttons */
          .stButton > button, .stLinkButton > a {
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.15s ease !important;
          }

          /* Editorial Page Header */
          .ou-header {
            display: flex;
            flex-wrap: wrap;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            padding: 4px 0 18px 0;
            margin-bottom: 14px;
            border-bottom: 1px solid #E2E8F0;
          }
          .ou-eyebrow {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #1D4ED8;
            margin-bottom: 4px;
          }
          .ou-title {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.025em;
            line-height: 1.2;
            margin: 0;
          }
          .ou-subtitle {
            font-size: 0.93rem;
            color: #475569;
            margin-top: 6px;
            line-height: 1.5;
            max-width: 780px;
          }

          /* Pills & Badges */
          .ou-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 600;
            line-height: 1.4;
            white-space: nowrap;
            border: 1px solid transparent;
          }
          .ou-pill-slate   { background: #F1F5F9; color: #334155; border-color: #E2E8F0; }
          .ou-pill-emerald { background: #ECFDF5; color: #065F46; border-color: #A7F3D0; }
          .ou-pill-indigo  { background: #EFF6FF; color: #1E40AF; border-color: #BFDBFE; }
          .ou-pill-amber   { background: #FFFBEB; color: #92400E; border-color: #FDE68A; }
          .ou-pill-rose    { background: #FEF2F2; color: #991B1B; border-color: #FECACA; }
          .ou-pill-violet  { background: #F5F3FF; color: #5B21B6; border-color: #DDD6FE; }
          .ou-pill-dark    { background: #0F172A; color: #FFFFFF; border-color: #0F172A; }

          .ou-pills-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
            margin: 2px 0 8px 0;
          }

          /* Senior Mentor Tip Box */
          .ou-tip {
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 3.5px solid #D97706;
            border-radius: 10px;
            padding: 11px 14px;
            margin: 8px 0 10px 0;
          }
          .ou-tip-label {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            color: #92400E;
            margin-bottom: 3px;
          }
          .ou-tip-text {
            font-size: 0.88rem;
            color: #451A03;
            line-height: 1.5;
          }

          /* Progress Bar */
          .ou-prog-wrap { margin: 6px 0 10px 0; }
          .ou-prog-head {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 4px;
          }
          .ou-prog-track {
            width: 100%;
            height: 7px;
            background: #E2E8F0;
            border-radius: 999px;
            overflow: hidden;
          }
          .ou-prog-fill {
            height: 100%;
            border-radius: 999px;
            transition: width 0.25s ease;
          }

          /* Section Kicker */
          .ou-kicker {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: #64748B;
            margin: 14px 0 8px 0;
          }

          /* Empty State */
          .ou-empty {
            background: #FFFFFF;
            border: 1px dashed #CBD5E1;
            border-radius: 14px;
            padding: 28px 20px;
            text-align: center;
            margin: 10px 0;
          }
          .ou-empty-title {
            font-size: 1rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
          }
          .ou-empty-sub {
            font-size: 0.88rem;
            color: #64748B;
          }

          /* Sidebar Brand Card */
          .ou-brand {
            padding: 4px 2px 12px 2px;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 10px;
          }
          .ou-brand-name {
            font-size: 1.25rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.03em;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .ou-brand-sub {
            font-size: 11.5px;
            color: #64748B;
            margin-top: 2px;
          }
          .ou-sidebar-card {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 11px 12px;
            margin: 8px 0;
          }
          .ou-sidebar-name {
            font-size: 0.92rem;
            font-weight: 700;
            color: #0F172A;
          }
          .ou-sidebar-meta {
            font-size: 11.5px;
            color: #475569;
            margin-top: 2px;
          }
          .ou-theater-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #FFFFFF;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
          }
          .ou-card-title {
            font-size: 0.97rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.35;
            margin: 2px 0 4px 0;
          }
          .ou-card-desc {
            font-size: 0.85rem;
            color: #475569;
            line-height: 1.48;
            margin-bottom: 8px;
          }
          .ou-card-meta {
            font-size: 12px;
            color: #64748B;
            margin-bottom: 6px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================================
# SAFE FORMATTING & HTML HELPERS
# =========================================================================


def safe_url(url: Optional[str]) -> Optional[str]:
    """Return a clean http(s) URL or None if invalid."""
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip()
    try:
        parsed = urlparse(cleaned)
        if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
            return cleaned
    except ValueError:
        return None
    return None


def fmt_mins(mins: Any) -> str:
    try:
        m = max(0, int(round(float(mins or 0))))
    except (ValueError, TypeError):
        m = 0
    hrs, rem = divmod(m, 60)
    if hrs and rem:
        return f"{hrs}h {rem}m"
    if hrs:
        return f"{hrs}h"
    return f"{rem}m"


def fmt_days(n: Any) -> str:
    try:
        val = max(0, int(n or 0))
    except (ValueError, TypeError):
        val = 0
    return f"{val} {'Day' if val == 1 else 'Days'}"


def fmt_bytes(size_bytes: Any) -> str:
    try:
        val = float(size_bytes or 0)
    except (ValueError, TypeError):
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if val < 1024.0:
            return f"{val:.1f} {unit}" if unit != "B" else f"{int(val)} B"
        val /= 1024.0
    return f"{val:.1f} TB"


def time_greeting() -> str:
    hour = datetime.now(IST).hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def pill_badge(text: str, variant: str = "slate") -> str:
    safe_text = html.escape(str(text or ""), quote=True)
    safe_var = variant if variant in ("slate", "emerald", "indigo", "amber", "rose", "violet", "dark") else "slate"
    return f'<span class="ou-pill ou-pill-{safe_var}">{safe_text}</span>'


def pills_row(items: list[tuple[str, str]]) -> str:
    spans = [pill_badge(label, var) for label, var in items if label]
    if not spans:
        return ""
    return f'<div class="ou-pills-row">{"".join(spans)}</div>'


def page_header(
    eyebrow: str,
    title: str,
    subtitle: str,
    badge_text: Optional[str] = None,
    badge_variant: str = "emerald",
) -> None:
    safe_eyebrow = html.escape(eyebrow, quote=True)
    safe_title = html.escape(title, quote=True)
    safe_sub = html.escape(subtitle, quote=True)
    badge_html = f"<div>{pill_badge(badge_text, badge_variant)}</div>" if badge_text else ""
    st.markdown(
        f"""
        <div class="ou-header">
          <div>
            <div class="ou-eyebrow">{safe_eyebrow}</div>
            <h1 class="ou-title">{safe_title}</h1>
            <div class="ou-subtitle">{safe_sub}</div>
          </div>
          {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def senior_tip_box(text: Optional[str], label: str = "Senior Mentor Tip") -> None:
    cleaned = (text or "").strip()
    if not cleaned:
        return
    st.markdown(
        f"""
        <div class="ou-tip">
          <div class="ou-tip-label">💡 {html.escape(label, quote=True)}</div>
          <div class="ou-tip-text">{html.escape(cleaned, quote=True)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar_html(pct: Any, label: str = "", color: str = INK_PRIMARY) -> str:
    try:
        val = max(0, min(100, int(round(float(pct or 0)))))
    except (ValueError, TypeError):
        val = 0
    safe_label = html.escape(label, quote=True)
    safe_color = html.escape(color, quote=True)
    header = (
        f'<div class="ou-prog-head"><span>{safe_label}</span><span>{val}%</span></div>'
        if label
        else ""
    )
    return (
        f'<div class="ou-prog-wrap">{header}'
        f'<div class="ou-prog-track"><div class="ou-prog-fill" style="width:{val}%;background:{safe_color};"></div></div>'
        f"</div>"
    )


def section_kicker(text: str) -> None:
    st.markdown(f'<div class="ou-kicker">{html.escape(text, quote=True)}</div>', unsafe_allow_html=True)


def empty_state(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="ou-empty">
          <div class="ou-empty-title">{html.escape(title, quote=True)}</div>
          <div class="ou-empty-sub">{html.escape(subtitle, quote=True)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_editorial_plotly(fig: Any, height: int = 320, showlegend: bool = True) -> Any:
    """Apply calm light editorial layout tokens to any Plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=26, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif", size=12, color=INK_PRIMARY),
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(size=11)),
        hoverlabel=dict(bgcolor="#0F172A", font_color="#FFFFFF", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E2E8F0", tickfont=dict(color=INK_SECONDARY))
    fig.update_yaxes(gridcolor="#F1F5F9", zerolinecolor="#E2E8F0", tickfont=dict(color=INK_SECONDARY))
    return fig


# =========================================================================
# DISTRACTION-FREE IN-APP YOUTUBE PLAYER
# =========================================================================


def is_youtube_playable(url: Optional[str]) -> tuple[bool, Optional[str], Optional[str]]:
    """Return `(playable, playlist_id, video_id)` for a URL."""
    cleaned = safe_url(url)
    if not cleaned:
        return False, None, None
    pid = extract_youtube_playlist_id(cleaned)
    vid = extract_youtube_video_id(cleaned)
    return bool(pid or vid), pid, vid


def _embed_html(raw_html: str, height: int) -> None:
    """Render trusted internal HTML cleanly using Streamlit 1.67 st.iframe (zero deprecations)."""
    if hasattr(st, "iframe"):
        st.iframe(raw_html, width="stretch", height=int(height))
    else:  # pragma: no cover
        components.html(raw_html, height=int(height), scrolling=False)


def render_youtube_player(
    url: Optional[str],
    title: str = "",
    provider: str = "",
    height: int = 410,
) -> None:
    """Render a distraction-free YouTube playlist/video iframe with safe fallback link."""
    cleaned = safe_url(url)
    if not cleaned:
        st.info("No valid video URL is linked to this item.")
        return

    playable, pid, vid = is_youtube_playable(cleaned)
    safe_title = html.escape(title or "Verified Free UPSC Lecture", quote=True)
    safe_prov = html.escape(provider or "Verified Free Educator", quote=True)

    if playable:
        if pid:
            embed_url = f"https://www.youtube-nocookie.com/embed/videoseries?list={html.escape(pid, quote=True)}&rel=0&modestbranding=1"
            mode_label = "Full Playlist Theater"
        else:
            embed_url = f"https://www.youtube-nocookie.com/embed/{html.escape(str(vid), quote=True)}?rel=0&modestbranding=1"
            mode_label = "Single Video Theater"

        iframe_height = max(260, int(height) - 24)
        st.markdown(
            f"""
            <div style="padding:9px 14px;background:#0F172A;color:#F8FAFC;border-radius:12px 12px 0 0;
                        display:flex;justify-content:space-between;align-items:center;gap:10px;
                        border:1px solid #0F172A;">
              <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                <span style="font-weight:700;font-size:13px;">{safe_title}</span>
                <span style="color:#94A3B8;font-size:12px;margin-left:8px;">&middot; {safe_prov}</span>
              </div>
              <span style="font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;
                           background:rgba(16,185,129,0.18);color:#6EE7B7;white-space:nowrap;">
                {mode_label}
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if hasattr(st, "iframe"):
            st.iframe(embed_url, width="stretch", height=iframe_height)
        else:  # pragma: no cover
            components.html(
                f'<iframe width="100%" height="{iframe_height}" src="{embed_url}" frameborder="0" allowfullscreen></iframe>',
                height=iframe_height + 10,
                scrolling=False,
            )
        st.link_button("Open on YouTube ↗", cleaned, width="content")
    else:
        with st.container(border=True):
            st.markdown(f"**{title or 'Verified YouTube Channel'}**")
            st.caption(
                f"{provider or 'Official / Verified Channel'} — Channel homepages cannot be embedded directly inside an iframe. Open directly on YouTube below."
            )
            st.link_button("Open Channel on YouTube ↗", cleaned, type="primary")


def render_lazy_youtube_player(
    url: Optional[str],
    *,
    title: str = "",
    provider: str = "",
    key: str,
    label: str = "▶ Watch Playlist In-App",
    height: int = 380,
) -> None:
    """Mount a YouTube iframe strictly on-demand when toggled open (zero hidden preload lag)."""
    playable, _, _ = is_youtube_playable(url)
    if not playable:
        return
    state_key = f"_yt_open_{key}"
    is_open = bool(st.session_state.get(state_key, False))
    btn_label = "✕ Close In-App Player" if is_open else label
    if st.button(btn_label, key=f"_yt_btn_{key}", type="secondary" if is_open else "primary"):
        st.session_state[state_key] = not is_open
        st.rerun()
    if is_open:
        render_youtube_player(url, title=title, provider=provider, height=height)


# =========================================================================
# WALL-CLOCK ACCURATE FOCUS TIMER COMPONENT (ZERO RERUN FLICKER)
# =========================================================================


def render_focus_timer_widget(
    default_minutes: int = 50,
    subject: str = "Indian Polity",
    topic: str = "",
) -> None:
    """Embed a smooth, wall-clock accurate HTML/CSS/JS Pomodoro Focus Timer."""
    mins = max(1, min(180, int(default_minutes or 50)))
    safe_subject = html.escape(subject or "UPSC Study Session", quote=True)
    safe_topic = html.escape(topic or "Deep Concept Reading & Active Recall", quote=True)
    init_json = json.dumps({"minutes": mins})

    timer_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    background: transparent;
    color: #0F172A;
    padding: 2px;
  }}
  .card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  }}
  .top-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }}
  .subj-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 11px;
    border-radius: 999px;
    background: #EFF6FF;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
  }}
  .chime-btn {{
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid #E2E8F0;
    background: #F8FAFC;
    color: #334155;
    cursor: pointer;
  }}
  .chime-btn.on {{
    background: #ECFDF5;
    color: #065F46;
    border-color: #A7F3D0;
  }}
  .topic {{
    font-size: 13px;
    color: #475569;
    margin-bottom: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .clock-wrap {{
    text-align: center;
    padding: 12px 0 14px 0;
  }}
  .clock {{
    font-size: 56px;
    font-weight: 800;
    letter-spacing: -0.04em;
    font-variant-numeric: tabular-nums;
    color: #0F172A;
    line-height: 1.05;
  }}
  .status-line {{
    font-size: 12px;
    font-weight: 600;
    color: #64748B;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .status-line.running {{ color: #059669; }}
  .status-line.done {{ color: #D97706; }}
  .bar-track {{
    width: 100%;
    height: 8px;
    background: #F1F5F9;
    border-radius: 999px;
    overflow: hidden;
    margin: 12px 0 16px 0;
  }}
  .bar-fill {{
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #0F172A 0%, #1D4ED8 100%);
    border-radius: 999px;
    transition: width 0.25s linear;
  }}
  .presets {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    margin-bottom: 14px;
  }}
  .preset {{
    font-size: 12px;
    font-weight: 600;
    padding: 5px 11px;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    background: #F8FAFC;
    color: #334155;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .preset:hover {{ background: #F1F5F9; border-color: #CBD5E1; }}
  .preset.active {{ background: #0F172A; color: #FFFFFF; border-color: #0F172A; }}
  .controls {{
    display: flex;
    gap: 8px;
    justify-content: center;
    align-items: center;
  }}
  .btn {{
    padding: 9px 18px;
    border-radius: 10px;
    font-size: 13.5px;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
    color: #0F172A;
    transition: all 0.15s ease;
  }}
  .btn:hover {{ background: #F8FAFC; }}
  .btn-primary {{
    background: #0F172A;
    color: #FFFFFF;
    border-color: #0F172A;
    min-width: 126px;
  }}
  .btn-primary:hover {{ background: #1E293B; }}
  .btn-primary.pause {{
    background: #D97706;
    border-color: #D97706;
  }}
  .custom-input {{
    width: 66px;
    padding: 6px 8px;
    border-radius: 8px;
    border: 1px solid #CBD5E1;
    font-size: 12.5px;
    font-weight: 600;
    text-align: center;
    color: #0F172A;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="top-row">
      <span class="subj-pill">🎯 {safe_subject}</span>
      <button id="chimeBtn" class="chime-btn on" type="button">🔔 Chime On</button>
    </div>
    <div class="topic">{safe_topic}</div>
    <div class="clock-wrap">
      <div id="clock" class="clock">50:00</div>
      <div id="statusLine" class="status-line">Ready to focus</div>
    </div>
    <div class="bar-track"><div id="barFill" class="bar-fill"></div></div>
    <div class="presets">
      <button class="preset" data-min="25" type="button">25m Pomodoro</button>
      <button class="preset" data-min="50" type="button">50m Deep Focus</button>
      <button class="preset" data-min="90" type="button">90m Mains Mock</button>
      <button class="preset" data-min="5" type="button">5m Break</button>
      <input id="customMin" class="custom-input" type="number" min="1" max="180" value="{mins}" title="Custom minutes" />
    </div>
    <div class="controls">
      <button id="toggleBtn" class="btn btn-primary" type="button">▶ Start Focus</button>
      <button id="resetBtn" class="btn" type="button">↺ Reset</button>
    </div>
  </div>
<script>
  const cfg = {init_json};
  let totalSec = cfg.minutes * 60;
  let remainingSec = totalSec;
  let running = false;
  let endWallMs = null;
  let rafHandle = null;
  let chimeOn = true;

  const clockEl = document.getElementById("clock");
  const statusEl = document.getElementById("statusLine");
  const barFill = document.getElementById("barFill");
  const toggleBtn = document.getElementById("toggleBtn");
  const resetBtn = document.getElementById("resetBtn");
  const chimeBtn = document.getElementById("chimeBtn");
  const customInput = document.getElementById("customMin");
  const presetBtns = Array.from(document.querySelectorAll(".preset"));

  function playChime() {{
    if (!chimeOn) return;
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      [523.25, 659.25, 783.99].forEach((freq, idx) => {{
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.0001, ctx.currentTime + idx * 0.16);
        gain.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + idx * 0.16 + 0.04);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + idx * 0.16 + 0.45);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(ctx.currentTime + idx * 0.16);
        osc.stop(ctx.currentTime + idx * 0.16 + 0.5);
      }});
    }} catch (e) {{}}
  }}

  function formatTime(sec) {{
    const s = Math.max(0, Math.ceil(sec));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return String(m).padStart(2, "0") + ":" + String(r).padStart(2, "0");
  }}

  function render() {{
    clockEl.textContent = formatTime(remainingSec);
    const pct = totalSec > 0 ? Math.min(100, Math.max(0, ((totalSec - remainingSec) / totalSec) * 100)) : 0;
    barFill.style.width = pct.toFixed(2) + "%";
  }}

  function setDuration(m) {{
    const clamped = Math.max(1, Math.min(180, parseInt(m, 10) || 25));
    running = false;
    if (rafHandle) cancelAnimationFrame(rafHandle);
    totalSec = clamped * 60;
    remainingSec = totalSec;
    customInput.value = clamped;
    toggleBtn.textContent = "▶ Start Focus";
    toggleBtn.classList.remove("pause");
    statusEl.textContent = "Ready to focus";
    statusEl.className = "status-line";
    presetBtns.forEach(b => b.classList.toggle("active", parseInt(b.dataset.min, 10) === clamped));
    render();
  }}

  function tick() {{
    if (!running) return;
    const diff = (endWallMs - Date.now()) / 1000;
    if (diff <= 0) {{
      remainingSec = 0;
      running = false;
      render();
      toggleBtn.textContent = "▶ Start Again";
      toggleBtn.classList.remove("pause");
      statusEl.textContent = "Session Complete — Log it on the right!";
      statusEl.className = "status-line done";
      playChime();
      return;
    }}
    remainingSec = diff;
    render();
    rafHandle = requestAnimationFrame(tick);
  }}

  toggleBtn.addEventListener("click", () => {{
    if (running) {{
      running = false;
      if (rafHandle) cancelAnimationFrame(rafHandle);
      toggleBtn.textContent = "▶ Resume";
      toggleBtn.classList.remove("pause");
      statusEl.textContent = "Paused";
      statusEl.className = "status-line";
    }} else {{
      if (remainingSec <= 0) remainingSec = totalSec;
      running = true;
      endWallMs = Date.now() + remainingSec * 1000;
      toggleBtn.textContent = "⏸ Pause";
      toggleBtn.classList.add("pause");
      statusEl.textContent = "Deep Focus In Progress";
      statusEl.className = "status-line running";
      tick();
    }}
  }});

  resetBtn.addEventListener("click", () => setDuration(customInput.value));
  presetBtns.forEach(b => b.addEventListener("click", () => setDuration(b.dataset.min)));
  customInput.addEventListener("change", () => setDuration(customInput.value));
  chimeBtn.addEventListener("click", () => {{
    chimeOn = !chimeOn;
    chimeBtn.classList.toggle("on", chimeOn);
    chimeBtn.textContent = chimeOn ? "🔔 Chime On" : "🔕 Chime Off";
  }});

  setDuration(cfg.minutes);
</script>
</body>
</html>
"""
    _embed_html(timer_html, height=330)


# =========================================================================
# NAVIGATION HANDOFF & GLOBAL SAFE ERROR BOUNDARY
# =========================================================================


def navigate_to(page_key: str, **params: Any) -> None:
    """Store cross-view handoff parameters and switch cleanly to another Streamlit page."""
    for k, v in params.items():
        st.session_state[k] = v
    nav_pages = st.session_state.get("_nav_pages") or {}
    target = nav_pages.get(page_key)
    if target is not None:
        st.switch_page(target)
    else:
        st.rerun()


def safe_page(render_fn: Callable[[], None], page_title: str = "View") -> Callable[[], None]:
    """Wrap any Streamlit view renderer in a fault-isolated recovery boundary."""

    def _wrapped() -> None:
        try:
            render_fn()
        except Exception as exc:
            # Never swallow Streamlit's internal control-flow signals (RerunException / StopException)
            exc_name = type(exc).__name__
            if exc_name in ("RerunException", "StopException", "SwitchPageException"):
                raise
            logger.exception("Error rendering view %s: %s", page_title, exc)
            with st.container(border=True):
                st.error(f"Something went wrong while rendering **{page_title}**.")
                st.caption(f"{exc_name}: {exc}")
                with st.expander("Technical diagnostics"):
                    st.code(traceback.format_exc(), language="text")
                c1, c2 = st.columns([1, 3])
                with c1:
                    if st.button("↻ Retry View", key=f"err_retry_{page_title}", type="primary", width="stretch"):
                        st.rerun()

    _wrapped.__name__ = getattr(render_fn, "__name__", f"view_{page_title}")
    return _wrapped
