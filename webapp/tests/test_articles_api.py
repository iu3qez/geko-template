import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


@pytest.fixture
def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def test_create_and_get_article(client):
    async with client as c:
        resp = await c.post("/api/articles", json={"titolo": "T", "contenuto_md": "x"})
        assert resp.status_code == 200
        art = resp.json()
        assert art["titolo"] == "T"

        got = await c.get(f"/api/articles/{art['id']}")
        assert got.status_code == 200
        assert got.json()["id"] == art["id"]
