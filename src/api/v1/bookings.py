from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import (
    get_booking_service,
    get_current_admin,
    get_current_user,
)
from src.models.booking import BookingStatus
from src.models.user import User
from src.schemas.booking import (
    BookingCreate,
    BookingFilterParams,
    BookingResponse,
)
from src.services.booking_service import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_in: BookingCreate,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await booking_service.create_booking(user_id=current_user.id, booking_in=booking_in)
    return BookingResponse.model_validate(booking)


@router.get("/my", response_model=list[BookingResponse])
async def get_my_bookings(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> list[BookingResponse]:
    bookings = await booking_service.get_user_bookings(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )
    return [BookingResponse.model_validate(b) for b in bookings]


@router.get("", response_model=list[BookingResponse])
async def list_all_bookings(
    space_id: int | None = Query(default=None),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    booking_service: BookingService = Depends(get_booking_service),
    _admin: User = Depends(get_current_admin),
) -> list[BookingResponse]:
    params = BookingFilterParams(
        space_id=space_id,
        status=status_filter,
        offset=offset,
        limit=limit,
    )
    bookings = await booking_service.list_all_bookings(params)
    return [BookingResponse.model_validate(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_details(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    booking = await booking_service.get_booking_by_id(booking_id=booking_id, current_user=current_user)
    return BookingResponse.model_validate(booking)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    booking_service: BookingService = Depends(get_booking_service),
) -> BookingResponse:
    cancelled_booking = await booking_service.cancel_booking(
        booking_id=booking_id,
        current_user=current_user,
    )
    return BookingResponse.model_validate(cancelled_booking)
