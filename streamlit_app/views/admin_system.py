"""Account & Auth, Admin Resource Catalog CRUD/Sync, Community Suggestions & 4-Subagent System Health Console."""

from __future__ import annotations

import html
from typing import Any

import pandas as pd
import streamlit as st

from backend.models import PREPARATION_STAGES
from streamlit_app.client import get_client
from streamlit_app.theme import (
    empty_state,
    fmt_bytes,
    fmt_mins,
    page_header,
    pills_row,
    safe_url,
    section_kicker,
)

RESOURCE_TYPES = ["YouTube", "PDF", "Website", "Notes", "PYQ"]
RESOURCE_LEVELS = ["Foundation", "Standard", "Advanced", "Prelims", "Mains", "CSAT", "Interview"]
RESOURCE_LANGUAGES = ["English", "English/Hinglish", "English/Hindi", "Hindi", "Hinglish"]
TARGET_YEARS = ["2026", "2027", "2028", "2029", "2030"]
PREFERRED_LANGS = ["Hinglish", "English", "Hindi"]


# =========================================================================
# TAB 1: ACCOUNT, AUTH, PROFILE & WORKSPACE SWITCHER
# =========================================================================


def _render_account_tab(workspace: dict[str, Any]) -> None:
    client = get_client()
    profile = workspace.get("profile") or {}
    is_auth = bool(workspace.get("authenticated"))
    is_demo = bool(workspace.get("is_demo", True))

    # Active Session Banner
    with st.container(border=True):
        st.markdown(
            pills_row([
                ("Signed In" if is_auth else "Preview Session", "emerald" if is_auth else "amber"),
                ("Demo Workspace" if is_demo else "Personal Account", "indigo" if not is_demo else "slate"),
                (f"Role: {str(profile.get('role') or 'student').title()}", "slate"),
                (f"Target CSE {profile.get('target_attempt_year', '2028')}", "dark"),
            ]),
            unsafe_allow_html=True,
        )
        st.markdown(f"### {profile.get('full_name') or 'Aspirant'}  `{profile.get('email', '')}`")
        st.caption(
            f"Stage: **{profile.get('preparation_stage', 'Foundation (Class 6-12)')}** · "
            f"Daily Goal: **{profile.get('daily_target_hours', 4)}h/day** · "
            f"Language: **{profile.get('preferred_language', 'Hinglish')}**"
        )

    left, right = st.columns(2, gap="medium")

    with left:
        section_kicker("Edit Profile & Daily Study Targets")
        with st.container(border=True):
            cur_stage = str(profile.get("preparation_stage") or PREPARATION_STAGES[1])
            cur_year = str(profile.get("target_attempt_year") or "2028")
            cur_lang = str(profile.get("preferred_language") or "Hinglish")
            with st.form(key="adm_profile_form"):
                p_name = st.text_input("Full Name", value=str(profile.get("full_name") or ""), key="adm_prof_name")
                p_stage = st.selectbox(
                    "Preparation Stage",
                    options=PREPARATION_STAGES,
                    index=PREPARATION_STAGES.index(cur_stage) if cur_stage in PREPARATION_STAGES else 1,
                    key="adm_prof_stage",
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    year_opts = TARGET_YEARS if cur_year in TARGET_YEARS else [cur_year] + TARGET_YEARS
                    p_year = st.selectbox("Target Year", options=year_opts, index=year_opts.index(cur_year), key="adm_prof_year")
                with c2:
                    p_hrs = st.number_input(
                        "Daily Goal (hrs)",
                        min_value=1,
                        max_value=16,
                        value=int(profile.get("daily_target_hours") or 4),
                        key="adm_prof_hrs",
                    )
                with c3:
                    p_lang = st.selectbox(
                        "Language",
                        options=PREFERRED_LANGS,
                        index=PREFERRED_LANGS.index(cur_lang) if cur_lang in PREFERRED_LANGS else 0,
                        key="adm_prof_lang",
                    )
                if st.form_submit_button("💾 Save Study Profile", type="primary", width="stretch"):
                    ok, msg = client.update_profile(
                        {
                            "full_name": p_name.strip(),
                            "preparation_stage": p_stage,
                            "target_attempt_year": str(p_year),
                            "daily_target_hours": int(p_hrs),
                            "preferred_language": p_lang,
                        }
                    )
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        section_kicker("Security & Account Lifecycle")
        with st.container(border=True):
            with st.form(key="adm_pwd_form"):
                new_pwd = st.text_input("New Password (min 6 chars)", type="password", key="adm_new_pwd")
                if st.form_submit_button("Update Password", width="stretch", disabled=not is_auth):
                    ok, msg = client.change_password(new_pwd)
                    st.success(msg) if ok else st.error(msg)
            if not is_auth:
                st.caption("Sign in on the right to enable password updates.")

            st.divider()
            if is_demo or not is_auth:
                st.caption("Account deletion is disabled on the default Demo workspace. Create a personal account to manage account lifecycle.")
            else:
                confirm_del = st.checkbox("I understand deleting my account permanently removes my notes, sessions & progress.", key="adm_del_acc_chk")
                if st.button("Permanently Delete My Account", key="adm_del_acc_btn", disabled=not confirm_del, width="stretch"):
                    ok, msg = client.delete_account()
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with right:
        section_kicker("Authentication & Session Control")
        with st.container(border=True):
            auth_mode = st.segmented_control(
                "Auth Action",
                options=["Sign In", "Create Account", "Demo / Sign Out"],
                default="Sign In",
                key="adm_auth_mode",
                label_visibility="collapsed",
            )
            if auth_mode == "Sign In":
                with st.form(key="adm_login_form"):
                    l_email = st.text_input("Email", placeholder="student@upschub.in", key="adm_login_email")
                    l_pwd = st.text_input("Password", type="password", key="adm_login_pwd")
                    if st.form_submit_button("Sign In", type="primary", width="stretch"):
                        ok, msg = client.login(l_email, l_pwd)
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                st.caption("Demo credentials: `student@upschub.in` / `openupsc123`")

            elif auth_mode == "Create Account":
                with st.form(key="adm_signup_form"):
                    s_name = st.text_input("Full Name", placeholder="Your Name", key="adm_su_name")
                    s_email = st.text_input("Email Address", placeholder="aspirant@example.com", key="adm_su_email")
                    s_pwd = st.text_input("Password (6+ chars)", type="password", key="adm_su_pwd")
                    s_c1, s_c2 = st.columns(2)
                    with s_c1:
                        s_stage = st.selectbox("Stage", options=PREPARATION_STAGES, index=1, key="adm_su_stage")
                    with s_c2:
                        s_year = st.selectbox("Target Year", options=TARGET_YEARS, index=2, key="adm_su_year")
                    s_hrs = st.slider("Daily Study Target (Hours)", min_value=1, max_value=12, value=4, key="adm_su_hrs")
                    if st.form_submit_button("Create Personal Account", type="primary", width="stretch"):
                        ok, msg = client.signup(
                            full_name=s_name,
                            email=s_email,
                            password=s_pwd,
                            preparation_stage=s_stage,
                            target_attempt_year=s_year,
                            daily_target_hours=int(s_hrs),
                        )
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            else:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🚀 Demo Login", key="adm_demo_login_btn", type="primary", width="stretch"):
                        ok, msg = client.demo_login()
                        if ok:
                            st.toast(msg)
                            st.rerun()
                with b2:
                    if st.button("Sign Out", key="adm_logout_btn", width="stretch"):
                        ok, msg = client.logout()
                        if ok:
                            st.toast(msg)
                            st.rerun()

        section_kicker("Admin Analytics Aspirant Switcher")
        with st.container(border=True):
            users = client.get_admin_users()
            if users:
                u_ids = [u["id"] for u in users]
                u_map = {u["id"]: u for u in users}
                cur_view = st.session_state.get("admin_view_user_id") or client.active_user_id
                if cur_view not in u_map:
                    cur_view = u_ids[0]
                picked = st.selectbox(
                    "Default Aspirant in Analytics Studio",
                    options=u_ids,
                    index=u_ids.index(cur_view),
                    format_func=lambda uid: f"{u_map[uid].get('full_name', uid)} ({u_map[uid].get('email', '')})",
                    key="adm_analytics_switcher",
                )
                if picked != st.session_state.get("admin_view_user_id"):
                    st.session_state["admin_view_user_id"] = picked
                    st.toast(f"Analytics view switched to {u_map[picked].get('full_name', picked)}.")
            else:
                st.caption("No registered aspirants found.")


# =========================================================================
# TAB 2: ADMIN RESOURCE CATALOG (CRUD + MASTER SYNC + VALIDATION)
# =========================================================================


def _render_catalog_admin_tab() -> None:
    client = get_client()
    resources = client.get_resources()
    facets = client.get_resource_facets()

    # Master Sync & Validation Control Bar
    section_kicker("Master Guide Synchronization & Catalog Validation")
    with st.container(border=True):
        a1, a2, a3 = st.columns([1.4, 1.4, 1.5])
        with a1:
            if st.button("🔄 Re-Sync from Master Guide", key="adm_resync_btn", type="primary", width="stretch"):
                with st.spinner("Synchronizing UPSC_FREE_RESOURCES_MASTER.md → JSON & SQLite..."):
                    ok, msg, rep = client.resync_resources(write_json=True)
                st.session_state["adm_last_resync"] = rep
                st.success(msg) if ok else st.error(msg)
                st.rerun()
        with a2:
            if st.button("✅ Run Catalog Validation Audit", key="adm_val_btn", width="stretch"):
                with st.spinner("Validating all 334 resources, 11 Master Guide parts & URLs..."):
                    st.session_state["adm_last_validation"] = client.validate_catalog()
        with a3:
            st.metric("Catalog Size", f"{len(resources)} Verified", f"{facets.get('playlist_count', 0)} Playable Playlists")

        val_rep = st.session_state.get("adm_last_validation")
        if isinstance(val_rep, dict):
            is_valid = bool(val_rep.get("valid", False))
            stats = val_rep.get("stats") or {}
            errs = val_rep.get("errors") or []
            warns = val_rep.get("warnings") or []
            if is_valid and not errs:
                st.success(
                    f"Catalog Validated Cleanly — **{stats.get('resources_count', len(resources))}** resources, "
                    f"**{stats.get('total_urls_checked', 0)}** URLs checked, **0 errors**, **{len(warns)} warnings**."
                )
            else:
                st.error(f"Validation found {len(errs)} error(s) and {len(warns)} warning(s).")
                if errs:
                    st.json(errs[:10])

    # Browse & Search Catalog
    section_kicker(f"Browse & Search Catalog ({len(resources)} Resources)")
    sf1, sf2, sf3 = st.columns([2.2, 1.3, 1.1])
    with sf1:
        cq = st.text_input("Search Catalog", placeholder="Filter by ID, title, provider, URL...", key="adm_cat_q")
    with sf2:
        all_subjs = ["All"] + sorted({str(r.get("subject", "")) for r in resources})
        c_subj = st.selectbox("Subject", options=all_subjs, key="adm_cat_subj")
    with sf3:
        c_type = st.selectbox("Type", options=["All"] + RESOURCE_TYPES, key="adm_cat_type")

    q_low = (cq or "").strip().lower()
    vis = [
        r
        for r in resources
        if (c_subj == "All" or r.get("subject") == c_subj)
        and (c_type == "All" or r.get("type") == c_type)
        and (
            not q_low
            or q_low in str(r.get("id", "")).lower()
            or q_low in str(r.get("title", "")).lower()
            or q_low in str(r.get("provider", "")).lower()
            or q_low in str(r.get("url", "")).lower()
        )
    ]

    if vis:
        df_res = pd.DataFrame(
            [
                {
                    "ID": r.get("id"),
                    "Title": r.get("title"),
                    "Subject": r.get("subject"),
                    "Type": r.get("type"),
                    "Level": r.get("level"),
                    "Provider": r.get("provider"),
                    "Part": r.get("masterPart") or r.get("master_part") or "",
                    "URL": r.get("url"),
                }
                for r in vis
            ]
        )
        st.dataframe(df_res, width="stretch", hide_index=True, height=290)
    else:
        empty_state("No catalog rows match your filter", "Clear filters to inspect all resources.")

    # Add & Edit/Delete CRUD Forms
    c_add, c_edit = st.columns(2, gap="medium")

    with c_add:
        section_kicker("Add New Free Resource")
        with st.container(border=True):
            with st.form(key="adm_add_res_form"):
                r_title = st.text_input("Resource Title *", placeholder="e.g., Complete Environment & Ecology NCERT Series", key="adm_add_title")
                r_url = st.text_input("Verified Free URL (https://...) *", placeholder="https://www.youtube.com/playlist?list=...", key="adm_add_url")
                ac1, ac2 = st.columns(2)
                with ac1:
                    r_subj = st.text_input("Subject *", value="Indian Polity", key="adm_add_subj")
                    r_type = st.selectbox("Format Type", options=RESOURCE_TYPES, key="adm_add_type")
                    r_lang = st.selectbox("Language", options=RESOURCE_LANGUAGES, index=1, key="adm_add_lang")
                with ac2:
                    r_prov = st.text_input("Provider / Educator *", value="Official / Educator", key="adm_add_prov")
                    r_lvl = st.selectbox("Level", options=RESOURCE_LEVELS, key="adm_add_lvl")
                    r_hrs = st.number_input("Est. Hours", min_value=0, max_value=500, value=10, key="adm_add_hrs")
                r_desc = st.text_area("Description", height=75, key="adm_add_desc")
                r_tip = st.text_input("Senior Mentor Tip (Optional)", key="adm_add_tip")
                r_tags = st.text_input("Tags (comma-separated)", value="UPSC, Free", key="adm_add_tags")
                if st.form_submit_button("+ Add to Verified Catalog", type="primary", width="stretch"):
                    tags_list = [t.strip() for t in r_tags.split(",") if t.strip()] or ["UPSC"]
                    ok, msg, _ = client.create_resource(
                        {
                            "title": r_title.strip(),
                            "url": r_url.strip(),
                            "subject": r_subj.strip(),
                            "type": r_type,
                            "provider": r_prov.strip(),
                            "level": r_lvl,
                            "language": r_lang,
                            "estimated_hours": int(r_hrs),
                            "description": r_desc.strip(),
                            "senior_tip": r_tip.strip() or None,
                            "tags": tags_list,
                        }
                    )
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    with c_edit:
        section_kicker("Edit or Delete Existing Resource")
        with st.container(border=True):
            if not vis:
                st.caption("Filter or select a resource above to edit.")
            else:
                r_ids = [r["id"] for r in vis[:100]]
                r_map = {r["id"]: r for r in vis[:100]}
                sel_rid = st.selectbox(
                    "Select Resource to Modify",
                    options=r_ids,
                    format_func=lambda rid: f"[{r_map[rid].get('subject')}] {str(r_map[rid].get('title', ''))[:55]}",
                    key="adm_edit_sel_rid",
                )
                target = r_map[sel_rid]
                with st.form(key=f"adm_edit_form_{sel_rid}"):
                    et = st.text_input("Title", value=str(target.get("title") or ""), key=f"adm_ed_t_{sel_rid}")
                    eu = st.text_input("URL", value=str(target.get("url") or ""), key=f"adm_ed_u_{sel_rid}")
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        es = st.text_input("Subject", value=str(target.get("subject") or ""), key=f"adm_ed_s_{sel_rid}")
                        cur_ty = str(target.get("type") or "YouTube")
                        ety = st.selectbox(
                            "Type",
                            options=RESOURCE_TYPES,
                            index=RESOURCE_TYPES.index(cur_ty) if cur_ty in RESOURCE_TYPES else 0,
                            key=f"adm_ed_ty_{sel_rid}",
                        )
                    with ec2:
                        ep = st.text_input("Provider", value=str(target.get("provider") or ""), key=f"adm_ed_p_{sel_rid}")
                        cur_lv = str(target.get("level") or "Foundation")
                        elv = st.selectbox(
                            "Level",
                            options=RESOURCE_LEVELS,
                            index=RESOURCE_LEVELS.index(cur_lv) if cur_lv in RESOURCE_LEVELS else 0,
                            key=f"adm_ed_lv_{sel_rid}",
                        )
                    ed_desc = st.text_area("Description", value=str(target.get("description") or ""), height=75, key=f"adm_ed_d_{sel_rid}")
                    ed_tip = st.text_input("Senior Tip", value=str(target.get("seniorTip") or target.get("senior_tip") or ""), key=f"adm_ed_tip_{sel_rid}")
                    if st.form_submit_button("💾 Save Resource Updates", type="primary", width="stretch"):
                        ok, msg, _ = client.update_resource(
                            sel_rid,
                            {
                                "title": et.strip(),
                                "url": eu.strip(),
                                "subject": es.strip(),
                                "type": ety,
                                "provider": ep.strip(),
                                "level": elv,
                                "description": ed_desc.strip(),
                                "senior_tip": ed_tip.strip() or None,
                            },
                        )
                        if ok:
                            st.toast(msg)
                            st.rerun()
                        else:
                            st.error(msg)

                del_chk = st.checkbox(f"Confirm permanent delete of `{sel_rid}`", key=f"adm_del_chk_{sel_rid}")
                if st.button("🗑 Delete Resource", key=f"adm_del_btn_{sel_rid}", disabled=not del_chk, width="stretch"):
                    ok, msg = client.delete_resource(sel_rid)
                    if ok:
                        st.toast(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# =========================================================================
# TAB 3: COMMUNITY SUGGESTIONS & REGISTERED ASPIRANTS
# =========================================================================


def _render_community_tab() -> None:
    client = get_client()
    suggestions = client.get_suggestions()
    users = client.get_admin_users()

    section_kicker(f"Community Free Resource Suggestions ({len(suggestions)})")
    if not suggestions:
        empty_state(
            "No community suggestions in the queue",
            "Students can submit free YouTube playlists or official links from the NCERT Explorer tab.",
        )
    else:
        for sug in suggestions:
            sid = str(sug.get("id", ""))
            status = str(sug.get("status") or "pending").lower()
            st_var = "emerald" if status == "approved" else ("rose" if status == "dismissed" else "amber")
            with st.container(border=True):
                c1, c2, c3 = st.columns([3.0, 1.1, 0.9])
                with c1:
                    st.markdown(
                        pills_row([
                            (status.title(), st_var),
                            (str(sug.get("subject") or "General"), "indigo"),
                            (str(sug.get("channel") or "Community Link"), "slate"),
                        ]),
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="ou-card-title">{html.escape(str(sug.get("chapter_title", "")), quote=True)}</div>',
                        unsafe_allow_html=True,
                    )
                    s_url = safe_url(sug.get("url"))
                    if s_url:
                        st.link_button("Inspect Link ↗", s_url)
                with c2:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button(
                        "✓ Approve & Publish",
                        key=f"adm_sug_app_{sid}",
                        type="primary",
                        disabled=status == "approved",
                        width="stretch",
                    ):
                        ok_s, msg_s = client.update_suggestion_status(sid, "approved")
                        if ok_s and safe_url(sug.get("url")):
                            client.create_resource(
                                {
                                    "title": str(sug.get("chapter_title") or "Community Recommended Resource"),
                                    "subject": str(sug.get("subject") or "General"),
                                    "provider": str(sug.get("channel") or "Community Verified"),
                                    "url": str(sug.get("url")),
                                    "type": "YouTube" if "youtu" in str(sug.get("url", "")).lower() else "Website",
                                    "description": "Approved community free UPSC resource suggestion.",
                                    "tags": ["UPSC", "Community"],
                                }
                            )
                        st.toast("Approved & published to catalog!" if ok_s else msg_s)
                        st.rerun()
                with c3:
                    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                    if st.button(
                        "Dismiss",
                        key=f"adm_sug_dis_{sid}",
                        disabled=status == "dismissed",
                        width="stretch",
                    ):
                        ok_d, msg_d = client.update_suggestion_status(sid, "dismissed")
                        st.toast(msg_d) if ok_d else st.error(msg_d)
                        st.rerun()

    st.divider()
    section_kicker(f"Registered Aspirants Directory ({len(users)})")
    if users:
        df_u = pd.DataFrame(
            [
                {
                    "Name": u.get("full_name"),
                    "Email": u.get("email"),
                    "Stage": u.get("preparation_stage"),
                    "Target": u.get("target_attempt_year"),
                    "Streak (d)": u.get("study_streak_days", 0),
                    "Sessions": u.get("session_count", 0),
                    "Focus Time": fmt_mins(u.get("total_minutes", 0)),
                    "Bookmarks": u.get("bookmark_count", 0),
                }
                for u in users
            ]
        )
        st.dataframe(df_u, width="stretch", hide_index=True)

        with st.expander("🔍 Inspect & Mentor-Edit Aspirant Notes"):
            u_ids = [u["id"] for u in users]
            u_map = {u["id"]: u for u in users}
            sel_u = st.selectbox(
                "Select Aspirant",
                options=u_ids,
                format_func=lambda uid: f"{u_map[uid].get('full_name')} ({u_map[uid].get('email')})",
                key="adm_insp_u",
            )
            details = client.get_admin_user_details(sel_u)
            u_notes = details.get("notes") or []
            if not u_notes:
                st.caption("This aspirant has not saved personal notes yet.")
            else:
                for n in u_notes[:10]:
                    nid = str(n.get("item_id", ""))
                    with st.form(key=f"adm_note_ed_{sel_u}_{nid}"):
                        st.markdown(f"**{n.get('item_title') or nid}** (`{n.get('item_category') or 'General'}`)")
                        new_body = st.text_area("Content", value=str(n.get("content") or ""), height=100, key=f"adm_ntxt_{sel_u}_{nid}")
                        if st.form_submit_button("Save Mentor Update"):
                            ok, msg = client.admin_update_note(sel_u, nid, new_body)
                            st.toast(msg) if ok else st.error(msg)
                            if ok:
                                st.rerun()


# =========================================================================
# TAB 4: SYSTEM TELEMETRY, ROLLING BACKUPS & 4-SUBAGENT HEALTH CONSOLE
# =========================================================================


def _render_system_health_tab() -> None:
    client = get_client()
    api_live = client.is_api_online(force=False)
    diag = client.get_system_diagnostics(include_doctor=False)
    db_rep = diag.get("database") or {}
    backups_info = diag.get("backups") or {}
    backup_items = backups_info.get("items") or []

    # Top Runtime Mode & DB Telemetry Strip
    section_kicker("Runtime Connectivity & SQLite WAL Integrity")
    top1, top2, top3, top4, top5 = st.columns(5)
    top1.metric("Data Transport", "FastAPI Live" if api_live else "Direct SQLite", client.api_base_url if api_live else "Offline Fallback Active")
    top2.metric("DB Integrity", "OK" if db_rep.get("ok") else "Check", f"Mode: {str(db_rep.get('journal_mode') or 'WAL').upper()}")
    top3.metric("SQLite Size", fmt_bytes(db_rep.get("size_bytes", 0)), f"{db_rep.get('table_count', 0)} tables")
    top4.metric("Total Rows", str(db_rep.get("total_rows", 0)), f"FK issues: {db_rep.get('foreign_key_violations', 0)}")
    top5.metric("Rolling Backups", str(len(backup_items)), "Atomic conn.backup()")

    # SQLite Tables + Rolling Backup Controls
    db_col, bk_col = st.columns([1.05, 1.2], gap="medium")

    with db_col:
        section_kicker("SQLite Table Row Inventory")
        with st.container(border=True):
            tables = db_rep.get("tables") or {}
            if tables:
                df_tbl = pd.DataFrame([{"Table": k, "Rows": v} for k, v in sorted(tables.items())])
                st.dataframe(df_tbl, width="stretch", hide_index=True, height=240)
            st.caption(f"DB Path: `{db_rep.get('db_path', '')}`")

    with bk_col:
        section_kicker("Online Atomic SQLite Backups")
        with st.container(border=True):
            b_act1, b_act2 = st.columns(2)
            with b_act1:
                if st.button("💾 Create Online Backup Now", key="adm_backup_now_btn", type="primary", width="stretch"):
                    ok, msg, _ = client.create_backup(max_backups=10)
                    st.toast(msg) if ok else st.error(msg)
                    st.rerun()
            with b_act2:
                if st.button("🔌 Re-Probe FastAPI Health", key="adm_reprobe_api_btn", width="stretch"):
                    live = client.is_api_online(force=True)
                    st.toast("FastAPI is LIVE!" if live else "FastAPI offline — Direct SQLite Fallback active.")
                    st.rerun()

            if backup_items:
                df_bk = pd.DataFrame(
                    [
                        {
                            "Snapshot": b.get("filename"),
                            "Size": fmt_bytes(b.get("size_bytes", 0)),
                            "Created (UTC)": str(b.get("created_at") or "")[:19].replace("T", " "),
                        }
                        for b in backup_items[:10]
                    ]
                )
                st.dataframe(df_bk, width="stretch", hide_index=True, height=200)
            else:
                st.info("No rolling backups captured yet. Click **Create Online Backup Now** to create an atomic snapshot.")

    st.divider()

    # 4 Independent Subagents Health Matrix
    section_kicker("4 Independent Subagents Architecture & Live Health Doctor")
    specs, boundary_report = client.get_subagents_registry()

    h_l, h_r = st.columns([2.8, 1.3])
    with h_l:
        b_ok = bool(boundary_report.get("ok", False))
        st.markdown(
            pills_row([
                ("Ownership Boundaries: Zero Overlap ✓" if b_ok else "Ownership Overlap Detected", "emerald" if b_ok else "rose"),
                (f"{len(specs)} Independent Subagents Registered", "indigo"),
            ]),
            unsafe_allow_html=True,
        )
    with h_r:
        if st.button("🩺 Run 4-Domain Health Doctor", key="adm_run_doctor_btn", type="primary", width="stretch"):
            with st.spinner("Probing resource, backend, frontend, and system domains..."):
                st.session_state["adm_doctor_report"] = client.run_subagents_doctor("all")

    doc_report = st.session_state.get("adm_doctor_report")
    if doc_report is None:
        # Run lightweight initial probe once per session so the matrix is immediately alive!
        doc_report = client.run_subagents_doctor("all")
        st.session_state["adm_doctor_report"] = doc_report

    domains_map = (doc_report or {}).get("domains") or {}
    if specs:
        for i in range(0, len(specs), 2):
            cols = st.columns(2, gap="medium")
            for off, spec in enumerate(specs[i : i + 2]):
                dom_key = spec.get("domain", "")
                dom_rep = domains_map.get(dom_key) or {}
                d_status = str(dom_rep.get("status") or "unknown").lower()
                st_var = "emerald" if d_status == "healthy" else ("amber" if d_status == "degraded" else "rose")
                summary = dom_rep.get("summary") or {}
                dur_ms = dom_rep.get("duration_ms", 0)
                checks = dom_rep.get("checks") or []

                with cols[off]:
                    with st.container(border=True):
                        st.markdown(
                            pills_row([
                                (f"{spec.get('id', dom_key)}", "dark"),
                                (d_status.upper(), st_var),
                                (f"{summary.get('ok', 0)}/{summary.get('total', len(checks))} checks OK", "slate"),
                                (f"{dur_ms} ms", "slate"),
                            ]),
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="ou-card-title">{html.escape(str(spec.get("name", "")), quote=True)}</div>'
                            f'<div class="ou-card-desc">{html.escape(str(spec.get("role", "")), quote=True)}</div>',
                            unsafe_allow_html=True,
                        )
                        st.caption("Owned Paths: " + ", ".join(f"`{p}`" for p in (spec.get("owned_paths") or [])))
                        with st.expander(f"Inspect {len(checks)} Diagnostic Check(s)"):
                            for chk in checks:
                                cst = chk.get("status", "ok")
                                icon = "🟢" if cst == "ok" else ("🟡" if cst == "warn" else "🔴")
                                st.markdown(f"{icon} **{chk.get('name')}** — {chk.get('detail')}")
    else:
        empty_state("Subagent registry unavailable", "Ensure subagents/registry.py is importable.")


# =========================================================================
# MAIN VIEW DISPATCHER
# =========================================================================


def render_admin_system() -> None:
    client = get_client()
    workspace = client.get_workspace()
    mode_lbl = client.connection_mode_label()

    page_header(
        eyebrow="Workspace Governance & Operations",
        title="Account, Admin Catalog & 4-Subagent Health Console",
        subtitle=(
            "Manage your study profile & authentication, perform full CRUD & Master Guide re-sync on the 334-resource catalog, "
            "review community suggestions, and monitor live health across all 4 independent subagents."
        ),
        badge_text=f"● {mode_lbl}",
        badge_variant="emerald" if mode_lbl == "FastAPI Live" else "indigo",
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Account & Study Targets",
        "🗂️ Admin Resource Catalog (CRUD + Sync)",
        "💬 Community Suggestions & Aspirants",
        "🩺 System & 4-Subagent Health Console",
    ])

    with tab1:
        _render_account_tab(workspace)
    with tab2:
        _render_catalog_admin_tab()
    with tab3:
        _render_community_tab()
    with tab4:
        _render_system_health_tab()
