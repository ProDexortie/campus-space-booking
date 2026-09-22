from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    BookingConflictException,
    EntityNotFoundException,
    InvalidBookingTimeException,
)
from src.models.space import Space, SpaceType
from src.models.user import User, UserRole
from src.repositories.booking_repository import BookingRepository
from src.repositories.space_repository import SpaceRepository
from src.schemas.booking import BookingCreate
from src.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_booking_duration_exceeds_max(db_session: AsyncSession) -> None:
    space_repo = SpaceRepository(db_session)
    booking_repo = BookingRepository(db_session)
    service = BookingService(booking_repo, space_repo)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=9)  # Max allowed is 8 hours

    booking_in = BookingCreate(space_id=1, start_time=start, end_time=end)

    with pytest.raises(InvalidBookingTimeException) as exc_info:
        await service.create_booking(user_id=1, booking_in=booking_in)
    assert "exceeds maximum limit" in str(exc_info.value)


@pytest.mark.asyncio
async def test_booking_duration_below_min(db_session: AsyncSession) -> None:
    space_repo = SpaceRepository(db_session)
    booking_repo = BookingRepository(db_session)
    service = BookingService(booking_repo, space_repo)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(minutes=15)  # Min allowed is 30 mins

    booking_in = BookingCreate(space_id=1, start_time=start, end_time=end)

    with pytest.raises(InvalidBookingTimeException) as exc_info:
        await service.create_booking(user_id=1, booking_in=booking_in)
    assert "at least 30 minutes" in str(exc_info.value)


@pytest.mark.asyncio
async def test_booking_inactive_space_not_found(db_session: AsyncSession) -> None:
    space_repo = SpaceRepository(db_session)
    booking_repo = BookingRepository(db_session)
    service = BookingService(booking_repo, space_repo)

    space = Space(
        title="Inactive Room",
        space_type=SpaceType.MEETING_ROOM,
        capacity=4,
        is_active=False,
    )
    db_session.add(space)
    await db_session.commit()
    await db_session.refresh(space)

    start = datetime.now(UTC) + timedelta(days=1)
    end = start + timedelta(hours=1)
    booking_in = BookingCreate(space_id=space.id, start_time=start, end_time=end)

    with pytest.raises(EntityNotFoundException):
        await service.create_booking(user_id=1, booking_in=booking_in)


@pytest.mark.asyncio
async def test_booking_conflict_logic(db_session: AsyncSession) -> None:
    space_repo = SpaceRepository(db_session)
    booking_repo = BookingRepository(db_session)
    service = BookingService(booking_repo, space_repo)

    user = User(
        email="test@campus.edu",
        hashed_password="hash",
        full_name="Tester",
        role=UserRole.STUDENT,
        is_active=True,
    )
    space = Space(
        title="Active Desk",
        space_type=SpaceType.DESK,
        capacity=1,
        is_active=True,
    )
    db_session.add_all([user, space])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(space)

    start = datetime.now(UTC) + timedelta(days=2)
    end = start + timedelta(hours=2)

    # First booking succeeds
    b1 = BookingCreate(space_id=space.id, start_time=start, end_time=end)
    created = await service.create_booking(user_id=user.id, booking_in=b1)
    assert created.id is not None

    # Overlapping booking fails
    overlap_b = BookingCreate(
        space_id=space.id,
        start_time=start + timedelta(minutes=30),
        end_time=end + timedelta(minutes=30),
    )
    with pytest.raises(BookingConflictException):
        await service.create_booking(user_id=user.id, booking_in=overlap_b)
