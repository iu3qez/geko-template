import pytest

from app.mcp import auth as auth_mod


class _FakeScalekit:
    def __init__(self, ok: bool):
        self._ok = ok
        self.last_options = None

    def validate_token(self, token, options=None):
        self.last_options = options
        if not self._ok:
            raise ValueError("invalid token")
        return {"client_id": "cli_1", "scope": "mcp:tools", "exp": 9999999999}


async def test_verify_token_invalid_returns_none(monkeypatch):
    verifier = auth_mod.ScalekitTokenVerifier(
        scalekit=_FakeScalekit(ok=False), resource_id="res_x"
    )
    assert await verifier.verify_token("bad") is None


async def test_verify_token_valid_returns_access_token(monkeypatch):
    verifier = auth_mod.ScalekitTokenVerifier(
        scalekit=_FakeScalekit(ok=True), resource_id="res_x"
    )
    tok = await verifier.verify_token("good")
    assert tok is not None
    assert tok.client_id == "cli_1"
    assert "mcp:tools" in tok.scopes
    assert "res_x" in verifier._scalekit.last_options.audience


async def test_verify_token_non_dict_result_fails_closed():
    class _WeirdScalekit:
        def validate_token(self, token, options=None):
            return True  # non-dict truthy

    verifier = auth_mod.ScalekitTokenVerifier(
        scalekit=_WeirdScalekit(), resource_id="res_x"
    )
    assert await verifier.verify_token("x") is None


def test_build_auth_none_without_env(monkeypatch):
    for var in ("SCALEKIT_ENVIRONMENT_URL", "SCALEKIT_CLIENT_ID",
                "SCALEKIT_CLIENT_SECRET", "SCALEKIT_RESOURCE_ID"):
        monkeypatch.delenv(var, raising=False)
    assert auth_mod.build_auth() is None
