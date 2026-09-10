from src.core.config import get_settings
from src.core.exceptions import EntityNotFoundException
from src.core.redis import get_cached_json, invalidate_cache_pattern, set_cached_json
from src.models.space import Space
from src.repositories.space_repository import SpaceRepository
from src.schemas.space import SpaceCreate, SpaceFilterParams, SpaceResponse, SpaceUpdate

settings = get_settings()


class SpaceService:
    def __init__(self, space_repository: SpaceRepository) -> None:
        self.space_repo = space_repository

    async def list_spaces(self, params: SpaceFilterParams) -> list[SpaceResponse]:
        cache_key = f"spaces:filter:{params.model_dump_json()}"
        cached_data = await get_cached_json(cache_key)
        if cached_data is not None:
            return [SpaceResponse.model_validate(item) for item in cached_data]

        spaces = await self.space_repo.get_filtered(params)
        response_items = [SpaceResponse.model_validate(space) for space in spaces]

        serializable = [item.model_dump(mode="json") for item in response_items]
        await set_cached_json(cache_key, serializable, ttl_seconds=settings.REDIS_CACHE_TTL_SECONDS)

        return response_items

    async def get_space_by_id(self, space_id: int) -> Space:
        space = await self.space_repo.get_by_id(space_id)
        if not space or not space.is_active:
            raise EntityNotFoundException(f"Space #{space_id} does not exist or is inactive")
        return space

    async def create_space(self, space_in: SpaceCreate) -> Space:
        space = Space(
            title=space_in.title,
            description=space_in.description,
            space_type=space_in.space_type,
            capacity=space_in.capacity,
            has_projector=space_in.has_projector,
            has_whiteboard=space_in.has_whiteboard,
            is_active=space_in.is_active,
        )
        created_space = await self.space_repo.create(space)
        await invalidate_cache_pattern("spaces:filter:*")
        return created_space

    async def update_space(self, space_id: int, space_in: SpaceUpdate) -> Space:
        space = await self.get_space_by_id(space_id)
        update_data = space_in.model_dump(exclude_unset=True)
        updated_space = await self.space_repo.update(space, update_data)
        await invalidate_cache_pattern("spaces:filter:*")
        return updated_space

    async def delete_space(self, space_id: int) -> None:
        space = await self.get_space_by_id(space_id)
        space.is_active = False
        await self.space_repo.update(space, {"is_active": False})
        await invalidate_cache_pattern("spaces:filter:*")
