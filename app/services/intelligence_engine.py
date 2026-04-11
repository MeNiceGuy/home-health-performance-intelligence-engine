from app.services.cms_enrichment import enrich_with_cms

def compute_risk_model(payload: dict):
    payload = enrich_with_cms(payload)

    star = float(payload.get("star_rating", 3) or 3)
    readmit = float(payload.get("readmission_rate", 15) or 15)
    satisfaction = float(payload.get("patient_satisfaction", 85) or 85)
    oasis = float(payload.get("oasis_timeliness", 90) or 90)

    cms_star = payload.get("cms_star_rating")
    cms_readmit = payload.get("cms_readmission")

    try:
        cms_star = float(cms_star) if cms_star not in (None, "", "Not Available") else None
    except Exception:
        cms_star = None

    try:
        cms_readmit = float(cms_readmit) if cms_readmit not in (None, "", "Not Available") else None
    except Exception:
        cms_readmit = None

    star_risk = (5 - star) * 15
    readmit_risk = readmit * 2
    satisfaction_risk = (100 - satisfaction) * 1.2
    oasis_risk = (100 - oasis) * 1.1

    total_risk = round(star_risk + readmit_risk + satisfaction_risk + oasis_risk)
    total_risk = min(total_risk, 100)

    if total_risk >= 75:
        tier = "High"
    elif total_risk >= 50:
        tier = "Moderate"
    else:
        tier = "Low"

    payment_impact = round((total_risk / 100) * -5, 2)

    return {
        "risk_score": total_risk,
        "risk_tier": tier,
        "payment_impact_pct": payment_impact,
        "cms_star_rating": cms_star,
        "cms_readmission": cms_readmit,
        "cms_agency_name": payload.get("cms_agency_name"),
    }

def generate_recommendations(payload: dict, risk: dict):
    recs = []

    if float(payload.get("readmission_rate", 0) or 0) > 14:
        recs.append("Implement readmission reduction protocol and follow-up scheduling.")

    if float(payload.get("oasis_timeliness", 100) or 100) < 92:
        recs.append("Improve OASIS documentation turnaround time.")

    if float(payload.get("patient_satisfaction", 100) or 100) < 90:
        recs.append("Enhance patient engagement and communication workflows.")

    if risk["risk_tier"] == "High":
        recs.append("Initiate immediate operational audit and leadership intervention.")

    if risk.get("cms_readmission") is not None:
        recs.append("Compare internal readmission performance against matched CMS benchmark.")

    if not recs:
        recs.append("Maintain current operational performance and monitor trends.")

    return recs

def build_intelligence_summary(payload: dict, risk: dict, recs: list):
    cms_section = ""
    if risk.get("cms_agency_name"):
        cms_section = f"""
CMS Benchmark Match:
- Agency: {risk.get('cms_agency_name')}
- CMS Star Rating: {risk.get('cms_star_rating')}
- CMS Hospitalization Rate: {risk.get('cms_readmission')}
"""

    return f"""
Strategic Intelligence Summary:

Risk Level: {risk['risk_tier']} ({risk['risk_score']}/100)

Estimated Reimbursement Impact:
{risk['payment_impact_pct']}%

Primary Operational Drivers:
- Readmission pressure
- Documentation workflow
- Patient satisfaction variability
{cms_section}
Recommended Actions:
- {' | '.join(recs)}
"""
