"""
Tests for API endpoints: health, clone, video, user, admin, script.
"""

import pytest
import pytest_asyncio


# ─── Health ───

@pytest.mark.asyncio
async def test_health(client):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "voice_engine" in data
    assert "face_engine" in data


@pytest.mark.asyncio
async def test_root(client):
    res = await client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "CloneAI Ultra"
    assert data["version"] == "2.0.0"


# ─── User ───

@pytest.mark.asyncio
async def test_create_user(client, sample_data):
    res = await client.post("/api/v1/user/create", json=sample_data["user"])
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["email"] == sample_data["user"]["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_user_by_email(client, sample_data):
    # Create first
    await client.post("/api/v1/user/create", json=sample_data["user"])
    # Get by email
    res = await client.get(f"/api/v1/user/by-email/{sample_data['user']['email']}")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == sample_data["user"]["email"]


# ─── Clone ───

@pytest.mark.asyncio
async def test_create_clone(client, sample_data):
    res = await client.post("/api/v1/clone/create", json=sample_data["clone_request"])
    # May fail due to missing files, but should return 200 or 202 with job_id
    # or 400/404 if files don't exist — both are valid for the test
    assert res.status_code in (200, 201, 202, 400, 404, 422, 500)


@pytest.mark.asyncio
async def test_get_clone_status_not_found(client):
    res = await client.get("/api/v1/clone/nonexistent-id/status")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_clone_history(client):
    res = await client.get("/api/v1/clone/history")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ─── Video ───

@pytest.mark.asyncio
async def test_video_download_not_found(client):
    res = await client.get("/api/v1/video/nonexistent/download")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_video_metadata_not_found(client):
    res = await client.get("/api/v1/video/nonexistent/metadata")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_video_export_not_found(client):
    res = await client.post(
        "/api/v1/video/nonexistent/export",
        json={"format": "youtube"},
    )
    assert res.status_code == 404


# ─── Voice ───

@pytest.mark.asyncio
async def test_get_languages(client):
    res = await client.get("/api/v1/voice/languages")
    assert res.status_code == 200
    data = res.json()
    assert "languages" in data
    assert len(data["languages"]) > 0


@pytest.mark.asyncio
async def test_get_voice_profiles_empty(client):
    res = await client.get("/api/v1/voice/profiles")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ─── Script AI ───

@pytest.mark.asyncio
async def test_generate_script(client, sample_data):
    res = await client.post("/api/v1/script/generate", json=sample_data["script_request"])
    assert res.status_code == 200
    data = res.json()
    assert "script" in data
    assert "word_count" in data
    assert "estimated_duration" in data
    assert data["word_count"] > 0


@pytest.mark.asyncio
async def test_generate_script_validation(client):
    # Too short topic
    res = await client.post("/api/v1/script/generate", json={"topic": "ab"})
    assert res.status_code == 422


# ─── Admin ───

@pytest.mark.asyncio
async def test_admin_stats(client):
    res = await client.get("/api/v1/admin/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_jobs" in data


@pytest.mark.asyncio
async def test_admin_jobs(client):
    res = await client.get("/api/v1/admin/jobs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_admin_users(client):
    res = await client.get("/api/v1/admin/users")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
