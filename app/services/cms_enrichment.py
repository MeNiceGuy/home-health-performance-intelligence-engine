from app.services.cms_integration import load_cms_data, match_agency

CMS_FILE = "data/cms_home_health.csv"

def enrich_with_cms(payload):
    try:
        cms_data = load_cms_data(CMS_FILE)
        match = match_agency(payload, cms_data)
        if match:
            payload["cms_star_rating"] = match.get("Quality of Patient Care Star Rating")
            payload["cms_readmission"] = match.get("Hospitalization Rate")
            payload["cms_agency_name"] = match.get("Agency Name")
    except Exception:
        pass
    return payload
