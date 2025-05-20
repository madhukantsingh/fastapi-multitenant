from celery import Celery
import os

CELERY_BROKER = os.getenv("CELERY_BROKER", "redis://redis:6379/0")

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER,
    backend=CELERY_BROKER
)

celery_app.conf.task_routes = {
    "app.tasks.billing.send_billing_email": {"queue": "billing"},
}
