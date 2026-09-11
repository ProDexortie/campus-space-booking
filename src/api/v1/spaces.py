from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_current_admin, get_space_service
from src.models.space import SpaceType
from src.schemas.space import SpaceCreate, SpaceFilterParams, SpaceResponse, SpaceUpdate
from src.services.space_service import SpaceService

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get("", response_model=list[SpaceResponse])
async def list_spaces(
    min_capacity: int | None = Query(default=None, ge=1),
    space_type: SpaceType | None = Query(default=None),
    has_projector: bool | None = Query(default=None),
    has_whiteboard: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    space_service: SpaceService = Depends(get_space_service),
) -> list[SpaceResponse]:
    filter_params = SpaceFilterParams(
        min_capacity=min_capacity,
        space_type=space_type,
        has_projector=has_projector,
        has_whiteboard=has_whiteboard,
        offset=offset,
        limit=limit,
    )
    return await space_service.list_spaces(filter_params)


@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(
    space_id: int,
    space_service: SpaceService = Depends(get_space_service),
) -> SpaceResponse:
    space = await space_service.get_space_by_id(space_id)
    return SpaceResponse.model_validate(space)


@router.post("", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    space_in: SpaceCreate,
    space_service: SpaceService = Depends(get_space_service),
    _admin: None = Depends(get_current_admin),
) -> SpaceResponse:
    created = await space_service.create_space(space_in)
    return SpaceResponse.model_validate(created)


@router.patch("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: int,
    space_in: SpaceUpdate,
    space_service: SpaceService = Depends(get_space_service),
    _admin: None = Depends(get_current_admin),
) -> SpaceResponse:
    updated = await space_service.update_space(space_id, space_in)
    return SpaceResponse.model_validate(updated)


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_space(
    space_id: int,
    space_service: SpaceService = Depends(get_space_service),
    _admin: None = Depends(get_current_admin),
) -> None:
    await space_service.delete_space(space_id)
