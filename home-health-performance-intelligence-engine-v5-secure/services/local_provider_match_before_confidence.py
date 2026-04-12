from __future__ import annotations

import csv
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "HH_Provider_Jan2026.csv"


def normalize_text(value: str) -> str:
    value = (value or "").lower().strip()
    keep = []
    for ch in value:
        if ch.isalnum() or ch.isspace():
            keep.append(ch)
        else:
            keep.append(" ")
    return " ".join("".join(keep).split())


def safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    raw = str(value).replace("%", "").replace(",", "").strip()
    try:
        return float(raw)
    except ValueError:
        return None


def confidence_label(score: float) -> str:
    if score >= 90:
        return "High"
    if score >= 70:
        return "Medium"
    return "Low"


def load_provider_rows() -> list[dict[str, Any]]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def score_row(row: dict[str, Any], agency_name: str, state: str, city: str) -> float:
    target_name = normalize_text(agency_name)
    target_state = normalize_text(state)
    target_city = normalize_text(city)

    row_name = normalize_text(row.get("Provider Name", ""))
    row_state = normalize_text(row.get("State", ""))
    row_city = normalize_text(row.get("City/Town", ""))

    score = 0.0
    if row_name:
        score += SequenceMatcher(None, target_name, row_name).ratio() * 100
        if target_name and target_name in row_name:
            score += 15
    if target_state and row_state == target_state:
        score += 20
    if target_city and row_city == target_city:
        score += 15
    elif target_city and target_city in row_city:
        score += 8
    return score


def build_verified_metrics(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "star_rating": safe_float(row.get("Quality of patient care star rating")),
        "patient_satisfaction": None,
        "readmission_rate": safe_float(row.get("PPR Risk-Standardized Rate")),
        "oasis_timeliness": safe_float(row.get("How often the home health team began their patients' care in a timely manner")),
        "pph_rate": safe_float(row.get("PPH Risk-Standardized Rate")),
        "spend_index": safe_float(row.get("How much Medicare spends on an episode of care at this agency, compared to Medicare spending across all agencies nationally")),
    }


def match_uploaded_provider_csv(agency_name: str, state: str, city: str) -> dict[str, Any] | None:
    rows = load_provider_rows()
    if not rows:
        return None

    ranked = sorted(
        ((score_row(row, agency_name, state, city), row) for row in rows),
        key=lambda x: x[0],
        reverse=True,
    )

    best_score, best_row = ranked[0]
    if best_score < 55:
        return None

    return {
        "source": "uploaded_provider_csv",
        "match_confidence": f"Matched from uploaded CSV ({best_score:.1f})",
        "confidence_level": confidence_label(best_score),
        "match_score": round(best_score, 1),
        "matched_provider": best_row.get("Provider Name", ""),
        "matched_state": best_row.get("State", ""),
        "matched_city": best_row.get("City/Town", ""),
        "verified_metrics": build_verified_metrics(best_row),
        "raw_row": best_row,
    }

