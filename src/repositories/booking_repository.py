from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.booking import Booking, BookingStatus
from src.repositories.base import BaseRepository
from src.schemas.booking import BookingFilterParams


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Booking, session)

    async def find_active_overlap(
        self,
        space_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: int | None = None,
        for_update: bool = False,
    ) -> Booking | None:
        query = select(Booking).where(
            Booking.space_id == space_id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
        )

        if exclude_booking_id is not None:
            query = query.where(Booking.id != exclude_booking_id)

        bind = self.session.bind
        dialect_name = bind.dialect.name if bind is not None else ""
        if for_update and dialect_name == "postgresql":
            query = query.with_for_update()

        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_by_user(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Booking]:
        query = (
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(desc(Booking.start_time))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_all_filtered(self, params: BookingFilterParams) -> Sequence[Booking]:
        query: Select = select(Booking)
        if params.space_id is not None:
            query = query.where(Booking.space_id == params.space_id)
        if params.status is not None:
            query = query.where(Booking.status == params.status)

        query = query.order_by(desc(Booking.start_time)).offset(params.offset).limit(params.limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_status(self, booking: Booking, new_status: BookingStatus) -> Booking:
        booking.status = new_status
        await self.session.flush()
        await self.session.refresh(booking)
        return booking
