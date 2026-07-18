import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def api_client():
    from platform.api import create_app
    app = create_app({
        "environment": "test",
        "database_url": "",
        "redis_url": "",
        "enable_database": False,
        "enable_redis": False,
        "enable_monolith": False,
    })
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthAPI:
    @pytest.mark.asyncio
    async def test_liveness(self, api_client):
        response = await api_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness(self, api_client):
        response = await api_client.get("/health/ready")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status(self, api_client):
        response = await api_client.get("/health/status")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data


class TestPatientAPI:
    @pytest.mark.asyncio
    async def test_search_empty(self, api_client):
        response = await api_client.get("/api/v1/patients/?q=&lab_id=")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, api_client):
        response = await api_client.get("/api/v1/patients/nonexistent")
        assert response.status_code == 404


class TestOrderAPI:
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, api_client):
        response = await api_client.get("/api/v1/orders/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_missing_fields(self, api_client):
        response = await api_client.post("/api/v1/orders/", json={})
        assert response.status_code == 400


class TestLabAPI:
    @pytest.mark.asyncio
    async def test_get_nonexistent(self, api_client):
        response = await api_client.get("/api/v1/labs/nonexistent")
        assert response.status_code == 404


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_login(self, api_client):
        response = await api_client.post("/api/v1/auth/login", json={"username": "admin", "password": "pass"})
        assert response.status_code == 200
