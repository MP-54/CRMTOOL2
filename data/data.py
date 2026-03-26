# data/data.py
from __future__ import annotations

import pandas as pd
import streamlit as st
from typing import List, Dict, Any

from config import supabase

TABLE_NAME = "Supabase Table"
PAGE_SIZE = 1000          # fetch in 1000-row chunks
ORDER_COLUMN = "id"       # unique, indexed column

def _fetch_page(start: int, page_size: int) -> List[Dict[str, Any]]:
    """Fetch one page using inclusive PostgREST ranges."""
    end = start + page_size - 1
    # Some versions only accept desc=, older ones default to ASC if you omit it.
    req = supabase.table(TABLE_NAME).select("*")
    try:
        req = req.order(ORDER_COLUMN, desc=False)  # ascending
    except TypeError:
        req = req.order(ORDER_COLUMN)              # fallback for older client
    res = req.range(start, end).execute()
    return res.data or []

def get_data(page_size: int = PAGE_SIZE, verbose: bool = False) -> pd.DataFrame:
    """Fetch ALL rows from Supabase with pagination."""
    try:
        if verbose:
            st.info("📡 Fetching data from Supabase with pagination…")

        all_rows: List[Dict[str, Any]] = []
        start = 0
        while True:
            chunk = _fetch_page(start, page_size)
            n = len(chunk)
            if verbose:
                st.caption(f"Fetched {n} rows (range {start}-{start + page_size - 1})")
            if n == 0:
                break
            all_rows.extend(chunk)
            if n < page_size:
                break
            start += page_size

        df = pd.DataFrame(all_rows)
        if verbose:
            st.success(f"✅ Loaded {len(df)} rows from {TABLE_NAME}.")
        return df

    except Exception as e:
        st.error(f"❌ Error loading data from Supabase: {e}")
        return pd.DataFrame()