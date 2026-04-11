def compute_risk_model(payload: dict):
    # Extract core metrics
    star = payload.get("star_rating", 3)
    readmit = payload.get("readmission_rate", 15)
    satisfaction = payload.get("patient_satisfaction", 85)
    oasis = payload.get("oasis_timeliness", 90)

    # Normalize risk components (higher = worse)
    star_risk = (5 - star) * 15
    readmit_risk = readmit * 2
    satisfaction_risk = (100 - satisfaction) * 1.2
    oasis_risk = (100 - oasis) * 1.1

    total_risk = round(
        star_risk +
        readmit_risk +
        satisfaction_risk +
        oasis_risk
    )

    # Cap risk at 100
    total_risk = min(total_risk, 100)

    # Tier classification
    if total_risk >= 75:
        tier = "High"
    elif total_risk >= 50:
        tier = "Moderate"
    else:
        tier = "Low"

    # Payment impact (simple proxy model)
    payment_impact = round((total_risk / 100) * -5, 2)  # up to -5%

    return {
        "risk_score": total_risk,
        "risk_tier": tier,
        "payment_impact_pct": payment_impact,
    }


def generate_recommendations(payload: dict, risk: dict):
    recs = []

    if payload.get("readmission_rate", 0) > 14:
        recs.append("Implement readmission reduction protocol and follow-up scheduling.")

    if payload.get("oasis_timeliness", 100) < 92:
        recs.append("Improve OASIS documentation turnaround time.")

    if payload.get("patient_satisfaction", 100) < 90:
        recs.append("Enhance patient engagement and communication workflows.")

    if risk["risk_tier"] == "High":
        recs.append("Initiate immediate operational audit and leadership intervention.")

    if not recs:
        recs.append("Maintain current operational performance and monitor trends.")

    return recs


def build_intelligence_summary(payload: dict, risk: dict, recs: list):
    return f"""
Strategic Intelligence Summary:

Risk Level: {risk['risk_tier']} ({risk['risk_score']}/100)

Estimated Reimbursement Impact:
{risk['payment_impact_pct']}%

Primary Operational Drivers:
- Readmission pressure
- Documentation workflow
- Patient satisfaction variability

Recommended Actions:
- {' | '.join(recs)}
"""
