"""
StockSight India SaaS — Login / Register landing page.
Entry point: `streamlit run Home.py`
Default admin: admin@stocksight.in / Admin@123!
"""
import streamlit as st

from core.auth import authenticate, bootstrap, current_user, login, register_user
from core.styles import inject_css, mhtml

st.set_page_config(
    page_title="StockSight India",
    page_icon="🇮🇳",
    layout="centered",
    initial_sidebar_state="collapsed",
)

bootstrap()   # init DB + seed admin on first run
inject_css()

# Already logged in → go to market home
if current_user():
    st.switch_page("pages/0_Market_Home.py")

# ── Hero ──────────────────────────────────────────────────────────────────────
mhtml("""
    <div style="text-align:center; padding: 32px 0 8px 0;">
        <div style="font-size:52px;">📈</div>
        <h1 style="color:#f1f5f9; font-size:32px; margin:8px 0 4px 0;">StockSight India</h1>
        <p style="color:#64748b; font-size:14px; margin:0;">
            NSE · BSE · Nifty 50 &nbsp;|&nbsp; Technical Analysis · AI Forecasting
        </p>
    </div>
""")

st.markdown("<br>", unsafe_allow_html=True)

# ── Auth tabs ─────────────────────────────────────────────────────────────────
tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

# ── Sign In ───────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        email    = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submit   = st.form_submit_button("Sign In", use_container_width=True, type="primary")

    if submit:
        if not email or not password:
            st.error("Please fill in all fields.")
        else:
            with st.spinner("Authenticating…"):
                user, err = authenticate(email.strip(), password)
            if err:
                st.error(f"❌ {err}")
            else:
                login(user)
                st.success(f"Welcome back, **{user['username']}**!")
                st.switch_page("pages/0_Market_Home.py")

    mhtml("""<p style="color:#475569; font-size:12px; text-align:center; margin-top:12px;">
        Demo admin: <code>admin@stocksight.in</code> / <code>Admin@123!</code>
        </p>""")

# ── Register ──────────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)

    reg_email    = st.text_input("Email", placeholder="you@example.com", key="reg_email")
    reg_username = st.text_input("Username", placeholder="johndoe (min 3 chars)", key="reg_user")
    reg_pw       = st.text_input("Password", type="password",
                                  placeholder="Create a strong password", key="reg_pw")

    # ── Real-time password requirements ──────────────────────────────────────
    if reg_pw:
        ok_len   = len(reg_pw) >= 8
        ok_upper = any(c.isupper() for c in reg_pw)
        ok_digit = any(c.isdigit() for c in reg_pw)

        def _row(ok: bool, label: str) -> str:
            color = "#4ade80" if ok else "#f87171"
            icon  = "✓" if ok else "✗"
            return (
                f'<div style="color:{color}; font-size:12px; margin:4px 0; '
                f'display:flex; align-items:center; gap:8px;">'
                f'<span style="font-weight:700; font-size:14px;">{icon}</span>'
                f'<span>{label}</span></div>'
            )

        mhtml(
            '<div style="background:#0f172a; border:1px solid #1e293b; border-radius:8px;'
            ' padding:10px 14px; margin:2px 0 8px 0;">'
            '<div style="color:#64748b; font-size:11px; letter-spacing:.06em;'
            ' text-transform:uppercase; margin-bottom:8px;">Password requirements</div>'
            + _row(ok_len,   "At least 8 characters")
            + _row(ok_upper, "At least one uppercase letter (A–Z)")
            + _row(ok_digit, "At least one number (0–9)")
            + '</div>'
        )

    reg_pw2 = st.text_input("Confirm Password", type="password",
                              placeholder="Re-enter your password", key="reg_pw2")

    # Confirm-password match indicator
    if reg_pw and reg_pw2:
        if reg_pw == reg_pw2:
            mhtml('<div style="color:#4ade80; font-size:12px; margin:2px 0 6px 0;">'
                  '✓ &nbsp;Passwords match</div>')
        else:
            mhtml('<div style="color:#f87171; font-size:12px; margin:2px 0 6px 0;">'
                  '✗ &nbsp;Passwords do not match</div>')

    reg_submit = st.button("Create Account", use_container_width=True,
                            type="primary", key="reg_submit")

    if reg_submit:
        if not all([reg_email, reg_username, reg_pw, reg_pw2]):
            st.error("Please fill in all fields.")
        elif reg_pw != reg_pw2:
            st.error("Passwords do not match.")
        else:
            with st.spinner("Creating account…"):
                user, err = register_user(reg_email.strip(), reg_username.strip(), reg_pw)
            if err:
                st.error(f"❌ {err}")
            else:
                login(user)
                st.success(f"Account created! Welcome, **{user['username']}**.")
                st.switch_page("pages/0_Market_Home.py")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(
    "StockSight India · Data via Yahoo Finance · "
    "Forecasting by Prophet · Built with Streamlit"
)
