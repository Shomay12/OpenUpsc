"""Interactive PYQ Practice Arena (24 UPSC Prelims, CSAT & Mains PYQs) + Official UPSC Hub & Archives."""

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
    safe_url,
    section_kicker,
    senior_tip_box,
)


def _render_pyq_arena(pyqs: list[dict[str, Any]], workspace: dict[str, Any]) -> None:
    client = get_client()
    attempts: dict[str, dict[str, Any]] = workspace.get("pyqAttempts") or {}
    notes_map: dict[str, str] = workspace.get("notes") or {}

    total_q = len(pyqs)
    attempted_count = sum(1 for q in pyqs if q["id"] in attempts)
    correct_count = sum(1 for q in pyqs if q["id"] in attempts and attempts[q["id"]].get("isCorrect"))
    acc_pct = int(round((correct_count / attempted_count) * 100)) if attempted_count else 0

    m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1, 1.1])
    m1.metric("Attempted", f"{attempted_count} / {total_q}")
    m2.metric("Correct", str(correct_count))
    m3.metric("Accuracy", f"{acc_pct}%" if attempted_count else "—")
    m4.metric("Remaining", str(max(0, total_q - attempted_count)))
    with m5:
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        confirm_reset = st.checkbox("Confirm reset", key="pyq_reset_confirm")
        if st.button(
            "↺ Reset Attempts",
            key="pyq_reset_btn",
            disabled=not confirm_reset or attempted_count == 0,
            width="stretch",
        ):
            ok, msg = client.reset_pyq_attempts()
            st.toast(msg) if ok else st.error(msg)
            st.rerun()

    # Filters
    types = ["All"] + sorted({str(q.get("type", "")) for q in pyqs if q.get("type")})
    papers = ["All"] + sorted({str(q.get("paper", "")) for q in pyqs if q.get("paper")})
    subjects = ["All"] + sorted({str(q.get("subject", "")) for q in pyqs if q.get("subject")})

    preset_subj = st.session_state.pop("pyq_preset_subject", None)
    if preset_subj in subjects:
        st.session_state["pyq_filter_subject"] = preset_subj

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_type = st.selectbox("Exam Stage", options=types, key="pyq_filter_type")
    with f2:
        sel_paper = st.selectbox("Paper", options=papers, key="pyq_filter_paper")
    with f3:
        sel_subj = st.selectbox("Subject", options=subjects, key="pyq_filter_subject")
    with f4:
        sel_status = st.selectbox(
            "Attempt Status",
            options=["All", "Unattempted", "Attempted", "Incorrect Only"],
            key="pyq_filter_status",
        )

    filtered: list[dict[str, Any]] = []
    for q in pyqs:
        qid = q["id"]
        att = attempts.get(qid)
        if sel_type != "All" and q.get("type") != sel_type:
            continue
        if sel_paper != "All" and q.get("paper") != sel_paper:
            continue
        if sel_subj != "All" and q.get("subject") != sel_subj:
            continue
        if sel_status == "Unattempted" and att is not None:
            continue
        if sel_status == "Attempted" and att is None:
            continue
        if sel_status == "Incorrect Only" and (att is None or att.get("isCorrect")):
            continue
        filtered.append(q)

    st.caption(f"Displaying **{len(filtered)}** authentic UPSC questions (server-verified grading).")
    if not filtered:
        empty_state("No PYQs match the selected filters", "Change Exam Stage, Subject, or Status to view more questions.")
        return

    for q in filtered:
        qid = str(q["id"])
        qtype = str(q.get("type") or "Prelims")
        qyear = q.get("year", "")
        qpaper = str(q.get("paper") or "")
        qsubj = str(q.get("subject") or "")
        qtopic = str(q.get("topic") or "")
        options = q.get("options") or []
        att = attempts.get(qid)

        badge_list = [
            (f"{qtype} {qyear}", "dark"),
            (qpaper, "indigo"),
            (qsubj, "slate"),
        ]
        if att is not None:
            if att.get("isCorrect"):
                badge_list.append(("✓ Correct", "emerald"))
            else:
                badge_list.append(("✕ Review Needed", "rose"))
        else:
            badge_list.append(("Unattempted", "amber"))

        with st.container(border=True):
            st.markdown(pills_row(badge_list), unsafe_allow_html=True)
            st.caption(f"Topic: {qtopic}")
            st.markdown(f"**{q.get('question', '')}**")

            if options:
                default_idx = 0
                if att and att.get("selectedOption") in options:
                    default_idx = options.index(att["selectedOption"])
                chosen = st.radio(
                    "Select your answer",
                    options=options,
                    index=default_idx,
                    key=f"pyq_opt_{qid}",
                    label_visibility="collapsed",
                )
                c_sub, c_rm, _ = st.columns([1.2, 1.3, 2.5])
                with c_sub:
                    if st.button(
                        "Check Answer" if att is None else "Re-Check Answer",
                        key=f"pyq_submit_{qid}",
                        type="primary",
                        width="stretch",
                    ):
                        ok, msg, res = client.record_pyq_attempt(
                            pyq_id=qid,
                            subject=qsubj,
                            selected_option=str(chosen),
                        )
                        if ok:
                            if res.get("is_correct"):
                                st.toast("Correct! Concept verified.")
                            else:
                                st.toast("Marked for review — check the explanation below.")
                            st.rerun()
                        else:
                            st.error(msg)
                with c_rm:
                    rel_path = str(q.get("relatedSubjectPath") or "")
                    if "/roadmaps/" in rel_path:
                        slug = rel_path.rsplit("/", 1)[-1]
                        if st.button("Open Roadmap →", key=f"pyq_rm_{qid}", width="stretch"):
                            navigate_to("roadmaps", roadmap_selected_subject=slug)

                if att is not None:
                    if att.get("isCorrect"):
                        st.markdown(
                            f"""
                            <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-left:4px solid #059669;
                                        border-radius:10px;padding:10px 14px;margin:8px 0;color:#065F46;font-size:0.9rem;">
                              <strong>✓ Correct!</strong> Your choice: <em>{html.escape(str(att.get('selectedOption', '')), quote=True)}</em>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div style="background:#FEF2F2;border:1px solid #FECACA;border-left:4px solid #DC2626;
                                        border-radius:10px;padding:10px 14px;margin:8px 0;color:#991B1B;font-size:0.9rem;">
                              <strong>✕ Incorrect.</strong> You chose <em>{html.escape(str(att.get('selectedOption', '')), quote=True)}</em>
                              &mdash; Official Answer: <strong>{html.escape(str(q.get('correctAnswer', '')), quote=True)}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    st.markdown(f"**Official Explanation:** {q.get('explanation', '')}")
                    senior_tip_box(q.get("seniorApproachTip"), label="Senior Elimination & Approach Tip")
            else:
                # Mains Subjective Question
                c_m1, c_m2, _ = st.columns([1.4, 1.4, 2.2])
                with c_m1:
                    if st.button(
                        "✓ Mark Practiced" if att is None else "✓ Practiced (Log Again)",
                        key=f"pyq_mains_done_{qid}",
                        type="primary" if att is None else "secondary",
                        width="stretch",
                    ):
                        ok, msg, _ = client.record_pyq_attempt(
                            pyq_id=qid,
                            subject=qsubj,
                            selected_option="Mains Practiced",
                            is_correct=True,
                        )
                        if ok:
                            st.toast("Mains PYQ marked practiced!")
                            st.rerun()
                with c_m2:
                    if st.button("⏱ 15m Answer Timer →", key=f"pyq_mains_timer_{qid}", width="stretch"):
                        navigate_to(
                            "study_workspace",
                            study_prefill={
                                "subject": qsubj,
                                "topic": f"Mains {qyear} {qpaper}: {qtopic}",
                                "minutes": 15,
                            },
                        )

                with st.expander("Reveal Model Framework, Explanation & Senior Directive Tip", expanded=att is not None):
                    st.markdown(f"**Model Approach & Core Points:** {q.get('explanation', '')}")
                    senior_tip_box(q.get("seniorApproachTip"), label="Senior Mains Structuring Tip")

            with st.expander("Personal PYQ Note & Mistake Log"):
                with st.form(key=f"pyq_note_form_{qid}"):
                    n_txt = st.text_area(
                        "Why I got this right/wrong or key value-addition points",
                        value=notes_map.get(qid, ""),
                        height=85,
                        key=f"pyq_note_txt_{qid}",
                    )
                    if st.form_submit_button("💾 Save PYQ Note", width="stretch"):
                        ok, msg, _ = client.save_note(
                            item_id=qid,
                            content=n_txt,
                            item_title=f"PYQ {qyear} ({qsubj}): {qtopic}",
                            item_category=f"PYQ · {qsubj}",
                        )
                        st.toast(msg) if ok else st.error(msg)
                        if ok:
                            st.rerun()


def _render_official_hub_and_archives(
    master_guide: dict[str, Any],
    question_papers: list[dict[str, Any]],
) -> None:
    official_hub = master_guide.get("official_hub") or []
    part7_items = master_guide.get("exam_papers_and_quizzes") or []

    # Section A: Official UPSC Exam Hub (9 Portals)
    section_kicker(f"Part 1 · Official UPSC Exam Hub ({len(official_hub)} Authoritative Portals)")
    for i in range(0, len(official_hub), 3):
        cols = st.columns(3, gap="medium")
        for off, item in enumerate(official_hub[i : i + 3]):
            with cols[off]:
                with st.container(border=True):
                    st.markdown(pills_row([("Official UPSC", "emerald")]), unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(item.get("purpose", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(item.get("url"))
                    if ext:
                        st.link_button("Open Official Portal ↗", ext, type="primary", width="stretch")

    st.divider()

    # Section B: Question Paper Archives (18) + Part 7 Quizzes & PYQ Playlists
    section_kicker(f"Part 7 · Question Paper Archives, QCAB, Toppers' Copies & Daily Quizzes ({len(question_papers)} Archives)")
    qf1, qf2 = st.columns([2.2, 1.4])
    with qf1:
        arch_q = st.text_input(
            "Search Archives",
            placeholder="Search UPSC official PDFs, CSAT papers, QCAB, toppers' copies, daily quizzes...",
            key="pyq_arch_search",
        )
    with qf2:
        stages = ["All"] + sorted({str(qp.get("stage", "")) for qp in question_papers if qp.get("stage")})
        arch_stage = st.selectbox("Stage Filter", options=stages, key="pyq_arch_stage")

    q_low = (arch_q or "").strip().lower()
    vis_qp = [
        qp
        for qp in question_papers
        if (arch_stage == "All" or qp.get("stage") == arch_stage)
        and (
            not q_low
            or q_low in str(qp.get("title", "")).lower()
            or q_low in str(qp.get("provider", "")).lower()
            or q_low in str(qp.get("description", "")).lower()
        )
    ]

    for i in range(0, len(vis_qp), 2):
        cols = st.columns(2, gap="medium")
        for off, qp in enumerate(vis_qp[i : i + 2]):
            with cols[off]:
                with st.container(border=True):
                    st.markdown(
                        pills_row([
                            (str(qp.get("stage") or "CSE"), "indigo"),
                            (str(qp.get("years") or "Multi-Year"), "slate"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(qp.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-meta">{html.escape(str(qp.get("provider", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(qp.get("description", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    ext = safe_url(qp.get("url"))
                    if ext:
                        st.link_button("Open Archive ↗", ext, width="stretch", type="primary")
                    playable, _, _ = is_youtube_playable(ext)
                    if playable:
                        render_lazy_youtube_player(
                            ext,
                            title=str(qp.get("title", "")),
                            provider=str(qp.get("provider", "")),
                            key=f"pyq_qp_{qp.get('id', i)}_{off}",
                            label="▶ Watch PYQ Analysis In-App",
                            height=360,
                        )

    if part7_items:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        section_kicker(f"Master Guide Part 7 · Verified Free Daily Quiz & Mock Platforms ({len(part7_items)})")
        for idx, item in enumerate(part7_items):
            if q_low and q_low not in str(item.get("title", "")).lower() and q_low not in str(item.get("coverage", "")).lower():
                continue
            ext = safe_url(item.get("url"))
            playable, _, _ = is_youtube_playable(ext)
            with st.container(border=True):
                c1, c2 = st.columns([3.6, 1.2])
                with c1:
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(item.get("title", "")), quote=True)}</div>'
                        f'<div class="ou-card-desc">{html.escape(str(item.get("coverage", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if ext:
                        st.link_button("Open Platform ↗", ext, width="stretch")
                if playable:
                    render_lazy_youtube_player(
                        ext,
                        title=str(item.get("title", "")),
                        provider="Verified Educator",
                        key=f"pyq_p7_{idx}",
                        label="▶ Watch Video Breakdown In-App",
                        height=380,
                    )


def render_pyqs() -> None:
    client = get_client()
    workspace = client.get_workspace()
    pyqs = client.get_pyqs()
    qps = client.get_question_papers()
    master_guide = client.get_master_guide()
    hub_count = len(master_guide.get("official_hub") or [])

    page_header(
        eyebrow="Exam Reality Calibration",
        title="Official UPSC Hub & PYQ Practice Arena",
        subtitle=(
            f"Practice {len(pyqs)} real UPSC Prelims, CSAT & Mains PYQs with authoritative grading and senior elimination tips, "
            f"plus direct access to all {hub_count} official UPSC portals and {len(qps)} question paper archives."
        ),
        badge_text=f"{len(pyqs)} Interactive PYQs · {len(qps)} Archives",
        badge_variant="violet",
    )

    tab1, tab2 = st.tabs([
        f"🎯 Interactive PYQ Arena ({len(pyqs)} Questions)",
        f"🏛️ Official UPSC Hub ({hub_count}) & Paper Archives ({len(qps)})",
    ])

    with tab1:
        _render_pyq_arena(pyqs, workspace)
    with tab2:
        _render_official_hub_and_archives(master_guide, qps)
