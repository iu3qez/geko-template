"""Autenticazione OAuth 2.1 dell'MCP GEKO via Scalekit.

Usa il provider ufficiale `ScalekitProvider` di FastMCP (stesso approccio del
progetto MQC_Award, già funzionante coi client Claude). Scalekit è
l'Authorization Server; il server MCP è Resource Server e valida i token
tramite le chiavi pubbliche dell'environment Scalekit.

`build_auth()` ritorna None se le env Scalekit non sono configurate, così i
test e lo sviluppo locale girano senza autenticazione.
"""

import logging
import os

log = logging.getLogger("geko.mcp.auth")


def build_auth():
    """Costruisce il provider Scalekit dalle env; None se non configurato."""
    env_url = os.environ.get("SCALEKIT_ENVIRONMENT_URL")
    resource_id = os.environ.get("SCALEKIT_RESOURCE_ID")
    base_url = os.environ.get("MCP_PUBLIC_URL")

    if not all([env_url, resource_id, base_url]):
        log.warning("Env Scalekit incomplete: MCP avviato SENZA auth.")
        return None

    from fastmcp.server.auth.providers.scalekit import ScalekitProvider

    return ScalekitProvider(
        environment_url=env_url,
        resource_id=resource_id,
        base_url=base_url,
    )
