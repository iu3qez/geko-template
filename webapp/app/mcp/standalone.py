"""Entrypoint standalone del server MCP GEKO (transport HTTP).

Gira come servizio dedicato (container `geko-mcp`), separato dalla webapp, per
compatibilità col client MCP di Claude (stesso pattern di MQC_Award).
Condivide il volume `./data` (SQLite) con la webapp, quindi i tool restano
in-process. FastMCP espone l'endpoint su `/mcp`.

Avvio: `python -m app.mcp.standalone`
"""

import asyncio
import os

from app.database import init_db
from app.mcp.server import mcp


def main() -> None:
    # Il volume DB è condiviso con la webapp, ma il container MCP potrebbe
    # avviarsi per primo: assicura che le tabelle esistano.
    asyncio.run(init_db())
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("MCP_PORT", "3003")),
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
