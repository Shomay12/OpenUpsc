"""Deep Focus Studio: Smooth Wall-Clock Focus Timer, Timetable Routine CRUD, Study Sessions Log & Markdown Notes Hub."""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    empty_state,
    fmt_mins,
    page_header,
    pills_row,
    render_focus_timer_widget,
    section_kicker,
)

IST = timezone(timedelta(hours=5, minutes=30))

UPSC_SUBJECTS = [
    "Indian Polity",
    "History",
    "Geography",
    "Economy",
    "Environment",
    "Science & Tech",
    "Current Affairs",
    "Ethics",
    "CSAT",
    "NCERT",
    "Art & Culture",
    "Governance & IR",
    "Mains & Essay",
    "Optionals",
    "Interview",
]

DAYS_OF_WEEK = ["Daily", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SESSION_TYPES = ["Focus", "Revision", "Answer Writing", "PYQ Practice", "Mock Test", "Break"]


def _consume_prefill() -> dict[str, Any]:
    prefill = st.session_state.pop("study_prefill", None)
    if isinstance(prefill, dict):
        subj = str(prefill.get("subject") or "Indian Polity")
        topic = str(prefill.get("topic") or "")
        mins = max(5, min(180, int(prefill.get("minutes") or 50)))
        st.session_state["sw_active_subject"] = subj
        st.session_state["sw_active_topic"] = topic
        st.session_state["sw_active_minutes"] = mins

    return {
        "subject": st.session_state.get("sw_active_subject", "Indian Polity"),
        "topic": st.session_state.get("sw_active_topic", "Active Reading & Concept Consolidation"),
        "minutes": int(st.session_state.get("sw_active_minutes", 50)),
    }


def _slugify_note_id(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "note").lower()).strip("-")[:42]
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")
    return f"note-{slug or 'custom'}-{stamp}"


def _compute_block_mins(start_str: str, end_str: str) -> int:
    try:
        sh, sm = (int(x) for x in start_str.split(":"))
        eh, em = (int(x) for x in end_str.split(":"))
        diff = (eh * 60 + em) - (sh * 60 + sm)
        return max(15, min(180, diff)) if diff > 0 else 50
    except Exception:
        return 50


def _render_timetable_tab(timetable: list[dict[str, Any]]) -> None:
    client = get_client()
    today_name = datetime.now(IST).strftime("%A")

    top_l, top_r = st.columns([2.0, 2.0])
    with top_l:
        view_scope = st.segmented_control(
            "Timetable View",
            options=["Today's Routine", "All Scheduled Blocks"],
            default="Today's Routine",
            key="sw_tt_scope",
            label_visibility="collapsed",
        )
    with top_r:
        done_cnt = sum(1 for ev in timetable if ev.get("completed"))
        st.caption(f"Today is **{today_name}** · **{done_cnt}/{len(timetable)}** blocks completed")

    visible = [
        ev
        for ev in timetable
        if view_scope != "Today's Routine" or ev.get("dayOfWeek") in ("Daily", today_name)
    ]

    if not visible:
        empty_state(
            "No timetable blocks in this view",
            "Add your daily UPSC routine blocks below (e.g., 06:30 Polity, 09:00 Current Affairs, 16:00 CSAT).",
        )
    else:
        for ev in visible:
            eid = str(ev["id"])
            is_done = bool(ev.get("completed"))
            day_lbl = str(ev.get("dayOfWeek") or "Daily")
            s_time = str(ev.get("startTime") or "06:30")
            e_time = str(ev.get("endTime") or "07:30")
            subj = str(ev.get("subject") or "UPSC")
            topic = str(ev.get("topic") or "")
            res_title = str(ev.get("resourceTitle") or "")

            with st.container(border=True):
                c_info, c_act1, c_act2, c_act3 = st.columns([3.0, 1.0, 1.05, 0.75])
                with c_info:
                    st.markdown(
                        pills_row([
                            (f"{s_time} – {e_time}", "dark"),
                            (day_lbl, "slate"),
                            (subj, "indigo"),
                            ("✓ Done" if is_done else "Scheduled", "emerald" if is_done else "amber"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(topic, quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    if res_title:
                        st.caption(f"Material: {res_title}")
                with c_act1:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button(
                        "↺ Undo" if is_done else "✓ Done",
                        key=f"sw_tt_toggle_{eid}",
                        type="secondary" if is_done else "primary",
                        width="stretch",
                    ):
                        ok, msg, _ = client.update_timetable_event(eid, {"completed": not is_done})
                        st.toast(msg) if ok else st.error(msg)
                        st.rerun()
                with c_act2:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("⏱ Load Timer", key=f"sw_tt_load_{eid}", width="stretch"):
                        st.session_state["study_prefill"] = {
                            "subject": subj,
                            "topic": topic,
                            "minutes": _compute_block_mins(s_time, e_time),
                        }
                        st.toast(f"Loaded '{subj}' into Focus Timer!")
                        st.rerun()
                with c_act3:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button("🗑", key=f"sw_tt_del_{eid}", help="Delete timetable block", width="stretch"):
                        ok, msg = client.delete_timetable_event(eid)
                        st.toast(msg) if ok else st.error(msg)
                        st.rerun()

                with st.expander("Edit Block Details"):
                    with st.form(key=f"sw_tt_edit_form_{eid}"):
                        ec1, ec2, ec3 = st.columns(3)
                        with ec1:
                            new_day = st.selectbox(
                                "Day",
                                options=DAYS_OF_WEEK,
                                index=DAYS_OF_WEEK.index(day_lbl) if day_lbl in DAYS_OF_WEEK else 0,
                                key=f"sw_tt_ed_day_{eid}",
                            )
                        with ec2:
                            new_start = st.text_input("Start (HH:MM)", value=s_time, key=f"sw_tt_ed_st_{eid}")
                        with ec3:
                            new_end = st.text_input("End (HH:MM)", value=e_time, key=f"sw_tt_ed_en_{eid}")
                        ec4, ec5 = st.columns(2)
                        with ec4:
                            new_subj = st.text_input("Subject", value=subj, key=f"sw_tt_ed_sub_{eid}")
                        with ec5:
                            new_topic = st.text_input("Topic", value=topic, key=f"sw_tt_ed_top_{eid}")
                        if st.form_submit_button("Save Block Changes", type="primary", width="stretch"):
                            ok, msg, _ = client.update_timetable_event(
                                eid,
                                {
                                    "day_of_week": new_day,
                                    "start_time": new_start.strip(),
                                    "end_time": new_end.strip(),
                                    "subject": new_subj.strip(),
                                    "topic": new_topic.strip(),
                                },
                            )
                            if ok:
                                st.toast(msg)
                                st.rerun()
                            else:
                                st.error(msg)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_kicker("Add New Timetable Block")
    with st.container(border=True):
        with st.form(key="sw_tt_add_form"):
            a1, a2, a3 = st.columns(3)
            with a1:
                add_day = st.selectbox("Day of Week", options=DAYS_OF_WEEK, key="sw_tt_add_day")
            with a2:
                add_start = st.text_input("Start Time (24h HH:MM)", value="07:00", key="sw_tt_add_start")
            with a3:
                add_end = st.text_input("End Time (24h HH:MM)", value="08:30", key="sw_tt_add_end")

            a4, a5, a6 = st.columns([1.2, 1.8, 1.4])
            with a4:
                add_subj = st.selectbox("Subject", options=UPSC_SUBJECTS, key="sw_tt_add_subj")
            with a5:
                add_topic = st.text_input("Topic / Target", placeholder="e.g., Laxmikanth Fundamental Rights + 15 PYQs", key="sw_tt_add_topic")
            with a6:
                add_res = st.text_input("Linked Material (Optional)", placeholder="e.g., Class 11 NCERT / Mrunal", key="sw_tt_add_res")

            if st.form_submit_button("+ Add Timetable Block", type="primary", width="stretch"):
                ok, msg, _ = client.create_timetable_event(
                    {
                        "day_of_week": add_day,
                        "start_time": add_start.strip(),
                        "end_time": add_end.strip(),
                        "subject": add_subj,
                        "topic": add_topic.strip(),
                        "resource_title": add_res.strip() or None,
                        "completed": False,
                    }
                )
                if ok:
                    st.toast(msg)
                    st.rerun()
                else:
                    st.error(msg)


def _render_sessions_tab(sessions: list[dict[str, Any]]) -> None:
    client = get_client()
    subjs = ["All"] + sorted({str(s.get("subject", "")) for s in sessions if s.get("subject")})

    f1, f2, f3 = st.columns([1.6, 1.4, 1.2])
    with f1:
        sel_subj = st.selectbox("Filter by Subject", options=subjs, key="sw_sess_subj_filter")
    filtered = [s for s in sessions if sel_subj == "All" or s.get("subject") == sel_subj]
    total_mins = sum(int(s.get("durationMinutes") or 0) for s in filtered if "break" not in str(s.get("sessionType") or "").lower())

    with f2:
        st.metric("Filtered Focus Time", fmt_mins(total_mins), f"{len(filtered)} entries")
    with f3:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if filtered:
            df_exp = pd.DataFrame(filtered)
            csv_bytes = df_exp.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Export Sessions CSV",
                data=csv_bytes,
                file_name="openupsc_study_sessions.csv",
                mime="text/csv",
                width="stretch",
            )

    if not filtered:
        empty_state("No study sessions logged yet", "Complete a Focus Timer session and log it above to build your streak!")
        return

    for s in filtered[:40]:
        sid = str(s["id"])
        subj = str(s.get("subject") or "UPSC")
        topic = str(s.get("topic") or "Focused Study")
        mins = int(s.get("durationMinutes") or 0)
        stype = str(s.get("sessionType") or "Focus")
        start_str = str(s.get("startTime") or "")[:16].replace("T", " ")
        s_notes = str(s.get("notes") or "")

        with st.container(border=True):
            c1, c2 = st.columns([4.2, 0.8])
            with c1:
                st.markdown(
                    pills_row([
                        (subj, "indigo"),
                        (stype, "emerald" if "break" not in stype.lower() else "slate"),
                        (fmt_mins(mins), "dark"),
                        (start_str, "slate"),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="ou-card-title">{html.escape(topic, quote=True)}</div>',
                    unsafe_allow_html=True,
                )
                if s_notes:
                    st.caption(s_notes)
            with c2:
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if st.button("🗑", key=f"sw_sess_del_{sid}", help="Delete session entry", width="stretch"):
                    ok, msg = client.delete_study_session(sid)
                    st.toast(msg) if ok else st.error(msg)
                    st.rerun()


def _render_notes_hub_tab(notes_list: list[dict[str, Any]]) -> None:
    client = get_client()

    top_l, top_r = st.columns([2.6, 1.4])
    with top_l:
        nq = st.text_input(
            "Search Personal Notes",
            placeholder="Filter by title, subject category, or keyword inside your notes...",
            key="sw_notes_search",
        )
    with top_r:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if notes_list:
            md_blocks = []
            for n in notes_list:
                md_blocks.append(
                    f"# {n.get('item_title') or n.get('item_id')}\n"
                    f"_Category: {n.get('item_category') or 'General'} | Updated: {str(n.get('updated_at') or '')[:16]}_\n\n"
                    f"{n.get('content') or ''}\n\n---\n"
                )
            st.download_button(
                "⬇ Export All Notes (.md)",
                data="\n".join(md_blocks).encode("utf-8"),
                file_name="openupsc_revision_notes.md",
                mime="text/markdown",
                width="stretch",
            )

    q_low = (nq or "").strip().lower()
    filtered = [
        n
        for n in notes_list
        if not q_low
        or q_low in str(n.get("item_title") or n.get("item_id") or "").lower()
        or q_low in str(n.get("item_category") or "").lower()
        or q_low in str(n.get("content") or "").lower()
    ]

    left, right = st.columns([1.05, 1.55], gap="medium")

    with left:
        section_kicker(f"Your Revision Notes ({len(filtered)})")
        if filtered:
            n_ids = [str(n["item_id"]) for n in filtered]
            n_map = {str(n["item_id"]): n for n in filtered}
            sel_nid = st.radio(
                "Select Note to Edit",
                options=n_ids,
                format_func=lambda nid: (
                    f"{n_map[nid].get('item_title') or nid} "
                    f"({n_map[nid].get('item_category') or 'General'})"
                ),
                key="sw_notes_picker",
                label_visibility="collapsed",
            )
        else:
            sel_nid = None
            empty_state("No notes match", "Create a new structured UPSC revision note below.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.expander("➕ Create New Markdown Note", expanded=not filtered):
            with st.form(key="sw_new_note_form"):
                ntitle = st.text_input("Note Title", placeholder="e.g., Basic Structure Doctrine Cases", key="sw_new_note_title")
                ncat = st.selectbox("Subject Category", options=UPSC_SUBJECTS, key="sw_new_note_cat")
                nbody = st.text_area(
                    "Initial Markdown Content",
                    height=130,
                    placeholder="## Key Points\n- Kesavananda Bharati (1973)\n- Minerva Mills (1980)",
                    key="sw_new_note_body",
                )
                if st.form_submit_button("Create Note", type="primary", width="stretch"):
                    if not ntitle.strip():
                        st.error("Please provide a note title.")
                    else:
                        new_id = _slugify_note_id(ntitle.strip())
                        ok, msg, _ = client.save_note(
                            item_id=new_id,
                            content=nbody,
                            item_title=ntitle.strip(),
                            item_category=ncat,
                        )
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    with right:
        section_kicker("Markdown Editor & Live Preview")
        if sel_nid:
            active_note = next((n for n in filtered if str(n["item_id"]) == sel_nid), None)
            if active_note:
                with st.container(border=True):
                    st.markdown(
                        pills_row([
                            (str(active_note.get("item_category") or "General"), "indigo"),
                            (f"Updated {str(active_note.get('updated_at') or '')[:16].replace('T', ' ')}", "slate"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"#### {active_note.get('item_title') or sel_nid}")
                    ed_tab, prev_tab = st.tabs(["✏️ Edit Markdown", "👁️ Rendered Preview"])
                    with ed_tab:
                        with st.form(key=f"sw_edit_note_form_{sel_nid}"):
                            ed_title = st.text_input(
                                "Title",
                                value=str(active_note.get("item_title") or sel_nid),
                                key=f"sw_edit_ntitle_{sel_nid}",
                            )
                            ed_cat = st.text_input(
                                "Category",
                                value=str(active_note.get("item_category") or "General"),
                                key=f"sw_edit_ncat_{sel_nid}",
                            )
                            ed_content = st.text_area(
                                "Markdown Content",
                                value=str(active_note.get("content") or ""),
                                height=260,
                                key=f"sw_edit_nbody_{sel_nid}",
                            )
                            if st.form_submit_button("💾 Save Changes", type="primary", width="stretch"):
                                ok, msg, _ = client.save_note(
                                    item_id=sel_nid,
                                    content=ed_content,
                                    item_title=ed_title.strip() or sel_nid,
                                    item_category=ed_cat.strip() or "General",
                                )
                                if ok:
                                    st.toast(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with prev_tab:
                        content_str = str(active_note.get("content") or "").strip()
                        if content_str:
                            st.markdown(content_str)
                        else:
                            st.caption("_This note is currently empty._")
        else:
            empty_state("Select or create a note", "Pick a revision note on the left to edit or preview Markdown.")


def render_study_workspace() -> None:
    client = get_client()
    prefill = _consume_prefill()
    workspace = client.get_workspace()
    analytics = workspace.get("analytics") or {}
    timetable = workspace.get("timetable") or []
    sessions = workspace.get("studySessions") or []
    notes_list = workspace.get("notesList") or []

    page_header(
        eyebrow="Deep Work Execution",
        title="Study Workspace · Focus Timer, Timetable & Notes",
        subtitle=(
            "Run wall-clock accurate distraction-free focus blocks, log completed sessions to build your IST streak, "
            "manage your daily UPSC routine, and maintain Markdown revision notes."
        ),
        badge_text=f"Today: {fmt_mins(analytics.get('today_minutes', 0))} · Streak: {analytics.get('study_streak_days', 0)}d",
        badge_variant="emerald",
    )

    # Top Focus Zone: Smooth HTML/JS Focus Timer + Log Completed Session Form
    t_col, log_col = st.columns([1.22, 1.0], gap="medium")

    with t_col:
        section_kicker("Distraction-Free Wall-Clock Focus Timer")
        render_focus_timer_widget(
            default_minutes=prefill["minutes"],
            subject=prefill["subject"],
            topic=prefill["topic"],
        )

    with log_col:
        section_kicker("Log Completed Focus Session")
        with st.container(border=True):
            subj_list = list(UPSC_SUBJECTS)
            if prefill["subject"] not in subj_list:
                subj_list.insert(0, prefill["subject"])

            with st.form(key="sw_log_session_form"):
                l_subj = st.selectbox(
                    "Subject",
                    options=subj_list,
                    index=subj_list.index(prefill["subject"]),
                    key="sw_log_subj",
                )
                l_topic = st.text_input(
                    "Topic Studied",
                    value=prefill["topic"],
                    placeholder="e.g., NCERT Class 11 Polity Ch. 2 Fundamental Rights",
                    key="sw_log_topic",
                )
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    l_mins = st.number_input(
                        "Duration (minutes)",
                        min_value=1,
                        max_value=600,
                        value=int(prefill["minutes"]),
                        step=5,
                        key="sw_log_mins",
                    )
                with c_d2:
                    l_type = st.selectbox("Session Type", options=SESSION_TYPES, key="sw_log_type")

                l_notes = st.text_input(
                    "Session Takeaway (Optional)",
                    placeholder="Quick summary or recall rating...",
                    key="sw_log_notes",
                )
                if st.form_submit_button("✓ Log Session & Update Streak", type="primary", width="stretch"):
                    ok, msg, _ = client.create_study_session(
                        {
                            "subject": l_subj,
                            "topic": l_topic.strip(),
                            "duration_minutes": int(l_mins),
                            "session_type": l_type,
                            "completed": True,
                            "notes": l_notes.strip() or None,
                        }
                    )
                    if ok:
                        st.session_state["sw_active_subject"] = l_subj
                        st.session_state["sw_active_topic"] = l_topic.strip()
                        st.session_state["sw_active_minutes"] = int(l_mins)
                        st.toast(f"{msg} ({l_mins}m {l_subj})")
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        f"📅 Daily Timetable ({len(timetable)} Blocks)",
        f"⏱ Study Sessions Log ({len(sessions)})",
        f"📝 Personal Markdown Notes ({len(notes_list)})",
    ])

    with tab1:
        _render_timetable_tab(timetable)
    with tab2:
        _render_sessions_tab(sessions)
    with tab3:
        _render_notes_hub_tab(notes_list)
