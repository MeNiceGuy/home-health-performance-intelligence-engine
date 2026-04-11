from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

PDF_DIR = Path("reports")
PDF_DIR.mkdir(exist_ok=True)

def markdown_to_simple_pdf(markdown_text: str, output_path: str) -> str:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path, pagesize=LETTER)
    story = []

    for line in markdown_text.splitlines():
        text = line.strip()
        if not text:
            story.append(Spacer(1, 8))
            continue

        if text.startswith("# "):
            story.append(Paragraph(text[2:], styles["Title"]))
        elif text.startswith("## "):
            story.append(Paragraph(text[3:], styles["Heading2"]))
        elif text.startswith("### "):
            story.append(Paragraph(text[4:], styles["Heading3"]))
        else:
            story.append(Paragraph(text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles["BodyText"]))

        story.append(Spacer(1, 6))

    doc.build(story)
    return output_path
