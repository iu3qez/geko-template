"""Test firma/verifica dei token di upload immagini."""

import pytest

from app.mcp import upload_tokens
from app.mcp.upload_tokens import TokenError


@pytest.fixture(autouse=True)
def signing_key(monkeypatch):
    monkeypatch.setenv("GEKO_UPLOAD_SIGNING_KEY", "test-secret-please-change")


def test_mint_verify_roundtrip():
    token = upload_tokens.mint(7, "schema.png", exp_epoch=2_000_000_000)
    claims = upload_tokens.verify(token, now=1_000_000_000)
    assert claims == {"aid": 7, "name": "schema.png", "exp": 2_000_000_000}


def test_tampered_payload_rejected():
    token = upload_tokens.mint(7, "schema.png", exp_epoch=2_000_000_000)
    payload, sig = token.split(".", 1)
    # Cambia il payload (altro articolo) mantenendo la vecchia firma.
    forged = upload_tokens.mint(999, "schema.png", exp_epoch=2_000_000_000).split(".", 1)[0]
    with pytest.raises(TokenError):
        upload_tokens.verify(f"{forged}.{sig}", now=1_000_000_000)


def test_expired_token_rejected():
    token = upload_tokens.mint(7, "x.png", exp_epoch=1_000)
    with pytest.raises(TokenError):
        upload_tokens.verify(token, now=2_000)


def test_malformed_token_rejected():
    with pytest.raises(TokenError):
        upload_tokens.verify("non-un-token", now=1_000)


def test_missing_key_rejected(monkeypatch):
    monkeypatch.delenv("GEKO_UPLOAD_SIGNING_KEY", raising=False)
    with pytest.raises(TokenError):
        upload_tokens.mint(7, "x.png", exp_epoch=2_000_000_000)
