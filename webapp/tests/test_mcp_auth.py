from app.mcp import auth as auth_mod


def test_build_auth_none_without_env(monkeypatch):
    for var in ("SCALEKIT_ENVIRONMENT_URL", "SCALEKIT_RESOURCE_ID", "MCP_PUBLIC_URL"):
        monkeypatch.delenv(var, raising=False)
    assert auth_mod.build_auth() is None


def test_build_auth_returns_scalekit_provider(monkeypatch):
    # build_auth deve costruire il provider ufficiale con le env corrette.
    import fastmcp.server.auth.providers.scalekit as sk

    captured = {}

    class _StubProvider:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(sk, "ScalekitProvider", _StubProvider)
    monkeypatch.setenv("SCALEKIT_ENVIRONMENT_URL", "https://org.scalekit.dev")
    monkeypatch.setenv("SCALEKIT_RESOURCE_ID", "res_123")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://geko-mcp.fabris.me/")

    provider = auth_mod.build_auth()

    assert isinstance(provider, _StubProvider)
    assert captured["environment_url"] == "https://org.scalekit.dev"
    assert captured["resource_id"] == "res_123"
    assert captured["base_url"] == "https://geko-mcp.fabris.me/"
