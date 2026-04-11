from fastapi import APIRouter
from services.obsidian_sync import export_report

router = APIRouter(prefix="/api/obsidian")

@router.post("/export")
def obsidian_export(payload: dict):
    return export_report(
        vault=payload["vault_path"],
        agency=payload["agency"],
        title=payload.get("title","Performance Report"),
        markdown=payload["markdown"],
        meta=payload.get("meta", {})
    )
