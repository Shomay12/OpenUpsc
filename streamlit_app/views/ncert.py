"""NCERT Class 6–12 Hub: Detailed Chapter Explorer (36 Books / 315 Chapters), Master 86-Book Directory & Bridge Textbooks."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    EMERALD,
    INDIGO,
    empty_state,
    is_youtube_playable,
    navigate_to,
    page_header,
    pills_row,
    progress_bar_html,
    render_lazy_youtube_player,
    render_youtube_player,
    safe_url,
    section_kicker,
    senior_tip_box,
)

PROGRESS_STEPS = [0, 25, 50, 75, 100]
PRIORITY_VARIANTS = {
    "Must Read": "rose",
    "High": "rose",
    "Important": "amber",
    "Selective": "slate",
}


def _render_chapter_explorer(
    books: list[dict[str, Any]],
    workspace: dict[str, Any],
) -> None:
    client = get_client()
    progress_map: dict[str, int] = workspace.get("progressMap") or {}
    notes_map: dict[str, str] = workspace.get("notes") or {}

    if not books:
        empty_state("NCERT catalog unavailable", "Verify backend/data/ncert.json is present.")
        return

    # Class Selector (6–12)
    classes = sorted({int(b.get("classNum", 6)) for b in books})
    preset_class = st.session_state.pop("ncert_selected_class", None)
    if preset_class in classes:
        st.session_state["ncert_class_pick"] = preset_class
    if st.session_state.get("ncert_class_pick") not in classes:
        st.session_state["ncert_class_pick"] = classes[0]

    sel_class = st.segmented_control(
        "Select NCERT Class",
        options=classes,
        default=st.session_state["ncert_class_pick"],
        format_func=lambda c: f"Class {c}",
        key="ncert_class_ctrl",
    )
    active_class = int(sel_class or st.session_state["ncert_class_pick"])
    st.session_state["ncert_class_pick"] = active_class

    class_books = [b for b in books if int(b.get("classNum", 0)) == active_class]
    if not class_books:
        empty_state(f"No core NCERT books for Class {active_class}", "Select another class above.")
        return

    # Class Progress Summary Bar
    avg_class_prog = int(round(sum(int(progress_map.get(b["id"], 0)) for b in class_books) / max(len(class_books), 1)))
    st.markdown(
        progress_bar_html(
            avg_class_prog,
            label=f"Class {active_class} Overall Mastery ({len(class_books)} Core Books)",
            color=EMERALD if avg_class_prog >= 75 else INDIGO,
        ),
        unsafe_allow_html=True,
    )

    # Book Picker
    book_ids = [b["id"] for b in class_books]
    book_by_id = {b["id"]: b for b in class_books}
    book_key = f"ncert_book_sel_c{active_class}"

    chosen_bid = st.selectbox(
        "Select Textbook",
        options=book_ids,
        format_func=lambda bid: (
            f"{book_by_id[bid].get('subjectName', '')} — {book_by_id[bid].get('bookTitle', '')} "
            f"({int(progress_map.get(bid, 0))}% done · {len(book_by_id[bid].get('chapters') or [])} ch.)"
        ),
        key=book_key,
    )
    book = book_by_id[chosen_bid]
    bid = str(book["id"])
    cur_prog = int(progress_map.get(bid, 0))
    pdf_url = safe_url(book.get("officialPdfUrl"))
    lec_url = safe_url(book.get("recommendedLectureUrl"))
    playable, _, _ = is_youtube_playable(lec_url)

    # Selected Book Command Card
    with st.container(border=True):
        h_l, h_r = st.columns([3.2, 1.2])
        with h_l:
            st.markdown(
                pills_row([
                    (f"Class {active_class}", "dark"),
                    (str(book.get("subjectName") or ""), "indigo"),
                    (f"Priority: {book.get('readingPriority', 'High')}", PRIORITY_VARIANTS.get(str(book.get("readingPriority")), "amber")),
                    (f"~{int(book.get('estimatedHours') or 0)} hrs", "slate"),
                    (f"Coverage: {book.get('coverageState', 'FULL')}", "emerald"),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown(f"### {book.get('bookTitle', '')}")
            if book.get("whyItMatters"):
                st.markdown(f"<div class='ou-card-desc'>{html.escape(str(book['whyItMatters']), quote=True)}</div>", unsafe_allow_html=True)
        with h_r:
            st.caption("Your Book Progress")
            closest = min(PROGRESS_STEPS, key=lambda x: abs(x - cur_prog))
            new_prog = st.selectbox(
                "Book Completion",
                options=PROGRESS_STEPS,
                index=PROGRESS_STEPS.index(closest),
                format_func=lambda x: f"{x}% Completed",
                key=f"ncert_prog_{bid}",
                label_visibility="collapsed",
            )
            if new_prog != cur_prog:
                ok, msg, _ = client.update_progress(bid, int(new_prog))
                if ok:
                    st.toast(msg)
                    st.rerun()

        act1, act2, act3 = st.columns(3)
        with act1:
            if pdf_url:
                st.link_button("📄 Official NCERT PDF ↗", pdf_url, type="primary", width="stretch")
        with act2:
            toggle_key = f"ncert_show_vid_{bid}"
            if lec_url:
                btn_lbl = "✕ Hide Lecture Player" if st.session_state.get(toggle_key) else "▶ Watch Playlist In-App"
                if st.button(btn_lbl, key=f"ncert_vid_btn_{bid}", width="stretch"):
                    st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
                    st.rerun()
        with act3:
            if st.button("⏱ Study Book in Focus Timer →", key=f"ncert_timer_book_{bid}", width="stretch"):
                navigate_to(
                    "study_workspace",
                    study_prefill={
                        "subject": str(book.get("subjectName") or "NCERT"),
                        "topic": f"Class {active_class} NCERT — {book.get('bookTitle', '')}",
                        "minutes": 50,
                    },
                )

        if st.session_state.get(f"ncert_show_vid_{bid}") and lec_url:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            render_youtube_player(
                lec_url,
                title=str(book.get("recommendedLectureTitle") or book.get("bookTitle") or ""),
                provider=str(book.get("recommendedLectureChannel") or "Verified Educator"),
                height=400,
            )

        senior_tip_box(book.get("seniorHinglishAdvice"), label="Senior Hinglish Mentor Advice")

        foc_col, skip_col = st.columns(2, gap="medium")
        with foc_col:
            focus_val = book.get("whatToFocusOn")
            if focus_val:
                focus_text = "; ".join(focus_val) if isinstance(focus_val, list) else str(focus_val)
                st.markdown(
                    f"""
                    <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:10px;padding:11px 14px;">
                      <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#065F46;margin-bottom:4px;">✓ What to Focus On</div>
                      <div style="font-size:0.86rem;color:#064E3B;line-height:1.5;">{html.escape(focus_text, quote=True)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with skip_col:
            skip_val = book.get("whatToSkip")
            if skip_val:
                skip_text = "; ".join(skip_val) if isinstance(skip_val, list) else str(skip_val)
                st.markdown(
                    f"""
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:11px 14px;">
                      <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#475569;margin-bottom:4px;">↷ What to Skip / Skim</div>
                      <div style="font-size:0.86rem;color:#334155;line-height:1.5;">{html.escape(skip_text, quote=True)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if book.get("revisionStrategy") or book.get("nextStep"):
            st.caption(
                f"**Revision Strategy:** {book.get('revisionStrategy', 'Active recall + PYQ linking')}  |  "
                f"**Next Step:** {book.get('nextStep', 'Standard Reference Book')}"
            )

    # Chapter-Wise Explorer
    chapters = book.get("chapters") or []
    section_kicker(f"Chapter-Wise Priority Map ({len(chapters)} Chapters)")
    cf1, cf2 = st.columns([1.4, 2.2])
    with cf1:
        prio_filter = st.selectbox(
            "Priority Filter",
            options=["All", "Must Read", "Important", "Selective"],
            key=f"ncert_ch_prio_{bid}",
        )
    with cf2:
        ch_search = st.text_input(
            "Search Chapters",
            placeholder="Filter chapters by title, concept, or key theme...",
            key=f"ncert_ch_q_{bid}",
        )

    q_ch = (ch_search or "").strip().lower()
    vis_chapters = [
        ch
        for ch in chapters
        if (prio_filter == "All" or str(ch.get("priority", "")) == prio_filter)
        and (
            not q_ch
            or q_ch in str(ch.get("title", "")).lower()
            or q_ch in str(ch.get("upscRelevanceNote", "")).lower()
            or any(q_ch in str(t).lower() for t in (ch.get("keyThemes") or []))
        )
    ]

    if not vis_chapters:
        empty_state("No matching chapters", "Adjust the priority filter or search keyword.")
    else:
        for ch in vis_chapters:
            cnum = ch.get("number", "")
            ctitle = str(ch.get("title") or "")
            cprio = str(ch.get("priority") or "Important")
            crel = str(ch.get("upscRelevanceNote") or "")
            themes = [str(t) for t in (ch.get("keyThemes") or [])]

            with st.container(border=True):
                cl, cr = st.columns([4.1, 1.1])
                with cl:
                    st.markdown(
                        pills_row([
                            (f"Ch. {cnum}", "dark"),
                            (cprio, PRIORITY_VARIANTS.get(cprio, "slate")),
                            (f"Relevance: {ch.get('upscRelevance', 'High')}", "indigo"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(ctitle, quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(crel, quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    if themes:
                        st.caption("Key Themes: " + " · ".join(themes))
                with cr:
                    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                    if st.button(
                        "⏱ Study →",
                        key=f"ncert_ch_timer_{bid}_{cnum}",
                        width="stretch",
                    ):
                        navigate_to(
                            "study_workspace",
                            study_prefill={
                                "subject": str(book.get("subjectName") or "NCERT"),
                                "topic": f"Class {active_class} {book.get('bookTitle', '')} — Ch.{cnum}: {ctitle}",
                                "minutes": 45,
                            },
                        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Personal Book Notes & Community Suggestion Form
    n_col, sug_col = st.columns(2, gap="medium")
    with n_col:
        section_kicker("Personal Book Notes (Markdown)")
        with st.container(border=True):
            with st.form(key=f"ncert_note_form_{bid}"):
                note_body = st.text_area(
                    f"Notes for {book.get('bookTitle', '')}",
                    value=notes_map.get(bid, ""),
                    height=150,
                    placeholder="Capture timelines, definitions, articles, and chapter takeaways...",
                    key=f"ncert_note_txt_{bid}",
                )
                if st.form_submit_button("💾 Save Personal Note", type="primary", width="stretch"):
                    ok, msg, _ = client.save_note(
                        item_id=bid,
                        content=note_body,
                        item_title=str(book.get("bookTitle") or ""),
                        item_category=str(book.get("subjectName") or "NCERT"),
                    )
                    st.toast(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

    with sug_col:
        section_kicker("Community: Suggest a Better Free Video")
        with st.container(border=True):
            with st.form(key=f"ncert_sug_form_{bid}"):
                s_ch = st.text_input(
                    "Chapter / Book Title",
                    value=f"Class {active_class} {book.get('bookTitle', '')}",
                    key=f"ncert_sug_ch_{bid}",
                )
                s_channel = st.text_input(
                    "Educator / Channel Name",
                    placeholder="e.g., Amit Sengupta / NCERT Official / Bookstawa",
                    key=f"ncert_sug_chan_{bid}",
                )
                s_url = st.text_input(
                    "Free YouTube Playlist or Official Link (https://...)",
                    placeholder="https://www.youtube.com/playlist?list=...",
                    key=f"ncert_sug_url_{bid}",
                )
                if st.form_submit_button("Submit Suggestion", width="stretch"):
                    ok, msg = client.create_suggestion(
                        {
                            "subject": str(book.get("subjectName") or "NCERT"),
                            "chapter_title": s_ch,
                            "chapter_num": active_class,
                            "channel": s_channel,
                            "url": s_url,
                        }
                    )
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


def _render_master_ncert_directory(master_guide: dict[str, Any]) -> None:
    portals = master_guide.get("ncert_portals") or []
    directory = master_guide.get("ncert_directory") or []

    # Official Textbook Portals Strip
    section_kicker(f"Official Government Textbook Portals ({len(portals)})")
    if portals:
        p_cols = st.columns(min(len(portals), 5))
        for idx, p in enumerate(portals[:5]):
            with p_cols[idx]:
                with st.container(border=True):
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(p.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-meta">{html.escape(str(p.get("offers", ""))[:105], quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(p.get("url"))
                    if ext:
                        st.link_button("Open Portal ↗", ext, width="stretch")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_kicker(f"Complete Master NCERT Directory ({len(directory)} Textbooks — Classic + NEP 2020 + Hindi)")

    f1, f2, f3, f4 = st.columns([1.0, 1.1, 1.1, 2.0])
    with f1:
        dir_class = st.selectbox(
            "Class",
            options=["All", 6, 7, 8, 9, 10, 11, 12],
            format_func=lambda x: "All Classes (6–12)" if x == "All" else f"Class {x}",
            key="ncert_dir_class",
        )
    with f2:
        dir_med = st.selectbox("Medium", options=["All", "English", "Hindi"], key="ncert_dir_medium")
    with f3:
        dir_ed = st.selectbox("Edition", options=["All", "Classic", "NEP New"], key="ncert_dir_edition")
    with f4:
        dir_q = st.text_input(
            "Search Textbooks",
            placeholder="Search by book title, subject, or GS mapping...",
            key="ncert_dir_q",
        )

    q_low = (dir_q or "").strip().lower()
    matched = [
        b
        for b in directory
        if (dir_class == "All" or int(b.get("class_num", 0)) == int(dir_class))
        and (dir_med == "All" or str(b.get("medium", "")) == dir_med)
        and (dir_ed == "All" or str(b.get("edition", "")) == dir_ed)
        and (
            not q_low
            or q_low in str(b.get("book_title", "")).lower()
            or q_low in str(b.get("subject", "")).lower()
            or q_low in str(b.get("priority_gs_map", "")).lower()
        )
    ]

    st.caption(f"Showing **{len(matched)}** of {len(directory)} official NCERT textbooks.")
    if not matched:
        empty_state("No NCERT textbooks match these filters", "Try switching Edition or Medium to All.")
        return

    for idx, b in enumerate(matched):
        vids = b.get("video_companions") or []
        with st.container(border=True):
            l_col, r_col = st.columns([3.7, 1.3])
            with l_col:
                ed_var = "emerald" if b.get("edition") == "NEP New" else "slate"
                med_var = "amber" if b.get("medium") == "Hindi" else "indigo"
                st.markdown(
                    pills_row([
                        (f"Class {b.get('class_num', '')}", "dark"),
                        (str(b.get("subject") or ""), "slate"),
                        (str(b.get("edition") or "Classic"), ed_var),
                        (str(b.get("medium") or "English"), med_var),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ou-card-title">{html.escape(str(b.get("book_title", "")), quote=True)}</div>'
                    f'<div class="ou-card-meta">{html.escape(str(b.get("priority_gs_map", "")), quote=True)}</div>',
                    unsafe_allow_html=True,
                )
            with r_col:
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                ext = safe_url(b.get("url"))
                if ext:
                    st.link_button("Official PDF ↗", ext, type="primary", width="stretch")

            if vids:
                with st.expander(f"▶ Verified Video Companions ({len(vids)})"):
                    for v_idx, vc in enumerate(vids):
                        v_url = safe_url(vc.get("url"))
                        if v_url:
                            st.caption(f"**{vc.get('title', b.get('subject', ''))}** — {vc.get('provider', 'Verified Educator')}")
                            render_lazy_youtube_player(
                                v_url,
                                title=f"Class {b.get('class_num')} {vc.get('title', b.get('subject', ''))}",
                                provider=str(vc.get("provider") or "Verified Educator"),
                                key=f"ncert_dir_vid_{idx}_{v_idx}",
                                label="▶ Play Video Companion In-App",
                                height=360,
                            )


def _render_bridge_textbooks(master_guide: dict[str, Any]) -> None:
    bridges = master_guide.get("bridge_textbooks") or []
    section_kicker(f"Post-NCERT Open-Access Bridge Textbooks & Universities ({len(bridges)} Portals)")
    st.caption(
        "Use Tamil Nadu Class 11–12 History, NIOS, IGNOU eGyanKosh, e-PG Pathshala, SWAYAM, and NPTEL "
        "to bridge from NCERTs to Mains & Optional depth — 100% free and government-backed."
    )
    if not bridges:
        empty_state("No bridge textbooks loaded", "Verify master_guide.json bridge_textbooks.")
        return

    for i in range(0, len(bridges), 2):
        cols = st.columns(2, gap="medium")
        for off, item in enumerate(bridges[i : i + 2]):
            with cols[off]:
                with st.container(border=True):
                    st.markdown(
                        pills_row([("Part 2.2 · Open-Access Bridge", "emerald")]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(item.get("best_used_for", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(item.get("url"))
                    if ext:
                        st.link_button("Open Free Repository ↗", ext, type="primary", width="stretch")


def render_ncert() -> None:
    client = get_client()
    workspace = client.get_workspace()
    books = client.get_ncert()
    master_guide = client.get_master_guide()

    total_chapters = sum(len(b.get("chapters") or []) for b in books)
    dir_count = len(master_guide.get("ncert_directory") or [])
    bridge_count = len(master_guide.get("bridge_textbooks") or [])

    page_header(
        eyebrow="Stage 1 · Foundation Backbone",
        title="NCERT Class 6–12 & Bridge Textbooks",
        subtitle=(
            f"Master all {len(books)} core UPSC NCERT textbooks ({total_chapters} prioritized chapters), "
            f"browse all {dir_count} Classic, NEP 2020 & Hindi edition official PDFs, and access {bridge_count} post-NCERT open repositories."
        ),
        badge_text=f"{len(books)} Core Books · {total_chapters} Chapters",
        badge_variant="emerald",
    )

    tab1, tab2, tab3 = st.tabs([
        f"📖 Chapter-Wise Explorer ({len(books)} Books / {total_chapters} Ch.)",
        f"📚 Complete Master Directory ({dir_count} Classic + NEP + Hindi)",
        f"🌉 Bridge Textbooks ({bridge_count} Portals)",
    ])

    with tab1:
        _render_chapter_explorer(books, workspace)
    with tab2:
        _render_master_ncert_directory(master_guide)
    with tab3:
        _render_bridge_textbooks(master_guide)
