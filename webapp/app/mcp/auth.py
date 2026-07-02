"""Autenticazione OAuth 2.1 dell'MCP GEKO delegata a Scalekit.

Scalekit è l'Authorization Server; questo modulo implementa il lato
Resource Server: valida i JWT in ingresso e, tramite RemoteAuthProvider,
espone il discovery /.well-known/oauth-protected-resource (RFC 9728).
Riusa la validazione già collaudata in ../mcp-proxy/auth_proxy.py.
"""

import asyncio
import logging
import os
from typing import Optional

from pydantic import AnyHttpUrl

from fastmcp.server.auth import AccessToken, RemoteAuthProvider, TokenVerifier

log = logging.getLogger("geko.mcp.auth")


class ScalekitTokenVerifier(TokenVerifier):
    """Valida i bearer token via Scalekit SDK e ne estrae i claim."""

    def __init__(self, scalekit, resource_id: str):
        super().__init__()
        self._scalekit = scalekit
        self._resource_id = resource_id if resource_id.startswith("res_") else f"res_{resource_id}"

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        from scalekit.common.scalekit import TokenValidationOptions

        options = TokenValidationOptions(audience=[self._resource_id])
        try:
            claims = await asyncio.to_thread(
                self._scalekit.validate_token, token, options=options
            )
        except Exception as e:  # token invalido/scaduto/audience errato
            log.info("Validazione token fallita: %s", e)
            return None

        if not isinstance(claims, dict):
            log.info("Validazione token: claim non validi (tipo inatteso)")
            return None

        scope = claims.get("scope", "")
        scopes = claims.get("scopes") or (scope.split() if scope else [])
        return AccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("sub") or "unknown",
            scopes=list(scopes),
            expires_at=claims.get("exp"),
            claims=claims,
        )


def build_auth() -> Optional[RemoteAuthProvider]:
    """Costruisce il provider auth dalle env; None se non configurato."""
    env_url = os.environ.get("SCALEKIT_ENVIRONMENT_URL")
    client_id = os.environ.get("SCALEKIT_CLIENT_ID")
    client_secret = os.environ.get("SCALEKIT_CLIENT_SECRET")
    resource_id = os.environ.get("SCALEKIT_RESOURCE_ID")
    public_url = os.environ.get("MCP_PUBLIC_URL")

    if not all([env_url, client_id, client_secret, resource_id, public_url]):
        log.warning("Env Scalekit incomplete: MCP avviato SENZA auth.")
        return None

    from scalekit import ScalekitClient

    scalekit = ScalekitClient(env_url=env_url, client_id=client_id, client_secret=client_secret)
    verifier = ScalekitTokenVerifier(scalekit=scalekit, resource_id=resource_id)

    # NB: nel compose la var è sempre presente ma può essere vuota (${VAR:-}),
    # quindi `or` (non il default di .get) per ricadere sull'AS composto.
    as_url = (
        os.environ.get("SCALEKIT_AUTHORIZATION_SERVER")
        or f"{env_url}/resources/{resource_id}"
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[AnyHttpUrl(as_url)],
        base_url=public_url,
    )
