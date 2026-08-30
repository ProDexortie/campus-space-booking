import jwt

from src.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
)
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.schemas.user import TokenResponse, UserCreate, UserLogin


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repo = user_repository

    async def register_user(self, user_in: UserCreate) -> User:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise UserAlreadyExistsException("A user with this email address is already registered")

        user = User(
            email=user_in.email.lower(),
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True,
        )
        return await self.user_repo.create(user)

    async def authenticate_user(self, credentials: UserLogin) -> TokenResponse:
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsException("User account is deactivated")

        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token = create_refresh_token(user_id=user.id, role=user.role.value)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_user_tokens(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise InvalidCredentialsException("Invalid or expired refresh token") from exc

        token_type = payload.get("type")
        if token_type != "refresh":
            raise InvalidCredentialsException("Invalid token type")

        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise InvalidCredentialsException("Malformed token payload")

        user = await self.user_repo.get_by_id(int(user_id_raw))
        if not user or not user.is_active:
            raise InvalidCredentialsException("User not found or inactive")

        new_access_token = create_access_token(user_id=user.id, role=user.role.value)
        new_refresh_token = create_refresh_token(user_id=user.id, role=user.role.value)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )
