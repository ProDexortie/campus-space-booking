import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.models.base import TimestampMixin

if TYPE_CHECKING:
    from src.models.booking import Booking


class SpaceType(str, enum.Enum):
    DESK = "desk"
    MEETING_ROOM = "meeting_room"
    LOUNGE_ZONE = "lounge_zone"


class Space(Base, TimestampMixin):
    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    space_type: Mapped[SpaceType] = mapped_column(
        Enum(SpaceType, name="space_type_enum", native_enum=False),
        default=SpaceType.DESK,
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    has_projector: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_whiteboard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="space",
        cascade="all, delete-orphan",
    )
