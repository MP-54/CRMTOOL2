import streamlit as st
import pandas as pd
import altair as alt
from data.data import get_data
from utils.schema import db_to_ui, SELECT_OPTIONS  # shared DB→UI mapping + options

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")

# ─── Visual palette ────────────────────────────────────────────────────────────
COLOR_CLIENT   = "#1f77b4"  # blue
COLOR_PROSPECT = "#B57EDC"  # lavender purple (replaces orange)

# ─── Helpers ──────────────────────────────────────────────────────────────────
REQUIRED_COLS = ["Sales", "Country", "Account type", "Investment firm"]

def ensure_columns(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Add any missing columns as empty strings to avoid key errors."""
    for c in cols:
        if c not in frame.columns:
            frame[c] = ""
    return frame

def safe_groupby_count(frame: pd.DataFrame, by_cols: list[str]) -> pd.DataFrame:
    """Groupby size reset, returns empty dataframe with expected columns if no rows."""
    for c in by_cols:
        if c not in frame.columns:
            frame[c] = ""
    if frame.empty:
        return pd.DataFrame(columns=[*by_cols, "Count"])
    return (
        frame
        .groupby(by_cols, dropna=False)
        .size()
        .reset_index(name="Count")
    )

def canon_account_type(s: pd.Series) -> pd.Series:
    """Normalize Account type to 'Client' / 'Prospect' (anything else → '')."""
    if s.name != "Account type":
        return s
    m = {"client": "Client", "prospect": "Prospect"}
    return (
        s.fillna("")
         .astype(str)
         .str.strip()
         .str.lower()
         .map(m)
         .fillna("")
    )

# ─── Load Data ─────────────────────────────────────────────────────────────────
df = get_data()
if df is None or df.empty:
    st.error("❌ Data could not be loaded.")
    st.stop()

# Use shared DB→UI mapping (handles underscores etc.)
df = db_to_ui(df)

# Ensure required columns exist (robust to schema differences)
df = ensure_columns(df, REQUIRED_COLS)

# Clean common text columns (trim)
for c in ["Sales", "Country", "Account type", "Investment firm"]:
    if c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

# Normalize Account type so charts group correctly
if "Account type" in df.columns:
    df["Account type"] = canon_account_type(df["Account type"])

# ─── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filters")

SALES_FILTER_OPTIONS   = ["All"] + SELECT_OPTIONS["Sales"]  # <- shared list
COUNTRY_FILTER_OPTIONS = ["All"] + sorted(
    x for x in df["Country"].dropna().unique().tolist() if x
)

sel_sales   = st.sidebar.selectbox("Sales Rep", SALES_FILTER_OPTIONS, index=0)
sel_country = st.sidebar.selectbox("Country",   COUNTRY_FILTER_OPTIONS, index=0)

# ─── Apply Filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
if sel_sales != "All":
    filtered = filtered[filtered["Sales"] == sel_sales]
if sel_country != "All":
    filtered = filtered[filtered["Country"] == sel_country]

# ─── KPI Metrics ───────────────────────────────────────────────────────────────
total_clients   = int((filtered["Account type"] == "Client").sum()) if "Account type" in filtered.columns else 0
total_prospects = int((filtered["Account type"] == "Prospect").sum()) if "Account type" in filtered.columns else 0
active_sales    = filtered["Sales"].nunique() if "Sales" in filtered.columns else 0

c1, c2, c3 = st.columns([1,1,2])
c1.metric("👥 Total Clients",   total_clients)
c2.metric("📈 Total Prospects", total_prospects)
c3.metric("📞 Active Sales Reps", active_sales)

st.markdown("---")

# ─── Chart: Clients & Prospects by Sales Rep ──────────────────────────────────
st.subheader("👥 By Sales Rep")
df_sales = safe_groupby_count(filtered, ["Sales", "Account type"])
if df_sales.empty:
    st.info("No data for the current filters.")
else:
    chart_sales = (
        alt.Chart(df_sales)
           .mark_bar()
           .encode(
               x=alt.X(
                   "Sales:N",
                   title="Sales Rep",
                   sort=alt.EncodingSortField(field="Count", op="sum", order="descending")
               ),
               y=alt.Y("Count:Q", title="Number of Accounts"),
               color=alt.Color(
                   "Account type:N",
                   title="Type",
                   scale=alt.Scale(
                       domain=["Client","Prospect"],
                       range=[COLOR_CLIENT, COLOR_PROSPECT]
                   )
               ),
               tooltip=["Sales","Account type","Count"]
           )
           .properties(height=300)
    )
    st.altair_chart(chart_sales, use_container_width=True)

# ─── Chart: Clients & Prospects by Country ────────────────────────────────────
st.subheader("🌍 By Country")
df_country = safe_groupby_count(filtered, ["Country", "Account type"])
if df_country.empty:
    st.info("No data for the current filters.")
else:
    chart_country = (
        alt.Chart(df_country)
           .mark_bar()
           .encode(
               x=alt.X(
                   "Country:N",
                   sort=alt.EncodingSortField(field="Count", op="sum", order="descending")
               ),
               y=alt.Y("Count:Q", title="Number of Accounts"),
               color=alt.Color(
                   "Account type:N",
                   title="Type",
                   scale=alt.Scale(
                       domain=["Client","Prospect"],
                       range=[COLOR_CLIENT, COLOR_PROSPECT]
                   )
               ),
               tooltip=["Country","Account type","Count"]
           )
           .properties(height=300)
    )
    st.altair_chart(chart_country, use_container_width=True)

# ─── Top 10 Firms (Clients vs. Prospects) ──────────────────────────────────────
st.subheader("🏆 Top 10 Firms with the most individuals")
top_firms = safe_groupby_count(filtered, ["Investment firm","Account type"])

if top_firms.empty:
    st.info("No data for the current filters.")
else:
    # pick top-10 overall by clients only
    top10_clients = (
        top_firms[top_firms["Account type"] == "Client"]
        .sort_values("Count", ascending=False)
        .head(10)["Investment firm"]
        .tolist()
    )
    if not top10_clients:
        st.info("No clients available to rank for the current filters.")
    else:
        top10 = top_firms[top_firms["Investment firm"].isin(top10_clients)]
        chart_firms = (
            alt.Chart(top10)
               .mark_bar()
               .encode(
                   x=alt.X("Count:Q", title="Clients / Prospects"),
                   y=alt.Y("Investment firm:N", sort=top10_clients, title="Investment Firm"),
                   color=alt.Color(
                       "Account type:N",
                       title="Type",
                       scale=alt.Scale(
                           domain=["Client","Prospect"],
                           range=[COLOR_CLIENT, COLOR_PROSPECT]
                       )
                   ),
                   tooltip=["Investment firm","Account type","Count"]
               )
               .properties(height=350)
        )
        st.altair_chart(chart_firms, use_container_width=True)

st.caption("💡 Use the filters on the left to refine this dashboard view.")
