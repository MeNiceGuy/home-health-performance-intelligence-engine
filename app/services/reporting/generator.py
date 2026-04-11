from pathlib import Path
from datetime import datetime

from app.services.intelligence_engine import (
    compute_risk_model,
    generate_recommendations,
    build_intelligence_summary,
)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def build_markdown_report(payload: dict):
    risk = compute_risk_model(payload)
    recs = generate_recommendations(payload, risk)
    summary = build_intelligence_summary(payload, risk, recs)

    alerts = payload.get("alerts", [])
    compliance = payload.get("compliance_findings", [])
    trends = payload.get("trend_summary", {})

    alerts_text = "\n".join(f"- {a}" for a in alerts) if alerts else "- None"
    compliance_text = "\n".join(f"- {c}" for c in compliance) if compliance else "- None"
    trends_text = "\n".join(f"- {k}: {v}" for k, v in trends.items()) if trends else "- None"

    return f"""# Boswell Consulting Group
## Home Health Performance Intelligence Report

## Executive Summary
Agency: {payload.get("agency_name")} | {payload.get("city")}, {payload.get("state")}

## Risk Analysis
- Risk Score: {risk['risk_score']}/100
- Risk Tier: {risk['risk_tier']}
- Estimated Payment Impact: {risk['payment_impact_pct']}%

## Performance Snapshot
- Star rating: {payload.get("star_rating")}
- Readmission rate: {payload.get("readmission_rate")}
- Patient satisfaction: {payload.get("patient_satisfaction")}
- OASIS timeliness: {payload.get("oasis_timeliness")}

## Strategic Intelligence
{summary}

## Recommendations
""" + "\n".join(f"- {r}" for r in recs) + f"""

## Alerts
{alerts_text}

## Compliance Findings
{compliance_text}

## Trend Summary
{trends_text}
"""

def save_markdown_report(agency_name: str, markdown: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name) or "agency"
    path = REPORTS_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(markdown, encoding="utf-8")
    return str(path)
