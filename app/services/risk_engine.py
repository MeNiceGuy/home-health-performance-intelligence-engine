def calculate_risk_level(data: dict) -> str:
    s = 0
    if (data.get("readmission_rate") or 0) > 3: s += 2
    if (data.get("turnover_rate") or 0) > 25: s += 2
    if (data.get("soc_delay_days") or 0) > 2: s += 1
    if (data.get("documentation_lag_hours") or 0) > 24: s += 1
    return "High" if s >= 4 else "Moderate" if s >= 2 else "Low"

def confidence_level(data: dict) -> str:
    if data.get("cms_verified"): return "High"
    if data.get("csv_matched"): return "Medium"
    if data.get("user_reported"): return "Low"
    return "Unknown"
