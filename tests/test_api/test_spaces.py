import pytest
from httpx import AsyncClient

from src.models.space import Space


@pytest.mark.asyncio
async def test_list_spaces(client: AsyncClient, sample_space: Space) -> None:
    response = await client.get("/api/v1/spaces")
    assert response.status_code == 200
    spaces = response.json()
    assert len(spaces) >= 1
    assert any(s["id"] == sample_space.id for s in spaces)


@pytest.mark.asyncio
async def test_create_space_admin_success(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    payload = {
        "title": "Meeting Room Beta",
        "description": "Medium conference room with 4K projector",
        "space_type": "meeting_room",
        "capacity": 8,
        "has_projector": True,
        "has_whiteboard": True,
        "is_active": True,
    }
    response = await client.post("/api/v1/spaces", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Meeting Room Beta"
    assert data["capacity"] == 8
    assert data["has_projector"] is True


@pytest.mark.asyncio
async def test_create_space_forbidden_for_student(
    client: AsyncClient,
    student_auth_headers: dict[str, str],
) -> None:
    payload = {
        "title": "Unauthorized Space",
        "capacity": 2,
    }
    response = await client.post("/api/v1/spaces", json=payload, headers=student_auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_space_by_id(client: AsyncClient, sample_space: Space) -> None:
    response = await client.get(f"/api/v1/spaces/{sample_space.id}")
    assert response.status_code == 200
    assert response.json()["title"] == sample_space.title


@pytest.mark.asyncio
async def test_get_nonexistent_space(client: AsyncClient) -> None:
    response = await client.get("/api/v1/spaces/999999")
    assert response.status_code == 404
