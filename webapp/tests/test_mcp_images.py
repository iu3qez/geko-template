"""Test dei tool MCP per l'upload immagini per-articolo."""

import base64

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import app.mcp.server as server_mod
from app.services import article_ops

PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture
def patch_session(db, monkeypatch):
    class _CtxSession:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(server_mod, "async_session", lambda: _CtxSession())


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(article_ops, "UPLOADS_DIR", tmp_path / "uploads")
    return tmp_path / "uploads"


async def _crea(client):
    return (await client.call_tool(
        "crea_articolo", {"titolo": "QMX", "contenuto_md": "![s](x.png)"}
    )).data


async def test_carica_immagine_tool(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        res = (await client.call_tool(
            "carica_immagine",
            {"articolo_id": art["id"], "nome_file": "x.png", "contenuto_base64": PNG_B64},
        )).data
        assert res["nome_file"] == "x.png"
        assert res["url"] == f"/uploads/articoli/{art['id']}/x.png"
        assert res["bytes"] > 0


async def test_carica_immagine_accepts_data_uri(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        res = (await client.call_tool(
            "carica_immagine",
            {
                "articolo_id": art["id"],
                "nome_file": "x.png",
                "contenuto_base64": f"data:image/png;base64,{PNG_B64}",
            },
        )).data
        assert res["bytes"] == len(base64.b64decode(PNG_B64))


async def test_lista_immagini_tool(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        await client.call_tool(
            "carica_immagine",
            {"articolo_id": art["id"], "nome_file": "x.png", "contenuto_base64": PNG_B64},
        )
        imgs = (await client.call_tool("lista_immagini", {"articolo_id": art["id"]})).data
        assert [i["nome_file"] for i in imgs] == ["x.png"]


async def test_elimina_immagine_tool(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        await client.call_tool(
            "carica_immagine",
            {"articolo_id": art["id"], "nome_file": "x.png", "contenuto_base64": PNG_B64},
        )
        res = (await client.call_tool(
            "elimina_immagine", {"articolo_id": art["id"], "nome_file": "x.png"}
        )).data
        assert res["ok"] is True
        imgs = (await client.call_tool("lista_immagini", {"articolo_id": art["id"]})).data
        assert imgs == []


async def test_overwrite_false_conflict_raises(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        args = {"articolo_id": art["id"], "nome_file": "x.png", "contenuto_base64": PNG_B64}
        await client.call_tool("carica_immagine", args)
        with pytest.raises(ToolError):
            await client.call_tool("carica_immagine", {**args, "sovrascrivi": False})


async def test_anteprima_typst_resolves_article_images(patch_session, uploads_tmp):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        typ = (await client.call_tool(
            "anteprima_typst",
            {"contenuto_md": "![s](x.png)", "articolo_id": art["id"]},
        )).data
        assert f'/data/uploads/articoli/{art["id"]}/x.png' in typ
