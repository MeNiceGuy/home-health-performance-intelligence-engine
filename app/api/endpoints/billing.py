from fastapi import APIRouter

router = APIRouter(prefix="/api/billing", tags=["billing"])

@router.get("/plans")
def billing_plans():
    return {
        "plans": [
            {"name": "Starter", "price_monthly": 49},
            {"name": "Pro", "price_monthly": 149},
            {"name": "Enterprise", "price_monthly": 499}
        ]
    }
