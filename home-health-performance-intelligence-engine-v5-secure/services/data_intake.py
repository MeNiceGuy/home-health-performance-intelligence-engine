from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any


NUMERIC_FIELDS = {
    "avg_monthly_patients",
    "clinicians_total",
    "star_rating",
    "readmission_rate",
    "patient_satisfaction",
    "oasis_timeliness",
    "soc_delay_days",
    "visit_completion_rate",
    "documentation_lag_hours",
    "turnover_rate",
    "open_positions",
    "visits_per_clinician_week",
}

BOOL_FIELDS = {"evv_present", "telehealth_present", "automation_present"}

LIST_FIELDS = {"pain_points"}

REQUIRED_MINIMAL_FIELDS = {"agency_name", "state", "city", "ownership_type"}


def _to_number(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return value
    raw = str(value).strip().replace(",", "").replace("%", "")
    if not raw:
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return value



def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}



def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in record.items():
        if key in NUMERIC_FIELDS:
            normalized[key] = _to_number(value)
        elif key in BOOL_FIELDS:
            normalized[key] = _to_bool(value)
        elif key in LIST_FIELDS:
            if value in (None, ""):
                normalized[key] = []
            elif isinstance(value, list):
                normalized[key] = value
            else:
                normalized[key] = [v.strip() for v in str(value).split(",") if v.strip()]
        else:
            normalized[key] = value.strip() if isinstance(value, str) else value

    missing = [field for field in REQUIRED_MINIMAL_FIELDS if not normalized.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    normalized.setdefault("pain_points", [])
    normalized.setdefault("notes", "")
    normalized.setdefault("cms_context", {})
    normalized.setdefault("scorecard", {})
    normalized.setdefault("monthly_series", [])
    return normalized



def parse_json_text(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON intake must contain a single object.")
    return normalize_record(data)



def parse_csv_text(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    rows = [normalize_record(dict(row)) for row in reader]
    if not rows:
        raise ValueError("CSV intake file is empty.")
    return rows



def load_intake_file(path: str | Path) -> dict[str, Any] | list[dict[str, Any]]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return parse_json_text(text)
    if path.suffix.lower() == ".csv":
        return parse_csv_text(text)
    raise ValueError("Supported intake formats are .json and .csv")
