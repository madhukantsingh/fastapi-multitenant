from celery import Celery
import os
import time

# Celery configuration
broker_url = os.getenv("CELERY_BROKER", "redis://redis:6379/0")
backend_url = os.getenv("CELERY_BACKEND", None)  # We can use Redis or RPC if needed, or leave None for demo
celery_app = Celery("app", broker=broker_url, backend=backend_url)

@celery_app.task
def send_billing_email(tenant_id: int, email_to: str, usage_summary: str, total_usage: int):
    """
    Celery task to send a billing email. In this dummy implementation, we just simulate the email.
    """
    # Simulate some email sending delay
    time.sleep(2)
    # For demo, just print to console (Celery worker log)
    print(f"[Celery] Sending billing email to '{email_to}' for Tenant {tenant_id}...")
    print(f"[Celery] Usage Summary: {usage_summary} (Total uses: {total_usage})")
    print("[Celery] Billing email sent (simulation).")
    return {"status": "sent", "tenant_id": tenant_id, "email": email_to}
