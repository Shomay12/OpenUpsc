"""Executive UPSC Readiness & Deep Analytics Studio."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from streamlit_app.client import get_client
from streamlit_app.theme import (
    AMBER,
    CHART_PALETTE,
    EMERALD,
    INDIGO,
    INK_PRIMARY,
    ROSE,
    apply_editorial_plotly,
    empty_state,
    fmt_days,
    fmt_mins,
    navigate_to,
    page_header,
    pills_row,
    progress_bar_html,
    section_kicker,
)


def _make_readiness_gauge(score: int) -> go.Figure:
    val = max(0, min(100, int(score or 0)))
    bar_color = EMERALD if val >= 75 else (INDIGO if val >= 45 else AMBER)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": " / 100", "font": {"size": 34, "color": INK_PRIMARY}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CBD5E1"},
                "bar": {"color": bar_color, "thickness": 0.72},
                "bgcolor": "#F1F5F9",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#FEF2F2"},
                    {"range": [40, 75], "color": "#EFF6FF"},
                    {"range": [75, 100], "color": "#ECFDF5"},
                ],
            },
        )
    )
    fig.update_layout(
        height=245,
        margin=dict(l=22, r=22, t=22, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color=INK_PRIMARY),
    )
    return fig


def render_analytics() -> None:
    client = get_client()
    users = client.get_admin_users()
    active_uid = st.session_state.get("admin_view_user_id") or client.active_user_id
    user_ids = [u["id"] for u in users]
    if active_uid not in user_ids and user_ids:
        active_uid = user_ids[0]
    user_by_id = {u["id"]: u for u in users}

    page_header(
        eyebrow="Executive Telemetry",
        title="UPSC Readiness & Deep Analytics Studio",
        subtitle=(
            "Quantify consistency, syllabus mastery across NCERT & 8 subject roadmaps, PYQ accuracy, "
            "and Class 6–12 resource coverage in one clear command view."
        ),
        badge_text="Live SQLite & API Telemetry",
        badge_variant="indigo",
    )

    # Aspirant selector (cleanly scoped when multiple aspirants exist)
    if len(users) > 1:
        sel_col, info_col = st.columns([2.2, 2.8])
        with sel_col:
            chosen_uid = st.selectbox(
                "Inspecting Aspirant Workspace",
                options=user_ids,
                index=user_ids.index(active_uid),
                format_func=lambda uid: (
                    f"{user_by_id[uid].get('full_name', uid)} — "
                    f"{user_by_id[uid].get('preparation_stage', '')} (Target {user_by_id[uid].get('target_attempt_year', '')})"
                ),
                key="an_user_switcher",
            )
            active_uid = chosen_uid
            st.session_state["admin_view_user_id"] = chosen_uid
        with info_col:
            u_obj = user_by_id.get(active_uid, {})
            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            st.markdown(
                pills_row([
                    (str(u_obj.get("email") or ""), "slate"),
                    (f"Daily Goal: {u_obj.get('daily_target_hours', 4)}h", "emerald"),
                ]),
                unsafe_allow_html=True,
            )

    analytics = client.get_analytics(user_id=active_uid)
    ncert_books = client.get_ncert()

    # Row 1: Top 5 KPI Metrics
    k1, k2, k3, k4, k5 = st.columns(5)
    readiness = int(analytics.get("readiness_score") or 0)
    today_mins = int(analytics.get("today_minutes") or 0)
    daily_target_mins = int(analytics.get("daily_target_minutes") or 240)
    today_pct = int(analytics.get("today_target_percent") or 0)
    weekly_mins = int(analytics.get("weekly_minutes") or 0)
    total_mins = int(analytics.get("total_minutes") or 0)
    pyq_acc = int(analytics.get("pyq_accuracy_percent") or 0)
    pyq_att = int(analytics.get("pyq_total_attempted") or 0)
    pyq_corr = int(analytics.get("pyq_total_correct") or 0)
    streak = int(analytics.get("study_streak_days") or 0)
    active_14 = int(analytics.get("active_days_last_14") or 0)

    k1.metric("UPSC Readiness", f"{readiness} / 100", f"Consistency {analytics.get('consistency_score', 0)}%")
    k2.metric("Today's Focus", fmt_mins(today_mins), f"{today_pct}% of {fmt_mins(daily_target_mins)}")
    k3.metric("Last 7 Days", fmt_mins(weekly_mins), f"All-time {fmt_mins(total_mins)}")
    k4.metric("PYQ Accuracy", f"{pyq_acc}%" if pyq_att else "—", f"{pyq_corr}/{pyq_att} correct" if pyq_att else "No attempts")
    k5.metric("Study Streak", fmt_days(streak), f"{active_14}/14 active days")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Row 2: Readiness Gauge + Recommended Next Focus & Catalog Telemetry
    g_col, rec_col = st.columns([1.0, 1.25], gap="medium")

    with g_col:
        section_kicker("Composite UPSC Readiness Gauge")
        with st.container(border=True):
            st.plotly_chart(_make_readiness_gauge(readiness), width="stretch", key="an_gauge_chart")
            c_sub1, c_sub2, c_sub3 = st.columns(3)
            c_sub1.metric("Consistency", f"{analytics.get('consistency_score', 0)}%")
            c_sub2.metric("Syllabus", f"{analytics.get('overall_progress_percent', 0)}%")
            c_sub3.metric("Sessions", str(analytics.get("total_sessions", 0)))

    with rec_col:
        section_kicker("Recommended Next Focus & Workspace Footprint")
        with st.container(border=True):
            weak = analytics.get("weak_subjects") or []
            if weak:
                for idx, w in enumerate(weak[:3]):
                    wl, wr = st.columns([3.2, 1.0])
                    with wl:
                        st.markdown(
                            progress_bar_html(
                                w.get("percent", 0),
                                label=str(w.get("subject", "Subject")),
                                color=AMBER if int(w.get("percent", 0)) < 35 else INDIGO,
                            ),
                            unsafe_allow_html=True,
                        )
                    with wr:
                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                        href = str(w.get("href") or "/roadmaps/polity")
                        if st.button("Study →", key=f"an_weak_jump_{idx}", width="stretch"):
                            if href == "/ncert":
                                navigate_to("ncert")
                            elif "/roadmaps/" in href:
                                navigate_to("roadmaps", roadmap_selected_subject=href.rsplit("/", 1)[-1])
                            else:
                                navigate_to("roadmaps")
            else:
                st.success("All core pillars have balanced progress!")

            st.divider()
            fp1, fp2, fp3, fp4 = st.columns(4)
            fp1.metric("Completed Items", str(analytics.get("catalog_completed", 0)))
            fp2.metric("In Progress", str(analytics.get("catalog_in_progress", 0)))
            fp3.metric("Bookmarks", str(analytics.get("bookmarks_count", 0)))
            fp4.metric("Notes Saved", str(analytics.get("notes_count", 0)))
            st.caption(
                f"Estimated study hours completed: **{analytics.get('catalog_completed_hours', 0)}h** / "
                f"**{analytics.get('catalog_total_hours', 0)}h** catalog depth · Top Focus Subject: **{analytics.get('top_subject') or '—'}**"
            )

    # Row 3: 14-Day Focus Trend + Focus Hours by Subject Donut
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    tr_col, dn_col = st.columns([1.45, 1.0], gap="medium")

    with tr_col:
        section_kicker("14-Day Daily Focus Trend (Minutes vs Daily Goal)")
        with st.container(border=True):
            daily_series = analytics.get("daily_series") or []
            if daily_series:
                df_daily = pd.DataFrame(daily_series)
                fig_trend = px.bar(
                    df_daily,
                    x="label",
                    y="minutes",
                    color_discrete_sequence=[INDIGO],
                    labels={"label": "Date (IST)", "minutes": "Focus Minutes"},
                )
                fig_trend.update_traces(marker_line_width=0, marker_cornerradius=6)
                fig_trend.add_hline(
                    y=daily_target_mins,
                    line_dash="dash",
                    line_color=EMERALD,
                    annotation_text=f"Daily Goal ({fmt_mins(daily_target_mins)})",
                    annotation_position="top left",
                    annotation_font_color=EMERALD,
                )
                apply_editorial_plotly(fig_trend, height=310, showlegend=False)
                st.plotly_chart(fig_trend, width="stretch", key="an_daily_trend_chart")
            else:
                empty_state("No 14-day focus data yet", "Log study sessions in the Study Workspace to see daily trends.")

    with dn_col:
        section_kicker("Focus Distribution by Subject")
        with st.container(border=True):
            subj_mins = [s for s in (analytics.get("subject_minutes") or []) if int(s.get("minutes") or 0) > 0]
            if subj_mins:
                df_sm = pd.DataFrame(subj_mins)
                df_sm["hours"] = (df_sm["minutes"] / 60.0).round(2)
                fig_donut = px.pie(
                    df_sm,
                    names="subject",
                    values="hours",
                    hole=0.56,
                    color_discrete_sequence=CHART_PALETTE,
                )
                fig_donut.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
                apply_editorial_plotly(fig_donut, height=310, showlegend=False)
                st.plotly_chart(fig_donut, width="stretch", key="an_subject_donut_chart")
            else:
                empty_state("No subject focus hours logged", "Log completed sessions in Study Workspace.")

    # Row 4: Syllabus Mastery (9 Pillars) + PYQ Accuracy by Subject
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    sm_col, pyq_col = st.columns([1.25, 1.0], gap="medium")

    with sm_col:
        section_kicker("Syllabus Mastery Across All 9 Core Pillars")
        with st.container(border=True):
            mastery = analytics.get("subject_mastery") or []
            if mastery:
                df_m = pd.DataFrame(mastery).sort_values("percent", ascending=True)
                fig_m = px.bar(
                    df_m,
                    x="percent",
                    y="subject",
                    orientation="h",
                    text="percent",
                    color="percent",
                    color_continuous_scale=["#F59E0B", "#1D4ED8", "#059669"],
                    range_color=[0, 100],
                    labels={"percent": "Completion (%)", "subject": ""},
                )
                fig_m.update_traces(texttemplate="%{text}%", textposition="outside", marker_cornerradius=5)
                fig_m.update_layout(coloraxis_showscale=False)
                fig_m.update_xaxes(range=[0, 112])
                apply_editorial_plotly(fig_m, height=340, showlegend=False)
                st.plotly_chart(fig_m, width="stretch", key="an_mastery_bar_chart")
            else:
                empty_state("Syllabus mastery not initialized", "Update progress on NCERT or Roadmaps to populate this chart.")

    with pyq_col:
        section_kicker("PYQ Accuracy by Subject")
        with st.container(border=True):
            pyq_by_subj = analytics.get("pyq_by_subject") or []
            if pyq_by_subj:
                df_pyq = pd.DataFrame(pyq_by_subj).sort_values("accuracy", ascending=True)
                fig_pyq = px.bar(
                    df_pyq,
                    x="accuracy",
                    y="subject",
                    orientation="h",
                    text="accuracy",
                    color_discrete_sequence=[EMERALD],
                    labels={"accuracy": "Accuracy (%)", "subject": ""},
                )
                fig_pyq.update_traces(texttemplate="%{text}%", textposition="outside", marker_cornerradius=5)
                fig_pyq.update_xaxes(range=[0, 115])
                apply_editorial_plotly(fig_pyq, height=230, showlegend=False)
                st.plotly_chart(fig_pyq, width="stretch", key="an_pyq_bar_chart")
                st.dataframe(
                    df_pyq[["subject", "attempted", "correct", "accuracy"]].rename(
                        columns={"subject": "Subject", "attempted": "Tried", "correct": "Correct", "accuracy": "Accuracy %"}
                    ),
                    width="stretch",
                    hide_index=True,
                )
            else:
                empty_state("No PYQ attempts recorded yet", "Visit the Interactive PYQ Arena to benchmark your exam accuracy.")

    # Row 5: NCERT Class 6–12 Resource Coverage vs Student Completion + Audit Table + Chapter Explorer
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_kicker("NCERT Class 6–12 Coverage Audit vs. Student Completion")
    ncert_audit = analytics.get("ncert_audit") or []
    with st.container(border=True):
        if ncert_audit:
            df_na = pd.DataFrame(ncert_audit)
            df_na["class_label"] = df_na["class_num"].apply(lambda c: f"Class {c}")

            fig_na = go.Figure()
            fig_na.add_trace(
                go.Bar(
                    name="Catalog Chapter Coverage %",
                    x=df_na["class_label"],
                    y=df_na["coverage_percent"],
                    marker_color="#94A3B8",
                    marker_cornerradius=5,
                )
            )
            fig_na.add_trace(
                go.Bar(
                    name="Your Completion %",
                    x=df_na["class_label"],
                    y=df_na["user_completion_percent"],
                    marker_color=EMERALD,
                    marker_cornerradius=5,
                )
            )
            fig_na.update_layout(barmode="group")
            fig_na.update_yaxes(range=[0, 110], title="Percent (%)")
            apply_editorial_plotly(fig_na, height=300, showlegend=True)
            st.plotly_chart(fig_na, width="stretch", key="an_ncert_audit_chart")

            st.dataframe(
                df_na[
                    [
                        "class_label",
                        "subjects",
                        "books",
                        "total_chapters",
                        "covered_chapters",
                        "coverage_percent",
                        "user_completion_percent",
                        "status",
                    ]
                ].rename(
                    columns={
                        "class_label": "Class",
                        "subjects": "Subjects",
                        "books": "Books",
                        "total_chapters": "Total Ch.",
                        "covered_chapters": "Covered Ch.",
                        "coverage_percent": "Catalog %",
                        "user_completion_percent": "Your %",
                        "status": "Status",
                    }
                ),
                width="stretch",
                hide_index=True,
            )
        else:
            empty_state("NCERT audit data unavailable", "Verify backend/data/ncert.json is present.")

        with st.expander("🔍 Filterable NCERT Chapter Explorer (315 Prioritized Chapters)"):
            cf1, cf2 = st.columns(2)
            with cf1:
                ch_cls = st.selectbox(
                    "Class",
                    options=["All", 6, 7, 8, 9, 10, 11, 12],
                    format_func=lambda c: "All Classes" if c == "All" else f"Class {c}",
                    key="an_ch_cls",
                )
            with cf2:
                ch_prio = st.selectbox("Priority", options=["All", "Must Read", "Important", "Selective"], key="an_ch_prio")
            ch_rows = []
            for bk in ncert_books:
                if ch_cls != "All" and int(bk.get("classNum", 0)) != int(ch_cls):
                    continue
                for ch in bk.get("chapters") or []:
                    if ch_prio != "All" and ch.get("priority") != ch_prio:
                        continue
                    ch_rows.append(
                        {
                            "Class": f"Class {bk.get('classNum')}",
                            "Subject": bk.get("subjectName"),
                            "Book": bk.get("bookTitle"),
                            "Ch #": ch.get("number"),
                            "Chapter Title": ch.get("title"),
                            "Priority": ch.get("priority"),
                            "UPSC Relevance": ch.get("upscRelevance"),
                        }
                    )
            if ch_rows:
                st.dataframe(pd.DataFrame(ch_rows), width="stretch", hide_index=True, height=320)
            else:
                st.caption("No chapters match this filter.")

    # Row 6: Free Resource Library Coverage
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_kicker(f"Verified Free Resource Library Coverage ({analytics.get('catalog_total_resources', 334)} Resources)")
    r_col1, r_col2 = st.columns([1.0, 1.4], gap="medium")

    with r_col1:
        with st.container(border=True):
            type_counts = analytics.get("catalog_type_counts") or {}
            if type_counts:
                df_t = pd.DataFrame([{"Format": k, "Count": v} for k, v in type_counts.items()]).sort_values("Count", ascending=False)
                fig_t = px.pie(df_t, names="Format", values="Count", hole=0.52, color_discrete_sequence=CHART_PALETTE)
                fig_t.update_traces(textinfo="label+value")
                apply_editorial_plotly(fig_t, height=290, showlegend=False)
                st.plotly_chart(fig_t, width="stretch", key="an_catalog_type_chart")
            else:
                empty_state("No catalog format telemetry", "Resync catalog in Admin & System.")

    with r_col2:
        with st.container(border=True):
            subj_counts = analytics.get("catalog_subject_counts") or {}
            if subj_counts:
                df_sc = pd.DataFrame([{"Subject": k, "Resources": v} for k, v in subj_counts.items()]).sort_values("Resources", ascending=True).tail(12)
                fig_sc = px.bar(
                    df_sc,
                    x="Resources",
                    y="Subject",
                    orientation="h",
                    text="Resources",
                    color_discrete_sequence=[INK_PRIMARY],
                )
                fig_sc.update_traces(textposition="outside", marker_cornerradius=5)
                apply_editorial_plotly(fig_sc, height=290, showlegend=False)
                st.plotly_chart(fig_sc, width="stretch", key="an_catalog_subj_chart")
            else:
                empty_state("No subject distribution data", "Resync catalog in Admin & System.")
