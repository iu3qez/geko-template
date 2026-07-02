import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import app.mcp.server as server_mod


@pytest.fixture
def patch_session(db, monkeypatch):
    """Fa usare ai tool la sessione di test invece del DB reale."""
    class _CtxSession:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(server_mod, "async_session", lambda: _CtxSession())


async def test_crea_articolo_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        result = await client.call_tool(
            "crea_articolo",
            {"titolo": "Antenna", "contenuto_md": "Testo **bold**."},
        )
        data = result.data
        assert data["titolo"] == "Antenna"
        assert data["id"] > 0


async def test_anteprima_typst_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        result = await client.call_tool(
            "anteprima_typst", {"contenuto_md": "Testo **bold**."}
        )
        assert "*bold*" in result.data


async def test_guida_convenzioni_resource(patch_session):
    async with Client(server_mod.mcp) as client:
        content = await client.read_resource("guida://convenzioni")
        assert "box-evidenza" in content[0].text


async def test_modifica_articolo_leaves_other_fields(patch_session):
    async with Client(server_mod.mcp) as client:
        created = (await client.call_tool(
            "crea_articolo",
            {"titolo": "T", "contenuto_md": "y", "sottotitolo": "S"},
        )).data
        updated = (await client.call_tool(
            "modifica_articolo", {"id": created["id"], "titolo": "T2"}
        )).data
        assert updated["titolo"] == "T2"
        assert updated["sottotitolo"] == "S"  # non passato -> deve restare intatto


async def test_leggi_articolo_missing_raises(patch_session):
    async with Client(server_mod.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool("leggi_articolo", {"id": 999999})


async def test_crea_numero_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        data = (await client.call_tool(
            "crea_numero", {"numero": "68", "mese": "Luglio", "anno": "2026"}
        )).data
        assert data["id"] > 0
        assert data["stato"] == "bozza"


async def test_crea_numero_id_usable_with_assegna(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "69", "mese": "Agosto", "anno": "2026"}
        )).data
        art = (await client.call_tool(
            "crea_articolo", {"titolo": "T", "contenuto_md": "y"}
        )).data
        assigned = (await client.call_tool(
            "assegna_a_numero", {"id": art["id"], "numero_ids": [num["id"]]}
        )).data
        assert [m["id"] for m in assigned["magazines"]] == [num["id"]]


async def test_crea_numero_duplicate_raises(patch_session):
    async with Client(server_mod.mcp) as client:
        await client.call_tool("crea_numero", {"numero": "70", "mese": "Luglio", "anno": "2026"})
        with pytest.raises(ToolError):
            await client.call_tool("crea_numero", {"numero": "70", "mese": "Agosto", "anno": "2026"})


async def test_crea_numero_invalid_month_raises(patch_session):
    async with Client(server_mod.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "crea_numero", {"numero": "71", "mese": "Luglioo", "anno": "2026"}
            )


async def test_modifica_numero_updates_stato(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "72", "mese": "Luglio", "anno": "2026"}
        )).data
        await client.call_tool("modifica_numero", {"id": num["id"], "stato": "pubblicato"})
        numeri = (await client.call_tool("lista_numeri", {})).data
        assert next(n for n in numeri if n["id"] == num["id"])["stato"] == "pubblicato"


async def test_elimina_numero_with_articles_then_forza(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "73", "mese": "Luglio", "anno": "2026"}
        )).data
        art = (await client.call_tool(
            "crea_articolo", {"titolo": "T", "contenuto_md": "y"}
        )).data
        await client.call_tool("assegna_a_numero", {"id": art["id"], "numero_ids": [num["id"]]})
        with pytest.raises(ToolError):
            await client.call_tool("elimina_numero", {"id": num["id"]})
        res = (await client.call_tool(
            "elimina_numero", {"id": num["id"], "forza": True}
        )).data
        assert res["eliminato"] == num["id"]
