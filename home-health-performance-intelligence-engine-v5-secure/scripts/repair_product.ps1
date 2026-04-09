$ErrorActionPreference = "Stop"

Set-Location "C:\Users\1bosw\OneDrive\Desktop\GitHub\home_health_master"

if (-not (Test-Path ".\templates")) { New-Item -ItemType Directory -Path ".\templates" | Out-Null }
if (-not (Test-Path ".\reports")) { New-Item -ItemType Directory -Path ".\reports" | Out-Null }
if (-not (Test-Path ".\uploads")) { New-Item -ItemType Directory -Path ".\uploads" | Out-Null }

@'
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT

def _build_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="BoswellTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=14,
        alignment=TA_LEFT,
    )

    heading1_style = ParagraphStyle(
        name="BoswellHeading1",
        parent=styles["Heading1"],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=8,
    )

    heading2_style = ParagraphStyle(
        name="BoswellHeading2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        name="BoswellBody",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=14,
        textColor=colors.black,
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        name="BoswellBullet",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-8,
        bulletIndent=0,
        spaceAfter=4,
    )

    return {
        "title": title_style,
        "h1": heading1_style,
        "h2": heading2_style,
        "body": body_style,
        "bullet": bullet_style,
    }

def _clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    return text.strip()

def _markdown_to_story(md_text: str, styles_dict: dict):
    story = []
    lines = md_text.splitlines()

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            story.append(Spacer(1, 0.08 * inch))
            continue

        clean = _clean_inline(line)

        if clean.startswith("# "):
            story.append(Paragraph(clean[2:].strip(), styles_dict["title"]))
        elif clean.startswith("## "):
            story.append(Paragraph(clean[3:].strip(), styles_dict["h1"]))
        elif clean.startswith("### "):
            story.append(Paragraph(clean[4:].strip(), styles_dict["h2"]))
        elif clean.startswith("- "):
            story.append(Paragraph(clean[2:].strip(), styles_dict["bullet"], bulletText="•"))
        elif clean[:2].isdigit() and ". " in clean:
            num = clean.split(".", 1)[0]
            text = clean.split(".", 1)[1].strip()
            story.append(Paragraph(text, styles_dict["bullet"], bulletText=f"{num}."))
        else:
            story.append(Paragraph(clean, styles_dict["body"]))

    return story

def md_to_pdf(md_text: str, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Boswell Consulting Group Report",
        author="Boswell Consulting Group",
    )

    styles_dict = _build_styles()
    story = _markdown_to_story(md_text, styles_dict)
    story.insert(0, Paragraph("Boswell Consulting Group", styles_dict["title"]))
    story.insert(1, Spacer(1, 20))
    story.insert(2, Paragraph("Home Health Strategy Report", styles_dict["h1"]))
    story.insert(3, PageBreak())

    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawString(0.75 * inch, 0.5 * inch, "Boswell Consulting Group")
        canvas.drawRightString(7.75 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return output_path

if __name__ == "__main__":
    sample_md = "# Boswell Consulting Group Report\n\n## Executive Summary\nSample"
    saved = md_to_pdf(sample_md, "sample_report.pdf")
    print(f"PDF saved to: {saved}")
'@ | Set-Content .\pdf_generator.py

@'
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import jsonschema
from openai import OpenAI
from pdf_generator import md_to_pdf

OUTPUT_DIR = Path(__file__).resolve().parent / "reports"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SYSTEM_PROMPT = """You are a senior healthcare strategy consultant specializing in privately owned U.S. home health agencies operating under HHVBP reimbursement pressure.

Your job is to produce a premium consulting-style recommendation report for Boswell Consulting Group.

Rules:
- Be practical, specific, and concise.
- Focus on operational efficiency, quality improvement, innovation adoption, and implementation feasibility.
- Do not make legal, medical, or reimbursement guarantees.
- Include estimated impact ranges where reasonable.
- Include at least one overlooked leadership insight.
- Include prioritization logic tied to ROI, feasibility, and speed to impact.
- Prefer lower-cost, higher-feasibility recommendations when the agency appears resource-constrained.
- Avoid generic AI hype.
- Write in a polished, executive tone suitable for a healthcare CEO, Administrator, or Director.
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
    "required": [
        "agency_name","region","agency_size","ownership_type","tech_stack","challenges",
        "hhvbp_concerns","workforce_issues","budget_posture","leadership_readiness",
        "learning_culture","notes"
    ]
}

def build_user_prompt(data: dict) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    return f"""
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

# Boswell Consulting Group Report

Prepared for: {data['agency_name']}
Prepared by: Boswell Consulting Group
Date: {today}

## Executive Summary
Write in a polished, executive tone suitable for a healthcare CEO, Administrator, or Director.

## Priority Innovation Recommendations
Give exactly 3 recommendations. For each include:
- Recommendation name
- Why it fits this agency
- Expected operational impact
- Expected HHVBP / quality impact
- Cost level: Low / Medium / High
- Risk level: Low / Medium / High
- Time horizon: 30 days / 60-90 days / 3-6 months / 6-12 months
- Decision Score (1–10 based on ROI potential, ease of implementation, and speed to impact)
- ROI potential score
- Ease of implementation score
- Speed to impact score

## Priority Ranking
Rank the 3 recommendations from highest to lowest priority and explain why.

## 90-Day Action Plan
Break into:
- Days 1-30
- Days 31-60
- Days 61-90

## Leadership and Learning Considerations
Explain how leadership readiness and learning culture may help or hinder execution.

## Resource Allocation Guidance
Explain what to fund first, what to delay, and what to avoid.

## Estimated ROI and Impact Ranges
For each recommendation include:
- Estimated operational improvement range
- Estimated financial or efficiency impact
- Key assumptions

## Overlooked Leadership Insight
Identify one important issue leadership may be underestimating.

## Client-Facing Summary
Write this as if it will be presented directly to agency executive leadership.

## Next Steps
For implementation support, strategic advisory, or customized analysis, contact Boswell Consulting Group.
"""

def save_report(markdown_text: str, agency_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name.strip()) or "agency"
    path = OUTPUT_DIR / f"{safe_name}_{timestamp}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path

def main():
    parser = argparse.ArgumentParser(description="Boswell Consulting Group Home Health Decision Engine")
    parser.add_argument("-i", "--input", type=str, required=True, help="Path to JSON file with agency profile data")
    parser.add_argument("-o", "--output", type=str, help="Optional output path for the markdown report")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            agency_data = json.load(f)
    except Exception as e:
        print(f"Failed to read input file: {e}")
        sys.exit(1)

    try:
        jsonschema.validate(instance=agency_data, schema=AGENCY_SCHEMA)
    except jsonschema.ValidationError as ve:
        print(f"Input validation error: {ve.message}")
        sys.exit(1)

    client = OpenAI()
    user_prompt = build_user_prompt(agency_data)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1800,
        )
        output_text = response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"API call failed: {exc}")
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
    else:
        output_path = save_report(output_text, agency_data["agency_name"])

    print(f"Markdown report saved to: {output_path}")

    pdf_path = output_path.with_suffix(".pdf")
    md_to_pdf(output_text, pdf_path)

    print(f"PDF report saved to: {pdf_path}")

if __name__ == "__main__":
    main()
'@ | Set-Content .\home_health_decision_engine_cli.py

@'
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from starlette.middleware.sessions import SessionMiddleware
import os
import sys
from pathlib import Path
import subprocess

app = FastAPI()

SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "changemeplease")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.post("/generate_report")
async def generate_report(
    request: Request,
    agency_json: UploadFile = File(...),
    output_format: str = Form("md")
):
    try:
        if not agency_json.filename:
            raise HTTPException(status_code=400, detail="No file was uploaded.")
        if not agency_json.filename.lower().endswith(".json"):
            raise HTTPException(status_code=400, detail="Please upload a valid JSON file.")

        content = await agency_json.read()
        input_path = UPLOAD_DIR / agency_json.filename
        with open(input_path, "wb") as f:
            f.write(content)

        base_name = Path(agency_json.filename).stem
        md_output = REPORTS_DIR / f"{base_name}.md"

        cmd = [
            sys.executable,
            str(BASE_DIR / "home_health_decision_engine_cli.py"),
            "-i", str(input_path),
            "-o", str(md_output)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Report generation failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        pdf_output = md_output.with_suffix(".pdf")
        requested_format = output_format.lower().strip()

        if requested_format == "pdf":
            if not pdf_output.exists():
                raise HTTPException(status_code=500, detail="PDF file was not created.")
            return FileResponse(str(pdf_output), media_type="application/pdf", filename=pdf_output.name)

        if not md_output.exists():
            raise HTTPException(status_code=500, detail="Markdown file was not created.")

        return FileResponse(str(md_output), media_type="text/markdown", filename=md_output.name)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected server error: {e}")
'@ | Set-Content .\server.py

@'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Boswell Consulting Group Decision Engine</title>
<style>
body{font-family:Arial,sans-serif;background:#0f172a;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.card{background:#1e293b;padding:30px;border-radius:14px;width:420px;box-shadow:0 8px 24px rgba(0,0,0,.35)}
h1{font-size:24px;margin-bottom:10px}
p{color:#cbd5e1}
input,select,button{width:100%;padding:12px;margin-top:12px;border-radius:8px;border:none}
button{background:#22c55e;color:#fff;font-weight:bold;cursor:pointer}
button:hover{background:#16a34a}
</style>
</head>
<body>
<div class="card">
<h1>Boswell Consulting Group Decision Engine</h1>
<p>Upload an agency profile JSON file to generate a strategy report.</p>
<form action="/generate_report" method="post" enctype="multipart/form-data">
<input type="file" name="agency_json" accept=".json" required>
<select name="output_format">
<option value="md">Markdown</option>
<option value="pdf">PDF</option>
</select>
<button type="submit">Generate Report</button>
</form>
</div>
</body>
</html>
'@ | Set-Content .\templates\index.html

@'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard</title>
</head>
<body>
<h1>Dashboard</h1>
<p>Boswell Consulting Group Decision Engine is running.</p>
</body>
</html>
'@ | Set-Content .\templates\dashboard.html

Write-Host "Files rewritten successfully."
Write-Host "Now run:"
Write-Host "python .\home_health_decision_engine_cli.py -i .\sample_agency_profile.json"
Write-Host "uvicorn server:app --reload"