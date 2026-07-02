"""Firma/verifica di URL di upload immagini (HMAC-SHA256, stdlib).

Coniati dal tool MCP `ottieni_upload_url` e verificati dalla route pubblica
`POST /upload/immagine`, entrambi in-process nel server `geko-mcp`. Il segreto
`GEKO_UPLOAD_SIGNING_KEY` è letto lazy da os.environ, così non serve a
import-time (test lo impostano via monkeypatch) e resta solo sul server.
"""

import base64
import hashlib
import hmac
import json
import os
import time


class TokenError(ValueError):
    """Token assente, malformato, con firma non valida o scaduto."""


class MissingKeyError(TokenError):
    """La chiave di firma del server non è configurata (feature disattivata)."""


def _signing_key() -> bytes:
    key = os.environ.get("GEKO_UPLOAD_SIGNING_KEY")
    if not key:
        raise MissingKeyError("GEKO_UPLOAD_SIGNING_KEY non configurata")
    return key.encode()


def _b64u(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64u_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(payload: str) -> str:
    return _b64u(hmac.new(_signing_key(), payload.encode(), hashlib.sha256).digest())


def mint(articolo_id: int, nome_file: str, exp_epoch: int) -> str:
    """Conia un token firmato che lega articolo, nome file e scadenza."""
    payload = _b64u(
        json.dumps(
            {"aid": articolo_id, "name": nome_file, "exp": exp_epoch},
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    return f"{payload}.{_sign(payload)}"


def verify(token: str, *, now: int | None = None) -> dict:
    """Valida un token e ritorna i claim, oppure solleva TokenError."""
    try:
        payload, sig = token.split(".", 1)
    except ValueError as exc:
        raise TokenError("token malformato") from exc
    if not hmac.compare_digest(sig, _sign(payload)):
        raise TokenError("firma non valida")
    try:
        claims = json.loads(_b64u_decode(payload))
        aid, name, exp = claims["aid"], claims["name"], claims["exp"]
    except (ValueError, KeyError, TypeError) as exc:
        raise TokenError("payload del token non valido") from exc
    if (now if now is not None else int(time.time())) >= exp:
        raise TokenError("token scaduto")
    return claims
