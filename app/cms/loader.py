import pandas as pd
from pathlib import Path

def load_cms_csv(path: str):
    return pd.read_csv(path)

def match_provider(df, agency_name, state=None, city=None):
    x = df.copy()
    if state and "State" in x.columns: x = x[x["State"].astype(str).str.upper() == state.upper()]
    if city and "City/Town" in x.columns: x = x[x["City/Town"].astype(str).str.upper() == city.upper()]
    name_col = next((c for c in x.columns if "Provider Name" in c or "Agency Name" in c), None)
    if not name_col: return None
    hit = x[x[name_col].astype(str).str.upper().str.contains(agency_name.upper(), na=False)]
    return None if hit.empty else hit.iloc[0].to_dict()
