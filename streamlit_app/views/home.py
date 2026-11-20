"""Home & Global Search Command Hub for OpenUPSC."""

from __future__ import annotations

import html
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    AMBER,
    EMERALD,
    INDIGO,
    INK_PRIMARY,
    empty_state,
    fmt_days,
    fmt_mins,
    is_youtube_playable,
    navigate_to,
    page_header,
    pill_badge,
    pills_row,
    progress_bar_html,
    safe_url,
    section_kicker,
    time_greeting,
)

IST = timezone(timedelta(hours=5, minutes=30))

SUBJECT_SHELF: list[tuple[str, str, str]] = [
    ("NCERT", "📘", "Class 6–12 Base"),
    ("Indian Polity", "⚖️", "Constitution & GS-2"),
    ("History", "🏛️", "Ancient to Modern"),
    ("Geography", "🗺️", "Physical & Indian"),
    ("Economy", "📈", "Macro & Budget"),
    ("Current Affairs", "🗞️", "PIB, PRS & Reports"),
    ("Environment", "🌿", "Ecology & Biodiversity"),
    ("Science & Tech", "🧬", "Space, Bio & Defence"),
    ("CSAT", "🧮", "Prelims Paper-II"),
    ("Ethics", "🧭", "GS-4 & Case Studies"),
    ("Art & Culture", "🎭", "Fine Arts & Heritage"),
    ("Question Papers", "📝", "Official PYQ Archives"),
]

FEATURED_PLAYLIST_IDS: tuple[str, ...] = (
    "res-sleepy-ncert-all",
    "res-hd-laxmikanth",
    "res-mrunal-economy-beginners",
    "res-bookstawa-modern",
)


def _compute_duration_minutes(start_hhmm: str, end_hhmm: str) -> int:
    try:
        sh, sm = (int(x) for x in start_hhmm.split(":"))
        eh, em = (int(x) for x in end_hhmm.split(":"))
        diff = (eh * 60 + em) - (sh * 60 + sm)
        return max(15, min(180, diff)) if diff > 0 else 50
    except Exception:
        return 50


def _resolve_next_study_item(workspace: dict[str, Any]) -> dict[str, Any]:
    today_weekday = datetime.now(IST).strftime("%A")
    timetable = workspace.get("timetable") or []
    for ev in timetable:
        if not ev.get("completed") and ev.get("dayOfWeek") in ("Daily", today_weekday):
            mins = _compute_duration_minutes(ev.get("startTime", "06:30"), ev.get("endTime", "07:30"))
            return {
                "source": f"Today's Timetable · {ev.get('startTime', '')}–{ev.get('endTime', '')}",
                "subject": ev.get("subject") or "Indian Polity",
                "topic": ev.get("topic") or "Scheduled Study Block",
                "minutes": mins,
                "resource_title": ev.get("resourceTitle") or "",
            }

    sessions = workspace.get("studySessions") or []
    if sessions:
        last = sessions[0]
        return {
            "source": "Resume Last Study Session",
            "subject": last.get("subject") or "Indian Polity",
            "topic": last.get("topic") or "Revision & Active Recall",
            "minutes": max(25, min(90, int(last.get("durationMinutes") or 50))),
            "resource_title": "",
        }

    return {
        "source": "Recommended Starter Block",
        "subject": "NCERT",
        "topic": "Class 11 Indian Constitution at Work — Chapter 1",
        "minutes": 50,
        "resource_title": "Official NCERT Direct PDF & Lecture",
    }


def _render_search_results(query: str, results: list[dict[str, Any]]) -> None:
    if not results:
        empty_state(
            f"No matches for “{query}”",
            "Try searching by subject (Polity, Geography, Economy), NCERT class (Class 11), book (Laxmikanth, Spectrum), or educator (Mrunal, Bookstawa, Sleepy Classes).",
        )
        return

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        src = str(item.get("source") or "resource").lower()
        grouped[src].append(item)

    labels = {
        "roadmap": ("Subject Roadmaps", "indigo"),
        "resource": ("Verified Free Resources", "emerald"),
        "ncert": ("NCERT Books & Chapters", "amber"),
        "pyq": ("UPSC PYQs", "violet"),
        "question_paper": ("Question Paper Archives", "slate"),
        "master_guide": ("11-Part Master Guide Links", "indigo"),
    }

    st.caption(f"Found **{len(results)}** verified matches across the OpenUPSC knowledge graph.")

    for idx_g, (src_key, items) in enumerate(grouped.items()):
        group_label, pill_var = labels.get(src_key, (src_key.replace("_", " ").title(), "slate"))
        section_kicker(f"{group_label} ({len(items)})")
        cols = st.columns(2)
        for idx, item in enumerate(items[:8]):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(
                        pills_row([(str(item.get("kind") or group_label), pill_var)]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-meta">{html.escape(str(item.get("subtitle", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    b1, b2 = st.columns(2)
                    href = str(item.get("href") or "")
                    ext_url = safe_url(item.get("url"))

                    with b1:
                        if src_key == "roadmap" and "/roadmaps/" in href:
                            rm_slug = href.rsplit("/", 1)[-1]
                            if st.button(
                                "Open Roadmap →",
                                key=f"hs_rm_{idx_g}_{idx}_{rm_slug}",
                                width="stretch",
                                type="primary",
                            ):
                                navigate_to("roadmaps", roadmap_selected_subject=rm_slug)
                        elif src_key == "ncert":
                            if st.button(
                                "Open NCERT →",
                                key=f"hs_ncert_{idx_g}_{idx}",
                                width="stretch",
                                type="primary",
                            ):
                                navigate_to("ncert")
                        elif src_key in ("pyq", "question_paper"):
                            if st.button(
                                "Practice PYQs →",
                                key=f"hs_pyq_{idx_g}_{idx}",
                                width="stretch",
                                type="primary",
                            ):
                                navigate_to("pyqs")
                        elif src_key == "resource":
                            rid = item.get("id")
                            playable, _, _ = is_youtube_playable(ext_url)
                            lbl = "▶ Watch in Library" if playable else "Open in Library →"
                            if st.button(
                                lbl,
                                key=f"hs_res_{idx_g}_{idx}_{rid}",
                                width="stretch",
                                type="primary",
                            ):
                                if playable and rid:
                                    navigate_to("library", lib_theater_resource_id=rid)
                                else:
                                    navigate_to("library", lib_preset_search=str(item.get("title", ""))[:60])
                        else:
                            if st.button(
                                "Explore Library →",
                                key=f"hs_mg_{idx_g}_{idx}",
                                width="stretch",
                            ):
                                navigate_to("library", lib_preset_search=query)
                    with b2:
                        if ext_url:
                            st.link_button("Direct Link ↗", ext_url, width="stretch")


def render_home() -> None:
    client = get_client()
    workspace = client.get_workspace()
    profile = workspace.get("profile") or {}
    analytics = workspace.get("analytics") or {}
    facets = client.get_resource_facets()

    name = profile.get("full_name") or profile.get("name") or "Aspirant"
    stage = profile.get("preparation_stage") or "Foundation (Class 6-12)"
    year = profile.get("target_attempt_year") or "2028"
    daily_target_hrs = int(profile.get("daily_target_hours") or 4)
    total_res = int(facets.get("total") or analytics.get("catalog_total_resources") or 334)

    page_header(
        eyebrow="OpenUPSC Command Workspace",
        title=f"{time_greeting()}, {name}",
        subtitle=(
            f"Distraction-free UPSC CSE preparation powered by {total_res} live-verified free resources, "
            "Class 6–12 NCERTs, 8 subject roadmaps, and real PYQ telemetry."
        ),
        badge_text=f"{stage} · Target CSE {year}",
        badge_variant="indigo",
    )

    # 1. Global Search Bar
    s_col, btn_col = st.columns([5, 1])
    with s_col:
        query = st.text_input(
            "Global Search",
            placeholder="Search 334 free resources, 11 Master Guide parts, 315 NCERT chapters, PYQs, or educators (e.g. Laxmikanth, Class 11 Geography, Mrunal, CSAT)...",
            label_visibility="collapsed",
            key="home_global_search",
        )
    with btn_col:
        if st.button("Explore All →", key="home_jump_library_btn", width="stretch"):
            navigate_to("library", lib_preset_search=query.strip() if query else "")

    if query and query.strip():
        results = client.global_search(query.strip(), limit=40)
        _render_search_results(query.strip(), results)
        st.divider()

    # 2. Four-Metric Readiness Snapshot
    m1, m2, m3, m4 = st.columns(4)
    today_mins = int(analytics.get("today_minutes") or 0)
    today_pct = int(analytics.get("today_target_percent") or 0)
    readiness = int(analytics.get("readiness_score") or 0)
    consistency = int(analytics.get("consistency_score") or 0)
    pyq_acc = int(analytics.get("pyq_accuracy_percent") or 0)
    pyq_att = int(analytics.get("pyq_total_attempted") or 0)
    pyq_corr = int(analytics.get("pyq_total_correct") or 0)
    streak = int(analytics.get("study_streak_days") or 0)
    active_14 = int(analytics.get("active_days_last_14") or 0)

    m1.metric("Today's Focus", fmt_mins(today_mins), f"{today_pct}% of {daily_target_hrs}h daily goal")
    m2.metric("UPSC Readiness Score", f"{readiness} / 100", f"Consistency {consistency}%")
    m3.metric("PYQ Accuracy", f"{pyq_acc}%" if pyq_att else "—", f"{pyq_corr}/{pyq_att} correct" if pyq_att else "No attempts yet")
    m4.metric("Study Streak", fmt_days(streak), f"{active_14}/14 active days")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # 3. Continue Studying + Recommended Next Focus
    left, right = st.columns([1.1, 1.0], gap="medium")

    with left:
        section_kicker("Continue Studying")
        next_item = _resolve_next_study_item(workspace)
        with st.container(border=True):
            st.markdown(
                pills_row([
                    (next_item["source"], "emerald"),
                    (f"{next_item['minutes']} min focus", "slate"),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="ou-card-title" style="font-size:1.12rem;">{html.escape(next_item["subject"], quote=True)}</div>'
                f'<div class="ou-card-desc">{html.escape(next_item["topic"], quote=True)}</div>',
                unsafe_allow_html=True,
            )
            if next_item.get("resource_title"):
                st.caption(f"Linked Material: {next_item['resource_title']}")

            st.markdown(
                progress_bar_html(
                    today_pct,
                    label=f"Today's Study Target ({fmt_mins(today_mins)} / {daily_target_hrs}h)",
                    color=EMERALD if today_pct >= 80 else INDIGO,
                ),
                unsafe_allow_html=True,
            )

            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button(
                    "▶ Start Focus Timer →",
                    key="home_continue_timer_btn",
                    type="primary",
                    width="stretch",
                ):
                    navigate_to(
                        "study_workspace",
                        study_prefill={
                            "subject": next_item["subject"],
                            "topic": next_item["topic"],
                            "minutes": next_item["minutes"],
                        },
                    )
            with c_btn2:
                if st.button("Open Deep Analytics", key="home_open_analytics_btn", width="stretch"):
                    navigate_to("analytics")

    with right:
        section_kicker("Recommended Next Focus")
        weak = analytics.get("weak_subjects") or []
        with st.container(border=True):
            if not weak:
                st.success("All core syllabus pillars are progressing evenly. Keep revising!")
            else:
                st.caption("Lowest completion pillars based on your NCERT & Roadmap progress:")
                for idx, item in enumerate(weak[:3]):
                    subj = str(item.get("subject") or "Subject")
                    pct = int(item.get("percent") or 0)
                    href = str(item.get("href") or "/roadmaps/polity")
                    row_l, row_r = st.columns([3.2, 1.1])
                    with row_l:
                        st.markdown(
                            progress_bar_html(
                                pct,
                                label=subj,
                                color=AMBER if pct < 35 else INDIGO,
                            ),
                            unsafe_allow_html=True,
                        )
                    with row_r:
                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                        if st.button("Focus →", key=f"home_weak_btn_{idx}", width="stretch"):
                            if href == "/ncert":
                                navigate_to("ncert")
                            elif "/roadmaps/" in href:
                                navigate_to("roadmaps", roadmap_selected_subject=href.rsplit("/", 1)[-1])
                            else:
                                navigate_to("roadmaps")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # 4. Browse by Subject Shelf (12 Interactive Cards)
    section_kicker("Browse Verified Catalog by Subject")
    subj_counts = facets.get("subject_counts") or {}
    for row_start in range(0, len(SUBJECT_SHELF), 4):
        cols = st.columns(4)
        for offset, (subj_name, icon, blurb) in enumerate(SUBJECT_SHELF[row_start : row_start + 4]):
            cnt = int(subj_counts.get(subj_name, 0))
            with cols[offset]:
                with st.container(border=True):
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
                        f'<span style="font-size:1.15rem;">{icon}</span>'
                        f'{pill_badge(f"{cnt} free", "slate")}'
                        f"</div>"
                        f'<div class="ou-card-title">{html.escape(subj_name, quote=True)}</div>'
                        f'<div class="ou-card-meta">{html.escape(blurb, quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        f"Browse {subj_name}",
                        key=f"home_shelf_{subj_name}",
                        width="stretch",
                    ):
                        navigate_to("library", lib_preset_subject=subj_name)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # 5. Featured Free Video Courses (Top 4 Playlists -> 1-Click Watch In-App)
    section_kicker("Featured Free Video Courses · Watch Distraction-Free In-App")
    all_video = client.get_resources(has_playlist=True)
    by_id = {r["id"]: r for r in all_video}
    featured: list[dict[str, Any]] = [by_id[fid] for fid in FEATURED_PLAYLIST_IDS if fid in by_id]
    if len(featured) < 4:
        for r in all_video:
            if r["id"] not in {x["id"] for x in featured}:
                featured.append(r)
            if len(featured) >= 4:
                break

    if featured:
        f_cols = st.columns(2)
        for idx, res in enumerate(featured[:4]):
            with f_cols[idx % 2]:
                with st.container(border=True):
                    st.markdown(
                        pills_row([
                            (str(res.get("subject") or "UPSC"), "indigo"),
                            (str(res.get("level") or "Foundation"), "slate"),
                            (str(res.get("language") or "Hinglish"), "emerald"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(res.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-meta">Educator: {html.escape(str(res.get("provider", "")), quote=True)}'
                        f' &middot; {int(res.get("estimatedHours") or 0)} hrs est.</div>'
                        f'<div class="ou-card-desc">{html.escape(str(res.get("seniorTip") or res.get("description") or "")[:175], quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button(
                            "▶ Watch In-App",
                            key=f"home_feat_watch_{res['id']}",
                            type="primary",
                            width="stretch",
                        ):
                            navigate_to("library", lib_theater_resource_id=res["id"])
                    with c2:
                        ext = safe_url(res.get("url"))
                        if ext:
                            st.link_button("YouTube ↗", ext, width="stretch")
    else:
        empty_state("Video Library Loading", "Visit the Free Resource Library to explore all verified YouTube playlists.")
