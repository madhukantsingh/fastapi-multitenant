from .celery_app import celery_app

@celery_app.task
def send_billing_email(tenant_id: int, email_to: str, summary: str, total_usage: int):
    print(f"[Billing Email] Tenant ID: {tenant_id}")
    print(f"To: {email_to}")
    print(f"Summary: {summary}")
    print(f"Total Usage: {total_usage}")
    # Simulate email logic
    return "Billing email sent successfully"
