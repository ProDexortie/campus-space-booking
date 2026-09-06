from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.space import SpaceType


class SpaceBase(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    description: str | None = None
    space_type: SpaceType = SpaceType.DESK
    capacity: int = Field(default=1, ge=1, le=500)
    has_projector: bool = False
    has_whiteboard: bool = False


class SpaceCreate(SpaceBase):
    is_active: bool = True


class SpaceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    space_type: SpaceType | None = None
    capacity: int | None = Field(default=None, ge=1, le=500)
    has_projector: bool | None = None
    has_whiteboard: bool | None = None
    is_active: bool | None = None


class SpaceResponse(SpaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class SpaceFilterParams(BaseModel):
    min_capacity: int | None = Field(default=None, ge=1)
    space_type: SpaceType | None = None
    has_projector: bool | None = None
    has_whiteboard: bool | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
