# config.py
import os
import streamlit as st
from supabase import create_client

# --- Read Supabase creds (you put them under [supabase] in secrets) ---
SUPABASE_URL = (
    st.secrets.get("supabase", {}).get("url")
    or os.getenv("SUPABASE_URL")
    or st.secrets.get("SUPABASE_URL")
)
SUPABASE_KEY = (
    st.secrets.get("supabase", {}).get("key")
    or os.getenv("SUPABASE_KEY")
    or st.secrets.get("SUPABASE_KEY")
)
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase credentials in secrets or env vars.")

# --- Trust the OS store (fixes many corporate SSL issues) ---
try:
    import truststore  # pip install truststore
    truststore.inject_into_ssl()
except Exception:
    pass

# --- Optional: use a custom corporate CA bundle if provided ---
# Put this in secrets.toml if needed:
# [ssl]
# ca_bundle_path = "certs/corporate_root.pem"
CA_BUNDLE = (
    st.secrets.get("ssl", {}).get("ca_bundle_path")
    or os.getenv("REQUESTS_CA_BUNDLE")
    or os.getenv("SSL_CERT_FILE")
)
if CA_BUNDLE:
    os.environ["REQUESTS_CA_BUNDLE"] = CA_BUNDLE
    os.environ["SSL_CERT_FILE"] = CA_BUNDLE

# --- Create the Supabase client (no http_client arg) ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)