from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.booking import BookingStatus


class BookingBase(BaseModel):
    space_id: int
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
    @model_validator(mode="after")
    def validate_time_window(self) -> "BookingCreate":
        start = self.start_time
        end = self.end_time

        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
            self.start_time = start

        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
            self.end_time = end

        if end <= start:
            raise ValueError("Booking end_time must be strictly after start_time")

        return self


class BookingResponse(BookingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: BookingStatus
    created_at: datetime


class BookingFilterParams(BaseModel):
    space_id: int | None = None
    status: BookingStatus | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=100)
