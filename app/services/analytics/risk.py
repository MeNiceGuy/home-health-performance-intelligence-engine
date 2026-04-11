def calculate_risk_summary(payload: dict) -> dict:
    star = payload.get("star_rating") or 0
    readmit = payload.get("readmission_rate") or 0
    satisfaction = payload.get("patient_satisfaction") or 0
    oasis = payload.get("oasis_timeliness") or 0
    doc_lag = payload.get("documentation_lag_hours") or 0
    turnover = payload.get("turnover_rate") or 0

    risk_points = 0

    if star and star < 3.0:
        risk_points += 25
    elif star and star < 4.0:
        risk_points += 12

    if readmit and readmit >= 20:
        risk_points += 20
    elif readmit and readmit >= 15:
        risk_points += 10

    if satisfaction and satisfaction < 80:
        risk_points += 15
    elif satisfaction and satisfaction < 90:
        risk_points += 8

    if oasis and oasis < 85:
        risk_points += 15
    elif oasis and oasis < 92:
        risk_points += 8

    if doc_lag and doc_lag >= 48:
        risk_points += 15
    elif doc_lag and doc_lag >= 24:
        risk_points += 8

    if turnover and turnover >= 30:
        risk_points += 10
    elif turnover and turnover >= 20:
        risk_points += 5

    risk_score = min(risk_points, 100)

    if risk_score >= 60:
        tier = "High"
    elif risk_score >= 30:
        tier = "Moderate"
    else:
        tier = "Low"

    estimated_payment_impact = round(-(risk_score / 100) * 5, 2)

    return {
        "risk_score": risk_score,
        "risk_tier": tier,
        "estimated_payment_impact_pct": estimated_payment_impact,
    }

def build_dashboard_summary(payload: dict) -> dict:
    scorecard = payload.get("scorecard", {})
    risk = calculate_risk_summary(payload)
    return {
        "agency_name": payload.get("agency_name"),
        "location": f"{payload.get('city','')}, {payload.get('state','')}".strip(", "),
        "scorecard": scorecard,
        "risk": risk,
        "alerts": payload.get("alerts", []),
        "compliance_findings": payload.get("compliance_findings", []),
        "trend_summary": payload.get("trend_summary", {}),
        "cms_context": payload.get("cms_context", {}),
    }
