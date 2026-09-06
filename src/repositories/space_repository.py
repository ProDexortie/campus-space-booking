from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.space import Space
from src.repositories.base import BaseRepository
from src.schemas.space import SpaceFilterParams


class SpaceRepository(BaseRepository[Space]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Space, session)

    def _build_filter_query(self, params: SpaceFilterParams) -> Select:
        query = select(Space).where(Space.is_active.is_(True))

        if params.min_capacity is not None:
            query = query.where(Space.capacity >= params.min_capacity)
        if params.space_type is not None:
            query = query.where(Space.space_type == params.space_type)
        if params.has_projector is not None:
            query = query.where(Space.has_projector.is_(params.has_projector))
        if params.has_whiteboard is not None:
            query = query.where(Space.has_whiteboard.is_(params.has_whiteboard))

        return query

    async def get_filtered(self, params: SpaceFilterParams) -> Sequence[Space]:
        query = self._build_filter_query(params)
        query = query.order_by(Space.id.asc()).offset(params.offset).limit(params.limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_filtered(self, params: SpaceFilterParams) -> int:
        query = select(func.count()).select_from(self._build_filter_query(params).subquery())
        result = await self.session.execute(query)
        return int(result.scalar_one_or_none() or 0)

    async def update(self, space: Space, update_data: dict[str, Any]) -> Space:
        for key, value in update_data.items():
            if hasattr(space, key) and value is not None:
                setattr(space, key, value)
        await self.session.flush()
        await self.session.refresh(space)
        return space
