from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from celery_app import celery_app


@celery_app.task(name="tasks.ping")
def ping():
    return "pong"


@celery_app.task(name="tasks.add")
def add(x, y):
    return x + y


@celery_app.task(name="tasks.generate_report_task")
def generate_report_task(data: dict, output_format: str = "pdf"):
    base_dir = Path(__file__).resolve().parent
    upload_dir = base_dir / "uploads"
    reports_dir = base_dir / "reports"
    upload_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    agency_name = (data.get("agency_name") or "agency").strip()
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in agency_name) or "agency"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding="utf-8", dir=str(upload_dir)) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)

    md_output = reports_dir / f"{safe_name}.md"

    result = subprocess.run(
        [sys.executable, str(base_dir / "home_health_decision_engine_cli_v2.py"), "-i", str(tmp_path), "-o", str(md_output)],
        capture_output=True,
        text=True,
        cwd=str(base_dir),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Report generation failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    pdf_output = md_output.with_suffix(".pdf")

    return {
        "agency_name": agency_name,
        "output_format": output_format.lower().strip(),
        "markdown_path": str(md_output),
        "pdf_path": str(pdf_output),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
