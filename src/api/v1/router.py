from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.bookings import router as bookings_router
from src.api.v1.spaces import router as spaces_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(spaces_router)
api_v1_router.include_router(bookings_router)
