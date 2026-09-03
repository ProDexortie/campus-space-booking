import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient) -> None:
    payload = {
        "email": "newstudent@campus.edu",
        "password": "securepassword123",
        "full_name": "Maria Ivanova",
        "role": "student",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@campus.edu"
    assert data["full_name"] == "Maria Ivanova"
    assert data["role"] == "student"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, student_user: User) -> None:
    payload = {
        "email": student_user.email,
        "password": "anotherpassword",
        "full_name": "Clone User",
        "role": "student",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, student_user: User) -> None:
    payload = {
        "email": student_user.email,
        "password": "password123",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, student_user: User) -> None:
    payload = {
        "email": student_user.email,
        "password": "wrong_password_here",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_profile_authenticated(
    client: AsyncClient,
    student_user: User,
    student_auth_headers: dict[str, str],
) -> None:
    response = await client.get("/api/v1/auth/me", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == student_user.email
    assert data["full_name"] == student_user.full_name


@pytest.mark.asyncio
async def test_get_profile_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
