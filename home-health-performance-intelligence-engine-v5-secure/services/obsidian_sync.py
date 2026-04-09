from pathlib import Path
from datetime import datetime
import re

def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", s).strip().replace(" ", "_")

def export_report(vault: str, agency: str, title: str, markdown: str, meta: dict | None = None):
    root = Path(vault).expanduser()
    agency_dir = root / "GeneratedReports" / _safe(agency)
    agency_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    note = agency_dir / f"{stamp}_{_safe(title)}.md"

    front = [
        "---",
        f"agency: {agency}",
        f"title: {title}",
        f"created: {datetime.now().isoformat()}",
    ]
    for k, v in (meta or {}).items():
        front.append(f"{k}: {v}")
    front += ["---", "", f"# {title}", ""]

    note.write_text("\n".join(front) + markdown, encoding="utf-8")

    moc = root / "AgencyProfiles" / f"{_safe(agency)}.md"
    moc.parent.mkdir(parents=True, exist_ok=True)

    body = moc.read_text(encoding="utf-8") if moc.exists() else f"# {agency}\n\n## Reports\n"
    body += f"- [[GeneratedReports/{_safe(agency)}/{note.name}|{title}]]\n"
    moc.write_text(body, encoding="utf-8")

    return {"note_path": str(note), "moc_path": str(moc)}
