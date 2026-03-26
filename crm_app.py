import os
import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image

# ──────────────────────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CRM App", layout="wide")

# ──────────────────────────────────────────────────────────────────────────────
# Auth config from secrets
# Expected in .streamlit/secrets.toml:
# [credentials]
#   [credentials.usernames.jdoe]
#   email = "john@doe.com"
#   name = "John Doe"
#   password = "$2b$12$..."
# [cookie]
# name = "some_name"
# key = "some_key"
# expiry_days = 30
# ──────────────────────────────────────────────────────────────────────────────
try:
    config = st.secrets.to_dict()
    credentials = config["credentials"]
    cookie_cfg = config["cookie"]
except Exception as e:
    st.error("❌ Missing or malformed auth configuration in secrets.")
    st.stop()

# Create authenticator
authenticator = stauth.Authenticate(
    credentials,
    cookie_cfg["name"],
    cookie_cfg["key"],
    cookie_cfg["expiry_days"],
)

fields = {
    "Form name": "Login",
    "Username": "Username",
    "Password": "Password",
    "Login": "Login",
}

# Render login form
authenticator.login(location="main", fields=fields)

# Get auth state from session
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

# Auth checks
if authentication_status is False:
    st.error("⚠️ Username/password is incorrect")
    st.stop()
elif authentication_status is None:
    st.warning("⚠️ Please enter your credentials")
    st.stop()

# If we reach here, user is authenticated
st.sidebar.success(f"👋 Welcome, {name}!")
authenticator.logout("Logout", "sidebar", key="logout_btn")

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar logo
# ──────────────────────────────────────────────────────────────────────────────
logo_path = os.path.join("assets", "TP_ICAP_Midcap_Logo.png")
if os.path.exists(logo_path):
    try:
        st.sidebar.image(Image.open(logo_path), use_container_width=True)
    except Exception:
        st.sidebar.warning("⚠️ Unable to load logo image file.")
else:
    st.sidebar.warning("⚠️ Logo not found. Please check assets/TP_ICAP_Midcap_Logo.png")

# ──────────────────────────────────────────────────────────────────────────────
# Navigation
# Note: This uses Streamlit's page objects API (as you had).
# ──────────────────────────────────────────────────────────────────────────────
dashboard = st.Page("reports/dashboard.py", title="Overview", icon=":material/dashboard:")
byclient  = st.Page("reports/byclient.py",  title="Client",            icon=":material/people:")
create  = st.Page("reports/create_client.py",  title="Add New Client",            icon=":material/people:")

clients_prospects = st.Page(
    "client_prospects.py",
    title="Sheet",
    icon=":material/table:",
)

help_page = st.Page(
    "Help/how_to_use.py",
    title="How to use",
    icon=":material/help:",
)

pg = st.navigation({
    "Help":          [help_page],
    "Focus":       [dashboard, byclient, create],
    "Database": [clients_prospects],
})

pg.run()

# Example run:
# streamlit run crm_app.py