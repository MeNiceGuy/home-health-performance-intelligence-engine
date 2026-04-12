# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from pdf_generator import md_to_pdf
from services.compliance import evaluate_compliance_risks
from services.scoring_engine import calculate_metric_score, generate_alerts
from services.trends import build_measure_trends

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are a senior healthcare strategy consultant.
Create executive-ready reports for home health agencies.
Separate facts, benchmarks, interpretations, and recommendations.
Never invent CMS values. If a metric is Not Provided, say so.
"""

AGENCY_SCHEMA = {
    "type": "object",
    "properties": {
        "agency_name": {"type": "string"},
        "state": {"type": "string"},
        "city": {"type": "string"},
        "ownership_type": {"type": "string"},
        "avg_monthly_patients": {"type": ["integer", "number", "null"]},
        "clinicians_total": {"type": ["integer", "number", "null"]},
        "star_rating": {"type": ["number", "null"]},
        "readmission_rate": {"type": ["number", "null"]},
        "patient_satisfaction": {"type": ["number", "null"]},
        "oasis_timeliness": {"type": ["number", "null"]},
        "soc_delay_days": {"type": ["number", "null"]},
        "visit_completion_rate": {"type": ["number", "null"]},
        "documentation_lag_hours": {"type": ["number", "null"]},
        "turnover_rate": {"type": ["number", "null"]},
        "open_positions": {"type": ["integer", "number", "null"]},
        "visits_per_clinician_week": {"type": ["number", "null"]},
        "ehr_vendor": {"type": "string"},
        "evv_present": {"type": "boolean"},
        "scheduling_software": {"type": "string"},
        "telehealth_present": {"type": "boolean"},
        "automation_present": {"type": "boolean"},
        "monthly_revenue_range": {"type": "string"},
        "cost_pressure_level": {"type": "string"},
        "improvement_budget": {"type": "string"},
        "leadership_readiness": {"type": "string"},
        "change_resistance": {"type": "string"},
        "training_infrastructure": {"type": "string"},
        "pain_points": {"type": "array", "items": {"type": "string"}},
        "cms_context": {"type": "object"},
        "scorecard": {"type": "object"},
        "notes": {"type": "string"},
        "monthly_series": {"type": "array"},
    },
    "required": [
        "agency_name", "state", "city", "ownership_type", "ehr_vendor", "evv_present",
        "scheduling_software", "telehealth_present", "automation_present", "monthly_revenue_range",
        "cost_pressure_level", "improvement_budget", "leadership_readiness", "change_resistance",
        "training_infrastructure", "pain_points", "cms_context", "scorecard", "notes"
    ],
}


def fmt(value: Any, suffix: str = "") -> str:
    if value is None:
        return "Not Provided"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}{suffix}"



def build_user_prompt(data: dict[str, Any]) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    scorecard = data["scorecard"]
    cms = data["cms_context"]
    compliance = data.get("compliance_findings", [])
    alerts = data.get("alerts", [])
    trends = data.get("trend_summary", {})
    pain_points = ", ".join(data.get("pain_points", [])) if data.get("pain_points") else "None listed"
    return f"""
Prepared date: {today}
Agency: {data['agency_name']} | {data['city']}, {data['state']}
Ownership: {data['ownership_type']}
Patients: {fmt(data.get('avg_monthly_patients'))}
Clinicians: {fmt(data.get('clinicians_total'))}

Operational metrics:
- Star rating: {fmt(data.get('star_rating'))}
- Readmission rate: {fmt(data.get('readmission_rate'), '%')}
- Patient satisfaction: {fmt(data.get('patient_satisfaction'), '%')}
- OASIS timeliness: {fmt(data.get('oasis_timeliness'), '%')}
- Start-of-care delay: {fmt(data.get('soc_delay_days'), ' days')}
- Visit completion rate: {fmt(data.get('visit_completion_rate'), '%')}
- Documentation lag: {fmt(data.get('documentation_lag_hours'), ' hours')}
- Turnover rate: {fmt(data.get('turnover_rate'), '%')}

Technology + finance:
- EHR: {data['ehr_vendor']}
- EVV: {data['evv_present']}
- Scheduling software: {data['scheduling_software']}
- Telehealth: {data['telehealth_present']}
- Automation: {data['automation_present']}
- Revenue range: {data['monthly_revenue_range']}
- Cost pressure: {data['cost_pressure_level']}
- Improvement budget: {data['improvement_budget']}

Execution conditions:
- Leadership readiness: {data['leadership_readiness']}
- Change resistance: {data['change_resistance']}
- Training infrastructure: {data['training_infrastructure']}
- Pain points: {pain_points}

CMS context:
- Match confidence: {cms.get('agency_match_confidence', 'Not Provided')}
- Confidence level: {cms.get('confidence_level', 'Not Provided')}
- Match score: {cms.get('match_score', 'Not Provided')}
- Verified metrics: {json.dumps(cms.get('verified_metrics', {}), ensure_ascii=False)}
- State benchmarks: {json.dumps(cms.get('state_benchmarks', {}), ensure_ascii=False)}
- CMS notes: {cms.get('notes', 'None')}

Scorecard:
- Total score: {scorecard['total_score']}/100
- Tier: {scorecard['tier']}
- Dominant priority: {scorecard['dominant_priority']}
- Estimated payment impact: {scorecard.get('estimated_payment_impact_pct', 0)}%
- Benchmark delta: {json.dumps(scorecard.get('benchmark_delta', {}), ensure_ascii=False)}
- Deductions: {json.dumps(scorecard['deductions'], ensure_ascii=False)}

Compliance findings: {json.dumps(compliance, ensure_ascii=False)}
Alerts: {json.dumps(alerts, ensure_ascii=False)}
Trend summary: {json.dumps(trends, ensure_ascii=False)}
Notes: {data.get('notes', '')}

Required headings:
# Home Health Performance Intelligence Report
## Data Transparency Notice

Matched Data Source:
- Uploaded Provider CSV
- Confidence Level: {cms.get('confidence_level','Unknown')}

## Executive Summary
## Performance Snapshot
## Benchmarking and Peer Position
## Compliance and Workflow Risks
## Metric-Based Findings
## Priority Innovation Recommendations
## Priority Ranking
## 90-Day Action Plan
## Leadership and Change Management Considerations
## Resource Allocation Guidance
## Estimated ROI and Impact Ranges
## Client-Facing Summary
""".strip()



def build_fallback_markdown(data: dict[str, Any]) -> str:
    s = data["scorecard"]
    findings = data.get("compliance_findings", [])
    alerts = data.get("alerts", [])
    trends = data.get("trend_summary", {})
    benchmark = s.get("benchmark_delta", {})
    recs = [
        {
            "name": "Documentation Discipline Sprint",
            "fit": "Best when documentation lag, OASIS timing, or visit completion are under pressure.",
            "trigger": "documentation lag, OASIS timeliness, visit completion rate",
            "impact": "Faster chart closure, tighter billing cycle, better survey readiness.",
            "hhvbp": "Supports timeliness and care coordination performance.",
            "cost": "Low",
            "risk": "Low",
            "horizon": "30 days",
            "score": 9 if data.get("documentation_lag_hours", 0) and data.get("documentation_lag_hours", 0) > 24 else 6,
        },
        {
            "name": "Referral-to-Start-of-Care Workflow Redesign",
            "fit": "Best when SOC delays, readmissions, or capacity bottlenecks are visible.",
            "trigger": "start-of-care delay, readmission rate, open positions",
            "impact": "Improves intake responsiveness and reduces avoidable care delays.",
            "hhvbp": "Supports access, quality performance, and potential payment protection.",
            "cost": "Medium",
            "risk": "Medium",
            "horizon": "60-90 days",
            "score": 8,
        },
        {
            "name": "Manager Coaching and Learning Cadence",
            "fit": "Best when leadership readiness is moderate and change resistance is present.",
            "trigger": "leadership readiness, training infrastructure, turnover",
            "impact": "Improves execution consistency and change adoption.",
            "hhvbp": "Builds operational capability to sustain performance gains.",
            "cost": "Low",
            "risk": "Low",
            "horizon": "3-6 months",
            "score": 7,
        },
    ]
    recs = sorted(recs, key=lambda x: x["score"], reverse=True)
    bullet_recs = "\n".join(
        [f"### {r['name']}\n- Why it fits: {r['fit']}\n- Trigger metrics: {r['trigger']}\n- Expected operational impact: {r['impact']}\n- Expected quality / HHVBP impact: {r['hhvbp']}\n- Cost level: {r['cost']}\n- Risk level: {r['risk']}\n- Time horizon: {r['horizon']}\n- Decision score: {r['score']}/10" for r in recs]
    )
    alert_lines = "\n".join([f"- {a['severity'].upper()}: {a['alert']}" for a in alerts]) or "- No immediate alerts generated."
    compliance_lines = "\n".join([f"- {f['compliance_flag']} ({f['severity']}): {f['issue']} Recommendation: {f['recommendation']}" for f in findings])
    trend_lines = "\n".join([f"- {k}: {v['trend']} (forecast next: {v['forecast_next']})" for k, v in trends.items()]) or "- Trend data Not Provided."
    return f"""# Home Health Performance Intelligence Report

## Data Transparency Notice

Matched Data Source:
- Uploaded Provider CSV
- Confidence Level: {cms.get('confidence_level','Unknown')}

Facts in this report are based on the agency intake file and any CMS values returned during lookup. CMS verified metrics and benchmark excerpts are shown in the CMS context field. Interpretive statements and recommendations are generated from the provided metrics and scoring logic.

## Executive Summary
{s['tier']} performance profile with a total score of {s['total_score']}/100. Dominant priority: {s['dominant_priority']} Estimated payment impact is {s.get('estimated_payment_impact_pct', 0)}%.

## Performance Snapshot
- Total score: {s['total_score']}/100
- Tier: {s['tier']}
- Dominant priority: {s['dominant_priority']}
- Peer rank hint: {s.get('peer_rank_hint', 'Not Provided')}
- Estimated payment impact: {s.get('estimated_payment_impact_pct', 0)}%

## Benchmarking and Peer Position
- Star rating delta vs benchmark: {benchmark.get('star_rating_delta')}
- Readmission delta vs benchmark: {benchmark.get('readmission_delta')}
- Patient satisfaction delta vs benchmark: {benchmark.get('patient_satisfaction_delta')}

## Compliance and Workflow Risks
{compliance_lines}

### Alerts
{alert_lines}

### Trends
{trend_lines}

## Metric-Based Findings
- Star rating: {fmt(data.get('star_rating'))}
- Readmission rate: {fmt(data.get('readmission_rate'), '%')}
- Patient satisfaction: {fmt(data.get('patient_satisfaction'), '%')}
- OASIS timeliness: {fmt(data.get('oasis_timeliness'), '%')}
- Start-of-care delay: {fmt(data.get('soc_delay_days'), ' days')}
- Documentation lag: {fmt(data.get('documentation_lag_hours'), ' hours')}
- Visit completion rate: {fmt(data.get('visit_completion_rate'), '%')}

## Priority Innovation Recommendations
{bullet_recs}

## Priority Ranking
1. {recs[0]['name']} â€” Highest near-term return based on current operational pressure.
2. {recs[1]['name']} â€” Important structural improvement with medium implementation effort.
3. {recs[2]['name']} â€” Capability-building move that helps sustain results.

## 90-Day Action Plan
- Days 1-30: Confirm baseline metrics, assign workflow owners, and launch highest-priority corrective sprint.
- Days 31-60: Measure early movement, coach managers, and tighten documentation and referral controls.
- Days 61-90: Re-score the agency, compare against benchmark movement, and decide whether to scale automation or staffing interventions.

## Leadership and Change Management Considerations
Leadership readiness and change resistance should determine rollout speed. Start with low-friction workflow changes, publish weekly scorecards, and assign one accountable leader for each priority area.

## Resource Allocation Guidance
Fund first: frontline workflow discipline and manager coaching. Delay second: broad automation purchases until process reliability improves. Avoid now: large platform changes without clear baseline improvement targets.

## Estimated ROI and Impact Ranges
- Documentation Discipline Sprint: 5-15% reduction in lag-related rework, modest billing cycle acceleration.
- Referral-to-Start-of-Care Workflow Redesign: 5-12% improvement in access and timely initiation discipline if staffing constraints are managed.
- Manager Coaching and Learning Cadence: 3-8% improvement in execution consistency and change adoption over one to two quarters.

## Client-Facing Summary
This agency should focus first on stabilizing the operational metrics that most affect reimbursement risk and execution reliability. The strongest near-term value will come from tighter documentation, faster start-of-care execution, and clearer manager accountability before pursuing broader technology expansion.
"""



def save_report(markdown_text: str, agency_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name.strip()) or "agency"
    path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path



def main() -> None:
    parser = argparse.ArgumentParser(description="Home Health Performance Intelligence Engine")
    parser.add_argument("-i", "--input", required=True, help="Path to agency JSON")
    parser.add_argument("-o", "--output", help="Optional markdown output path")
    args = parser.parse_args()
    try:
        agency_data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        jsonschema.validate(instance=agency_data, schema=AGENCY_SCHEMA)
    except Exception as exc:
        print(f"Input error: {exc}")
        sys.exit(1)

    agency_data["scorecard"] = calculate_metric_score(agency_data)
    agency_data["compliance_findings"] = evaluate_compliance_risks(agency_data)
    agency_data["trend_summary"] = build_measure_trends(agency_data)
    agency_data["alerts"] = generate_alerts(agency_data["scorecard"], agency_data["compliance_findings"], agency_data["trend_summary"])

    output_text: str
    if os.getenv("OPENAI_API_KEY") and OpenAI is not None:
        try:
            client = OpenAI()
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(agency_data)},
                ],
                temperature=0.3,
                max_tokens=2200,
            )
            output_text = response.choices[0].message.content.strip()
        except Exception as exc:
            print(f"API call failed, using fallback report builder: {exc}")
            output_text = build_fallback_markdown(agency_data)
    else:
        output_text = build_fallback_markdown(agency_data)

    output_path = Path(args.output) if args.output else save_report(output_text, agency_data["agency_name"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"Markdown report saved to: {output_path}")
    try:
        pdf_path = output_path.with_suffix(".pdf")
        md_to_pdf(output_text, pdf_path)
        print(f"PDF report saved to: {pdf_path}")
    except Exception as exc:
        print(f"PDF generation failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()



