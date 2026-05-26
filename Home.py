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

# Already logged in → go straight to dashboard
if current_user():
    st.switch_page("pages/1_Dashboard.py")

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
                st.switch_page("pages/1_Dashboard.py")

    mhtml("""<p style="color:#475569; font-size:12px; text-align:center; margin-top:12px;">
        Demo admin: <code>admin@stocksight.in</code> / <code>Admin@123!</code>
        </p>""")

# ── Register ──────────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("register_form", clear_on_submit=True):
        reg_email    = st.text_input("Email", placeholder="you@example.com", key="reg_email")
        reg_username = st.text_input("Username", placeholder="johndoe", key="reg_user")
        reg_pw       = st.text_input(
            "Password", type="password",
            placeholder="Min 8 chars, 1 uppercase, 1 digit",
            key="reg_pw",
        )
        reg_pw2   = st.text_input("Confirm Password", type="password", key="reg_pw2")
        reg_submit = st.form_submit_button(
            "Create Account", use_container_width=True, type="primary"
        )

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
                st.switch_page("pages/1_Dashboard.py")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption(
    "StockSight India · Data via Yahoo Finance · "
    "Forecasting by Prophet · Built with Streamlit"
)
