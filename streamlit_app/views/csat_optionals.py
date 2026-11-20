"""CSAT Prelims Paper-II Kit (Part 9), Optional Subjects Repositories (Part 10.1) & Personality Test / Interview (Part 10.2)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    empty_state,
    is_youtube_playable,
    navigate_to,
    page_header,
    pills_row,
    render_lazy_youtube_player,
    render_youtube_player,
    safe_url,
    section_kicker,
    senior_tip_box,
)


def _render_csat_tab(csat_kit: list[dict[str, Any]]) -> None:
    senior_tip_box(
        "CSAT Paper-II (66.67 / 200 qualifying) eliminates more well-prepared GS aspirants every year than any other paper. "
        "Dedicate 45 minutes daily from January onwards: NCERT Class 8–10 Maths + 2014–2024 UPSC CSAT PYQs + reading comprehension.",
        label="Senior CSAT Survival Strategy",
    )

    playable_csat = [item for item in csat_kit if item.get("youtube_playlist_id") or is_youtube_playable(item.get("url"))[0]]

    # Quick In-App CSAT Playlist Theater
    if playable_csat:
        section_kicker(f"In-App CSAT Lecture Theater ({len(playable_csat)} Full Free Playlists)")
        with st.container(border=True):
            pl_labels = [f"{it.get('title', 'CSAT')} ({it.get('resource_type', 'Video')})" for it in playable_csat]
            pl_map = dict(zip(pl_labels, playable_csat))
            chosen = st.selectbox(
                "Pick a Free CSAT Playlist to Watch In-App",
                options=pl_labels,
                key="csat_theater_pick",
            )
            active_pl = pl_map[chosen]
            c1, c2 = st.columns([1.4, 1.4])
            with c1:
                show_player = st.toggle("▶ Load Embedded CSAT Playlist Player", value=False, key="csat_theater_toggle")
            with c2:
                if st.button("🎯 Practice CSAT PYQs Now →", key="csat_jump_pyq_btn", type="primary", width="stretch"):
                    navigate_to("pyqs", pyq_preset_subject="CSAT")
            if show_player:
                render_youtube_player(
                    active_pl.get("url"),
                    title=str(active_pl.get("title", "")),
                    provider=str(active_pl.get("resource_type", "Verified Free CSAT Series")),
                    height=400,
                )

    section_kicker(f"Part 9 · Complete CSAT Free Kit ({len(csat_kit)} Verified Resources)")
    rtypes = ["All"] + sorted({str(x.get("resource_type", "")) for x in csat_kit if x.get("resource_type")})
    f1, f2 = st.columns([1.5, 2.2])
    with f1:
        sel_rt = st.selectbox("Resource Type", options=rtypes, key="csat_filter_type")
    with f2:
        q = st.text_input("Search CSAT Resources", placeholder="e.g., UNGIST, Sleepy, Drishti, NCERT Maths, Quant...", key="csat_filter_q")

    q_low = (q or "").strip().lower()
    matched = [
        item
        for item in csat_kit
        if (sel_rt == "All" or item.get("resource_type") == sel_rt)
        and (
            not q_low
            or q_low in str(item.get("title", "")).lower()
            or q_low in str(item.get("resource_type", "")).lower()
        )
    ]

    if not matched:
        empty_state("No CSAT resources matched", "Reset filters to view all 16 verified CSAT resources.")
        return

    for i in range(0, len(matched), 2):
        cols = st.columns(2, gap="medium")
        for off, item in enumerate(matched[i : i + 2]):
            ext = safe_url(item.get("url"))
            playable, _, _ = is_youtube_playable(ext)
            with cols[off]:
                with st.container(border=True):
                    st.markdown(
                        pills_row([
                            (str(item.get("resource_type") or "CSAT"), "indigo" if playable else "emerald"),
                            ("Playable In-App" if playable else "Direct Link", "dark" if playable else "slate"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    if ext:
                        st.link_button("Open Resource ↗", ext, type="primary", width="stretch")
                    if playable:
                        render_lazy_youtube_player(
                            ext,
                            title=str(item.get("title", "")),
                            provider="Verified CSAT Course",
                            key=f"csat_pl_{i}_{off}",
                            label="▶ Watch Playlist Here",
                            height=340,
                        )


def _render_optionals_tab(optionals: list[dict[str, Any]]) -> None:
    section_kicker(f"Part 10.1 · Free Open-Access Optional Subject Repositories ({len(optionals)} Major Optionals)")
    st.caption(
        "Combine IGNOU eGyanKosh BA/MA open courseware & e-PG Pathshala postgraduate notes with verified free "
        "optional YouTube lecture playlists."
    )
    if not optionals:
        empty_state("Optional repositories unavailable", "Verify master_guide.json optionals.")
        return

    subj_names = [str(o.get("subject", "Optional")) for o in optionals]
    opt_map = {str(o.get("subject", "Optional")): o for o in optionals}

    sel_opt = st.segmented_control(
        "Select Optional Subject",
        options=subj_names,
        default=subj_names[0],
        key="opt_subject_ctrl",
    )
    active_opt = opt_map[sel_opt or subj_names[0]]

    acad_links = active_opt.get("academic_links") or []
    vid_links = active_opt.get("video_links") or []

    with st.container(border=True):
        st.markdown(
            pills_row([
                (f"Optional · {active_opt.get('subject', '')}", "dark"),
                (f"{len(acad_links)} Open-Access Academic Sources", "emerald"),
                (f"{len(vid_links)} Free Video Series", "indigo"),
            ]),
            unsafe_allow_html=True,
        )
        st.markdown(f"### {active_opt.get('subject', '')} Optional — Zero-Cost Study Kit")

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown("**📚 Open-Access University Notes & Textbooks**")
            if acad_links:
                for lk in acad_links:
                    url = safe_url(lk.get("url"))
                    with st.container(border=True):
                        st.markdown(f"**{lk.get('title', '')}**")
                        if url:
                            st.link_button("Open Free Academic Portal ↗", url, type="primary", width="stretch")
            else:
                st.caption("Use IGNOU eGyanKosh and e-PG Pathshala repositories.")

        with c2:
            st.markdown("**🎥 Verified Free Optional Video Lectures**")
            if vid_links:
                for vl in vid_links:
                    url = safe_url(vl.get("url"))
                    playable, _, _ = is_youtube_playable(url)
                    with st.container(border=True):
                        st.markdown(f"**{vl.get('title', '')}**")
                        if url:
                            st.link_button("Open on YouTube ↗", url, width="stretch")
                        if playable:
                            render_lazy_youtube_player(
                                url,
                                title=str(vl.get("title", "")),
                                provider=f"{active_opt.get('subject', '')} Optional",
                                key=f"opt_pl_{active_opt.get('subject', 'opt')}_{vl.get('title', '')[:18]}",
                                label="▶ Watch Optional Playlist In-App",
                                height=350,
                            )
            else:
                st.caption("No direct video playlists linked yet.")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    with st.expander(f"Overview of All {len(optionals)} Optional Subjects"):
        for opt in optionals:
            st.markdown(
                f"- **{opt.get('subject', '')}**: {len(opt.get('academic_links') or [])} academic portals, "
                f"{len(opt.get('video_links') or [])} verified video courses."
            )


def _render_interview_tab(interview_items: list[dict[str, Any]]) -> None:
    section_kicker(f"Part 10.2 · Personality Test (Interview) & DAF Preparation ({len(interview_items)} Resources)")
    senior_tip_box(
        "The UPSC Personality Test (275 marks) evaluates mental alertness, balanced judgment, ethical integrity, and deep awareness of your Detailed Application Form (DAF) — "
        "home state, district, graduation subject, hobbies, and optional paper. Watch toppers' mock interviews to observe calm body language and structured diplomacy.",
        label="DAF & Board Composure Guidance",
    )

    if not interview_items:
        empty_state("Interview prep resources unavailable", "Verify master_guide.json interview_prep.")
        return

    for idx, item in enumerate(interview_items):
        url = safe_url(item.get("url"))
        playable, _, _ = is_youtube_playable(url)
        with st.container(border=True):
            c1, c2 = st.columns([3.5, 1.3])
            with c1:
                st.markdown(
                    pills_row([
                        ("Personality Test · 275 Marks", "violet"),
                        ("Playable In-App" if playable else "Official Resource", "emerald"),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                    f'<div class="ou-card-desc">{html.escape(str(item.get("purpose", "")), quote=True)}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if url:
                    st.link_button("Open Source ↗", url, type="primary", width="stretch")
            if playable:
                render_lazy_youtube_player(
                    url,
                    title=str(item.get("title", "")),
                    provider="UPSC Personality Test Prep",
                    key=f"int_pl_{idx}",
                    label="▶ Watch Mock Interviews / Discussions In-App",
                    height=380,
                )

    with st.container(border=True):
        st.markdown("**✅ DAF Self-Audit Checklist (Before Mock Interviews)**")
        d1, d2 = st.columns(2)
        with d1:
            st.markdown(
                "- **Home State & District**: Demographics, GI tags, economy, key schemes, historical heritage.\n"
                "- **Graduation & Work Exp**: Core fundamentals + how your degree adds value to civil administration.\n"
                "- **Service Preference**: Clear, honest rationale for IAS / IFS / IPS / IRS order."
            )
        with d2:
            st.markdown(
                "- **Hobbies & Achievements**: Factual depth without bluffing — prepare 10 follow-up questions per hobby.\n"
                "- **Current Issues Balance**: Always frame answers with Constitutional values, data, pros/cons, and Way Forward.\n"
                "- **Honesty Rule**: Saying *'I am not sure, Sir/Ma'am, I will read up on it'* beats guessing every time."
            )


def render_csat_optionals() -> None:
    client = get_client()
    master_guide = client.get_master_guide()
    csat_kit = master_guide.get("csat_kit") or []
    optionals = master_guide.get("optionals") or []
    interview_items = master_guide.get("interview_prep") or []

    page_header(
        eyebrow="Complete 3-Stage UPSC Readiness",
        title="CSAT Paper-II, Optionals & Personality Test (DAF)",
        subtitle=(
            f"Master Prelims CSAT with {len(csat_kit)} verified free courses, explore {len(optionals)} major Optional "
            f"open-access repositories, and prepare for the Personality Test with {len(interview_items)} curated DAF & mock resources."
        ),
        badge_text="Parts 9 & 10 · 100% Free",
        badge_variant="indigo",
    )

    tab1, tab2, tab3 = st.tabs([
        f"🧮 CSAT Paper-II Kit ({len(csat_kit)})",
        f"🎓 Optional Subjects ({len(optionals)} Subjects)",
        f"🎙️ Interview & DAF Prep ({len(interview_items)})",
    ])

    with tab1:
        _render_csat_tab(csat_kit)
    with tab2:
        _render_optionals_tab(optionals)
    with tab3:
        _render_interview_tab(interview_items)
