import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_MAP = {
    "Starter": os.getenv("STRIPE_PRICE_STARTER"),
    "Pro": os.getenv("STRIPE_PRICE_PRO"),
    "Enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE"),
}

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

def create_checkout_session(plan_name: str, customer_email: str):
    price_id = PRICE_MAP.get(plan_name)
    if not price_id:
        raise ValueError(f"No Stripe price configured for plan: {plan_name}")

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=customer_email,
        success_url=f"{APP_BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{APP_BASE_URL}/billing/cancel",
    )
    return session

def verify_webhook(payload: bytes, sig_header: str):
    secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    return stripe.Webhook.construct_event(payload, sig_header, secret)
