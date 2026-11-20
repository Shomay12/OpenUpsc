"""Free Resource Library (334 Verified Resources), In-App Video Theater & YouTube Channel Directory."""

from __future__ import annotations

import html
import math
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

FORMAT_PILLS: list[str] = [
    "All",
    "Video Playlists",
    "Official PDFs",
    "Question Papers",
    "Notes & Portals",
    "Saved ★",
]

PROGRESS_STEPS: list[int] = [0, 25, 50, 75, 100]
ITEMS_PER_PAGE = 18

TYPE_VARIANT_MAP: dict[str, str] = {
    "YouTube": "indigo",
    "PDF": "emerald",
    "PYQ": "violet",
    "Notes": "amber",
    "Website": "slate",
}


def _apply_handoff_presets() -> None:
    """Apply incoming cross-view filter presets before widgets are rendered."""
    preset_subj = st.session_state.pop("lib_preset_subject", None)
    if preset_subj:
        st.session_state["lib_subject"] = preset_subj
        st.session_state["lib_format_pill"] = "All"
        st.session_state["lib_page"] = 1

    preset_search = st.session_state.pop("lib_preset_search", None)
    if preset_search is not None:
        st.session_state["lib_search"] = str(preset_search)
        st.session_state["lib_page"] = 1

    preset_part = st.session_state.pop("lib_preset_part", None)
    if preset_part is not None:
        st.session_state["lib_part"] = preset_part
        st.session_state["lib_page"] = 1


def _matches_format_pill(res: dict[str, Any], fmt_pill: str, bookmarked_ids: set[str]) -> bool:
    if fmt_pill == "All":
        return True
    rtype = str(res.get("type") or "").lower()
    if fmt_pill == "Video Playlists":
        return rtype == "youtube" or bool(res.get("youtubePlaylistId"))
    if fmt_pill == "Official PDFs":
        return rtype == "pdf"
    if fmt_pill == "Question Papers":
        return rtype == "pyq" or "question paper" in str(res.get("subject") or "").lower()
    if fmt_pill == "Notes & Portals":
        return rtype in ("notes", "website")
    if fmt_pill == "Saved ★":
        return res.get("id") in bookmarked_ids
    return True


def _render_video_theater(
    resource: dict[str, Any],
    *,
    bookmarked_ids: set[str],
    progress_map: dict[str, int],
    notes_map: dict[str, str],
) -> None:
    client = get_client()
    rid = str(resource.get("id") or "custom-video")
    title = str(resource.get("title") or "Verified Video Course")
    provider = str(resource.get("provider") or "Verified Educator")
    subject = str(resource.get("subject") or "UPSC")
    level = str(resource.get("level") or "Foundation")
    lang = str(resource.get("language") or "Hinglish")
    url = str(resource.get("url") or "")
    senior_tip = str(resource.get("seniorTip") or resource.get("senior_tip") or "")
    is_catalog_item = not rid.startswith("direct-")

    with st.container(border=True):
        top_l, top_r = st.columns([5, 1])
        with top_l:
            st.markdown(
                pills_row([
                    ("▶ Distraction-Free Video Theater", "dark"),
                    (subject, "indigo"),
                    (level, "slate"),
                    (lang, "emerald"),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown(f"### {title}")
        with top_r:
            if st.button("✕ Close Theater", key="lib_close_theater_btn", width="stretch"):
                st.session_state.pop("lib_theater_resource_id", None)
                st.session_state.pop("lib_theater_custom", None)
                st.rerun()

        p_col, dock_col = st.columns([1.65, 1.0], gap="medium")
        with p_col:
            render_youtube_player(url, title=title, provider=provider, height=430)

        with dock_col:
            st.markdown("**Study Control Dock**")
            if is_catalog_item:
                is_bm = rid in bookmarked_ids
                cur_prog = int(progress_map.get(rid, 0))
                b_col, prog_col = st.columns(2)
                with b_col:
                    bm_lbl = "★ Bookmarked" if is_bm else "☆ Bookmark"
                    if st.button(
                        bm_lbl,
                        key=f"lib_theater_bm_{rid}",
                        type="primary" if is_bm else "secondary",
                        width="stretch",
                    ):
                        ok, msg, _ = client.toggle_bookmark(rid)
                        st.toast(msg) if ok else st.error(msg)
                        st.rerun()
                with prog_col:
                    closest = min(PROGRESS_STEPS, key=lambda x: abs(x - cur_prog))
                    new_prog = st.selectbox(
                        "Progress",
                        options=PROGRESS_STEPS,
                        index=PROGRESS_STEPS.index(closest),
                        format_func=lambda x: f"{x}% Done",
                        key=f"lib_theater_prog_{rid}",
                        label_visibility="collapsed",
                    )
                    if new_prog != cur_prog:
                        ok, msg, _ = client.update_progress(rid, int(new_prog))
                        if ok:
                            st.toast(msg)
                            st.rerun()

            if senior_tip:
                senior_tip_box(senior_tip)

            existing_note = notes_map.get(rid, "")
            with st.form(key=f"lib_theater_note_form_{rid}"):
                note_val = st.text_area(
                    "Quick Personal Note (Markdown)",
                    value=existing_note,
                    height=135,
                    placeholder="Jot down timestamps, key articles, definitions, or revision hooks...",
                    key=f"lib_theater_note_txt_{rid}",
                )
                if st.form_submit_button("💾 Save Note", width="stretch", type="primary"):
                    ok, msg, _ = client.save_note(
                        item_id=rid,
                        content=note_val,
                        item_title=title,
                        item_category=subject,
                    )
                    st.toast(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()

            if st.button(
                "⏱ Study with Focus Timer →",
                key=f"lib_theater_timer_{rid}",
                width="stretch",
            ):
                navigate_to(
                    "study_workspace",
                    study_prefill={"subject": subject, "topic": title[:120], "minutes": 50},
                )


def _render_catalog_tab(
    workspace: dict[str, Any],
    facets: dict[str, Any],
    all_resources: list[dict[str, Any]],
) -> None:
    client = get_client()
    bookmarked_ids = set(workspace.get("bookmarkedIds") or [])
    progress_map: dict[str, int] = workspace.get("progressMap") or {}
    notes_map: dict[str, str] = workspace.get("notes") or {}
    by_id = {r["id"]: r for r in all_resources}

    # In-App Video Theater (if active)
    theater_rid = st.session_state.get("lib_theater_resource_id")
    theater_custom = st.session_state.get("lib_theater_custom")
    if theater_rid and theater_rid in by_id:
        _render_video_theater(
            by_id[theater_rid],
            bookmarked_ids=bookmarked_ids,
            progress_map=progress_map,
            notes_map=notes_map,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    elif isinstance(theater_custom, dict) and theater_custom.get("url"):
        _render_video_theater(
            theater_custom,
            bookmarked_ids=bookmarked_ids,
            progress_map=progress_map,
            notes_map=notes_map,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Format Pills Bar
    if "lib_format_pill" not in st.session_state:
        st.session_state["lib_format_pill"] = "All"

    fmt_pill = st.segmented_control(
        "Format",
        options=FORMAT_PILLS,
        default=st.session_state["lib_format_pill"],
        key="lib_format_pill_ctrl",
        label_visibility="collapsed",
    )
    active_fmt = fmt_pill or "All"
    st.session_state["lib_format_pill"] = active_fmt

    # Multi-Facet Filter Bar
    subject_options = ["All"] + [s["name"] for s in (facets.get("subjects") or [])]
    level_options = ["All"] + [lv["name"] for lv in (facets.get("levels") or [])]
    lang_options = ["All"] + [lg["name"] for lg in (facets.get("languages") or [])]
    part_entries = facets.get("master_parts") or []
    part_options: list[Any] = ["All"] + [int(p["part_number"]) for p in part_entries]
    part_labels = {int(p["part_number"]): f"Part {p['part_number']}: {p['title'][:36]} ({p['count']})" for p in part_entries}

    # Ensure preset subject exists in options safely
    if st.session_state.get("lib_subject") not in subject_options:
        st.session_state["lib_subject"] = "All"
    if st.session_state.get("lib_level") not in level_options:
        st.session_state["lib_level"] = "All"
    if st.session_state.get("lib_lang") not in lang_options:
        st.session_state["lib_lang"] = "All"
    if st.session_state.get("lib_part") not in part_options:
        st.session_state["lib_part"] = "All"

    f1, f2, f3, f4, f5, f6 = st.columns([2.2, 1.35, 1.1, 1.15, 1.5, 0.85])
    with f1:
        search_q = st.text_input(
            "Search",
            placeholder="Search title, educator, tag, topic...",
            key="lib_search",
        )
    with f2:
        subj_counts = facets.get("subject_counts") or {}
        selected_subj = st.selectbox(
            "Subject",
            options=subject_options,
            format_func=lambda s: f"All Subjects ({len(all_resources)})" if s == "All" else f"{s} ({subj_counts.get(s, 0)})",
            key="lib_subject",
        )
    with f3:
        selected_level = st.selectbox("Level", options=level_options, key="lib_level")
    with f4:
        selected_lang = st.selectbox("Language", options=lang_options, key="lib_lang")
    with f5:
        selected_part = st.selectbox(
            "Master Guide Part",
            options=part_options,
            format_func=lambda p: "All Parts (1–10)" if p == "All" else part_labels.get(int(p), f"Part {p}"),
            key="lib_part",
        )
    with f6:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Reset", key="lib_reset_filters_btn", width="stretch"):
            for k in ("lib_search", "lib_subject", "lib_level", "lib_lang", "lib_part", "lib_format_pill_ctrl", "lib_page"):
                st.session_state.pop(k, None)
            st.session_state["lib_format_pill"] = "All"
            st.rerun()

    # Apply Filtering Fast In-Memory (100% consistent across API & Fallback)
    filtered: list[dict[str, Any]] = []
    q_low = (search_q or "").strip().lower()
    for r in all_resources:
        if not _matches_format_pill(r, active_fmt, bookmarked_ids):
            continue
        if selected_subj != "All" and str(r.get("subject") or "").lower() != selected_subj.lower():
            continue
        if selected_level != "All" and str(r.get("level") or "").lower() != selected_level.lower():
            continue
        if selected_lang != "All" and selected_lang.lower() not in str(r.get("language") or "").lower():
            continue
        if selected_part != "All":
            mp = r.get("masterPart") if r.get("masterPart") is not None else r.get("master_part")
            if mp != int(selected_part):
                continue
        if q_low:
            haystack = " ".join(
                [
                    str(r.get("title") or ""),
                    str(r.get("provider") or ""),
                    str(r.get("subject") or ""),
                    str(r.get("category") or ""),
                    str(r.get("description") or ""),
                    str(r.get("classLevel") or r.get("class_level") or ""),
                    " ".join(str(t) for t in (r.get("tags") or [])),
                ]
            ).lower()
            if q_low not in haystack:
                continue
        filtered.append(r)

    total_matched = len(filtered)
    total_pages = max(1, math.ceil(total_matched / ITEMS_PER_PAGE))
    cur_page = int(st.session_state.get("lib_page", 1))
    if cur_page > total_pages:
        cur_page = 1
        st.session_state["lib_page"] = 1

    # Result Count + Top Pagination Controls
    start_idx = (cur_page - 1) * ITEMS_PER_PAGE
    end_idx = min(total_matched, start_idx + ITEMS_PER_PAGE)

    bar_l, bar_r = st.columns([2.4, 1.6])
    with bar_l:
        if total_matched:
            st.caption(
                f"Showing **{start_idx + 1}–{end_idx}** of **{total_matched}** verified free resources "
                f"(Page {cur_page} of {total_pages})"
            )
        else:
            st.caption("0 matching resources")
    with bar_r:
        if total_pages > 1:
            p1, p2, p3 = st.columns([1, 1.3, 1])
            with p1:
                if st.button("← Prev", key="lib_prev_top", disabled=cur_page <= 1, width="stretch"):
                    st.session_state["lib_page"] = max(1, cur_page - 1)
                    st.rerun()
            with p2:
                chosen_p = st.selectbox(
                    "Page",
                    options=list(range(1, total_pages + 1)),
                    index=cur_page - 1,
                    format_func=lambda n: f"Page {n}/{total_pages}",
                    key="lib_page_jump_top",
                    label_visibility="collapsed",
                )
                if chosen_p != cur_page:
                    st.session_state["lib_page"] = int(chosen_p)
                    st.rerun()
            with p3:
                if st.button("Next →", key="lib_next_top", disabled=cur_page >= total_pages, width="stretch"):
                    st.session_state["lib_page"] = min(total_pages, cur_page + 1)
                    st.rerun()

    if not filtered:
        empty_state(
            "No resources match your current filters",
            "Click Reset Filters above or broaden your subject/format selection.",
        )
        return

    # 2-Column Paginated Card Grid
    page_items = filtered[start_idx:end_idx]
    for row_i in range(0, len(page_items), 2):
        cols = st.columns(2, gap="medium")
        for col_offset, res in enumerate(page_items[row_i : row_i + 2]):
            rid = str(res["id"])
            rtype = str(res.get("type") or "Resource")
            subject = str(res.get("subject") or "UPSC")
            level = str(res.get("level") or "Foundation")
            lang = str(res.get("language") or "English")
            provider = str(res.get("provider") or "Official Source")
            desc = str(res.get("description") or "")
            senior_tip = str(res.get("seniorTip") or res.get("senior_tip") or "")
            hrs = int(res.get("estimatedHours") or res.get("estimated_hours") or 0)
            mp = res.get("masterPart") if res.get("masterPart") is not None else res.get("master_part")
            url = safe_url(res.get("url"))
            playable, _, _ = is_youtube_playable(url)
            is_bm = rid in bookmarked_ids
            cur_prog = int(progress_map.get(rid, 0))
            tags = [str(t) for t in (res.get("tags") or [])][:5]

            pills_list = [
                (rtype, TYPE_VARIANT_MAP.get(rtype, "slate")),
                (subject, "slate"),
                (level, "slate"),
            ]
            if mp:
                pills_list.append((f"Part {mp}", "emerald"))
            if cur_prog >= 100:
                pills_list.append(("✓ Done", "emerald"))
            elif cur_prog > 0:
                pills_list.append((f"{cur_prog}%", "amber"))

            with cols[col_offset]:
                with st.container(border=True):
                    st.markdown(pills_row(pills_list), unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(res.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-meta">By {html.escape(provider, quote=True)} &middot; {html.escape(lang, quote=True)}'
                        f'{f" &middot; ~{hrs}h" if hrs else ""} &middot; ✓ Free</div>'
                        f'<div class="ou-card-desc">{html.escape(desc[:195] + ("…" if len(desc) > 195 else ""), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    if tags:
                        st.caption(" · ".join(f"#{t}" for t in tags))

                    a1, a2, a3 = st.columns([1.45, 0.85, 1.05])
                    with a1:
                        if playable:
                            if st.button(
                                "▶ Watch Here",
                                key=f"lib_watch_{rid}",
                                type="primary",
                                width="stretch",
                            ):
                                st.session_state["lib_theater_resource_id"] = rid
                                st.session_state.pop("lib_theater_custom", None)
                                st.rerun()
                        elif url:
                            st.link_button("Open Resource ↗", url, width="stretch", type="primary")
                    with a2:
                        if st.button(
                            "★ Saved" if is_bm else "☆ Save",
                            key=f"lib_bm_{rid}",
                            width="stretch",
                        ):
                            ok, msg, _ = client.toggle_bookmark(rid)
                            st.toast(msg) if ok else st.error(msg)
                            st.rerun()
                    with a3:
                        closest = min(PROGRESS_STEPS, key=lambda x: abs(x - cur_prog))
                        new_p = st.selectbox(
                            "Progress",
                            options=PROGRESS_STEPS,
                            index=PROGRESS_STEPS.index(closest),
                            format_func=lambda x: f"{x}%",
                            key=f"lib_prog_{rid}",
                            label_visibility="collapsed",
                        )
                        if new_p != cur_prog:
                            ok, msg, _ = client.update_progress(rid, int(new_p))
                            if ok:
                                st.toast(msg)
                                st.rerun()

                    with st.expander("Senior Tip, External Link & Personal Note"):
                        if senior_tip:
                            senior_tip_box(senior_tip)
                        if url:
                            st.link_button("Open Direct Source ↗", url)
                        note_default = notes_map.get(rid, "")
                        with st.form(key=f"lib_card_note_form_{rid}"):
                            n_val = st.text_area(
                                "Personal Revision Note",
                                value=note_default,
                                height=90,
                                key=f"lib_card_note_txt_{rid}",
                            )
                            if st.form_submit_button("Save Note", width="stretch"):
                                ok, msg, _ = client.save_note(
                                    item_id=rid,
                                    content=n_val,
                                    item_title=str(res.get("title", "")),
                                    item_category=subject,
                                )
                                st.toast(msg) if ok else st.error(msg)
                                if ok:
                                    st.rerun()

    # Bottom Pagination Footer
    if total_pages > 1:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        bp1, bp2, bp3 = st.columns([1, 2, 1])
        with bp1:
            if st.button("← Previous Page", key="lib_prev_bot", disabled=cur_page <= 1, width="stretch"):
                st.session_state["lib_page"] = max(1, cur_page - 1)
                st.rerun()
        with bp2:
            st.markdown(
                f'<div style="text-align:center;padding-top:8px;font-size:13px;color:#475569;font-weight:600;">'
                f"Page {cur_page} of {total_pages} ({total_matched} resources)</div>",
                unsafe_allow_html=True,
            )
        with bp3:
            if st.button("Next Page →", key="lib_next_bot", disabled=cur_page >= total_pages, width="stretch"):
                st.session_state["lib_page"] = min(total_pages, cur_page + 1)
                st.rerun()


def _render_channels_tab(master_guide: dict[str, Any]) -> None:
    vid_lib = master_guide.get("video_library") or {}
    official_ch = vid_lib.get("official_channels") or []
    subject_ch = vid_lib.get("subject_channels") or []
    direct_pl = vid_lib.get("direct_playlists") or []

    c1, c2 = st.columns([2.2, 1.5])
    with c1:
        ch_q = st.text_input(
            "Search Verified Channels & Playlists",
            placeholder="Filter by channel name, educator, handle, or UPSC subject...",
            key="lib_ch_search",
        )
    with c2:
        ch_scope = st.selectbox(
            "Channel Directory Group",
            options=[
                f"All Verified Channels ({len(official_ch) + len(subject_ch)})",
                f"Official Govt & NCERT Channels ({len(official_ch)})",
                f"Verified UPSC Subject Channels ({len(subject_ch)})",
            ],
            key="lib_ch_scope",
        )

    q_low = (ch_q or "").strip().lower()
    rows: list[dict[str, Any]] = []
    if ch_scope.startswith("All") or ch_scope.startswith("Official"):
        for ch in official_ch:
            rows.append({**ch, "_group": "Official Govt / NCERT", "_desc": ch.get("best_for", "")})
    if ch_scope.startswith("All") or ch_scope.startswith("Verified UPSC"):
        for ch in subject_ch:
            rows.append({**ch, "_group": "UPSC Subject Channel", "_desc": ch.get("specialty", "")})

    if q_low:
        rows = [
            r
            for r in rows
            if q_low in str(r.get("title", "")).lower()
            or q_low in str(r.get("_desc", "")).lower()
            or q_low in str(r.get("handle", "")).lower()
        ]

    section_kicker(f"Verified Free YouTube Channels ({len(rows)})")
    if not rows:
        empty_state("No matching YouTube channels", "Try clearing your search filter.")
    else:
        for i in range(0, len(rows), 2):
            cols = st.columns(2, gap="medium")
            for off, ch in enumerate(rows[i : i + 2]):
                with cols[off]:
                    with st.container(border=True):
                        badge_var = "emerald" if "Official" in ch["_group"] else "indigo"
                        st.markdown(
                            pills_row([(ch["_group"], badge_var), (str(ch.get("handle") or ""), "slate")]),
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="ou-card-title">{html.escape(str(ch.get("title", "")), quote=True)}</div>'
                            f'<div class="ou-card-desc">{html.escape(str(ch.get("_desc", "")), quote=True)}</div>',
                            unsafe_allow_html=True,
                        )
                        b1, b2 = st.columns(2)
                        with b1:
                            ext = safe_url(ch.get("url"))
                            if ext:
                                st.link_button("Open Channel ↗", ext, width="stretch", type="primary")
                        with b2:
                            if st.button(
                                "Find Playlists →",
                                key=f"lib_ch_find_{i}_{off}_{ch.get('title', '')[:18]}",
                                width="stretch",
                            ):
                                st.session_state["lib_preset_search"] = str(ch.get("title", "")).split("(")[0].strip()
                                st.rerun()

    st.divider()
    section_kicker(f"Direct Master Curated Playlists ({len(direct_pl)} Playable Series)")
    filtered_pl = [
        p
        for p in direct_pl
        if not q_low
        or q_low in str(p.get("title", "")).lower()
        or q_low in str(p.get("theme", "")).lower()
        or q_low in str(p.get("educator", "")).lower()
    ]
    for idx, pl in enumerate(filtered_pl):
        with st.container(border=True):
            c_left, c_right = st.columns([3.5, 1.1])
            p_url = safe_url(pl.get("url"))
            with c_left:
                st.markdown(
                    pills_row([
                        (str(pl.get("theme") or "Playlist"), "indigo"),
                        (str(pl.get("educator") or "Verified Educator"), "slate"),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ou-card-title">{html.escape(str(pl.get("title", "")), quote=True)}</div>',
                    unsafe_allow_html=True,
                )
            with c_right:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if p_url:
                    st.link_button("YouTube ↗", p_url, width="stretch")
            if p_url:
                render_lazy_youtube_player(
                    p_url,
                    title=str(pl.get("title", "")),
                    provider=str(pl.get("educator", "")),
                    key=f"lib_direct_pl_{idx}",
                    label="▶ Watch Full Playlist In-App",
                    height=390,
                )


def render_library() -> None:
    _apply_handoff_presets()
    client = get_client()
    workspace = client.get_workspace()
    facets = client.get_resource_facets()
    all_resources = client.get_resources()
    master_guide = client.get_master_guide()

    vid_lib = master_guide.get("video_library") or {}
    ch_total = len(vid_lib.get("official_channels") or []) + len(vid_lib.get("subject_channels") or [])

    page_header(
        eyebrow="Verified Open-Access Catalog",
        title="Free Resource Library & Video Theater",
        subtitle=(
            f"Browse all {len(all_resources)} live-verified free UPSC playlists, official NCERT PDFs, government reports, "
            "and question papers — watch playlists distraction-free right inside OpenUPSC."
        ),
        badge_text=f"{len(all_resources)} Verified · {facets.get('playlist_count', 94)} In-App Playlists",
        badge_variant="emerald",
    )

    tab1, tab2 = st.tabs([
        f"📚 Resource Catalog ({len(all_resources)})",
        f"📺 Verified YouTube Channels ({ch_total}) & Direct Playlists",
    ])

    with tab1:
        _render_catalog_tab(workspace, facets, all_resources)
    with tab2:
        _render_channels_tab(master_guide)
