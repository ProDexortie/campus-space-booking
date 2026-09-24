from celery import Celery

from src.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "campus_booking",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.notification_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "cleanup-expired-bookings-every-15-mins": {
            "task": "src.tasks.notification_tasks.cleanup_expired_bookings",
            "schedule": 900.0,
        },
    },
)
