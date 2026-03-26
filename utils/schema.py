# utils/schema.py
import pandas as pd

# ---------- DB <-> UI column names ----------
# Left = Supabase column name; Right = pretty UI name
DB_TO_UI = {
    "Investment_firm": "Investment firm",
    "Business_Description": "Business Description",
    "Account_Management": "Account Management",
    "Account_type": "Account type",
    "Investor_Profile": "Investor Profile",
    "AUM_M": "AUM (M€)",
    "Min_Market_Cap_M": "Min Market Cap (M€)",
    "First_Name": "First Name",
    "Last_Name": "Last Name",
    "Job_Position": "Job Position",
    "Office_Phone": "Office Phone",
    "Personal_Phone": "Personal Phone",
    "Person_Description": "Person Description",
    "Access_Research": "Access Research",
    "Sales_Corner": "Sales Corner",
    "VIP_List": "VIP List",
    "Daily_Sales_Morning": "Daily Sales Morning",
    "Payment_Research": "Payment Research",
    "Open_Trading": "Open Trading",
    "Capital_Increase": "Capital Increase",
    "Early_Look": "Early Look",
    "Market_Sondage": "Market Sondage",
    "Corner_Stone": "Corner Stone",
    # These are already nice in most schemas, but fallback works if not mapped:
    # "IPO": "IPO",
    # "Reclassement": "Reclassement",
    # "Convertible": "Convertible",
    # Plus common pass-throughs:
    "Language": "Language",
    "Activity": "Activity",
    "Website": "Website",
    "Note": "Note",
    "Country": "Country",
    "Sales": "Sales",
    "Strategy": "Strategy",
    "Thematic": "Thematic",
    "Investment_Zone": "Investment Zone",  # if your DB column has underscore
    "Universe": "Universe",
}
UI_TO_DB = {v: k for k, v in DB_TO_UI.items()}

# ---------- Canonical select options (same everywhere) ----------
SELECT_OPTIONS = {
    "Sales": ["Chloé","Louis","Maxence","Thomas","Corpo","Sarah","Trading",
              "Louis/Maxence","Louis/Thomas","Maxence/Thomas"],
    "Investor Profile": ["Long Only","Long/Short","Private Equity"],
    "Strategy": ["Value","Garp","Event Driven"],
    "Thematic": ["Generalist","Biotech","Green"],
    "Investment Zone": ["France","Italy","Europe"],
    "Universe": ["Micro","Small","Mid","SMID","Multi-cap"],
}

# ---------- Checkbox columns (use booleans in DB) ----------
TOGGLE_COLS = [
    "Access Research","Sales Corner","VIP List","Daily Sales Morning",
    "Payment Research","Open Trading","Capital Increase","IPO",
    "Reclassement","Convertible","Early Look","Market Sondage","Corner Stone"
]

# ---------- Helpers ----------
def db_to_ui(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns from DB names (underscores) to UI names (pretty)."""
    return df.rename(columns=DB_TO_UI)

def to_bool(v) -> bool:
    """Coerce legacy values ('X','1','true', etc.) to True/False."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return False
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"x","true","1","t","yes","y"}

def ensure_toggle_bools(df: pd.DataFrame) -> pd.DataFrame:
    """Make sure all toggle columns are boolean for the UI grid/forms."""
    for col in TOGGLE_COLS:
        if col not in df.columns:
            df[col] = False
        else:
            df[col] = df[col].apply(to_bool)
    return df

def uniq(df: pd.DataFrame, col: str) -> list:
    """Unique non-null values as list, or [''] if missing/empty."""
    if col not in df.columns:
        return [""]
    vals = df[col].dropna().astype(str).unique().tolist()
    return vals if len(vals) else [""]

def safe_index(options: list, current) -> int:
    """Index of current in options; 0 if not found."""
    try:
        return options.index(current if current is not None else "")
    except ValueError:
        return 0

def map_ui_updates_to_db(updates_ui: dict) -> dict:
    """Map UI keys→DB keys and coerce toggle values to booleans for Supabase."""
    payload = {}
    for k_ui, v in updates_ui.items():
        k_db = UI_TO_DB.get(k_ui, k_ui)
        if k_ui in TOGGLE_COLS:
            payload[k_db] = bool(v)
        else:
            payload[k_db] = v
    return payload