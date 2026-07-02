"""Test d'integrazione dell'MCP CON lifespan in esecuzione.

httpx.ASGITransport NON esegue il lifespan di default: il session manager
di FastMCP non viene inizializzato e /mcp/ risponde con errore 500 invece
che con il flusso OAuth reale (vedi tests/test_mcp_mount.py). Qui usiamo
asgi-lifespan.LifespanManager per eseguire il lifespan davvero e osservare
il comportamento reale del 401 + WWW-Authenticate (RFC 9728) e della
route di discovery, in modo hermetico (nessuna rete, nessuna chiamata a
Scalekit: un token che fallisce la validazione va benissimo).

Riproduce anche lo stesso pattern di montaggio di app.main (mount di
mcp_app su /mcp + route .well-known duplicate alla radice) per verificare
che l'URL annunciato in resource_metadata sia effettivamente raggiungibile.
"""

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import AnyHttpUrl

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider, TokenVerifier

MCP_PUBLIC_URL = "https://geko-mcp.fabris.me"


class _StubVerifier(TokenVerifier):
    """Rifiuta sempre: basta a esercitare il percorso 401, senza rete."""

    async def verify_token(self, token: str):
        return None


def _build_app(mount_well_known_at_root: bool) -> FastAPI:
    auth = RemoteAuthProvider(
        token_verifier=_StubVerifier(),
        authorization_servers=[AnyHttpUrl("https://example.scalekit.example/as")],
        base_url=MCP_PUBLIC_URL,
    )
    mcp = FastMCP(name="test-geko-mcp", auth=auth)
    mcp_app = mcp.http_app(path="/")

    app = FastAPI(lifespan=lambda a: mcp_app.lifespan(a))
    if mount_well_known_at_root:
        # Stesso fix applicato in app.main: senza queste route duplicate a
        # livello di radice, l'URL annunciato in resource_metadata (radice
        # del dominio pubblico) non è raggiungibile perché le route
        # dell'auth provider vivono altrimenti solo dentro il sub-app
        # montato su /mcp.
        for route in mcp.auth.get_well_known_routes(mcp_path="/"):
            app.router.routes.append(route)
    app.mount("/mcp", mcp_app)
    return app


async def test_unauthenticated_mcp_request_returns_401_with_www_authenticate():
    app = _build_app(mount_well_known_at_root=True)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
            assert resp.status_code == 401
            assert "WWW-Authenticate" in resp.headers
            assert "resource_metadata=" in resp.headers["WWW-Authenticate"]


async def test_resource_metadata_url_advertised_is_actually_reachable():
    """Indagine FIX #3: dove viene servita la metadata RFC 9728 e l'URL
    annunciato dal 401 corrispondono?

    Con SOLO il mount su /mcp (senza il fix), la metadata annunciata da
    WWW-Authenticate punta alla radice del dominio pubblico
    (https://geko-mcp.fabris.me/.well-known/oauth-protected-resource) ma è
    raggiungibile solo su /mcp/.well-known/oauth-protected-resource -> 404
    alla radice. Con il fix (route duplicate a livello di root, applicato
    in app.main) l'URL annunciato risponde 200.
    """
    app = _build_app(mount_well_known_at_root=True)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
            www_auth = resp.headers["WWW-Authenticate"]
            # Estrae il valore di resource_metadata="..."
            marker = 'resource_metadata="'
            start = www_auth.index(marker) + len(marker)
            end = www_auth.index('"', start)
            advertised_url = www_auth[start:end]
            assert advertised_url == f"{MCP_PUBLIC_URL}/.well-known/oauth-protected-resource"

            # L'URL annunciato deve essere raggiungibile alla radice del
            # dominio (non solo sotto /mcp).
            root_resp = await c.get("/.well-known/oauth-protected-resource")
            assert root_resp.status_code == 200
            assert root_resp.json()["resource"] == f"{MCP_PUBLIC_URL}/"

            # Resta raggiungibile anche sotto /mcp (route originale di FastMCP).
            nested_resp = await c.get("/mcp/.well-known/oauth-protected-resource")
            assert nested_resp.status_code == 200


async def test_without_root_well_known_fix_root_metadata_is_404():
    """Prova di regressione: senza il fix (route .well-known duplicate alla
    radice), l'URL annunciato in resource_metadata NON è raggiungibile —
    dimostra il mismatch investigato per FIX #3."""
    app = _build_app(mount_well_known_at_root=False)
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            root_resp = await c.get("/.well-known/oauth-protected-resource")
            assert root_resp.status_code == 404
            nested_resp = await c.get("/mcp/.well-known/oauth-protected-resource")
            assert nested_resp.status_code == 200
