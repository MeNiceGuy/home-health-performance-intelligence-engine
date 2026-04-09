import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import jsonschema
from openai import OpenAI

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are a senior healthcare strategy consultant specializing in privately owned U.S. home health agencies operating under HHVBP reimbursement pressure.

Your job is to produce a premium consulting-style recommendation report.

Rules:
- Be practical, specific, and concise.
- Focus on operational efficiency, quality improvement, innovation adoption, and implementation feasibility.
- Do not make legal, medical, or reimbursement guarantees.
- Include estimated impact ranges where reasonable.
- Include at least one overlooked leadership insight.
- Prefer lower-cost, higher-feasibility recommendations when the agency appears resource-constrained.
- Avoid generic AI hype. Sound like an experienced operator and strategist.
- Output in clean markdown with the exact section headings requested.
"""

AGENCY_SCHEMA = {
    "type": "object",
    "properties": {
        "agency_name": {"type": "string"},
        "region": {"type": "string"},
        "agency_size": {"type": "string"},
        "ownership_type": {"type": "string", "enum": ["Privately owned", "Government", "Nonprofit"]},
        "tech_stack": {"type": "string"},
        "challenges": {"type": "string"},
        "hhvbp_concerns": {"type": "string"},
        "workforce_issues": {"type": "string"},
        "budget_posture": {"type": "string", "enum": ["lean budget", "moderate", "generous"]},
        "leadership_readiness": {"type": "string", "enum": ["low", "moderate", "high"]},
        "learning_culture": {"type": "string", "enum": ["nascent", "developing", "mature"]},
        "notes": {"type": "string"}
    },
    "required": ["agency_name", "region", "agency_size", "ownership_type", "tech_stack", "challenges", "hhvbp_concerns", "workforce_issues", "budget_posture", "leadership_readiness", "learning_culture", "notes"]
}

def build_user_prompt(data: dict) -> str:
    return dedent(f"""
    Create a premium Home Health Innovation Decision Report for the following agency profile.

    AGENCY PROFILE
    - Agency name: {data['agency_name']}
    - Region: {data['region']}
    - Agency size: {data['agency_size']}
    - Ownership type: {data['ownership_type']}
    - Current technology stack: {data['tech_stack']}
    - Primary operational challenges: {data['challenges']}
    - HHVBP / quality concerns: {data['hhvbp_concerns']}
    - Workforce issues: {data['workforce_issues']}
    - Budget posture: {data['budget_posture']}
    - Leadership readiness: {data['leadership_readiness']}
    - Learning culture maturity: {data['learning_culture']}
    - Additional notes: {data['notes']}

    REQUIRED OUTPUT
    Use exactly these headings:

    # Home Health Innovation Decision Report

    ## Executive Summary

    ## Priority Innovation Recommendations

    ## Priority Ranking

    ## 90-Day Action Plan

    ## Leadership and Learning Considerations

    ## Resource Allocation Guidance
    ## Estimated ROI and Impact Ranges
    For each recommendation include:
    - Estimated operational improvement range
    - Estimated financial or efficiency impact
    - Key assumptions

    ## Overlooked Leadership Insight
    Identify one important issue leadership may be underestimating.

    ## Client-Facing Summary
    """.strip())

def save_report(markdown_text: str, agency_name: str, requested_output: Path | None = None) -> Path:
    if requested_output:
        requested_output.parent.mkdir(parents=True, exist_ok=True)
        requested_output.write_text(markdown_text, encoding="utf-8")
        return requested_output

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name.strip()) or "agency"
    path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            agency_data = json.load(f)
        jsonschema.validate(instance=agency_data, schema=AGENCY_SCHEMA)
    except Exception as e:
        print(f"Input error: {e}", file=sys.stderr)
        sys.exit(1)

    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(agency_data)},
            ],
            temperature=0.4,
            max_tokens=1400,
        )
        output_text = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else None
    saved = save_report(output_text, agency_data["agency_name"], output_path)
    print(f"Report saved to: {saved}")

if __name__ == "__main__":
    main()