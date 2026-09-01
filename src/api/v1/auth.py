from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.api.dependencies import get_auth_service, get_current_user
from src.models.user import User
from src.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await auth_service.register_user(user_in)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.authenticate_user(credentials)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.refresh_user_tokens(payload.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
