"""Current Affairs, Official Government Reports (Part 4), News & Think-Tanks (Part 5) & Curated Notes (Part 6)."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    empty_state,
    is_youtube_playable,
    page_header,
    pills_row,
    render_lazy_youtube_player,
    render_youtube_player,
    safe_url,
    section_kicker,
)


def _render_gs_radar_tab(categories: list[dict[str, Any]], news_items: list[dict[str, Any]]) -> None:
    # Quick Official Broadcast Theater (Sansad TV Perspective & AIR Spotlight)
    broadcasts = [
        item
        for item in news_items
        if item.get("youtube_playlist_id") or is_youtube_playable(item.get("url"))[0]
    ]
    if broadcasts:
        section_kicker("Quick Official Government Broadcast Player")
        with st.container(border=True):
            b_titles = [str(b.get("title", "Broadcast")) for b in broadcasts]
            b_map = {str(b.get("title", "Broadcast")): b for b in broadcasts}
            chosen_b = st.segmented_control(
                "Select Broadcast",
                options=b_titles,
                default=b_titles[0],
                key="ca_broadcast_pick",
                label_visibility="collapsed",
            )
            active_b = b_map[chosen_b or b_titles[0]]
            st.caption(str(active_b.get("usage") or "Official public-service UPSC current affairs discussion."))
            show_b = st.toggle("▶ Open Embedded Broadcast Player", value=False, key="ca_broadcast_toggle")
            if show_b:
                render_youtube_player(
                    active_b.get("url"),
                    title=str(active_b.get("title", "")),
                    provider="Official Public Broadcast (100% Free)",
                    height=390,
                )
            else:
                ext = safe_url(active_b.get("url"))
                if ext:
                    st.link_button("Open Broadcast Playlist on YouTube ↗", ext)

    section_kicker(f"GS Paper-Wise Current Affairs Radar ({len(categories)} Core Tracks)")
    if not categories:
        empty_state("Current affairs radar unavailable", "Check backend/data/current_affairs.json.")
        return

    for idx, cat in enumerate(categories):
        with st.container(border=True):
            st.markdown(
                pills_row([
                    (str(cat.get("gsPaper") or "GS"), "indigo"),
                    (f"{len(cat.get('keySources') or [])} Verified Sources", "emerald"),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown(f"### {cat.get('title', '')}")
            st.markdown(
                f"<div class='ou-card-desc'>{html.escape(str(cat.get('description', '')), quote=True)}</div>",
                unsafe_allow_html=True,
            )

            topics = cat.get("highYieldTopics") or []
            if topics:
                st.markdown("**High-Yield UPSC Themes**")
                st.markdown(pills_row([(str(t), "amber") for t in topics]), unsafe_allow_html=True)

            sources = cat.get("keySources") or []
            if sources:
                st.markdown("**Authoritative Free Sources & How to Use**")
                s_cols = st.columns(2, gap="small")
                for s_idx, src in enumerate(sources):
                    with s_cols[s_idx % 2]:
                        with st.container(border=True):
                            st.markdown(
                                pills_row([(str(src.get("type") or "Portal"), "slate"), ("100% Free", "emerald")]),
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<div class="ou-card-title">{html.escape(str(src.get("name", "")), quote=True)}</div>'
                                f'<div class="ou-card-desc">{html.escape(str(src.get("howToUse", "")), quote=True)}</div>',
                                unsafe_allow_html=True,
                            )
                            s_url = safe_url(src.get("url"))
                            if s_url:
                                st.link_button("Visit Source ↗", s_url, width="stretch")


def _render_govt_reports_tab(reports: list[dict[str, Any]]) -> None:
    section_kicker(f"Part 4 · Official Government Reports, PRS & Primary Data ({len(reports)} Portals)")
    subsections = ["All"] + sorted({str(r.get("subsection", "")) for r in reports if r.get("subsection")})

    f1, f2 = st.columns([1.8, 2.0])
    with f1:
        sel_sub = st.selectbox("Primary Data Category", options=subsections, key="ca_rep_sub")
    with f2:
        q = st.text_input(
            "Search Reports & Portals",
            placeholder="e.g., PRS, Economic Survey, RBI, NITI Aayog, ISFR, ISRO, PIB...",
            key="ca_rep_q",
        )

    q_low = (q or "").strip().lower()
    matched = [
        r
        for r in reports
        if (sel_sub == "All" or r.get("subsection") == sel_sub)
        and (
            not q_low
            or q_low in str(r.get("title", "")).lower()
            or q_low in str(r.get("utility", "")).lower()
            or q_low in str(r.get("subsection", "")).lower()
        )
    ]

    st.caption(f"Showing **{len(matched)}** of {len(reports)} authoritative primary data portals.")
    if not matched:
        empty_state("No government reports match your search", "Clear search or pick All categories.")
        return

    for i in range(0, len(matched), 2):
        cols = st.columns(2, gap="medium")
        for off, item in enumerate(matched[i : i + 2]):
            with cols[off]:
                with st.container(border=True):
                    sub_short = str(item.get("subsection") or "Primary Data").split(" ", 1)[0]
                    st.markdown(
                        pills_row([(f"Section {sub_short}", "emerald"), ("Official Primary Source", "slate")]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(item.get("utility", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(item.get("url"))
                    if ext:
                        st.link_button("Open Primary Source ↗", ext, type="primary", width="stretch")


def _render_news_thinktanks_tab(news_items: list[dict[str, Any]]) -> None:
    section_kicker(f"Part 5 · Official Broadcasts, Newspapers & Think-Tanks ({len(news_items)} Sources)")
    subsections = ["All"] + sorted({str(r.get("subsection", "")) for r in news_items if r.get("subsection")})

    f1, f2 = st.columns([1.8, 2.0])
    with f1:
        sel_sub = st.selectbox("Source Type", options=subsections, key="ca_news_sub")
    with f2:
        q = st.text_input("Search News & Think-Tanks", placeholder="e.g., Sansad TV, AIR, ORF, IDSA, EPW, Indian Express...", key="ca_news_q")

    q_low = (q or "").strip().lower()
    matched = [
        r
        for r in news_items
        if (sel_sub == "All" or r.get("subsection") == sel_sub)
        and (
            not q_low
            or q_low in str(r.get("title", "")).lower()
            or q_low in str(r.get("usage", "")).lower()
        )
    ]

    if not matched:
        empty_state("No news or think-tank sources matched", "Try clearing your search.")
        return

    for idx, item in enumerate(matched):
        ext = safe_url(item.get("url"))
        playable, _, _ = is_youtube_playable(ext)
        is_official = "5.1" in str(item.get("subsection", ""))
        with st.container(border=True):
            c1, c2 = st.columns([3.6, 1.2])
            with c1:
                st.markdown(
                    pills_row([
                        ("Official Broadcast" if is_official else "Newspaper / Think-Tank", "emerald" if is_official else "indigo"),
                        ("Playable In-App" if playable else "Direct Web", "dark" if playable else "slate"),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                    f'<div class="ou-card-desc">{html.escape(str(item.get("usage", "")), quote=True)}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if ext:
                    st.link_button("Open Source ↗", ext, type="primary", width="stretch")
            if playable:
                render_lazy_youtube_player(
                    ext,
                    title=str(item.get("title", "")),
                    provider="Official Broadcast",
                    key=f"ca_news_vid_{idx}",
                    label="▶ Watch Official Broadcast Playlist In-App",
                    height=380,
                )


def _render_curated_notes_tab(notes_items: list[dict[str, Any]]) -> None:
    section_kicker(f"Part 6 · Free Curated Notes, Monthly Magazines & Toppers' Copies ({len(notes_items)} Platforms)")
    q = st.text_input(
        "Search Curated Platforms",
        placeholder="e.g., Vision IAS, InsightsIAS, ForumIAS, Drishti, PMF IAS, Toppers...",
        key="ca_notes_q",
    )
    q_low = (q or "").strip().lower()
    matched = [
        n
        for n in notes_items
        if not q_low
        or q_low in str(n.get("title", "")).lower()
        or q_low in str(n.get("description", "")).lower()
    ]

    if not matched:
        empty_state("No curated platforms matched", "Try another search keyword.")
        return

    for i in range(0, len(matched), 2):
        cols = st.columns(2, gap="medium")
        for off, item in enumerate(matched[i : i + 2]):
            with cols[off]:
                with st.container(border=True):
                    st.markdown(pills_row([("Part 6 · Free Open Notes", "amber")]), unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(item.get("description", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(item.get("url"))
                    if ext:
                        st.link_button("Open Free Notes ↗", ext, type="primary", width="stretch")


def render_current_affairs() -> None:
    client = get_client()
    categories = client.get_current_affairs()
    master_guide = client.get_master_guide()

    reports = master_guide.get("govt_reports") or []
    news_items = master_guide.get("news_and_thinktanks") or []
    curated_notes = master_guide.get("curated_notes") or []

    page_header(
        eyebrow="Primary Data & Current Affairs",
        title="Current Affairs, Govt Reports & Think-Tanks",
        subtitle=(
            f"Replace coaching noise with {len(reports)} authoritative government reports & PRS portals, "
            f"{len(news_items)} official broadcasts & think-tanks, and {len(curated_notes)} free monthly magazines & toppers' notes."
        ),
        badge_text=f"{len(reports) + len(news_items) + len(curated_notes)} Verified Portals",
        badge_variant="emerald",
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        f"📡 GS Radar ({len(categories)} Tracks) & Broadcasts",
        f"🏛️ Govt Reports & PRS ({len(reports)})",
        f"🗞️ News & Think-Tanks ({len(news_items)})",
        f"📑 Free Curated Notes ({len(curated_notes)})",
    ])

    with tab1:
        _render_gs_radar_tab(categories, news_items)
    with tab2:
        _render_govt_reports_tab(reports)
    with tab3:
        _render_news_thinktanks_tab(news_items)
    with tab4:
        _render_curated_notes_tab(curated_notes)
