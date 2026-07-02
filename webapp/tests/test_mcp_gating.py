"""Test della logica di gating dell'MCP (fail-closed in produzione).

Vedi app.main.mcp_should_mount: se l'auth Scalekit non è configurata
(secure=False) l'MCP NON deve montarsi quando ENVIRONMENT=production,
per evitare di esporre un server MCP senza autenticazione. Fuori
produzione (test/sviluppo) resta montato per comodità.
"""

from app.main import mcp_should_mount


def test_secure_always_mounts_regardless_of_environment():
    assert mcp_should_mount(True, "production") is True
    assert mcp_should_mount(True, "") is True
    assert mcp_should_mount(True, "development") is True


def test_insecure_in_production_does_not_mount():
    assert mcp_should_mount(False, "production") is False
    assert mcp_should_mount(False, "Production") is False  # case-insensitive


def test_insecure_outside_production_mounts():
    assert mcp_should_mount(False, "") is True
    assert mcp_should_mount(False, "development") is True
    assert mcp_should_mount(False, "test") is True
