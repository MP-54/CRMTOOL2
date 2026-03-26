# client_prospects.py
import pandas as pd
import streamlit as st

from data.data import get_data
from config import supabase
from utils.schema import (
    db_to_ui, map_ui_updates_to_db, ensure_toggle_bools, to_bool,
    SELECT_OPTIONS, TOGGLE_COLS, DB_TO_UI, UI_TO_DB
)

st.set_page_config(page_title="Info Sheet", layout="wide")
st.title("Info Sheet")

DEBUG = False
TABLE_NAME = "Supabase Table"

# ───────────────────────── Helpers ─────────────────────────

def _boolify_toggles_inplace(df: pd.DataFrame) -> pd.DataFrame:
    for col in TOGGLE_COLS:
        if col in df.columns:
            df[col] = df[col].map(lambda x: bool(x) if pd.notna(x) else False)
    return df

def update_row_in_supabase(row_id: int, changes_ui: dict) -> bool:
    if not changes_ui:
        return True
    for col in TOGGLE_COLS:
        if col in changes_ui:
            changes_ui[col] = bool(changes_ui[col])
    payload_db = map_ui_updates_to_db(changes_ui)
    try:
        if DEBUG:
            st.caption(f"UPDATE id={row_id}"); st.write(payload_db)
        supabase.table(TABLE_NAME).update(payload_db).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ Update failed (id={row_id}): {e}")
        return False

def insert_row_in_supabase(row: pd.Series) -> int | None:
    payload_ui = row.to_dict()
    for col in TOGGLE_COLS:
        if col in payload_ui:
            payload_ui[col] = bool(payload_ui[col])
    payload_db = map_ui_updates_to_db(payload_ui)
    payload_db.pop("id", None)
    try:
        # prefer returning representation (gives back id); fall back if not supported
        res = supabase.table(TABLE_NAME).insert(payload_db, returning="representation").execute()
        rows = getattr(res, "data", None) or []
        return rows[0].get("id") if rows else None
    except Exception:
        try:
            res = supabase.table(TABLE_NAME).insert(payload_db).execute()
            rows = getattr(res, "data", None) or []
            return rows[0].get("id") if rows else None
        except Exception as e2:
            st.error(f"❌ Insert failed: {e2}")
            if DEBUG: st.write({"payload": payload_db})
            return None

def delete_rows_in_supabase(ids: list[int]) -> int:
    if not ids:
        return 0
    deleted = 0
    # chunk to avoid URL length/timeouts
    for i in range(0, len(ids), 800):
        batch = list(map(int, ids[i:i+800]))
        try:
            supabase.table(TABLE_NAME).delete().in_("id", batch).execute()
            deleted += len(batch)
        except Exception as e:
            st.error(f"❌ Delete failed for batch {i//800+1}: {e}")
            break
    return deleted

def load_master_df() -> pd.DataFrame:
    df = get_data()
    if df is None or df.empty:
        return pd.DataFrame()
    df = db_to_ui(df)
    df = ensure_toggle_bools(df)
    return df

def opts_from_df(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    s = df[col].dropna().astype(str).str.strip()
    s = s[s != ""]
    vals = sorted(s.unique().tolist(), key=lambda x: x.lower())
    return vals

def safe_sorted_all_opt(vals: list) -> list:
    cleaned = [str(v).strip() for v in vals if pd.notna(v) and str(v).strip() != ""]
    return ["All"] + sorted(cleaned, key=lambda x: x.lower())

# ───────────── Session state: data + editor mode ─────────────

if "master_df" not in st.session_state:
    st.session_state.master_df = load_master_df()

if "editing_enabled" not in st.session_state:
    st.session_state.editing_enabled = False

if "grid_version" not in st.session_state:
    st.session_state.grid_version = 0

def toggle_editing():
    st.session_state.editing_enabled = not st.session_state.editing_enabled
    st.session_state.grid_version += 1  # force grid rebuild

master_df: pd.DataFrame = st.session_state.master_df.copy()
if master_df.empty or "id" not in master_df.columns:
    st.error("❌ Failed to load data or missing 'id' column."); st.stop()

# ───────────────────────── Top controls ─────────────────────────

tc1, tc2 = st.columns([1, 3])
with tc1:
    if st.button("🔄 Reload from Supabase"):
        st.session_state.master_df = load_master_df()
        st.success("✅ Reloaded.")
        st.rerun()
with tc2:
    st.caption("Tip: delete rows directly in the grid while Editing is ON, then click Save.")

# ───────────────────────── Filters ─────────────────────────

with st.container(border=True):
    c1, c2, c3, c4, c5, c6 = st.columns(6, gap="small")

    def opts(col):
        vals = master_df[col].unique().tolist() if col in master_df.columns else []
        return safe_sorted_all_opt(vals)

    acct_type_opts = opts("Account type")
    acct_mgmt_opts = opts("Account Management")
    firm_opts      = opts("Investment firm")
    sales_opts     = opts("Sales")
    country_opts   = opts("Country")
    strat_opts     = opts("Strategy")

    sel_acct_type = c1.selectbox("Account Type", acct_type_opts)
    sel_acct_mgmt = c2.selectbox("Account Management", acct_mgmt_opts)
    sel_firm      = c3.multiselect("Investment Firm", firm_opts, default=["All"])
    sel_sales     = c4.multiselect("Sales", sales_opts, default=["All"])
    sel_country   = c5.multiselect("Country", country_opts, default=["All"])
    sel_strategy  = c6.multiselect("Strategy", strat_opts, default=["All"])

filtered_data = master_df.copy()
if sel_acct_type != "All":
    filtered_data = filtered_data[filtered_data["Account type"] == sel_acct_type]
if sel_acct_mgmt != "All":
    filtered_data = filtered_data[filtered_data["Account Management"] == sel_acct_mgmt]
if "All" not in sel_firm:
    filtered_data = filtered_data[filtered_data["Investment firm"].isin(sel_firm)]
if "All" not in sel_sales:
    filtered_data = filtered_data[filtered_data["Sales"].isin(sel_sales)]
if "All" not in sel_country:
    filtered_data = filtered_data[filtered_data["Country"].isin(sel_country)]
if "All" not in sel_strategy:
    filtered_data = filtered_data[filtered_data["Strategy"].isin(sel_strategy)]

# Toggle filters
st.markdown("### Show only rows with:")
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    ar  = st.checkbox("Access Research")
    sc  = st.checkbox("Sales Corner")
    vip = st.checkbox("VIP List")
with col_b:
    dsm = st.checkbox("Daily Sales Morning")
    pr  = st.checkbox("Payment Research")
    ot  = st.checkbox("Open Trading")
with col_c:
    ci  = st.checkbox("Capital Increase")
    ipo = st.checkbox("IPO")
    rc  = st.checkbox("Reclassement")
with col_d:
    cv  = st.checkbox("Convertible")
    el  = st.checkbox("Early Look")
with col_e:
    ms  = st.checkbox("Market Sondage")
    cs  = st.checkbox("Corner Stone")

filtered_data = ensure_toggle_bools(filtered_data)
if ar:  filtered_data = filtered_data[filtered_data["Access Research"]]
if sc:  filtered_data = filtered_data[filtered_data["Sales Corner"]]
if vip: filtered_data = filtered_data[filtered_data["VIP List"]]
if dsm: filtered_data = filtered_data[filtered_data["Daily Sales Morning"]]
if pr:  filtered_data = filtered_data[filtered_data["Payment Research"]]
if ot:  filtered_data = filtered_data[filtered_data["Open Trading"]]
if ci:  filtered_data = filtered_data[filtered_data["Capital Increase"]]
if ipo: filtered_data = filtered_data[filtered_data["IPO"]]
if rc:  filtered_data = filtered_data[filtered_data["Reclassement"]]
if cv:  filtered_data = filtered_data[filtered_data["Convertible"]]
if el:  filtered_data = filtered_data[filtered_data["Early Look"]]
if ms:  filtered_data = filtered_data[filtered_data["Market Sondage"]]
if cs:  filtered_data = filtered_data[filtered_data["Corner Stone"]]

# Center toggle columns
css = "\n".join([f"""
th[data-field="{col}"], td[data-field="{col}"] {{
  display:flex!important; justify-content:center!important;
}}
""" for col in TOGGLE_COLS])
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Grid columns
col_config = {
    "id": st.column_config.TextColumn("id", disabled=True, width="small"),
    "Investment firm": st.column_config.TextColumn("Investment firm"),
    "Account Management": st.column_config.SelectboxColumn(
        "Account Management", options=[""] + opts_from_df(master_df, "Account Management")
    ),
    "Sales": st.column_config.SelectboxColumn("Sales", options=[""] + SELECT_OPTIONS["Sales"]),
    "Account type": st.column_config.SelectboxColumn(
        "Account type", options=[""] + opts_from_df(master_df, "Account type")
    ),
    "Investor Profile": st.column_config.SelectboxColumn(
        "Investor Profile", options=[""] + SELECT_OPTIONS["Investor Profile"]
    ),
    "Strategy": st.column_config.SelectboxColumn(
        "Strategy", options=[""] + SELECT_OPTIONS["Strategy"]
    ),
    "Thematic": st.column_config.SelectboxColumn(
        "Thematic", options=[""] + SELECT_OPTIONS["Thematic"]
    ),
    "Investment Zone": st.column_config.SelectboxColumn(
        "Investment Zone", options=[""] + SELECT_OPTIONS["Investment Zone"]
    ),
    "Universe": st.column_config.SelectboxColumn(
        "Universe", options=[""] + SELECT_OPTIONS["Universe"]
    ),
}
col_config.update({col: st.column_config.CheckboxColumn(col, width="small") for col in TOGGLE_COLS})

# Editor (versioned key + disabled when OFF)
GRID_KEY = f"data_editor_{st.session_state.grid_version}"
edited = st.data_editor(
    filtered_data,
    key=GRID_KEY,
    disabled=not st.session_state.editing_enabled,
    num_rows="dynamic" if st.session_state.editing_enabled else "fixed",
    height=600,
    use_container_width=False,
    column_config=col_config,
)

# ───────────────────── Bottom controls + Save ─────────────────────

st.write("")
cL, cM, cR = st.columns([1.6, 1.6, 3.2])
with cL:
    st.button("✏️ Enable / Disable Editing", on_click=toggle_editing)
with cM:
    st.markdown(f"**Status:** {'🟢 Editing ON' if st.session_state.editing_enabled else '🔴 Editing OFF'}")
with cR:
    if st.button("💾 Save to Supabase"):
        if "id" not in edited.columns:
            st.error("❌ 'id' column is required.")
        else:
            before = filtered_data.copy()
            after  = edited.copy()
            _boolify_toggles_inplace(after)

            # map ids for comparison
            try:
                before_ids = pd.to_numeric(before["id"], errors="coerce")
                after_ids  = pd.to_numeric(after["id"], errors="coerce")
            except Exception:
                before_ids = before["id"]
                after_ids  = after["id"]

            vb = before.set_index("id", drop=False)
            va = after.set_index("id", drop=False)

            updated = inserted = deleted = failed = 0

            # --- Updates (ids that exist in both)
            existing_ids = [rid for rid in vb.index.tolist() if pd.notna(rid) and rid in va.index]
            for rid in existing_ids:
                try:
                    rid_int = int(rid)
                except Exception:
                    continue
                brow, arow = vb.loc[rid], va.loc[rid]
                changes_ui = {}
                for col in after.columns:
                    if col == "id" or col not in before.columns:
                        continue
                    b, a = brow[col], arow[col]
                    same = (pd.isna(b) and pd.isna(a)) or (b == a)
                    if not same:
                        changes_ui[col] = a
                if changes_ui:
                    if update_row_in_supabase(rid_int, changes_ui):
                        updated += 1
                        for k_ui, v_ui in changes_ui.items():
                            st.session_state.master_df.loc[st.session_state.master_df["id"] == rid_int, k_ui] = v_ui
                    else:
                        failed += 1

            # --- Inserts (rows with no id)
            new_rows_df = after[after["id"].isna()].copy()
            for _, new_row in new_rows_df.iterrows():
                new_id = insert_row_in_supabase(new_row)
                if new_id is not None:
                    inserted += 1
                else:
                    failed += 1

            # --- Deletes (ids present before but missing after)
            before_id_set = set(x for x in vb.index.tolist() if pd.notna(x))
            after_id_set  = set(x for x in va.index.tolist() if pd.notna(x))
            to_delete_ids = sorted(list(before_id_set - after_id_set))
            if to_delete_ids:
                deleted += delete_rows_in_supabase([int(x) for x in to_delete_ids])

            # Feedback
            if failed == 0:
                st.success(f"✅ {updated} updated, {inserted} inserted, {deleted} deleted.")
            else:
                st.warning(f"⚠️ {updated} updated, {inserted} inserted, {deleted} deleted, {failed} failed.")

            # Always refresh after writes
            st.session_state.master_df = load_master_df()
            st.rerun()
