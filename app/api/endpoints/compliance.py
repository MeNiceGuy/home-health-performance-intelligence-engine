from fastapi import APIRouter

router = APIRouter(prefix="/compliance")

STATE_DATA = {
    "VA": {"license_required": True, "survey_required": True, "medicare": True},
    "TX": {"license_required": True, "survey_required": True, "medicare": True},
    "CA": {"license_required": True, "survey_required": True, "medicare": True}
}

@router.get("/{state}")
def get_compliance(state: str):
    return STATE_DATA.get(state.upper(), {"error": "State not configured"})
