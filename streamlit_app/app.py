"""OpenUPSC Flagship Streamlit Application — Unified Student, Analytics & Admin Workspace."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.client import get_client  # noqa: E402
from streamlit_app.theme import (  # noqa: E402
    fmt_days,
    fmt_mins,
    inject_theme,
    navigate_to,
    pill_badge,
    safe_page,
)
from streamlit_app.views.admin_system import render_admin_system  # noqa: E402
from streamlit_app.views.analytics import render_analytics  # noqa: E402
from streamlit_app.views.csat_optionals import render_csat_optionals  # noqa: E402
from streamlit_app.views.current_affairs import render_current_affairs  # noqa: E402
from streamlit_app.views.home import render_home  # noqa: E402
from streamlit_app.views.library import render_library  # noqa: E402
from streamlit_app.views.ncert import render_ncert  # noqa: E402
from streamlit_app.views.pyqs import render_pyqs  # noqa: E402
from streamlit_app.views.roadmaps import render_roadmaps  # noqa: E402
from streamlit_app.views.study_workspace import render_study_workspace  # noqa: E402


def _render_sidebar_shell() -> None:
    """Render the calm editorial sidebar brand, live mode pill, aspirant card, and quick controls."""
    client = get_client()
    workspace = client.get_workspace()
    profile = workspace.get("profile") or {}
    analytics = workspace.get("analytics") or {}

    api_live = client.is_api_online()
    mode_badge = pill_badge(
        "● FastAPI Live" if api_live else "● Direct SQLite Mode",
        "emerald" if api_live else "indigo",
    )

    name = str(profile.get("full_name") or profile.get("name") or "Aspirant")
    stage = str(profile.get("preparation_stage") or "Foundation (Class 6-12)")
    year = str(profile.get("target_attempt_year") or "2028")
    today_mins = int(analytics.get("today_minutes") or 0)
    streak = int(analytics.get("study_streak_days") or 0)
    readiness = int(analytics.get("readiness_score") or 0)
    total_res = int(analytics.get("catalog_total_resources") or 334)
    is_demo = bool(workspace.get("is_demo", True))

    with st.sidebar:
        st.markdown(
            f"""
            <div class="ou-brand">
              <div class="ou-brand-name">🏛️ OpenUPSC</div>
              <div class="ou-brand-sub">100% Free Editorial UPSC CSE Platform</div>
              <div style="margin-top:8px;">{mode_badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="ou-sidebar-card">
              <div class="ou-sidebar-name">{html.escape(name, quote=True)}{' · Demo' if is_demo else ''}</div>
              <div class="ou-sidebar-meta">{html.escape(stage, quote=True)} &middot; CSE {html.escape(year, quote=True)}</div>
              <div style="display:flex;justify-content:space-between;margin-top:8px;padding-top:8px;border-top:1px solid #E2E8F0;font-size:11.5px;color:#334155;font-weight:600;">
                <span>Today: {html.escape(fmt_mins(today_mins), quote=True)}</span>
                <span>🔥 {html.escape(fmt_days(streak), quote=True)}</span>
                <span>🎯 {readiness}%</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        q1, q2 = st.columns(2)
        with q1:
            if st.button("↻ Refresh", key="sb_refresh_btn", width="stretch"):
                client.clear_caches()
                client.is_api_online(force=True)
                st.rerun()
        with q2:
            if st.button("⏱ Timer", key="sb_timer_btn", width="stretch"):
                navigate_to("study_workspace")

        st.markdown(
            f"""
            <div style="margin-top:14px;padding-top:10px;border-top:1px solid #E2E8F0;font-size:11.5px;color:#64748B;line-height:1.5;">
              <strong style="color:#0F172A;">{total_res} Verified Free Resources</strong><br/>
              Class 6–12 NCERTs · 8 Roadmaps · 11-Part Master Guide · Zero Paywalls
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_navigation() -> tuple[dict[str, st.Page], dict[str, list[st.Page]]]:
    """Construct all 10 fault-isolated page handles and grouped navigation sections."""
    pages: dict[str, st.Page] = {
        "home": st.Page(
            safe_page(render_home, "Home & Search"),
            title="Home & Search",
            icon=":material/home:",
            url_path="home",
            default=True,
        ),
        "study_workspace": st.Page(
            safe_page(render_study_workspace, "Study Workspace"),
            title="Study Workspace",
            icon=":material/timer:",
            url_path="study",
        ),
        "library": st.Page(
            safe_page(render_library, "Free Resource Library"),
            title="Free Resource Library",
            icon=":material/library_books:",
            url_path="library",
        ),
        "ncert": st.Page(
            safe_page(render_ncert, "NCERT Class 6-12"),
            title="NCERT Class 6–12",
            icon=":material/menu_book:",
            url_path="ncert",
        ),
        "roadmaps": st.Page(
            safe_page(render_roadmaps, "Subject Roadmaps"),
            title="Subject Roadmaps",
            icon=":material/route:",
            url_path="roadmaps",
        ),
        "pyqs": st.Page(
            safe_page(render_pyqs, "PYQs & Official Hub"),
            title="PYQs & Official Hub",
            icon=":material/quiz:",
            url_path="pyqs",
        ),
        "current_affairs": st.Page(
            safe_page(render_current_affairs, "Current Affairs & Reports"),
            title="Current Affairs & Reports",
            icon=":material/newspaper:",
            url_path="current-affairs",
        ),
        "csat_optionals": st.Page(
            safe_page(render_csat_optionals, "CSAT, Optionals & Interview"),
            title="CSAT, Optionals & Interview",
            icon=":material/school:",
            url_path="csat-optionals",
        ),
        "analytics": st.Page(
            safe_page(render_analytics, "Readiness Analytics"),
            title="Readiness Analytics",
            icon=":material/monitoring:",
            url_path="analytics",
        ),
        "admin_system": st.Page(
            safe_page(render_admin_system, "Account, Admin & Health"),
            title="Account, Admin & Health",
            icon=":material/admin_panel_settings:",
            url_path="admin-system",
        ),
    }

    sections: dict[str, list[st.Page]] = {
        "Workspace": [pages["home"], pages["study_workspace"]],
        "Learn & Practice": [
            pages["library"],
            pages["ncert"],
            pages["roadmaps"],
            pages["pyqs"],
            pages["current_affairs"],
            pages["csat_optionals"],
        ],
        "Insights & Operations": [pages["analytics"], pages["admin_system"]],
    }
    return pages, sections


def main() -> None:
    """Run the unified OpenUPSC Streamlit Flagship application."""
    st.set_page_config(
        page_title="OpenUPSC — Free UPSC CSE Workspace",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()

    pages_map, sections = build_navigation()
    st.session_state["_nav_pages"] = pages_map

    current_page = st.navigation(sections, position="sidebar", expanded=True)
    _render_sidebar_shell()
    current_page.run()


if __name__ == "__main__":
    main()
