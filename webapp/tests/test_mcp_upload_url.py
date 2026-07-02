"""Test del tool MCP ottieni_upload_url e della route /upload/immagine."""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import app.mcp.server as server_mod
from app.mcp import upload_tokens
from app.services import article_ops


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("GEKO_UPLOAD_SIGNING_KEY", "test-secret-please-change")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://geko-mcp.example/")


@pytest.fixture
def patch_session(db, monkeypatch):
    class _CtxSession:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(server_mod, "async_session", lambda: _CtxSession())


async def _crea(client):
    return (await client.call_tool(
        "crea_articolo", {"titolo": "QMX", "contenuto_md": "![s](x.png)"}
    )).data


async def test_ottieni_upload_url_ritorna_url_firmato(patch_session):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        res = (await client.call_tool(
            "ottieni_upload_url",
            {"articolo_id": art["id"], "nomi_file": ["a.png", "schema.svg"]},
        )).data
        assert [r["nome_file"] for r in res] == ["a.png", "schema.svg"]
        for r in res:
            assert r["url"].startswith("https://geko-mcp.example/upload/immagine?token=")
            token = r["url"].split("token=", 1)[1]
            claims = upload_tokens.verify(token, now=0)
            assert claims["aid"] == art["id"]
            assert claims["name"] == r["nome_file"]
            assert claims["exp"] == r["scade_a"]


async def test_ottieni_upload_url_articolo_inesistente(patch_session):
    async with Client(server_mod.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "ottieni_upload_url", {"articolo_id": 9999, "nomi_file": ["a.png"]}
            )


async def test_ottieni_upload_url_estensione_non_valida(patch_session):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        with pytest.raises(ToolError):
            await client.call_tool(
                "ottieni_upload_url",
                {"articolo_id": art["id"], "nomi_file": ["malware.exe"]},
            )


import base64

import httpx

# PNG 1x1 valido (stesso usato negli altri test immagini)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(article_ops, "UPLOADS_DIR", tmp_path / "uploads")
    return tmp_path / "uploads"


async def _post_upload(token: str, filename: str, data: bytes):
    app = server_mod.mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.post(
            "/upload/immagine",
            params={"token": token},
            files={"file": (filename, data, "image/png")},
        )


async def test_upload_immagine_happy_path(db, patch_session, uploads_tmp):
    art = await article_ops.create_article(db, titolo="QMX", contenuto_md="![s](x.png)")
    token = upload_tokens.mint(art["id"], "x.png", exp_epoch=2_000_000_000)
    resp = await _post_upload(token, "qualsiasi-nome-locale.png", PNG_BYTES)
    assert resp.status_code == 200
    body = resp.json()
    assert body["nome_file"] == "x.png"
    assert body["url"] == f"/uploads/articoli/{art['id']}/x.png"
    assert (uploads_tmp / "articoli" / str(art["id"]) / "x.png").read_bytes() == PNG_BYTES


async def test_upload_immagine_token_invalido(db, patch_session, uploads_tmp):
    resp = await _post_upload("token.fasullo", "x.png", PNG_BYTES)
    assert resp.status_code == 401


async def test_upload_immagine_file_mancante(db, patch_session, uploads_tmp):
    art = await article_ops.create_article(db, titolo="QMX", contenuto_md="x")
    token = upload_tokens.mint(art["id"], "x.png", exp_epoch=2_000_000_000)
    app = server_mod.mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/upload/immagine", params={"token": token})
    assert resp.status_code == 400
