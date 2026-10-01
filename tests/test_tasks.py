from src.tasks.celery_app import celery_app
from src.tasks.notification_tasks import send_booking_confirmation


def test_celery_task_registration() -> None:
    assert "src.tasks.notification_tasks.send_booking_confirmation" in celery_app.tasks
    assert "src.tasks.notification_tasks.cleanup_expired_bookings" in celery_app.tasks


def test_send_booking_confirmation_execution() -> None:
    result = send_booking_confirmation.run(
        booking_id=1,
        user_email="test@example.com",
        space_title="Quiet Room 101",
        start_time_iso="2026-10-01T10:00:00Z",
        end_time_iso="2026-10-01T12:00:00Z",
    )
    assert result["status"] == "delivered"
    assert result["booking_id"] == "1"
    assert result["recipient"] == "test@example.com"
