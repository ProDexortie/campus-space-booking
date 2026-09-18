from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from src.core.config import get_settings
from src.core.exceptions import (
    BookingConflictException,
    EntityNotFoundException,
    InvalidBookingTimeException,
    PermissionDeniedException,
)
from src.models.booking import Booking, BookingStatus
from src.models.user import User, UserRole
from src.repositories.booking_repository import BookingRepository
from src.repositories.space_repository import SpaceRepository
from src.schemas.booking import BookingCreate, BookingFilterParams

settings = get_settings()


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        space_repository: SpaceRepository,
    ) -> None:
        self.booking_repo = booking_repository
        self.space_repo = space_repository

    async def create_booking(self, user_id: int, booking_in: BookingCreate) -> Booking:
        now = datetime.now(UTC)
        if booking_in.start_time < now - timedelta(minutes=2):
            raise InvalidBookingTimeException("Cannot create a reservation in the past")

        duration = booking_in.end_time - booking_in.start_time
        max_duration = timedelta(hours=settings.MAX_BOOKING_DURATION_HOURS)
        min_duration = timedelta(minutes=settings.MIN_BOOKING_DURATION_MINUTES)

        if duration > max_duration:
            raise InvalidBookingTimeException(
                f"Booking duration exceeds maximum limit of {settings.MAX_BOOKING_DURATION_HOURS} hours"
            )

        if duration < min_duration:
            raise InvalidBookingTimeException(
                f"Booking duration must be at least {settings.MIN_BOOKING_DURATION_MINUTES} minutes"
            )

        space = await self.space_repo.get_by_id(booking_in.space_id)
        if not space or not space.is_active:
            raise EntityNotFoundException(f"Space #{booking_in.space_id} does not exist or is inactive")

        overlap = await self.booking_repo.find_active_overlap(
            space_id=booking_in.space_id,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            for_update=True,
        )
        if overlap:
            raise BookingConflictException("Selected space is already reserved for the requested time slot")

        booking = Booking(
            user_id=user_id,
            space_id=booking_in.space_id,
            start_time=booking_in.start_time,
            end_time=booking_in.end_time,
            status=BookingStatus.CONFIRMED,
        )
        created_booking = await self.booking_repo.create(booking)

        try:
            from src.tasks.notification_tasks import send_booking_confirmation

            send_booking_confirmation.delay(
                booking_id=created_booking.id,
                user_email=f"user_{user_id}@campus.local",
                space_title=space.title,
                start_time_iso=created_booking.start_time.isoformat(),
                end_time_iso=created_booking.end_time.isoformat(),
            )
        except Exception:
            pass

        return created_booking

    async def get_user_bookings(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Booking]:
        return await self.booking_repo.list_by_user(user_id=user_id, offset=offset, limit=limit)

    async def list_all_bookings(self, params: BookingFilterParams) -> Sequence[Booking]:
        return await self.booking_repo.list_all_filtered(params)

    async def get_booking_by_id(self, booking_id: int, current_user: User) -> Booking:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise EntityNotFoundException(f"Booking #{booking_id} was not found")

        if booking.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise PermissionDeniedException("You do not have permission to view this reservation")

        return booking

    async def cancel_booking(self, booking_id: int, current_user: User) -> Booking:
        booking = await self.get_booking_by_id(booking_id, current_user)

        if booking.status != BookingStatus.CONFIRMED:
            raise InvalidBookingTimeException(f"Cannot cancel booking with current status '{booking.status.value}'")

        return await self.booking_repo.update_status(booking, BookingStatus.CANCELLED)
