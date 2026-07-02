import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_mcp_endpoint_requires_auth_or_mounted():
    """Con auth attiva: 401. Senza env (test): l'endpoint /mcp esiste (non è il catch-all SPA).

    Nota: httpx ASGITransport non esegue il lifespan per default, quindi il
    session manager di FastMCP non è inizializzato in questo test e la
    richiesta produce un errore 500 invece di una risposta JSON-RPC valida.
    Va bene: l'obiettivo è dimostrare che la richiesta raggiunge il sub-app
    MCP montato su /mcp, non il catch-all SPA (che risponderebbe 405, dato
    che gestisce solo GET, o comunque non produrrebbe l'errore specifico del
    session manager FastMCP). Usiamo raise_app_exceptions=False per poter
    ispezionare lo status code invece di far propagare l'eccezione.
    """
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        # Il catch-all SPA non registra la route POST -> 405 (Method Not
        # Allowed) se la richiesta non raggiunge /mcp; 404 se raggiungesse un
        # path non gestito. Nessuno dei due deve verificarsi: la richiesta
        # deve arrivare al sub-app MCP montato.
        assert resp.status_code not in (404, 405)


def test_mcp_mounted_before_spa_catchall():
    """Il mount /mcp deve precedere il catch-all SPA, altrimenti la SPA
    intercetta il traffico GET dell'MCP (incl. il discovery OAuth)."""
    from app.main import app
    paths = [getattr(r, "path", None) for r in app.routes]
    assert "/mcp" in paths, "il sub-app MCP non è montato su /mcp"
    mcp_idx = paths.index("/mcp")
    catchall_idx = next(
        i for i, p in enumerate(paths) if p == "/{full_path:path}"
    )
    assert mcp_idx < catchall_idx, (
        "il mount /mcp deve essere registrato PRIMA del catch-all SPA"
    )
