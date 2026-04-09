from __future__ import annotations

from typing import Any

def build_cms_snapshot(agency_name: str, state: str, city: str | None = None) -> dict[str, Any]:
    return {
        "match_found": False,
        "provider_name": None,
        "ccn": None,
        "state": state.upper().strip() if state else None,
        "city": city,
        "address": None,
        "phone": None,
        "star_rating": None,
        "timely_initiation_of_care": None,
        "patient_satisfaction": None,
        "state_benchmarks": {
            "star_rating": None,
            "timely_initiation_of_care": None,
            "patient_satisfaction": None,
        },
        "hhvbp": {},
        "raw_provider": {},
        "raw_state": {},
        "cms_status": "disabled_pending_verified_source",
        "cms_notice": "Live CMS lookup is temporarily disabled until a verified source is connected."
    }
