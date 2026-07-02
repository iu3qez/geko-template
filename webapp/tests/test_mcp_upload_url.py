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
