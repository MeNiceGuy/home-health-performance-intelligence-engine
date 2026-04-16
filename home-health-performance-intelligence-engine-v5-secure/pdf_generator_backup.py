# -*- coding: utf-8 -*-

from pathlib import Path
import re

import matplotlib.pyplot as plt
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

BRAND_NAVY = colors.HexColor("#0F172A")
BRAND_BLUE = colors.HexColor("#1D4ED8")
BRAND_SLATE = colors.HexColor("#334155")
BRAND_LIGHT = colors.HexColor("#CBD5E1")
BRAND_SOFT = colors.HexColor("#F8FAFC")
TEXT_DARK = colors.HexColor("#111827")
ACCENT = colors.HexColor("#0EA5E9")

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "logo.png"


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CoverTitleBCG",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=BRAND_NAVY,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverSubtitleBCG",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=BRAND_SLATE,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ReportTitleBCG",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=BRAND_NAVY,
            spaceBefore=8,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeadingBCG",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=BRAND_BLUE,
            spaceBefore=14,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SubHeadingBCG",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=BRAND_NAVY,
            spaceBefore=10,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyBCG",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.2,
            textColor=TEXT_DARK,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="MetaBCG",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=BRAND_SLATE,
            alignment=TA_LEFT,
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletBCG",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.2,
            textColor=TEXT_DARK,
            leftIndent=16,
            firstLineIndent=0,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="FooterBCG",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=BRAND_SLATE,
            alignment=TA_CENTER,
        )
    )

    return styles


def clean_text(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    return text.strip()


def parse_markdown(md_text: str):
    lines = md_text.splitlines()
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        if line.strip().startswith("|") and line.strip().endswith("|"):
            table_lines = []
            while i < len(lines):
                current = lines[i].rstrip()
                if current.strip().startswith("|") and current.strip().endswith("|"):
                    table_lines.append(current)
                    i += 1
                else:
                    break
            blocks.append(("table", table_lines))
            continue

        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
        elif line.strip() == "---":
            blocks.append(("rule", ""))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        elif len(line) > 3 and line[0].isdigit() and ". " in line[:4]:
            parts = line.split(". ", 1)
            if len(parts) == 2:
                blocks.append(("numbered", (parts[0], parts[1].strip())))
            else:
                blocks.append(("body", line))
        else:
            blocks.append(("body", line))

        i += 1

    return blocks


def make_table(table_lines, styles):
    rows = []
    for line in table_lines:
        stripped = line.strip().strip("|")
        cols = [clean_text(col.strip()) for col in stripped.split("|")]
        rows.append(cols)

    filtered_rows = []
    for row in rows:
        joined = "".join(row).replace("-", "").replace(":", "").strip()
        if joined == "":
            continue
        filtered_rows.append(row)

    if not filtered_rows:
        return Spacer(1, 0.1 * inch)

    data = []
    for row in filtered_rows:
        data.append([Paragraph(cell, styles["BodyBCG"]) for cell in row])

    col_count = max(len(r) for r in filtered_rows)
    usable_width = 7.0 * inch
    col_width = usable_width / col_count
    col_widths = [col_width] * col_count

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, BRAND_LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_SOFT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def extract_score_breakdown(md_text: str):
    patterns = {
        "leadership": r"Leadership:\s*(\d+)\s*/\s*25",
        "learning_culture": r"Learning Culture:\s*(\d+)\s*/\s*25",
        "budget_strength": r"Budget Strength:\s*(\d+)\s*/\s*20",
        "technology_maturity": r"Technology Maturity:\s*(\d+)\s*/\s*20",
        "operational_burden": r"Operational Burden:\s*-(\d+)",
    }

    breakdown = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, md_text, flags=re.IGNORECASE)
        if match:
            breakdown[key] = int(match.group(1))

    required_keys = {
        "leadership",
        "learning_culture",
        "budget_strength",
        "technology_maturity",
        "operational_burden",
    }

    if required_keys.issubset(set(breakdown.keys())):
        return breakdown
    return None


def generate_score_chart(breakdown: dict, output_path: Path):
    labels = [
        "Leadership",
        "Learning",
        "Budget",
        "Technology",
        "Burden (-)",
    ]
    values = [
        breakdown["leadership"],
        breakdown["learning_culture"],
        breakdown["budget_strength"],
        breakdown["technology_maturity"],
        -breakdown["operational_burden"],
    ]

    plt.figure(figsize=(8, 4.2))
    bars = plt.bar(labels, values)

    plt.title("Performance Score Breakdown")
    plt.axhline(0, linewidth=1)
    plt.ylabel("Score Contribution")
    plt.tight_layout()

    for bar, value in zip(bars, values):
        height = bar.get_height()
        y = height + 0.5 if height >= 0 else height - 1.2
        plt.text(bar.get_x() + bar.get_width() / 2, y, str(value), ha="center", va="bottom")

    plt.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close()


def add_cover_page(story, styles):
    story.append(Spacer(1, 0.5 * inch))

    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH))
        logo.drawHeight = 0.9 * inch
        logo.drawWidth = 2.4 * inch
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Boswell Consulting Group", styles["CoverTitleBCG"]))
    story.append(Paragraph("Strategic Advisory & Decision Intelligence", styles["CoverSubtitleBCG"]))
    story.append(Spacer(1, 0.18 * inch))
    story.append(HRFlowable(width="82%", thickness=1.4, color=ACCENT))
    story.append(Spacer(1, 0.22 * inch))
    story.append(Paragraph("Executive Strategy Report", styles["ReportTitleBCG"]))
    story.append(Paragraph("Confidential Client Deliverable", styles["CoverSubtitleBCG"]))
    story.append(Spacer(1, 3.0 * inch))
    story.append(Paragraph("Prepared by Boswell Consulting Group", styles["CoverSubtitleBCG"]))
    story.append(Paragraph("Premium Consulting Deliverable", styles["CoverSubtitleBCG"]))
    story.append(Spacer(1, 0.18 * inch))
    story.append(HRFlowable(width="60%", thickness=0.8, color=BRAND_LIGHT))
    story.append(Spacer(1, 0.28 * inch))
    story.append(
        Paragraph(
            "This report is intended for executive review, strategic planning, and implementation prioritization.",
            styles["CoverSubtitleBCG"],
        )
    )
    story.append(Spacer(1, 0.5 * inch))
    story.append(PageBreak())


def build_story(md_text: str, chart_path: Path | None = None):
    styles = build_styles()
    story = []
    add_cover_page(story, styles)

    blocks = parse_markdown(md_text)
    chart_inserted = False

    for block_type, value in blocks:
        if block_type == "h1":
            story.append(Spacer(1, 0.12 * inch))
            story.append(HRFlowable(width="100%", thickness=1.2, color=BRAND_BLUE))
            story.append(Spacer(1, 0.08 * inch))
            story.append(Paragraph(clean_text(value), styles["ReportTitleBCG"]))
            story.append(Spacer(1, 0.04 * inch))

        elif block_type == "h2":
            story.append(Spacer(1, 0.03 * inch))
            story.append(Paragraph(clean_text(value), styles["SectionHeadingBCG"]))

            if clean_text(value).lower() == "performance snapshot" and chart_path and chart_path.exists() and not chart_inserted:
                story.append(Spacer(1, 0.08 * inch))
                chart = Image(str(chart_path))
                chart.drawWidth = 6.4 * inch
                chart.drawHeight = 3.2 * inch
                chart.hAlign = "CENTER"
                story.append(chart)
                story.append(Spacer(1, 0.12 * inch))
                chart_inserted = True

        elif block_type == "h3":
            story.append(
                KeepTogether(
                    [
                        Spacer(1, 0.02 * inch),
                        Paragraph(clean_text(value), styles["SubHeadingBCG"]),
                    ]
                )
            )

        elif block_type == "rule":
            story.append(Spacer(1, 0.04 * inch))
            story.append(HRFlowable(width="100%", thickness=0.7, color=BRAND_LIGHT))
            story.append(Spacer(1, 0.06 * inch))

        elif block_type == "bullet":
            story.append(Paragraph(clean_text(value), styles["BulletBCG"], bulletText="•"))

        elif block_type == "numbered":
            num, text = value
            story.append(Paragraph(clean_text(text), styles["BulletBCG"], bulletText=f"{num}."))

        elif block_type == "table":
            story.append(Spacer(1, 0.08 * inch))
            story.append(make_table(value, styles))
            story.append(Spacer(1, 0.12 * inch))

        elif block_type == "body":
            text = clean_text(value)
            low = text.lower()

            if low.startswith("prepared for:") or low.startswith("prepared by:") or low.startswith("date:"):
                story.append(Paragraph(f"<b>{text}</b>", styles["MetaBCG"]))
            else:
                story.append(Paragraph(text, styles["BodyBCG"]))

    return story


def add_page_decor(canvas, doc):
    canvas.saveState()

    canvas.setStrokeColor(BRAND_LIGHT)
    canvas.setLineWidth(0.7)
    canvas.line(0.65 * inch, 10.3 * inch, 7.85 * inch, 10.3 * inch)

    if LOGO_PATH.exists():
        try:
            canvas.drawImage(
                str(LOGO_PATH),
                0.72 * inch,
                10.38 * inch,
                width=0.55 * inch,
                height=0.22 * inch,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(BRAND_SLATE)
    canvas.drawString(1.35 * inch, 10.46 * inch, "Boswell Consulting Group")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(BRAND_SLATE)
    canvas.drawString(0.75 * inch, 0.45 * inch, "Boswell Consulting Group")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")

    canvas.restoreState()


def md_to_pdf(md_text: str, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chart_path = output_path.with_name(f"{output_path.stem}_score_chart.png")
    breakdown = extract_score_breakdown(md_text)

    if breakdown:
        try:
            generate_score_chart(breakdown, chart_path)
        except Exception:
            chart_path = None
    else:
        chart_path = None

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.65 * inch,
        title="Boswell Consulting Group Report",
        author="Boswell Consulting Group",
        subject="Strategic Consulting Deliverable",
    )

    story = build_story(md_text, chart_path=chart_path)
    doc.build(story, onFirstPage=add_page_decor, onLaterPages=add_page_decor)

    if chart_path and chart_path.exists():
        try:
            chart_path.unlink()
        except Exception:
            pass

    return output_path


if __name__ == "__main__":
    sample_md = """
# Boswell Consulting Group Report

Prepared for: Sample Care Agency
Prepared by: Boswell Consulting Group
Date: April 06, 2026

---

## Executive Summary
This is a sample premium consulting deliverable.

## Performance Snapshot
- Benchmark Score: 43/100
- Position: Below Industry Benchmark

## Score Breakdown
- Leadership: 15/25
- Learning Culture: 15/25
- Budget Strength: 6/20
- Technology Maturity: 5/20
- Operational Burden: -18

## Priority Innovation Recommendations
### 1. Scheduling Optimization
- Reduce conflicts
- Improve staffing reliability

## Estimated ROI and Impact Ranges

| Recommendation | Operational Improvement | Financial Impact | Key Assumptions |
|---|---|---|---|
| Scheduling Optimization | 20-30% | $20K-$40K | Staff adoption |

## Client-Facing Summary
This report demonstrates premium formatting, layout, and visual scoring.
"""
    saved = md_to_pdf(sample_md, "sample_premium_report.pdf")
    print(f"PDF saved to: {saved}")