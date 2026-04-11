from __future__ import annotations
import csv
from typing import Any

DATA_PATH = "data/home_health.csv"


def load_data():
    try:
        with open(DATA_PATH, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _coerce_float(value: Any):
    try:
        return float(str(value).replace("%", "").replace(",", "").strip())
    except Exception:
        return None


def build_cms_snapshot(agency_name: str, state: str, city: str | None = None):
    rows = load_data()

    agency = agency_name.lower().strip()
    city_l = (city or "").lower().strip()
    state_l = state.lower().strip()

    best = None
    best_score = -1

    for row in rows:
        name = (row.get("provider_name") or row.get("Provider Name") or "").lower().strip()
        row_state = (row.get("state") or row.get("State") or "").lower().strip()
        row_city = (row.get("city") or row.get("City") or "").lower().strip()

        score = 0
        if agency and agency in name:
            score += 10
        if name and name in agency:
            score += 6
        if city_l and city_l == row_city:
            score += 3
        if state_l and state_l == row_state:
            score += 2

        if score > best_score:
            best_score = score
            best = row

    if not best or best_score <= 0:
        return {
            "match_found": False,
            "cms_status": "csv_loaded_no_match",
            "row_count": len(rows)
        }

    return {
        "match_found": True,
        "provider_name": best.get("provider_name") or best.get("Provider Name"),
        "ccn": best.get("ccn") or best.get("CCN") or best.get("provider_id") or best.get("Provider ID"),
        "state": best.get("state") or best.get("State"),
        "city": best.get("city") or best.get("City"),
        "address": best.get("address") or best.get("Address"),
        "phone": best.get("telephone_number") or best.get("Phone Number") or best.get("phone"),
        "star_rating": _coerce_float(best.get("quality_of_patient_care_star_rating") or best.get("Quality of Patient Care Star Rating")),
        "timely_initiation_of_care": _coerce_float(best.get("how_often_the_home_health_team_began_their_patients_care_in_a_timely_manner") or best.get("How Often the Home Health Team Began Their Patients' Care in a Timely Manner")),
        "patient_satisfaction": _coerce_float(best.get("percent_of_patients_who_reported_that_their_home_health_team_communicated_well_with_them") or best.get("Percent of Patients Who Reported that Their Home Health Team Communicated Well With Them")),
        "cms_status": "csv_verified",
        "row_count": len(rows)
    }
