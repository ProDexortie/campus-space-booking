from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from src.models.space import Space


@pytest.mark.asyncio
async def test_create_booking_success(
    client: AsyncClient,
    sample_space: Space,
    student_auth_headers: dict[str, str],
) -> None:
    start_time = datetime.now(UTC) + timedelta(days=1, hours=2)
    end_time = start_time + timedelta(hours=2)

    payload = {
        "space_id": sample_space.id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    response = await client.post("/api/v1/bookings", json=payload, headers=student_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["space_id"] == sample_space.id
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_create_booking_overlap_conflict_409(
    client: AsyncClient,
    sample_space: Space,
    student_auth_headers: dict[str, str],
) -> None:
    start_time = datetime.now(UTC) + timedelta(days=2, hours=10)
    end_time = start_time + timedelta(hours=2)

    payload = {
        "space_id": sample_space.id,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    first_resp = await client.post("/api/v1/bookings", json=payload, headers=student_auth_headers)
    assert first_resp.status_code == 201

    # Attempt to book an overlapping time slot (starts 1 hour before first ends)
    overlap_payload = {
        "space_id": sample_space.id,
        "start_time": (start_time + timedelta(hours=1)).isoformat(),
        "end_time": (end_time + timedelta(hours=1)).isoformat(),
    }
    conflict_resp = await client.post("/api/v1/bookings", json=overlap_payload, headers=student_auth_headers)
    assert conflict_resp.status_code == 409
    assert "already reserved" in conflict_resp.json()["detail"]


@pytest.mark.asyncio
async def test_create_booking_in_the_past_rejected(
    client: AsyncClient,
    sample_space: Space,
    student_auth_headers: dict[str, str],
) -> None:
    past_start = datetime.now(UTC) - timedelta(days=1)
    past_end = past_start + timedelta(hours=1)

    payload = {
        "space_id": sample_space.id,
        "start_time": past_start.isoformat(),
        "end_time": past_end.isoformat(),
    }
    response = await client.post("/api/v1/bookings", json=payload, headers=student_auth_headers)
    assert response.status_code == 400
    assert "in the past" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_my_bookings_list(
    client: AsyncClient,
    sample_space: Space,
    student_auth_headers: dict[str, str],
) -> None:
    start_time = datetime.now(UTC) + timedelta(days=3, hours=1)
    end_time = start_time + timedelta(hours=1)

    await client.post(
        "/api/v1/bookings",
        json={
            "space_id": sample_space.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        headers=student_auth_headers,
    )

    response = await client.get("/api/v1/bookings/my", headers=student_auth_headers)
    assert response.status_code == 200
    bookings = response.json()
    assert isinstance(bookings, list)
    assert len(bookings) >= 1


@pytest.mark.asyncio
async def test_cancel_booking_workflow(
    client: AsyncClient,
    sample_space: Space,
    student_auth_headers: dict[str, str],
) -> None:
    start_time = datetime.now(UTC) + timedelta(days=4)
    end_time = start_time + timedelta(hours=1)

    create_resp = await client.post(
        "/api/v1/bookings",
        json={
            "space_id": sample_space.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        headers=student_auth_headers,
    )
    booking_id = create_resp.json()["id"]

    cancel_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=student_auth_headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    second_cancel = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=student_auth_headers,
    )
    assert second_cancel.status_code == 400
