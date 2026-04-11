def can_generate_report(user):
    # Simple SaaS gating logic
    if user.role == "admin":
        return True

    # Example limit (starter plan)
    if getattr(user, "reports_generated", 0) >= 10:
        return False

    return True


def create_checkout_session(*args, **kwargs):
    # Placeholder until Stripe checkout is fully wired
    return {
        "url": "/pricing",
        "id": "placeholder-checkout-session"
    }


def verify_webhook(payload, sig_header, webhook_secret):
    # Placeholder until Stripe webhook verification is fully wired
    return {
        "type": "webhook.placeholder",
        "data": {
            "object": {}
        }
    }
