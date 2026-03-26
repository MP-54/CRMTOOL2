# byclient.py  — Clients (by firm) view with company edit dialog
import streamlit as st
import pandas as pd
import altair as alt  # kept for parity with your project (unused here)
from data.data import get_data
from config import supabase
from html import escape  # used to safely render note text
from utils.schema import (
    db_to_ui, map_ui_updates_to_db, ensure_toggle_bools, to_bool,
    SELECT_OPTIONS, TOGGLE_COLS, uniq, safe_index
)

st.set_page_config(page_title="Clients (by firm)", layout="wide")
st.title("Clients")

DEBUG = False
TABLE_NAME = "Supabase Table"  # exact Supabase table name


# ──────────────────────────────────────────────────────────────────────────────
# Supabase helpers
# ──────────────────────────────────────────────────────────────────────────────

def update_client(row_id: int, updates_ui: dict) -> bool:
    """Map UI keys → DB keys, then update a single row by id."""
    if not updates_ui:
        return True
    payload = map_ui_updates_to_db(updates_ui)
    try:
        if DEBUG:
            st.caption(f"Update id={row_id} payload:"); st.write(payload)
        supabase.table(TABLE_NAME).update(payload).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Supabase Error: {e}")
        if DEBUG:
            st.write({"payload": payload})
        return False


def update_company_fields(firm: str, website: str, description: str) -> bool:
    """Update Website & Business Description for ALL rows of a firm."""
    payload_ui = {
        "Website": website,
        "Business Description": description,
    }
    payload_db = map_ui_updates_to_db(payload_ui)
    try:
        supabase.table(TABLE_NAME).update(payload_db).eq("investment_firm", firm).execute()
        return True
    except Exception as e:
        st.error(f"❌ Supabase error updating company '{firm}': {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Load & normalize
# ──────────────────────────────────────────────────────────────────────────────

client_data = get_data()
if client_data is None or client_data.empty:
    st.error("❌ Data couldn't be loaded.")
    st.stop()
if "id" not in client_data.columns:
    st.error("❌ 'id' column is required.")
    st.stop()

# DB snake_case → UI labels; toggles → booleans
client_data = db_to_ui(client_data)
client_data = ensure_toggle_bools(client_data)


# ──────────────────────────────────────────────────────────────────────────────
# Dialogs
# ──────────────────────────────────────────────────────────────────────────────

@st.dialog("Edit company", width="large")
def show_company_dialog(firm: str):
    # Prefill with current values from your dataset
    firm_rows = client_data[client_data["Investment firm"] == firm]
    cur_site = firm_rows["Website"].dropna().astype(str).iloc[0] if not firm_rows.empty else ""
    cur_desc = firm_rows["Business Description"].dropna().astype(str).iloc[0] if not firm_rows.empty else ""

    site = st.text_input("Website", cur_site, key=f"comp_site_{firm}")
    desc = st.text_area("Description", cur_desc, height=140, key=f"comp_desc_{firm}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save", key=f"comp_save_{firm}"):
            if update_company_fields(firm, site, desc):
                # Update local dataframe for instant UI feedback
                client_data.loc[client_data["Investment firm"] == firm, "Website"] = site
                client_data.loc[client_data["Investment firm"] == firm, "Business Description"] = desc
                st.success("✅ Company info updated.")
                st.rerun()
    with c2:
        if st.button("Cancel", key=f"comp_cancel_{firm}"):
            st.rerun()


@st.dialog("Change Information", width="large")
def show_edit_dialog(idx: int):
    client = client_data.loc[idx]
    row_id = int(client["id"])

    col0_1, col0_2 = st.columns(2)
    with col0_1:
        am_opts = uniq(client_data, "Account Management")
        selected_account_management = st.selectbox(
            "Account Management",
            am_opts,
            index=safe_index(am_opts, client.get("Account Management", "")),
            key=f"am_{idx}",
        )
        at_opts = uniq(client_data, "Account type")
        selected_account_type = st.selectbox(
            "Account Type",
            at_opts,
            index=safe_index(at_opts, client.get("Account type", "")),
            key=f"accttype_{idx}",
        )
    with col0_2:
        selected_sales = st.selectbox(
            "Sales",
            SELECT_OPTIONS["Sales"],
            index=safe_index(SELECT_OPTIONS["Sales"], client.get("Sales", "")),
            key=f"sales_{idx}",
        )
        act_opts = uniq(client_data, "Activity")
        selected_activity = st.selectbox(
            "Activity",
            act_opts,
            index=safe_index(act_opts, client.get("Activity", "")),
            key=f"activity_{idx}",
        )

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        new_first = st.text_input("First Name", client.get("First Name", ""), key=f"dlg_first_{idx}")
        new_firm  = st.text_input("Investment Firm", client.get("Investment firm", ""), key=f"dlg_firm_{idx}")
    with col2:
        new_last  = st.text_input("Last Name",  client.get("Last Name", ""), key=f"dlg_last_{idx}")
        new_job_position = st.text_input("Job Position", client.get("Job Position", ""), key=f"dlg_job_{idx}")

    new_country = st.text_input("Country", client.get("Country", ""), key=f"dlg_country_{idx}")
    new_email   = st.text_input("Email",   client.get("Mail", ""),    key=f"dlg_email_{idx}")

    col3, col4 = st.columns(2)
    with col3:
        new_office_phone = st.text_input("Office Phone", client.get("Office Phone", ""), key=f"dlg_office_{idx}")
    with col4:
        new_personal_phone = st.text_input("Personal Phone", client.get("Personal Phone", ""), key=f"dlg_personal_{idx}")

    new_linkedin           = st.text_input("LinkedIn", client.get("Linkedin", ""), key=f"dlg_linkedin_{idx}")
    new_client_description = st.text_area("Description", client.get("Person Description", ""), key=f"dlg_person_desc_{idx}")
    new_latest_note        = st.text_area("Latest Note", client.get("Note", ""), key=f"dlg_note_{idx}")

    st.write("---")
    new_company_website     = st.text_input("Company Website", client.get("Website", ""), key=f"dlg_company_website_{idx}")
    new_company_description = st.text_area("Company Description", client.get("Business Description", ""), key=f"dlg_company_description_{idx}")
    st.write("---")

    # Toggles
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        selected_new_access_research   = c1.checkbox("Access Research",     value=to_bool(client.get("Access Research")),     key=f"ar_{idx}")
        selected_new_sales_corner      = c2.checkbox("Sales Corner",        value=to_bool(client.get("Sales Corner")),        key=f"sc_{idx}")
        selected_new_vip_list          = c3.checkbox("VIP List",            value=to_bool(client.get("VIP List")),            key=f"vip_{idx}")
        selected_new_sales_morning     = c4.checkbox("Daily Sales Morning", value=to_bool(client.get("Daily Sales Morning")), key=f"dsm_{idx}")

    with st.container(border=True):
        d1, d2, d3, d4 = st.columns(4)
        selected_new_payment_research = d1.checkbox("Payment Research", value=to_bool(client.get("Payment Research")), key=f"pr_{idx}")
        selected_new_open_trading     = d2.checkbox("Open Trading",     value=to_bool(client.get("Open Trading")),     key=f"ot_{idx}")
        d3.write(""); d4.write("")

    with st.container(border=True):
        e1, e2, e3, e4 = st.columns(4)
        selected_new_capital_increase = e1.checkbox("Capital Increase", value=to_bool(client.get("Capital Increase")), key=f"ci_{idx}")
        selected_new_IPO              = e2.checkbox("IPO",              value=to_bool(client.get("IPO")),              key=f"ipo_{idx}")
        selected_new_reclassement     = e3.checkbox("Reclassement",     value=to_bool(client.get("Reclassement")),     key=f"recl_{idx}")
        selected_new_convertible      = e4.checkbox("Convertible",      value=to_bool(client.get("Convertible")),      key=f"conv_{idx}")

    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        selected_new_early_look     = f1.checkbox("Early Look",     value=to_bool(client.get("Early Look")),     key=f"el_{idx}")
        selected_new_market_sondage = f2.checkbox("Market Sondage", value=to_bool(client.get("Market Sondage")), key=f"ms_{idx}")
        selected_new_corner_stone   = f3.checkbox("Corner Stone",   value=to_bool(client.get("Corner Stone")),   key=f"cs_{idx}")
        f4.write("")

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save Changes", key=f"dlg_save_{idx}"):
            updates_ui = {
                "Account Management": selected_account_management,
                "Sales": selected_sales,
                "Account type": selected_account_type,
                "Activity": selected_activity,
                "First Name": new_first,
                "Last Name": new_last,
                "Investment firm": new_firm,
                "Job Position": new_job_position,
                "Country": new_country,
                "Mail": new_email,
                "Office Phone": new_office_phone,
                "Personal Phone": new_personal_phone,
                "Linkedin": new_linkedin,
                "Person Description": new_client_description,
                "Note": new_latest_note,
                "Website": new_company_website,
                "Business Description": new_company_description,
                "Access Research": selected_new_access_research,
                "Sales Corner": selected_new_sales_corner,
                "VIP List": selected_new_vip_list,
                "Daily Sales Morning": selected_new_sales_morning,
                "Payment Research": selected_new_payment_research,
                "Open Trading": selected_new_open_trading,
                "Capital Increase": selected_new_capital_increase,
                "IPO": selected_new_IPO,
                "Reclassement": selected_new_reclassement,
                "Convertible": selected_new_convertible,
                "Early Look": selected_new_early_look,
                "Market Sondage": selected_new_market_sondage,
                "Corner Stone": selected_new_corner_stone,
            }
            if update_client(row_id, updates_ui):
                for k, v in updates_ui.items():
                    client_data.at[idx, k] = v
                st.success("✅ Informations mises à jour dans Supabase !")
                st.rerun()
    with col_cancel:
        if st.button("Cancel", key=f"dlg_cancel_{idx}"):
            st.rerun()


@st.dialog("Edit Client's info", width="large")
def show_edit_box_2(idx: int):
    client = client_data.loc[idx]
    row_id = int(client["id"])

    st.subheader(f"Edit Client's Info : {client.get('First Name','')} {client.get('Last Name','')}")

    col1, col2 = st.columns(2)
    with col1:
        new_first        = st.text_input("First Name",        client.get("First Name",""),       key=f"first_{idx}")
        new_last         = st.text_input("Last Name",         client.get("Last Name",""),        key=f"last_{idx}")
        new_job          = st.text_input("Job Position",      client.get("Job Position",""),     key=f"job_{idx}")
        new_email        = st.text_input("Email",             client.get("Mail",""),             key=f"mail_{idx}")
    with col2:
        new_office_phone = st.text_input("Office Phone",      client.get("Office Phone",""),     key=f"office_{idx}")
        new_personal     = st.text_input("Personal Phone",    client.get("Personal Phone",""),   key=f"personal_{idx}")
        new_country      = st.text_input("Country",           client.get("Country",""),          key=f"country_{idx}")
        new_min_mcap     = st.text_input("Min Market Cap (M€)", client.get("Min Market Cap (M€)", ""), key=f"mmc_{idx}")

    st.write("---")

    col3, col4, col5 = st.columns(3)
    with col3:
        acct_opts = ["", *uniq(client_data, "Account type")]
        new_acct = st.selectbox("Account Type", acct_opts, index=safe_index(acct_opts, client.get("Account type","")), key=f"acct_{idx}")
        act_opts = ["", *uniq(client_data, "Activity")]
        new_activity = st.selectbox("Activity", act_opts, index=safe_index(act_opts, client.get("Activity","")), key=f"act_{idx}")
        sales_opts = ["", *SELECT_OPTIONS["Sales"]]
        new_sales = st.selectbox("Sales", sales_opts, index=safe_index(sales_opts, client.get("Sales","")), key=f"sales2_{idx}")
    with col4:
        lang_opts = ["", *uniq(client_data, "Language")]
        new_lang = st.selectbox("Language", lang_opts, index=safe_index(lang_opts, client.get("Language","")), key=f"lang_{idx}")
        prof_opts = ["", *SELECT_OPTIONS["Investor Profile"]]
        new_profile = st.selectbox("Investor Profile", prof_opts, index=safe_index(prof_opts, client.get("Investor Profile","")), key=f"profile_{idx}")
        strat_opts = ["", *SELECT_OPTIONS["Strategy"]]
        new_strategy = st.selectbox("Strategy", strat_opts, index=safe_index(strat_opts, client.get("Strategy","")), key=f"strategy_{idx}")
    with col5:
        them_opts = ["", *SELECT_OPTIONS["Thematic"]]
        new_thematic = st.selectbox("Thematic", them_opts, index=safe_index(them_opts, client.get("Thematic","")), key=f"thematic_{idx}")
        zone_opts = ["", *SELECT_OPTIONS["Investment Zone"]]
        new_zone = st.selectbox("Investment Zone", zone_opts, index=safe_index(zone_opts, client.get("Investment Zone","")), key=f"zone_{idx}")
        uni_opts = ["", *SELECT_OPTIONS["Universe"]]
        new_universe = st.selectbox("Universe", uni_opts, index=safe_index(uni_opts, client.get("Universe","")), key=f"universe_{idx}")

    st.write("---")
    new_note = st.text_area("Note", value=client.get("Note",""), key=f"note_{idx}", height=140,
                            placeholder="Add or update a note about this client…")

    if st.button("Save Changes", key=f"save_{idx}"):
        updates_ui = {
            "First Name": new_first,
            "Last Name": new_last,
            "Job Position": new_job,
            "Mail": new_email,
            "Office Phone": new_office_phone,
            "Personal Phone": new_personal,
            "Country": new_country,
            "Min Market Cap (M€)": new_min_mcap,
            "Account type": new_acct,
            "Activity": new_activity,
            "Sales": new_sales,
            "Language": new_lang,
            "Investor Profile": new_profile,
            "Strategy": new_strategy,
            "Thematic": new_thematic,
            "Investment Zone": new_zone,
            "Universe": new_universe,
            "Note": new_note,
        }
        if update_client(row_id, updates_ui):
            for k, v in updates_ui.items():
                client_data.at[idx, k] = v
            st.success("✅ Info updated in Supabase!")
            st.rerun()


@st.dialog("Edit Client's Access", width="large")
def show_edit_box_3(idx: int):
    client = client_data.loc[idx]
    row_id = int(client["id"])
    st.subheader(f"Edit Client's Access : {client.get('First Name','')} {client.get('Last Name','')}")

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        access_research     = c1.checkbox("Access Research",      value=to_bool(client.get("Access Research")),       key=f"ar2_{idx}")
        sales_corner        = c2.checkbox("Sales Corner",         value=to_bool(client.get("Sales Corner")),          key=f"sc2_{idx}")
        vip_list            = c3.checkbox("VIP List",             value=to_bool(client.get("VIP List")),              key=f"vl2_{idx}")
        daily_sales_morning = c4.checkbox("Daily Sales Morning",  value=to_bool(client.get("Daily Sales Morning")),   key=f"dsm2_{idx}")

    with st.container(border=True):
        d1, d2, d3, d4 = st.columns(4)
        payment_research = d1.checkbox("Payment Research", value=to_bool(client.get("Payment Research")), key=f"pr2_{idx}")
        open_trading     = d2.checkbox("Open Trading",     value=to_bool(client.get("Open Trading")),     key=f"ot2_{idx}")
        d3.write(""); d4.write("")

    with st.container(border=True):
        e1, e2, e3, e4 = st.columns(4)
        capital_increase = e1.checkbox("Capital Increase", value=to_bool(client.get("Capital Increase")), key=f"ci2_{idx}")
        ipo              = e2.checkbox("IPO",              value=to_bool(client.get("IPO")),              key=f"ipo2_{idx}")
        reclassement     = e3.checkbox("Reclassement",     value=to_bool(client.get("Reclassement")),     key=f"recl2_{idx}")
        convertible      = e4.checkbox("Convertible",      value=to_bool(client.get("Convertible")),      key=f"conv2_{idx}")

    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        early_look     = f1.checkbox("Early Look",     value=to_bool(client.get("Early Look")),     key=f"el2_{idx}")
        market_sondage = f2.checkbox("Market Sondage", value=to_bool(client.get("Market Sondage")), key=f"ms2_{idx}")
        corner_stone   = f3.checkbox("Corner Stone",   value=to_bool(client.get("Corner Stone")),   key=f"cs2_{idx}")
        f4.write("")

    st.write("---")
    if st.button("Save Access", key=f"save_access_{idx}"):
        access_cols_ui = {
            "Access Research": access_research,
            "Sales Corner":    sales_corner,
            "VIP List":        vip_list,
            "Daily Sales Morning": daily_sales_morning,
            "Payment Research": payment_research,
            "Open Trading":     open_trading,
            "Capital Increase": capital_increase,
            "IPO":              ipo,
            "Reclassement":     reclassement,
            "Convertible":      convertible,
            "Early Look":       early_look,
            "Market Sondage":   market_sondage,
            "Corner Stone":     corner_stone
        }
        for k, v in access_cols_ui.items():
            client_data.at[idx, k] = v
        if update_client(row_id, access_cols_ui):
            st.success("✅ Access updated in Supabase!")
            st.rerun()

@st.dialog("Edit Company", width="large")
def show_company_dialog(firm_name: str):
    # Pull current values from the existing dataframe for this firm
    firm_df = client_data[client_data["Investment firm"] == firm_name]

    cur_web = ""
    if "Website" in firm_df.columns and not firm_df["Website"].dropna().empty:
        cur_web = str(firm_df["Website"].dropna().iloc[0])

    cur_desc = ""
    if "Business Description" in firm_df.columns and not firm_df["Business Description"].dropna().empty:
        cur_desc = str(firm_df["Business Description"].dropna().iloc[0])

    new_web  = st.text_input("Company Website", cur_web, key=f"company_web_{firm_name}")
    new_desc = st.text_area("Company Description", cur_desc, height=160, key=f"company_desc_{firm_name}")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Save", key=f"company_save_{firm_name}"):
            # Map UI -> DB, then update ALL rows for this firm in Supabase
            updates_ui = {"Website": new_web, "Business Description": new_desc}
            payload = map_ui_updates_to_db(updates_ui)
            try:
                # IMPORTANT: filter by DB column name "investment_firm"
                supabase.table(TABLE_NAME).update(payload).eq("Investment_firm", firm_name).execute()
                st.success("✅ Company info updated.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Supabase update failed: {e}")
    with c2:
        st.button("Cancel", key=f"company_cancel_{firm_name}", on_click=lambda: None)

# ──────────────────────────────────────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────────────────────────────────────

with st.container(border=True):
    col1, col2, col3 = st.columns(3, gap="small")
    investment_firm_unique = list(client_data["Investment firm"].dropna().unique()) if "Investment firm" in client_data.columns else []
    first_name_unique      = sorted(client_data["First Name"].dropna().unique().tolist()) if "First Name" in client_data.columns else []
    last_name_unique       = list(client_data["Last Name"].dropna().unique().tolist()) if "Last Name" in client_data.columns else []

    selected_investment_firm = col1.multiselect("Select Investment Firm", options=investment_firm_unique, key="investment_firm_filter")
    selected_first_name = col2.multiselect("Select First Name", options=first_name_unique, key="first_name_filter")
    selected_last_name  = col3.multiselect("Select Last Name", options=last_name_unique, key="last_name_filter")

# Only render the heavy UI once a filter is applied
has_filter = bool(selected_investment_firm or selected_first_name or selected_last_name)
if not has_filter:
    st.info("Select a firm or a person to load data.")
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Filtering
# ──────────────────────────────────────────────────────────────────────────────

filtered_data = client_data.copy()
if selected_investment_firm:
    filtered_data = filtered_data[filtered_data["Investment firm"].isin(selected_investment_firm)]
if selected_first_name:
    filtered_data = filtered_data[filtered_data["First Name"].isin(selected_first_name)]
if selected_last_name:
    filtered_data = filtered_data[filtered_data["Last Name"].isin(selected_last_name)]


# ──────────────────────────────────────────────────────────────────────────────
# Views
# ──────────────────────────────────────────────────────────────────────────────

if selected_first_name or selected_last_name:
    # Specific person view
    if len(filtered_data) == 1:
        client = filtered_data.iloc[0]
        index = filtered_data.index[0]

        if "edit_mode" not in st.session_state:
            st.session_state.edit_mode = False

        col1_0, col2_0 = st.columns([2, 1])

        if not st.session_state.edit_mode:
            # Left: info cards
            with col1_0:
                with st.container(border=True):
                    st.subheader("Client Information")

                    # badges
                    acct_type     = client.get("Account type", "") or ""
                    stat_type     = client.get("Activity", "") or ""
                    sales_type    = client.get("Sales", "") or ""
                    language_type = client.get("Language", "") or ""

                    badges = []
                    if acct_type:
                        badges.append(f":{'green' if acct_type == 'Client' else 'orange'}-badge[{acct_type}]")
                    if stat_type:
                        badges.append(f":{'green' if stat_type == 'Actif' else 'red'}-badge[{stat_type}]")
                    if sales_type:
                        badges.append(f":gray-badge[{sales_type}]")
                    if language_type:
                        badges.append(f":blue-badge[Speak: {language_type}]")
                    if badges:
                        st.markdown("  ".join(badges))

                    # grid
                    c1, c2, c3, c4, c5, c6, c7 = st.columns(7, gap="small")
                    c1.markdown("**Name**");            c1.markdown(f"{client.get('First Name','')} {client.get('Last Name','')}")
                    c2.markdown("**Firm**");            c2.markdown(f"{client.get('Investment firm','')}")
                    c3.markdown("**Job Position**");    c3.markdown(f"{client.get('Job Position','')}")
                    c4.markdown("**Country**");         c4.markdown(f"{client.get('Country','')}")
                    c5.markdown("**Email**");           c5.markdown(f"{client.get('Mail','')}")
                    c6.markdown("**Office Phone**");    c6.markdown(f"{client.get('Office Phone','')}")
                    c7.markdown("**Personal Phone**");  c7.markdown(f"{client.get('Personal Phone','')}")

                    st.write("---")
                    c8, c9, c10, c11, c12, c13 = st.columns(6)
                    c8.markdown("**Investor Profile**"); c8.markdown(f"{client.get('Investor Profile','')}")
                    c9.markdown("**Strategy**");         c9.markdown(f"{client.get('Strategy','')}")
                    c10.markdown("**Thematic**");        c10.markdown(f"{client.get('Thematic','')}")
                    c11.markdown("**Investment Zone**"); c11.markdown(f"{client.get('Investment Zone','')}")
                    c12.markdown("**Universe**");        c12.markdown(f"{client.get('Universe','')}")
                    c13.markdown("**Min Market Cap (M€)**"); c13.markdown(f"{client.get('Min Market Cap (M€)','')}")

                    st.write("---")
                    c14, c15 = st.columns(2)
                    c14.markdown("**Description**"); c14.markdown(f"{client.get('Person Description','')}")
                    c15.markdown("**LinkedIn**");    c15.markdown(f"{client.get('Linkedin','')}")

                with st.container(border=True):
                    st.subheader("Company Information")
                    x1, x2 = st.columns(2)
                    x1.markdown("**Firm**");    x1.markdown(f"{client.get('Investment firm','')}")
                    x2.markdown("**Website**"); x2.markdown(f"{client.get('Website','') or 'N/A'}")
                    st.write("---")
                    st.markdown("**Description**"); st.markdown(f"{client.get('Business Description','') or 'N/A'}")

            # Right: Access overview compact
            with col2_0:
                with st.container(border=True):
                    hL, hR = st.columns([1, 0.25])
                    with hL:
                        st.subheader("Access & Participation")
                    with hR:
                        show_off = st.checkbox("Hide tags", value=True, key="show_tags_person_v2")

                card = st.container(border=True)

                top_items = [
                    ("Access Research", to_bool(client.get("Access Research"))),
                    ("Sarah Morning",   to_bool(client.get("Sales Corner"))),
                    ("VIP List",        to_bool(client.get("VIP List"))),
                    ("Sales Morning",   to_bool(client.get("Daily Sales Morning"))),
                ]
                top_chips = []
                for label, on in top_items:
                    if on or show_off:
                        top_chips.append(f":{'green' if on else 'gray'}-badge[{label}]")
                if top_chips:
                    card.markdown(" ".join(top_chips))

                participation = [
                    ("Capital Increase", "Capital Increase"),
                    ("IPO",              "IPO"),
                    ("Reclassement",     "Reclassement"),
                    ("Convertible",      "Convertible"),
                    ("Early Look",       "Early Look"),
                    ("Market Sondage",   "Market Sondage"),
                    ("Corner Stone",     "Corner Stone"),
                ]
                part_chips = []
                for col_key, label in participation:
                    on = to_bool(client.get(col_key))
                    if on or show_off:
                        part_chips.append(f":{'green' if on else 'gray'}-badge[{label}]")
                if part_chips:
                    card.markdown(" ".join(part_chips))

                b1, b2 = card.columns([1, 0.2])
                with b2:
                    if st.button("Edit", key=f"edit_access_single_{index}"):
                        show_edit_box_3(index)

            st.write("---")
            if st.button("Edit Info"):
                show_edit_dialog(index)

    elif len(filtered_data) > 1:
        st.warning("More than one client matches the selected names. Please narrow down your selection.")
    else:
        st.info("No client matches the selected name(s).")

with st.container(border=True):
    # Determine how many distinct firms are visible in the current filtered view
    firm_names = []
    if "Investment firm" in filtered_data.columns:
        firm_names = sorted(filtered_data["Investment firm"].dropna().unique().tolist())
    single_firm = firm_names[0] if len(firm_names) == 1 else None

    # Header row: title (left) + Edit button (right)
    head_l, head_r = st.columns([6, 1])
    with head_l:
        st.subheader(", ".join(selected_investment_firm) if selected_investment_firm else (single_firm or ""))
    with head_r:
        # Show the edit button ONLY when exactly one firm is in scope
        if single_firm and st.button("Edit", key="edit_company_btn"):
            show_company_dialog(single_firm)

    # Keep the two-column layout under the header to stay aligned with the right panel
    xL, xR = st.columns([0.5, 1.5])
    with xL:
        st.markdown("**Website**")
        websites = []
        if "Website" in filtered_data.columns:
            websites = filtered_data["Website"].dropna().unique().tolist()
        st.markdown(websites[0] if websites else "N/A")
    with xR:
        st.markdown("**Description**")
        descs = []
        if "Business Description" in filtered_data.columns:
            descs = filtered_data["Business Description"].dropna().unique().tolist()
        st.markdown(descs[0] if descs else "N/A")

    st.write("---")

    # Unified headers — one row spanning both sides keeps baselines aligned
    hdrL, hdrR = st.columns([2, 1])
    with hdrL:
        st.subheader("Clients")
        h1, h2, h3, h4, h5, h6 = st.columns([0.9, 0.8, 1.3, 1, 1, 0.6])
        h1.markdown("**Client Name**")
        h2.markdown("**Job Position**")
        h3.markdown("**Email**")
        h4.markdown("**Office Number**")
        h5.markdown("**Personal Number**")
        h6.markdown("**Country**")
    with hdrR:
        st.subheader("Access & Participation")
        show_off_list = st.checkbox("Hide tags", value=True, key="show_tags_list_v3")

    # --- tiny style for the note preview chip ---
    st.markdown("""
    <style>
    .note-chip{
    margin:.4rem 0 .2rem 0;
    padding:.6rem .8rem;
    border:1px solid rgba(255,255,255,.08);
    border-radius:.6rem;
    background:rgba(255,255,255,.03);
    font-size:.92rem; line-height:1.25rem;
    white-space:pre-wrap;
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    # One loop = each person is a single row with two columns (always aligned)
    for idx, row in filtered_data.iterrows():
        rowwrap = st.container()  # no border here; borders on inner cards
        left, right = rowwrap.columns([2, 1])

        # LEFT: Person card
        with left:
            card = st.container(border=True)
            c1, c2, c3, c4, c5, c6 = card.columns([0.9, 0.8, 1.3, 1, 1, 0.6])

            c1.markdown(f"\n{row.get('First Name','')} {row.get('Last Name','')}")
            c2.markdown(f"\n{row.get('Job Position','')}")
            c3.markdown(f"\n{row.get('Mail','')}")
            c4.markdown(f"\n{row.get('Office Phone','')}")
            c5.markdown(f"\n{row.get('Personal Phone','')}")
            c6.markdown(f"\n{row.get('Country','')}")

            # badges
            badges = []
            specs = [
                ('Account type', lambda v: "green" if v == "Client" else "orange"),
                ('Activity',     lambda v: "green" if v == "Actif" else "red"),
                ('Sales',        lambda v: "blue"),
                ('Language',     lambda v: "blue"),
                ('Investor Profile', lambda v: "grey"),
                ('Strategy',     lambda v: "grey"),
                ('Thematic',     lambda v: "grey"),
                ('Investment Zone', lambda v: "grey"),
                ('Universe',     lambda v: "grey"),
                ('Min Market Cap (M€)', lambda v: "grey"),
            ]
            for colname, color_fn in specs:
                val = row.get(colname, '') or ''
                if val:
                    color = color_fn(val)
                    label = val if colname != 'Language' else f"Speak: {val}"
                    badges.append(f":{color}-badge[{label}]")
            if badges:
                card.markdown(" ".join(badges))

            # --- Latest Note preview (between badges and Edit) ---
            note_txt = (row.get("Note") or "").strip()
            if note_txt:
                # short preview chip (clamped to ~3 lines)
                card.markdown(
                    f"<div class='note-chip'><b>Latest note</b><br>{escape(note_txt)}</div>",
                    unsafe_allow_html=True
                )
                # optional full view if long
                if len(note_txt) > 220:
                    with card.expander("Show full note"):
                        st.write(note_txt)

            # Edit button stays at the very bottom of the card
            if card.button("Edit", key=f"edit_{idx}"):
                show_edit_box_2(idx)

        # RIGHT: Access card (for same person)
        with right:
            card2 = st.container(border=True)

            top_items = [
                ("Access Research", to_bool(row.get("Access Research"))),
                ("Sarah Morning",   to_bool(row.get("Sales Corner"))),
                ("VIP List",        to_bool(row.get("VIP List"))),
                ("Sales Morning",   to_bool(row.get("Daily Sales Morning"))),
            ]
            top_chips = []
            for label, on in top_items:
                if on or show_off_list:
                    top_chips.append(f":{'green' if on else 'gray'}-badge[{label}]")
            if top_chips:
                card2.markdown(" ".join(top_chips))

            participation = [
                ("Capital Increase", "Capital Increase"),
                ("IPO",              "IPO"),
                ("Reclassement",     "Reclassement"),
                ("Convertible",      "Convertible"),
                ("Early Look",       "Early Look"),
                ("Market Sondage",   "Market Sondage"),
                ("Corner Stone",     "Corner Stone"),
            ]
            part_chips = []
            for col_key, label in participation:
                on = to_bool(row.get(col_key))
                if on or show_off_list:
                    part_chips.append(f":{'green' if on else 'gray'}-badge[{label}]")
            if part_chips:
                card2.markdown(" ".join(part_chips))

            e1, e2 = card2.columns([1, 0.2])
            with e2:
                if st.button("Edit", key=f"edit_access{idx}"):
                    show_edit_box_3(idx)

    else:
        st.info("Please select a filter to view client data.")