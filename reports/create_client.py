# reports/create_client.py
import streamlit as st
import pandas as pd

from data.data import get_data
from config import supabase
from utils.schema import (
    db_to_ui, map_ui_updates_to_db, ensure_toggle_bools,
    SELECT_OPTIONS, TOGGLE_COLS, safe_index
)

st.set_page_config(page_title="Create Client", layout="wide")
st.title("Create")

TABLE_NAME = "Supabase Table"
DEBUG = False

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def load_ui_df() -> pd.DataFrame:
    df = get_data()
    if df is None or df.empty:
        return pd.DataFrame()
    df = db_to_ui(df)
    return ensure_toggle_bools(df)

ui_df = load_ui_df()

def opt_unique(col: str) -> list[str]:
    if col not in ui_df.columns:
        return []
    s = ui_df[col].dropna().astype(str).str.strip()
    s = s[s != ""]
    return sorted(s.unique().tolist(), key=lambda x: x.lower())

CREATE_KEY = "_create_client"
if CREATE_KEY not in st.session_state:
    st.session_state[CREATE_KEY] = {
        "step": 1,
        "data": {
            # Firm
            "Investment firm": "",
            "Website": "",
            "Business Description": "",
            # Person
            "First Name": "",
            "Last Name": "",
            "Job Position": "",
            "Country": "",
            "Mail": "",
            "Office Phone": "",
            "Personal Phone": "",
            "Linkedin": "",
            "Language": "",
            "Account Management": "",
            "Account type": "",
            "Sales": "",
            "Activity": "",
            # Profile selects
            "Investor Profile": "",
            "Strategy": "",
            "Thematic": "",
            "Investment Zone": "",
            "Universe": "",
            "Min Market Cap (M€)": "",
            # Access toggles
            **{c: False for c in TOGGLE_COLS},
            # Notes
            "Person Description": "",
            "Note": "",
        }
    }

def reset_create_state(close_dialog: bool = True):
    st.session_state[CREATE_KEY] = {
        "step": 1,
        "data": {
            "Investment firm": "",
            "Website": "",
            "Business Description": "",
            "First Name": "",
            "Last Name": "",
            "Job Position": "",
            "Country": "",
            "Mail": "",
            "Office Phone": "",
            "Personal Phone": "",
            "Linkedin": "",
            "Language": "",
            "Account Management": "",
            "Account type": "",
            "Sales": "",
            "Activity": "",
            "Investor Profile": "",
            "Strategy": "",
            "Thematic": "",
            "Investment Zone": "",
            "Universe": "",
            "Min Market Cap (M€)": "",
            **{c: False for c in TOGGLE_COLS},
            "Person Description": "",
            "Note": "",
        }
    }
    if close_dialog:
        st.session_state["show_create_wizard"] = False

def insert_row(payload_ui: dict) -> int | None:
    # ensure toggles are bools
    for c in TOGGLE_COLS:
        if c in payload_ui:
            payload_ui[c] = bool(payload_ui[c])
    # map UI -> DB and drop id
    payload_db = map_ui_updates_to_db(payload_ui)
    payload_db.pop("id", None)
    try:
        res = supabase.table(TABLE_NAME).insert(payload_db, returning="representation").execute()
        rows = getattr(res, "data", None) or []
        return rows[0].get("id") if rows else None
    except Exception:
        # fallback (older clients)
        try:
            res = supabase.table(TABLE_NAME).insert(payload_db).execute()
            rows = getattr(res, "data", None) or []
            return rows[0].get("id") if rows else None
        except Exception as e2:
            st.error(f"❌ Insert failed: {e2}")
            if DEBUG: st.write({"payload_db": payload_db})
            return None

# ──────────────────────────────────────────────────────────────────────────────
# Wizard Dialog
# ──────────────────────────────────────────────────────────────────────────────
@st.dialog("Create a new client", width="large")
def show_create_wizard():
    s = st.session_state[CREATE_KEY]
    step, data = s["step"], s["data"]

    # Progress chips
    steps = ["Firm", "Person", "Access", "Notes & Save"]
    chips = []
    for i, name in enumerate(steps, 1):
        color = "green" if i < step else ("blue" if i == step else "gray")
        chips.append(f":{color}-badge[{i}. {name}]")
    st.markdown(" ".join(chips))
    st.write("---")

    # STEP 1 — Firm
    if step == 1:
        c1, c2 = st.columns([1.4, 1])
        with c1:
            data["Investment firm"] = st.text_input("Investment firm *", value=data["Investment firm"])
            data["Business Description"] = st.text_area("Company description", value=data["Business Description"], height=120)
        with c2:
            data["Website"] = st.text_input("Company website", value=data["Website"])

        st.caption("Fields with * are required.")
        colb = st.columns([1, 1, 6])
        with colb[0]:
            if st.button("Cancel", key=f"{CREATE_KEY}_cancel_1"):
                reset_create_state(close_dialog=True)
                st.rerun()
        with colb[1]:
            disabled = (data["Investment firm"].strip() == "")
            if st.button("Next →", disabled=disabled, key=f"{CREATE_KEY}_next_1"):
                s["step"] = 2
                st.session_state["show_create_wizard"] = True
                st.rerun()

    # STEP 2 — Person
    elif step == 2:
        c1, c2 = st.columns(2)
        with c1:
            data["First Name"] = st.text_input("First name *", value=data["First Name"], key=f"{CREATE_KEY}_first_name")
            data["Last Name"]  = st.text_input("Last name *",  value=data["Last Name"],  key=f"{CREATE_KEY}_last_name")
            data["Job Position"] = st.text_input("Job position", value=data["Job Position"], key=f"{CREATE_KEY}_job")
            # Country as selectbox with proper index
            country_opts = [""] + opt_unique("Country")
            data["Country"] = st.selectbox(
                "Country", country_opts,
                index=safe_index(country_opts, data.get("Country", "")),
                key=f"{CREATE_KEY}_country"
            )
            data["Mail"] = st.text_input("Email", value=data["Mail"], key=f"{CREATE_KEY}_mail")
        with c2:
            data["Office Phone"] = st.text_input("Office phone", value=data["Office Phone"], key=f"{CREATE_KEY}_office_phone")
            data["Personal Phone"] = st.text_input("Personal phone", value=data["Personal Phone"], key=f"{CREATE_KEY}_personal_phone")
            data["Linkedin"] = st.text_input("LinkedIn", value=data["Linkedin"], key=f"{CREATE_KEY}_linkedin")
            lang_opts = [""] + opt_unique("Language")
            data["Language"] = st.selectbox(
                "Language", lang_opts,
                index=safe_index(lang_opts, data.get("Language", "")),
                key=f"{CREATE_KEY}_language"
            )

        st.write("---")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            opts = [""] + opt_unique("Account Management")
            data["Account Management"] = st.selectbox(
                "Account Management", opts,
                index=safe_index(opts, data.get("Account Management", "")),
                key=f"{CREATE_KEY}_acct_mgmt"
            )
        with g2:
            opts = [""] + opt_unique("Account type")
            data["Account type"] = st.selectbox(
                "Account type", opts,
                index=safe_index(opts, data.get("Account type", "")),
                key=f"{CREATE_KEY}_acct_type"
            )
        with g3:
            opts = [""] + SELECT_OPTIONS.get("Sales", [])
            data["Sales"] = st.selectbox(
                "Sales", opts,
                index=safe_index(opts, data.get("Sales", "")),
                key=f"{CREATE_KEY}_sales"
            )
        with g4:
            opts = [""] + opt_unique("Activity")
            data["Activity"] = st.selectbox(
                "Activity", opts,
                index=safe_index(opts, data.get("Activity", "")),
                key=f"{CREATE_KEY}_activity"
            )

        st.write("---")
        h1, h2, h3, h4, h5, h6 = st.columns(6)
        with h1:
            opts = [""] + SELECT_OPTIONS.get("Investor Profile", [])
            data["Investor Profile"] = st.selectbox(
                "Investor Profile", opts,
                index=safe_index(opts, data.get("Investor Profile", "")),
                key=f"{CREATE_KEY}_inv_profile"
            )
        with h2:
            opts = [""] + SELECT_OPTIONS.get("Strategy", [])
            data["Strategy"] = st.selectbox(
                "Strategy", opts,
                index=safe_index(opts, data.get("Strategy", "")),
                key=f"{CREATE_KEY}_strategy"
            )
        with h3:
            opts = [""] + SELECT_OPTIONS.get("Thematic", [])
            data["Thematic"] = st.selectbox(
                "Thematic", opts,
                index=safe_index(opts, data.get("Thematic", "")),
                key=f"{CREATE_KEY}_thematic"
            )
        with h4:
            opts = [""] + SELECT_OPTIONS.get("Investment Zone", [])
            data["Investment Zone"] = st.selectbox(
                "Investment Zone", opts,
                index=safe_index(opts, data.get("Investment Zone", "")),
                key=f"{CREATE_KEY}_inv_zone"
            )
        with h5:
            opts = [""] + SELECT_OPTIONS.get("Universe", [])
            data["Universe"] = st.selectbox(
                "Universe", opts,
                index=safe_index(opts, data.get("Universe", "")),
                key=f"{CREATE_KEY}_universe"
            )
        with h6:
            data["Min Market Cap (M€)"] = st.text_input(
                "Min Market Cap (M€)", value=data["Min Market Cap (M€)"],
                key=f"{CREATE_KEY}_min_mc"
            )

        colb = st.columns([1, 1, 1, 5])
        with colb[0]:
            if st.button("← Back", key=f"{CREATE_KEY}_back_2"):
                s["step"] = 1
                st.session_state["show_create_wizard"] = True
                st.rerun()
        with colb[1]:
            if st.button("Cancel", key=f"{CREATE_KEY}_cancel_2"):
                reset_create_state(close_dialog=True)
                st.rerun()
        with colb[2]:
            disabled = (data["First Name"].strip() == "" or data["Last Name"].strip() == "")
            if st.button("Next →", disabled=disabled, key=f"{CREATE_KEY}_next_2"):
                s["step"] = 3
                st.session_state["show_create_wizard"] = True
                st.rerun()

    # STEP 3 — Access
    elif step == 3:
        st.caption("Toggle the client’s access & participation.")
        cols = st.columns(4)
        for i, colname in enumerate(TOGGLE_COLS):
            with cols[i % 4]:
                data[colname] = st.checkbox(
                    colname,
                    value=bool(data.get(colname, False)),
                    key=f"{CREATE_KEY}_toggle_{colname}"
                )
        st.write("---")
        colb = st.columns([1, 1, 1, 5])
        with colb[0]:
            if st.button("← Back", key=f"{CREATE_KEY}_back_3"):
                s["step"] = 2
                st.session_state["show_create_wizard"] = True
                st.rerun()
        with colb[1]:
            if st.button("Cancel", key=f"{CREATE_KEY}_cancel_3"):
                reset_create_state(close_dialog=True)
                st.rerun()
        with colb[2]:
            if st.button("Next →", key=f"{CREATE_KEY}_next_3"):
                s["step"] = 4
                st.session_state["show_create_wizard"] = True
                st.rerun()

    # STEP 4 — Notes & Save
    elif step == 4:
        c1, c2 = st.columns(2)
        with c1:
            data["Person Description"] = st.text_area(
                "Person description", value=data["Person Description"], height=130, key=f"{CREATE_KEY}_person_desc"
            )
        with c2:
            data["Note"] = st.text_area("Latest note", value=data["Note"], height=130, key=f"{CREATE_KEY}_note")

        st.write("---")

        # Duplicate email hint
        dup_hint = ""
        if "Mail" in ui_df.columns and data["Mail"].strip():
            exists = ui_df["Mail"].astype(str).str.lower().eq(data["Mail"].strip().lower()).any()
            if exists:
                dup_hint = "⚠️ A client with this email already exists."
        if dup_hint:
            st.warning(dup_hint)

        colb = st.columns([1, 1, 1.3, 4.7])
        with colb[0]:
            if st.button("← Back", key=f"{CREATE_KEY}_back_4"):
                s["step"] = 3
                st.session_state["show_create_wizard"] = True
                st.rerun()
        with colb[1]:
            if st.button("Cancel", key=f"{CREATE_KEY}_cancel_4"):
                reset_create_state(close_dialog=True)
                st.rerun()
        with colb[2]:
            disabled = any(not data[k].strip() for k in ["Investment firm", "First Name", "Last Name"])
            if st.button("✅ Save", disabled=disabled, key=f"{CREATE_KEY}_save"):
                new_id = insert_row(data.copy())
                if new_id is not None:
                    st.success(f"Client created (id {new_id}) 🎉")
                    # Close wizard and reset
                    reset_create_state(close_dialog=True)
                    # Refresh UI cache for next time
                    st.session_state.pop("show_create_wizard", None)
                    st.rerun()
                else:
                    st.error("Could not create the client. Please check fields and try again.")

# ──────────────────────────────────────────────────────────────────────────────
# Page content
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("Click below to add a new client with a guided, step-by-step popup.")
cta = st.container(border=True)
c1, c2 = cta.columns([1, 4])
with c1:
    if st.button("➕ Create a client", type="primary", use_container_width=True, key=f"{CREATE_KEY}_launch"):
        st.session_state["show_create_wizard"] = True

with c2:
    st.caption("You’ll be asked about the firm, the person, their access, and any notes. Data is saved to Supabase.")

# Keep the dialog open across reruns until Cancel/Save
if st.session_state.get("show_create_wizard"):
    show_create_wizard()
