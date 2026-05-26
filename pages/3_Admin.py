"""
StockSight India SaaS — Admin Panel (admin role only).
User management, activation toggles, deletion, and platform stats.
"""
import streamlit as st
import pandas as pd

from core.auth import (
    current_user, logout, require_admin,
    list_users, toggle_active, delete_user, get_stats,
)
from core.styles import inject_css, metric_card, role_badge, mhtml

st.set_page_config(
    page_title="Admin — StockSight India",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

user = require_admin()
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔧 Admin Panel")
    mhtml(
        f"""<div style="background:#111827; border:1px solid #1e3a5f; border-radius:10px;
            padding:10px 14px; margin-bottom:4px;">
            <span style="color:#94a3b8; font-size:12px;">Signed in as</span><br>
            <span style="color:#f1f5f9; font-weight:700;">@{user['username']}</span>
            <span style="color:#c084fc; font-size:11px; margin-left:6px;">[ADMIN]</span>
        </div>"""
    )
    if st.button("Sign Out", use_container_width=True):
        logout()

    st.divider()
    st.markdown("#### Navigation")
    section = st.radio(
        "Section",
        ["📊 Platform Stats", "👥 User Management"],
        label_visibility="collapsed",
    )

# ── Main content ──────────────────────────────────────────────────────────────
st.markdown("# 🔧 Admin Panel")
st.divider()

stats = get_stats()

if section == "📊 Platform Stats":
    st.subheader("📊 Platform Overview")
    st.markdown("<br>", unsafe_allow_html=True)

    s_cols = st.columns(4)
    metric_card(s_cols[0], "Total Users",      str(stats["total_users"]))
    metric_card(s_cols[1], "Active Users",     str(stats["active_users"]))
    metric_card(s_cols[2], "Watchlist Items",  str(stats["total_watchlist"]))
    metric_card(s_cols[3], "Admins",           str(stats["admin_count"]))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("👥 Recent Registrations")

    users = list_users()
    if not users:
        st.info("No users yet.")
    else:
        recent = users[:10]
        rows = []
        for u in recent:
            rows.append({
                "Username":   u["username"],
                "Email":      u["email"],
                "Role":       u["role"].upper(),
                "Active":     "✅" if u["is_active"] else "🔴",
                "Watchlist":  u["watchlist_count"],
                "Joined":     u["created_at"].strftime("%d %b %Y") if u["created_at"] else "—",
                "Last Login": u["last_login"].strftime("%d %b %Y %H:%M") if u["last_login"] else "Never",
            })
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

else:  # User Management
    st.subheader("👥 User Management")

    users = list_users()
    if not users:
        st.info("No users registered yet.")
        st.stop()

    # Search / filter
    search = st.text_input("🔍 Search by username or email", placeholder="Type to filter…")
    if search:
        q = search.lower()
        users = [u for u in users if q in u["username"] or q in u["email"]]

    st.markdown(f"Showing **{len(users)}** user(s)")
    st.markdown("<br>", unsafe_allow_html=True)

    for u in users:
        is_self = u["id"] == user["id"]

        with st.container():
            c1, c2, c3 = st.columns([4, 3, 2])

            with c1:
                status_dot = "🟢" if u["is_active"] else "🔴"
                mhtml(
                    f"""<div style="padding:6px 0;">
                        {status_dot}
                        <span style="color:#f1f5f9; font-weight:700;">@{u['username']}</span>
                        {role_badge(u['role'])}
                        <br>
                        <span style="color:#64748b; font-size:12px;">{u['email']}</span>
                    </div>"""
                )

            with c2:
                joined   = u["created_at"].strftime("%d %b %Y") if u["created_at"] else "—"
                last_log = u["last_login"].strftime("%d %b %Y") if u["last_login"] else "Never"
                mhtml(
                    f"""<div style="color:#94a3b8; font-size:12px; padding:6px 0;">
                        Joined: <b>{joined}</b><br>
                        Last login: <b>{last_log}</b><br>
                        Watchlist items: <b>{u['watchlist_count']}</b>
                    </div>"""
                )

            with c3:
                if not is_self:
                    toggle_label = "🔴 Deactivate" if u["is_active"] else "🟢 Activate"
                    if st.button(toggle_label, key=f"tog_{u['id']}", use_container_width=True):
                        toggle_active(u["id"])
                        st.rerun()

                    if st.button(
                        "🗑️ Delete", key=f"del_{u['id']}", use_container_width=True,
                        type="primary",
                    ):
                        st.session_state[f"confirm_del_{u['id']}"] = True

                    if st.session_state.get(f"confirm_del_{u['id']}"):
                        st.warning(f"Delete **@{u['username']}**? This cannot be undone.")
                        col_yes, col_no = st.columns(2)
                        if col_yes.button("Yes, delete", key=f"yes_{u['id']}", type="primary"):
                            delete_user(u["id"])
                            del st.session_state[f"confirm_del_{u['id']}"]
                            st.rerun()
                        if col_no.button("Cancel", key=f"no_{u['id']}"):
                            del st.session_state[f"confirm_del_{u['id']}"]
                            st.rerun()
                else:
                    mhtml('<span style="color:#475569; font-size:12px;">(current session)</span>')

            st.divider()
