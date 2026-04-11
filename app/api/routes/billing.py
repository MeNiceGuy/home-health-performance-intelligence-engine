from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import require_role, get_current_user
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User
from app.schemas.admin import BillingCheckoutRequest
from app.services.billing import create_checkout_session, verify_webhook
from app.services.admin_service import update_subscription_from_stripe
from app.services.audit import append_audit_event
from app.core.config import STRIPE_WEBHOOK_SECRET

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/checkout")
def billing_checkout(
    payload: BillingCheckoutRequest,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if current_user.organization_id is None:
        raise HTTPException(status_code=400, detail="User has no organization.")
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    session = create_checkout_session(org.slug, payload.plan)
    append_audit_event(
        db=db,
        action="billing_checkout_created",
        detail=f"Checkout created for plan {payload.plan}",
        organization_id=current_user.organization_id,
        username=current_user.username,
    )
    return {"checkout_url": session.url, "session_id": session.id}

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    event = verify_webhook(payload, sig_header, STRIPE_WEBHOOK_SECRET)

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        org_slug = session_obj.get("metadata", {}).get("organization_slug")
        plan = session_obj.get("metadata", {}).get("plan", "starter")

        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if org:
            update_subscription_from_stripe(
                db=db,
                organization_id=org.id,
                stripe_customer_id=session_obj.get("customer"),
                stripe_subscription_id=session_obj.get("subscription"),
                plan_name=plan,
                status="active",
                current_period_end=None,
            )
            append_audit_event(
                db=db,
                action="billing_webhook_processed",
                detail=f"Subscription activated for plan {plan}",
                organization_id=org.id,
                username="system",
            )

    return {"received": True}

@router.get("/success")
def billing_success():
    return {"status": "success"}

@router.get("/cancel")
def billing_cancel():
    return {"status": "cancelled"}
