from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from celery import Task
from sqlalchemy import update

from src.core.database import async_session_factory
from src.models.booking import Booking, BookingStatus
from src.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="src.tasks.notification_tasks.send_booking_confirmation", bind=True, max_retries=3)
def send_booking_confirmation(
    self: Task,
    booking_id: int,
    user_email: str,
    space_title: str,
    start_time_iso: str,
    end_time_iso: str,
) -> dict[str, str]:
    try:
        logger.info(
            "Sending booking confirmation for #%d to %s: space '%s' from %s to %s",
            booking_id,
            user_email,
            space_title,
            start_time_iso,
            end_time_iso,
        )
        # In production this integrates with an SMTP or SES provider
        return {
            "status": "delivered",
            "booking_id": str(booking_id),
            "recipient": user_email,
        }
    except Exception as exc:
        logger.error("Failed to send booking notification #%d: %s", booking_id, exc)
        raise self.retry(exc=exc, countdown=60) from exc


async def _async_cleanup_expired_bookings() -> int:
    now = datetime.now(UTC)
    async with async_session_factory() as session:
        statement = (
            update(Booking)
            .where(
                Booking.status == BookingStatus.CONFIRMED,
                Booking.end_time < now,
            )
            .values(status=BookingStatus.EXPIRED)
        )
        result = await session.execute(statement)
        await session.commit()
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0)


@celery_app.task(name="src.tasks.notification_tasks.cleanup_expired_bookings")
def cleanup_expired_bookings() -> dict[str, int]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    count = loop.run_until_complete(_async_cleanup_expired_bookings())
    logger.info("Marked %d past reservations as EXPIRED", count)
    return {"expired_count": count}
