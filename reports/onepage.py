import streamlit as st
import pandas as pd
from data.data import get_data
from config import supabase  # use the same client as in other pages

# ──────────────────────────────────────────────────────────────────────────────
# Page setup
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")

# ──────────────────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────────────────
client_data = get_data()
if client_data is None or client_data.empty:
    st.error("❌ Data could not be loaded.")
    st.stop()

# make sure we have an 'id' column for updates
if "id" not in client_data.columns:
    st.error("❌ Missing required 'id' column in Supabase table.")
    st.stop()

# initialize session state storage
if "df" not in st.session_state:
    st.session_state.df = client_data.copy()

if "editing_enabled" not in st.session_state:
    st.session_state.editing_enabled = False


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def uniq(series: pd.Series) -> list:
    vals = series.dropna().unique().tolist()
    # keep original behavior: include NaNs implicitly as blanks in table, filters get "All"
    return vals

def update_row_in_supabase(row_id: int, updates: dict) -> bool:
    """Update a single row by id in Supabase Table."""
    if not updates:
        return True
    try:
        supabase.table("Supabase Table").update(updates).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Supabase update failed for id={row_id}: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Section 2. Filters
# ──────────────────────────────────────────────────────────────────────────────
st.write("## Filters")

with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4, gap="small")
    with col4:
        container_col4 = st.container(border=True)

    # Build unique option lists from current dataset
    account_type_unique          = uniq(client_data["Account type"])
    vendeur_unique               = uniq(client_data["Sales"])
    country_unique               = uniq(client_data["Country"])
    access_research_unique       = uniq(client_data["Access Research"])
    vip_unique                   = uniq(client_data["VIP List"])
    daily_sales_morning_unique   = uniq(client_data["Daily Sales Morning"])
    payment_research_unique      = uniq(client_data["Payment Research"])
    open_trading_unique          = uniq(client_data["Open Trading"])
    account_management_unique    = uniq(client_data["Account Management"])
    investment_firm_unique       = uniq(client_data["Investment firm"])
    strategy_unique              = uniq(client_data["Strategy"])

    # Prefix with "All" where relevant
    account_type_options         = ["All"] + account_type_unique
    vendeur_options              = ["All"] + vendeur_unique
    country_options              = ["All"] + country_unique
    access_research_options      = ["All"] + access_research_unique
    vip_options                  = ["All"] + vip_unique
    daily_sales_morning_options  = ["All"] + daily_sales_morning_unique
    payment_research_options     = ["All"] + payment_research_unique
    open_trading_options         = ["All"] + open_trading_unique
    account_management_options   = ["All"] + account_management_unique
    investment_firm_options      = ["All"] + investment_firm_unique
    strategy_options             = ["All"] + strategy_unique

    # --- Create filters in the UI ---
    selected_account_types = col1.segmented_control(
        "Select Account Type",
        options=account_type_options,
        default="All",
        key="account_type_filter"
    )
    selected_account_management = col1.segmented_control(
        "Select Account Management",
        options=account_management_options,
        default="All",
        key="account_management_filter"
    )
    selected_investment_firm = col2.multiselect(
        "Select Investment Firm",
        options=investment_firm_options,
        default=["All"],
        key="investment_firm_filter"
    )
    selected_vendeurs = col2.multiselect(
        "Select Sales",
        options=vendeur_options,
        default=["All"],
        key="vendeur_filter"
    )
    selected_country = col3.multiselect(
        "Select Country",
        options=country_options,
        default=["All"],
        key="country_filter"
    )
    selected_strategy = col3.multiselect(
        "Select Strategy",
        options=strategy_options,
        default=["All"],
        key="strategy_filter"
    )

    with container_col4:
        firstcol, secondcol = st.columns(2, gap="small")
        with firstcol:
            selected_access_research = st.segmented_control(
                "Access Research",
                options=access_research_options,
                default="All",
                key="access_research_filter"
            )
            selected_vip = st.segmented_control(
                "VIP Client",
                options=vip_options,
                default="All",
                key="vip_filter"
            )
            selected_daily_sales_morning = st.segmented_control(
                "Daily Sales Morning",
                options=daily_sales_morning_options,
                default="All",
                key="daily_sales_morning_filter"
            )
        with secondcol:
            selected_payment_research = st.segmented_control(
                "Payment Research",
                options=payment_research_options,
                default="All",
                key="payment_research"
            )
            selected_open_trading = st.segmented_control(
                "Open Trading",
                options=open_trading_options,
                default="All",
                key="open_trading"
            )

    # --- Apply filter logic ---
    filtered_data = client_data.copy()

    if selected_account_types != "All":
        filtered_data = filtered_data[filtered_data["Account type"].isin([selected_account_types])]

    if selected_account_management != "All":
        filtered_data = filtered_data[filtered_data["Account Management"].isin([selected_account_management])]

    if "All" not in selected_investment_firm:
        filtered_data = filtered_data[filtered_data["Investment firm"].isin(selected_investment_firm)]

    if "All" not in selected_vendeurs:
        filtered_data = filtered_data[filtered_data["Sales"].isin(selected_vendeurs)]

    if "All" not in selected_country:
        filtered_data = filtered_data[filtered_data["Country"].isin(selected_country)]

    if "All" not in selected_strategy:
        filtered_data = filtered_data[filtered_data["Strategy"].isin(selected_strategy)]

    if selected_access_research != "All":
        filtered_data = filtered_data[filtered_data["Access Research"].isin([selected_access_research])]

    if selected_vip != "All":
        filtered_data = filtered_data[filtered_data["VIP List"].isin([selected_vip])]

    if selected_daily_sales_morning != "All":
        filtered_data = filtered_data[filtered_data["Daily Sales Morning"].isin([selected_daily_sales_morning])]

    if selected_payment_research != "All":
        # ⚠️ your original code filtered the wrong column; fixed below:
        filtered_data = filtered_data[filtered_data["Payment Research"].isin([selected_payment_research])]

    if selected_open_trading != "All":
        filtered_data = filtered_data[filtered_data["Open Trading"].isin([selected_open_trading])]

    # --- Search Engine applied on the filtered data ---
    text_search = col1.text_input("Search Engine", "", key="search_engine")
    if text_search:
        mask = filtered_data.astype(str).apply(
            lambda row: row.str.contains(text_search, case=False).any(), axis=1
        )
        filtered_data = filtered_data[mask]


# ──────────────────────────────────────────────────────────────────────────────
# SECTION 3 : Editable table
# ──────────────────────────────────────────────────────────────────────────────
edited_filtered_df = st.data_editor(
    filtered_data,
    num_rows="dynamic" if st.session_state.editing_enabled else "fixed",
    use_container_width=False,
    key="data_editor",
    height=650,
    column_config={
        "Investment firm": st.column_config.TextColumn(label="Investment Firm", help="Full Name"),
        "Account Management": st.column_config.SelectboxColumn(
            "Account Management", help="The category of the column", width="medium",
            options=account_management_unique
        ),
        "Sales": st.column_config.SelectboxColumn(
            "Sales", help="The category of the column", width="medium",
            options=vendeur_unique
        ),
        "Account type": st.column_config.SelectboxColumn(
            "Account Type", help="The Account Type of the Person", width="medium",
            options=account_type_unique
        ),
        "Strategy": st.column_config.SelectboxColumn()
    }
)

# ──────────────────────────────────────────────────────────────────────────────
# SECTION 4 : Buttons (Edit / Save)
# ──────────────────────────────────────────────────────────────────────────────
btn_col1, btn_col2, empty_col1, empty_col2, empty_col3, empty_col4, empty_col5 = st.columns(7)

with btn_col1:
    if st.button("Edit Data" if not st.session_state.editing_enabled else "Disable Editing", key="edit_toggle"):
        st.session_state.editing_enabled = not st.session_state.editing_enabled
        st.rerun()

with btn_col2:
    if st.button("Save Changes", key="save_button"):
        # We only update rows visible in the current filtered view.
        # Compare edited_filtered_df to the original filtered_data, row-by-row (by 'id')
        updates_count = 0
        failures = 0

        # Make sure 'id' is present in the edited frame (Streamlit keeps it if it was in the data)
        if "id" not in edited_filtered_df.columns:
            st.error("❌ 'id' column is required in the edited data to sync with Supabase.")
        else:
            # Align dtypes to avoid false diffs
            orig = filtered_data.copy()
            edit = edited_filtered_df.copy()

            # set index to id for easy compare
            orig = orig.set_index("id", drop=False)
            edit = edit.set_index("id", drop=False)

            common_ids = edit.index.intersection(orig.index)

            # iterate and compute changed columns per row
            for row_id in common_ids:
                before = orig.loc[row_id]
                after  = edit.loc[row_id]

                # build per-row dict of changed values
                changed = {}
                for col in edit.columns:
                    if col == "id":
                        continue
                    # Only update columns that exist in both and differ (NaNs handled)
                    if col in orig.columns:
                        b = before[col]
                        a = after[col]
                        if pd.isna(b) and pd.isna(a):
                            continue
                        if (pd.isna(b) and not pd.isna(a)) or (not pd.isna(b) and pd.isna(a)) or (a != b):
                            changed[col] = a

                if changed:
                    ok = update_row_in_supabase(int(row_id), changed)
                    if ok:
                        updates_count += 1
                        # also update session df mirror
                        st.session_state.df.loc[st.session_state.df["id"] == row_id, list(changed.keys())] = list(changed.values())
                    else:
                        failures += 1

            if failures == 0:
                st.success(f"✅ {updates_count} row(s) updated in Supabase.")
            else:
                st.warning(f"⚠️ {updates_count} row(s) updated, {failures} failed.")

        st.rerun()