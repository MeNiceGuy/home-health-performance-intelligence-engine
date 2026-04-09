import os
import sys
from datetime import datetime
from pathlib import Path
from textwrap import dedent

try:
    from openai import OpenAI
except ImportError:
    print("The 'openai' package is not installed. Run: python -m pip install --user openai")
    sys.exit(1)

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are a senior healthcare strategy consultant specializing in privately owned U.S. home health agencies operating under HHVBP reimbursement pressure.

Your job is to produce a premium consulting-style recommendation report.

Rules:
- Be practical, specific, and concise.
- Focus on operational efficiency, quality improvement, innovation adoption, and implementation feasibility.
- Do not make legal, medical, or reimbursement guarantees.
- When estimating impact, present directional estimates and explain assumptions.
- Prefer lower-cost, higher-feasibility recommendations when the agency appears resource-constrained.
- Avoid generic AI hype. Sound like an experienced operator and strategist.
- Output in clean markdown with the exact section headings requested.
"""

def ask(prompt_text: str, default: str = "", choices=None) -> str:
    """Prompt user with optional default and choices for validation."""
    while True:
        prompt_suffix = f" [{default}]" if default else ""
        if choices:
            choices_str = "/".join(str(c) for c in choices)
            prompt_suffix += f" (options: {choices_str})"
        raw = input(f"{prompt_text}{prompt_suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if choices and raw not in choices:
            print(f"Invalid input. Please enter one of: {choices_str}")
            continue
        if raw:
            return raw
        print("Input cannot be empty.")



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
    Provide a tight summary of the agency situation and your overall recommendation.

    ## Priority Innovation Recommendations
    Give exactly 3 recommendations. For each recommendation include:
    - Recommendation name
    - Why it fits this agency
    - Expected operational impact
    - Expected HHVBP / quality impact
    - Cost level: Low / Medium / High
    - Risk level: Low / Medium / High
    - Time horizon: 30 days / 60-90 days / 3-6 months / 6-12 months

    ## Priority Ranking
    Rank the 3 recommendations from 1 to 3 and explain why.

    ## 90-Day Action Plan
    Break into:
    - Days 1-30
    - Days 31-60
    - Days 61-90

    ## Leadership and Learning Considerations
    Explain how leadership readiness and learning culture may help or hinder execution.

    ## Resource Allocation Guidance
    Explain what to fund first, what to delay, and what to avoid.

    ## Client-Facing Summary
    End with a short, polished summary that could be pasted into a client deliverable.

    Keep the report focused, useful, and realistic for a privately owned home health agency.
    """.strip())

def save_report(markdown_text: str, agency_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name.strip()) or "agency"
    path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path

def main() -> None:
    print("\n=== Home Health Innovation Decision Engine ===\n")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set in your environment.")
        print('PowerShell (current session): $env:OPENAI_API_KEY="your_key_here"')
        sys.exit(1)

    data = {
        "agency_name": ask("Agency name", "Sample Home Health Agency"),
        "region": ask("Region", "Mid-Atlantic"),
        "agency_size": ask("Agency size", "25 employees"),
        "ownership_type": ask("Ownership type", "Privately owned", choices=["Privately owned", "Government", "Nonprofit"]),
        "tech_stack": ask("Current technology stack", "EVV, EHR, no telehealth"),
        "challenges": ask("Primary operational challenges", "low quality scores, staff burnout, slow care coordination"),
        "hhvbp_concerns": ask("HHVBP / quality concerns", "readmissions, patient satisfaction, documentation lag"),
        "workforce_issues": ask("Workforce issues", "caregiver turnover, scheduling strain"),
        "budget_posture": ask("Budget posture", "lean budget", choices=["lean budget", "moderate", "generous"]),
        "leadership_readiness": ask("Leadership readiness", "moderate", choices=["low", "moderate", "high"]),
        "learning_culture": ask("Learning culture maturity", "developing", choices=["nascent", "developing", "mature"]),
        "notes": ask("Additional notes", "none"),
    }

    user_prompt = build_user_prompt(data)

    client = OpenAI()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1400,
        )
    except Exception as exc:
        print(f"\nAPI call failed: {exc}\n")
        sys.exit(1)

    output_text = response.choices[0].message.content.strip()
    report_path = save_report(output_text, data["agency_name"])

    print("\n=== REPORT PREVIEW ===\n")
    print(output_text)
    print(f"\nSaved report to: {report_path}")

if __name__ == "__main__":
    main()
