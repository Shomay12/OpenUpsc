"""Step-by-Step Subject Roadmaps (8 Pillars / 34 Steps), Standard Core Books (Part 3) & 5-Phase Study Sequence (Part 11)."""

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
    safe_url,
    section_kicker,
    senior_tip_box,
)

PROGRESS_STEPS = [0, 25, 50, 75, 100]


def _render_roadmaps_tab(roadmaps: list[dict[str, Any]], workspace: dict[str, Any]) -> None:
    client = get_client()
    progress_map: dict[str, int] = workspace.get("progressMap") or {}
    notes_map: dict[str, str] = workspace.get("notes") or {}

    if not roadmaps:
        empty_state("Roadmaps dataset not loaded", "Ensure backend/data/roadmaps.json exists.")
        return

    rm_ids = [r["subjectId"] for r in roadmaps]
    rm_by_id = {r["subjectId"]: r for r in roadmaps}

    # Respect cross-view navigation preset (e.g., Home weak subjects / Global Search)
    preset = st.session_state.pop("roadmap_selected_subject", None)
    if preset in rm_by_id:
        st.session_state["rm_subject_picker"] = preset
    if st.session_state.get("rm_subject_picker") not in rm_by_id:
        st.session_state["rm_subject_picker"] = rm_ids[0]

    def _rm_avg(rm: dict[str, Any]) -> int:
        steps = rm.get("steps") or []
        if not steps:
            return 0
        return int(round(sum(int(progress_map.get(s["id"], 0)) for s in steps) / len(steps)))

    sel_rm_id = st.selectbox(
        "Choose Subject Pillar",
        options=rm_ids,
        format_func=lambda rid: (
            f"{rm_by_id[rid].get('subjectName', rid)} — "
            f"{_rm_avg(rm_by_id[rid])}% complete ({len(rm_by_id[rid].get('steps') or [])} milestones)"
        ),
        key="rm_subject_picker",
    )
    rm = rm_by_id[sel_rm_id]
    steps = rm.get("steps") or []
    rm_avg = _rm_avg(rm)

    with st.container(border=True):
        st.markdown(
            pills_row([
                (f"{len(steps)} Structured Milestones", "indigo"),
                (f"{rm_avg}% Mastered", "emerald" if rm_avg >= 60 else "amber"),
            ]),
            unsafe_allow_html=True,
        )
        st.markdown(f"### {rm.get('subjectName', '')}")
        st.markdown(f"<div class='ou-card-desc'>{html.escape(str(rm.get('description', '')), quote=True)}</div>", unsafe_allow_html=True)
        st.markdown(
            progress_bar_html(rm_avg, label=f"{rm.get('subjectName', '')} Overall Completion", color=EMERALD if rm_avg >= 75 else INDIGO),
            unsafe_allow_html=True,
        )
        senior_tip_box(rm.get("overviewAdvice"), label="Senior Subject Strategy")

    if not steps:
        empty_state("No roadmap steps defined", "Add steps to this roadmap to track milestones.")
        return

    # Visual Step Selector
    section_kicker("Select Milestone Step")
    step_ids = [s["id"] for s in steps]
    step_by_id = {s["id"]: s for s in steps}
    step_pick = st.segmented_control(
        "Milestone",
        options=step_ids,
        default=step_ids[0],
        format_func=lambda sid: (
            f"{'✓ ' if int(progress_map.get(sid, 0)) >= 100 else ''}Step {step_by_id[sid].get('stepNumber', '')}: "
            f"{str(step_by_id[sid].get('title', ''))[:28]} ({int(progress_map.get(sid, 0))}%)"
        ),
        key=f"rm_step_ctrl_{sel_rm_id}",
        label_visibility="collapsed",
    )
    active_sid = step_pick or step_ids[0]
    step = step_by_id[active_sid]
    cur_prog = int(progress_map.get(active_sid, 0))

    with st.container(border=True):
        sh1, sh2 = st.columns([3.2, 1.3])
        with sh1:
            st.markdown(
                pills_row([
                    (f"Milestone {step.get('stepNumber', '')}", "dark"),
                    (str(step.get("level") or "Core"), "indigo"),
                    (f"⏱ {step.get('estimatedTime', '')}", "slate"),
                ]),
                unsafe_allow_html=True,
            )
            st.markdown(f"### {step.get('title', '')}")
            if step.get("tagline"):
                st.caption(step["tagline"])
        with sh2:
            st.caption("Milestone Progress")
            closest = min(PROGRESS_STEPS, key=lambda x: abs(x - cur_prog))
            new_p = st.selectbox(
                "Step Progress",
                options=PROGRESS_STEPS,
                index=PROGRESS_STEPS.index(closest),
                format_func=lambda x: f"{x}% Completed",
                key=f"rm_step_prog_{active_sid}",
                label_visibility="collapsed",
            )
            if new_p != cur_prog:
                ok, msg, _ = client.update_progress(active_sid, int(new_p))
                if ok:
                    st.toast(msg)
                    st.rerun()

        senior_tip_box(step.get("seniorGuidance"), label="Senior Mentor Step Guidance")

        c_left, c_right = st.columns([1.15, 1.0], gap="medium")
        with c_left:
            checklist = step.get("actionChecklist") or []
            if checklist:
                st.markdown("**Action Checklist**")
                for item in checklist:
                    st.markdown(f"- {item}")
        with c_right:
            pyq_focus = step.get("pyqFocusArea")
            if pyq_focus:
                st.markdown(
                    f"""
                    <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:12px 14px;">
                      <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#1E40AF;margin-bottom:4px;">🎯 PYQ Focus Area</div>
                      <div style="font-size:0.86rem;color:#1E3A8A;line-height:1.5;">{html.escape(str(pyq_focus), quote=True)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("⏱ Focus Timer on This Step →", key=f"rm_step_timer_{active_sid}", width="stretch"):
                navigate_to(
                    "study_workspace",
                    study_prefill={
                        "subject": str(rm.get("subjectName") or sel_rm_id.title()),
                        "topic": f"Step {step.get('stepNumber')}: {step.get('title', '')}",
                        "minutes": 50,
                    },
                )

        # Verified Resources for this Step
        step_res = step.get("resources") or []
        if step_res:
            section_kicker(f"Verified Free Materials for Step {step.get('stepNumber')} ({len(step_res)})")
            for idx, r in enumerate(step_res):
                r_url = safe_url(r.get("url"))
                playable, _, _ = is_youtube_playable(r_url)
                with st.container(border=True):
                    rl, rr = st.columns([3.5, 1.3])
                    with rl:
                        st.markdown(
                            pills_row([
                                (str(r.get("type") or "Resource"), "indigo" if playable else "emerald"),
                                (str(r.get("provider") or "Verified Source"), "slate"),
                                (f"~{int(r.get('estimatedHours') or 0)}h" if r.get("estimatedHours") else "", "slate"),
                            ]),
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="ou-card-title">{html.escape(str(r.get("title", "")), quote=True)}</div>'
                            f'<div class="ou-card-desc">{html.escape(str(r.get("description", "")), quote=True)}</div>',
                            unsafe_allow_html=True,
                        )
                    with rr:
                        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                        if r_url:
                            st.link_button("Open Source ↗", r_url, type="primary", width="stretch")
                    if playable:
                        render_lazy_youtube_player(
                            r_url,
                            title=str(r.get("title", "")),
                            provider=str(r.get("provider", "")),
                            key=f"rm_res_{active_sid}_{idx}",
                            label="▶ Watch Playlist Distraction-Free In-App",
                            height=390,
                        )

        # Personal Step Notes
        with st.expander("Personal Notes for This Milestone"):
            with st.form(key=f"rm_note_form_{active_sid}"):
                nt = st.text_area(
                    "Markdown Revision Notes",
                    value=notes_map.get(active_sid, ""),
                    height=120,
                    key=f"rm_note_txt_{active_sid}",
                )
                if st.form_submit_button("💾 Save Milestone Note", type="primary", width="stretch"):
                    ok, msg, _ = client.save_note(
                        item_id=active_sid,
                        content=nt,
                        item_title=f"{rm.get('subjectName')} — {step.get('title')}",
                        item_category=str(rm.get("subjectName") or "Roadmap"),
                    )
                    st.toast(msg) if ok else st.error(msg)
                    if ok:
                        st.rerun()


def _render_standard_books_tab(master_guide: dict[str, Any]) -> None:
    std_books = master_guide.get("standard_books") or []
    section_kicker(f"Part 3 · Standard Core Books & 100% Free Legal Companions ({len(std_books)} Subjects)")
    st.caption(
        "Every classic UPSC reference book (Laxmikanth, Spectrum, GC Leong, Ramesh Singh, Shankar IAS) paired with "
        "verified free bare Acts, government PDFs, and full chapter-by-chapter YouTube lecture series."
    )

    f1, f2 = st.columns([2.2, 1.5])
    with f1:
        q = st.text_input("Search Standard Books & Companions", placeholder="e.g., Laxmikanth, Spectrum, Economy, Ethics...", key="rm_std_q")
    with f2:
        subjs = ["All"] + [str(b.get("subject", "")) for b in std_books]
        sel_s = st.selectbox("Subject Filter", options=subjs, key="rm_std_subj")

    q_low = (q or "").strip().lower()
    for idx, sb in enumerate(std_books):
        if sel_s != "All" and sb.get("subject") != sel_s:
            continue
        comps = sb.get("companions") or []
        hay = (str(sb.get("subject", "")) + " " + str(sb.get("standard_book", "")) + " " + " ".join(str(c.get("title", "")) for c in comps)).lower()
        if q_low and q_low not in hay:
            continue

        with st.container(border=True):
            st.markdown(
                pills_row([(str(sb.get("subject") or ""), "indigo"), (f"{len(comps)} Free Companions", "emerald")]),
                unsafe_allow_html=True,
            )
            st.markdown(f"#### 📘 {sb.get('standard_book', '')}")
            for c_idx, comp in enumerate(comps):
                c_url = safe_url(comp.get("url"))
                c_type = str(comp.get("type") or "Resource")
                playable, _, _ = is_youtube_playable(c_url)
                row_l, row_r = st.columns([3.7, 1.2])
                with row_l:
                    st.markdown(
                        f"{pills_row([(c_type, 'indigo' if playable else 'slate')])}"
                        f"**{html.escape(str(comp.get('title', '')), quote=True)}**",
                        unsafe_allow_html=True,
                    )
                with row_r:
                    if c_url:
                        st.link_button("Open Free ↗", c_url, width="stretch")
                if playable:
                    render_lazy_youtube_player(
                        c_url,
                        title=str(comp.get("title", "")),
                        provider=str(sb.get("subject", "")),
                        key=f"rm_std_{idx}_{c_idx}",
                        label=f"▶ Watch “{str(comp.get('title', ''))[:40]}” In-App",
                        height=370,
                    )


def _render_study_sequence_tab(phases: list[dict[str, Any]], workspace: dict[str, Any]) -> None:
    client = get_client()
    progress_map: dict[str, int] = workspace.get("progressMap") or {}

    if not phases:
        empty_state("5-Phase Study Sequence unavailable", "Check master_guide.json study_sequence.")
        return

    phase_ids = [f"seq-phase-{p.get('phase_number', idx + 1)}" for idx, p in enumerate(phases)]
    overall_pct = int(round(sum(int(progress_map.get(pid, 0)) for pid in phase_ids) / max(len(phase_ids), 1)))

    st.markdown(
        progress_bar_html(overall_pct, label="Zero-Cost Beginner-to-Interview Journey Progress (Part 11)", color=EMERALD if overall_pct >= 60 else INDIGO),
        unsafe_allow_html=True,
    )

    for idx, ph in enumerate(phases):
        pnum = ph.get("phase_number", idx + 1)
        pid = f"seq-phase-{pnum}"
        cur_p = int(progress_map.get(pid, 0))

        with st.container(border=True):
            top_l, top_r = st.columns([3.3, 1.3])
            with top_l:
                st.markdown(
                    pills_row([
                        (f"Phase {pnum}", "dark"),
                        (str(ph.get("timeframe") or ""), "amber"),
                        ("✓ Completed" if cur_p >= 100 else (f"{cur_p}% In Progress" if cur_p > 0 else "Upcoming"), "emerald" if cur_p >= 100 else "slate"),
                    ]),
                    unsafe_allow_html=True,
                )
                st.markdown(f"### {ph.get('title', '')}")
            with top_r:
                st.caption("Phase Progress")
                closest = min(PROGRESS_STEPS, key=lambda x: abs(x - cur_p))
                new_p = st.selectbox(
                    f"Phase {pnum} Progress",
                    options=PROGRESS_STEPS,
                    index=PROGRESS_STEPS.index(closest),
                    format_func=lambda x: f"{x}% Done",
                    key=f"seq_prog_{pid}",
                    label_visibility="collapsed",
                )
                if new_p != cur_p:
                    ok, msg, _ = client.update_progress(pid, int(new_p))
                    if ok:
                        st.toast(msg)
                        st.rerun()

            tasks = ph.get("tasks") or []
            if tasks:
                st.markdown("**Action Plan**")
                for t in tasks:
                    st.markdown(f"- {t}")

            links = ph.get("links") or []
            if links:
                st.markdown("**Direct Verified Starting Links**")
                l_cols = st.columns(min(len(links), 4))
                for l_idx, lk in enumerate(links):
                    lbl = str(lk.get("label") or lk.get("title") or "Open Resource")
                    url = safe_url(lk.get("url"))
                    if url:
                        with l_cols[l_idx % len(l_cols)]:
                            st.link_button(f"{lbl[:30]} ↗", url, width="stretch")


def render_roadmaps() -> None:
    client = get_client()
    workspace = client.get_workspace()
    roadmaps = client.get_roadmaps()
    master_guide = client.get_master_guide()
    phases = client.get_study_sequence()

    total_steps = sum(len(r.get("steps") or []) for r in roadmaps)
    std_count = len(master_guide.get("standard_books") or [])

    page_header(
        eyebrow="Guided Syllabus Execution",
        title="Subject Roadmaps, Standard Books & 5-Phase Sequence",
        subtitle=(
            f"Follow {len(roadmaps)} structured UPSC subject roadmaps ({total_steps} milestones), "
            f"{std_count} standard reference book free-companion guides, and the complete zero-cost 5-phase sequence."
        ),
        badge_text=f"{len(roadmaps)} Pillars · {total_steps} Steps · {len(phases)} Phases",
        badge_variant="indigo",
    )

    tab1, tab2, tab3 = st.tabs([
        f"🗺️ Subject Roadmaps ({len(roadmaps)} Pillars / {total_steps} Steps)",
        f"📚 Standard Core Books ({std_count} Subjects)",
        f"🚀 Zero-Cost 5-Phase Sequence ({len(phases)} Phases)",
    ])

    with tab1:
        _render_roadmaps_tab(roadmaps, workspace)
    with tab2:
        _render_standard_books_tab(master_guide)
    with tab3:
        _render_study_sequence_tab(phases, workspace)
