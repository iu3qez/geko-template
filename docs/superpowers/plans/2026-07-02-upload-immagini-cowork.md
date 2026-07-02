# Upload immagini da Cowork via URL firmato — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dare a Claude Cowork un canale binario affidabile per caricare le immagini di un articolo su Geko, senza base64 nel modello, tramite un URL firmato coniato via tool MCP e caricato con `curl -F`.

**Architecture:** Un tool MCP (`ottieni_upload_url`) — protetto dall'OAuth Scalekit già attivo sul connettore — conia URL firmati HMAC a scadenza breve, uno per nome file. Una route custom pubblica di FastMCP (`POST /upload/immagine`), non protetta dal middleware auth, riceve il multipart, **verifica la firma** e salva col nome esatto riusando `article_ops.save_article_image`. Firma e verifica avvengono nello stesso processo `geko-mcp`, che condivide il volume `./data`.

**Tech Stack:** Python, FastMCP v3 (`@mcp.tool`, `@mcp.custom_route`), Starlette (Request/JSONResponse), stdlib `hmac`/`hashlib`/`json`/`base64`, SQLAlchemy async, pytest-asyncio, httpx (ASGITransport per i test di route).

## Global Constraints

- Riuso obbligatorio di `app/services/article_ops.py` come fonte unica (no duplicazione della logica immagini). Valori verbatim: `ALLOWED_IMAGE_EXTENSIONS = {".jpg",".jpeg",".png",".gif",".webp",".svg"}`, `MAX_IMAGE_BYTES = 10*1024*1024`, path per-articolo `data/uploads/articoli/{id}/{nome_file}`.
- Nessuna nuova dipendenza runtime: solo stdlib per firma/verifica.
- Secret **`GEKO_UPLOAD_SIGNING_KEY`** letto **lazy** da `os.environ` dentro le funzioni (mai a import-time), così i test lo impostano via `monkeypatch.setenv`. Se assente: tool solleva `ValueError`, route risponde 503.
- URL assoluto costruito da `MCP_PUBLIC_URL` (già env del container `geko-mcp`).
- Lingua: italiano per docstring/commenti/messaggi d'errore, inglese per il codice.
- Test in `webapp/tests/`, `asyncio_mode=auto` (già in `pytest.ini`); eseguire in venv locale (`webapp/.venv`) per PEP 668.
- Il token lega `articolo_id` **e** `nome_file`; la route usa il nome dal token, non quello del multipart.

---

### Task 1: Modulo firma/verifica token (`upload_tokens.py`)

**Files:**
- Create: `webapp/app/mcp/upload_tokens.py`
- Test: `webapp/tests/test_upload_tokens.py`

**Interfaces:**
- Consumes: `os.environ["GEKO_UPLOAD_SIGNING_KEY"]`.
- Produces:
  - `class TokenError(ValueError)`
  - `mint(articolo_id: int, nome_file: str, exp_epoch: int) -> str`
  - `verify(token: str, *, now: int | None = None) -> dict` → `{"aid": int, "name": str, "exp": int}`; solleva `TokenError` su malformazione, firma errata, scadenza, o chiave mancante.

- [ ] **Step 1: Write the failing test**

```python
# webapp/tests/test_upload_tokens.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_upload_tokens.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.mcp.upload_tokens'`

- [ ] **Step 3: Write minimal implementation**

```python
# webapp/app/mcp/upload_tokens.py
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


def _signing_key() -> bytes:
    key = os.environ.get("GEKO_UPLOAD_SIGNING_KEY")
    if not key:
        raise TokenError("GEKO_UPLOAD_SIGNING_KEY non configurata")
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
    claims = json.loads(_b64u_decode(payload))
    if (now if now is not None else int(time.time())) >= claims["exp"]:
        raise TokenError("token scaduto")
    return claims
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_upload_tokens.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add webapp/app/mcp/upload_tokens.py webapp/tests/test_upload_tokens.py
git commit -m "feat(mcp): firma/verifica token per upload immagini via URL firmato"
```

---

### Task 2: Tool MCP `ottieni_upload_url`

**Files:**
- Modify: `webapp/app/mcp/server.py` (import section righe 1-11; nuovo tool dopo `elimina_immagine`)
- Test: `webapp/tests/test_mcp_upload_url.py`

**Interfaces:**
- Consumes: `upload_tokens.mint`, `article_ops.get_article`, `article_ops._sanitize_nome_file`, `article_ops.ALLOWED_IMAGE_EXTENSIONS`, env `MCP_PUBLIC_URL` + `GEKO_UPLOAD_SIGNING_KEY`.
- Produces: tool `ottieni_upload_url(articolo_id: int, nomi_file: list[str], scadenza_minuti: int = 15) -> list[dict]`, ogni elemento `{"nome_file": str, "url": str, "scade_a": int}`.

- [ ] **Step 1: Write the failing test**

```python
# webapp/tests/test_mcp_upload_url.py
"""Test del tool MCP ottieni_upload_url e della route /upload/immagine."""

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import app.mcp.server as server_mod
from app.mcp import upload_tokens
from app.services import article_ops


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("GEKO_UPLOAD_SIGNING_KEY", "test-secret-please-change")
    monkeypatch.setenv("MCP_PUBLIC_URL", "https://geko-mcp.example/")


@pytest.fixture
def patch_session(db, monkeypatch):
    class _CtxSession:
        async def __aenter__(self):
            return db

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(server_mod, "async_session", lambda: _CtxSession())


async def _crea(client):
    return (await client.call_tool(
        "crea_articolo", {"titolo": "QMX", "contenuto_md": "![s](x.png)"}
    )).data


async def test_ottieni_upload_url_ritorna_url_firmato(patch_session):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        res = (await client.call_tool(
            "ottieni_upload_url",
            {"articolo_id": art["id"], "nomi_file": ["a.png", "schema.svg"]},
        )).data
        assert [r["nome_file"] for r in res] == ["a.png", "schema.svg"]
        for r in res:
            assert r["url"].startswith("https://geko-mcp.example/upload/immagine?token=")
            token = r["url"].split("token=", 1)[1]
            claims = upload_tokens.verify(token, now=0)
            assert claims["aid"] == art["id"]
            assert claims["name"] == r["nome_file"]
            assert claims["exp"] == r["scade_a"]


async def test_ottieni_upload_url_articolo_inesistente(patch_session):
    async with Client(server_mod.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "ottieni_upload_url", {"articolo_id": 9999, "nomi_file": ["a.png"]}
            )


async def test_ottieni_upload_url_estensione_non_valida(patch_session):
    async with Client(server_mod.mcp) as client:
        art = await _crea(client)
        with pytest.raises(ToolError):
            await client.call_tool(
                "ottieni_upload_url",
                {"articolo_id": art["id"], "nomi_file": ["malware.exe"]},
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_mcp_upload_url.py::test_ottieni_upload_url_ritorna_url_firmato -q`
Expected: FAIL con `ToolError` "Unknown tool: ottieni_upload_url" (il tool non esiste ancora)

- [ ] **Step 3: Add imports**

In `webapp/app/mcp/server.py`, sostituire il blocco import (righe 1-11) aggiungendo `os`, `time`, e `upload_tokens`:

```python
"""Server MCP GEKO: tool per creare/gestire articoli conformi al template."""

import base64
import os
import time
from typing import Optional

from fastmcp import FastMCP

from ..database import async_session
from ..services import article_ops
from . import upload_tokens
from .auth import build_auth
from .conventions import CONVENZIONI, markdown_preview
```

- [ ] **Step 4: Add the tool**

In `webapp/app/mcp/server.py`, dopo il tool `elimina_immagine` (prima di `@mcp.resource("guida://convenzioni")`), inserire:

```python
@mcp.tool
async def ottieni_upload_url(
    articolo_id: int,
    nomi_file: list[str],
    scadenza_minuti: int = 15,
) -> list[dict]:
    """Conia URL di upload firmati per le immagini di un articolo.

    Pensato per Claude Cowork: invece del base64, l'agente carica ogni file
    con `curl -F file=@<path-locale> "<url>"` (i byte non passano dal modello).
    `nomi_file` sono i nomi *esatti* usati nel Markdown (es. `![](schema.png)`
    → `"schema.png"`). Formati: PNG, JPG/JPEG, GIF, WEBP, SVG. Gli URL scadono
    dopo `scadenza_minuti` (1-60, default 15). Ritorna
    [{nome_file, url, scade_a}, ...].
    """
    if not 1 <= scadenza_minuti <= 60:
        raise ValueError("scadenza_minuti deve essere tra 1 e 60")
    base = os.environ.get("MCP_PUBLIC_URL", "").rstrip("/")
    if not base:
        raise ValueError("MCP_PUBLIC_URL non configurata")

    async with async_session() as db:
        if await article_ops.get_article(db, articolo_id) is None:
            raise ValueError(f"Articolo {articolo_id} non trovato")

    exp = int(time.time()) + scadenza_minuti * 60
    risultati = []
    for nome in nomi_file:
        nome = article_ops._sanitize_nome_file(nome)
        ext = os.path.splitext(nome)[1].lower()
        if ext not in article_ops.ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Estensione non supportata: {ext or '(nessuna)'}. "
                f"Ammesse: {', '.join(sorted(article_ops.ALLOWED_IMAGE_EXTENSIONS))}"
            )
        token = upload_tokens.mint(articolo_id, nome, exp)
        risultati.append(
            {"nome_file": nome, "url": f"{base}/upload/immagine?token={token}", "scade_a": exp}
        )
    return risultati
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_mcp_upload_url.py -k "ottieni_upload_url" -q`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add webapp/app/mcp/server.py webapp/tests/test_mcp_upload_url.py
git commit -m "feat(mcp): tool ottieni_upload_url conia URL firmati per upload immagini"
```

---

### Task 3: Route custom pubblica `POST /upload/immagine`

**Files:**
- Modify: `webapp/app/mcp/server.py` (aggiungere import Starlette; nuova route dopo il tool `ottieni_upload_url`)
- Test: `webapp/tests/test_mcp_upload_url.py` (aggiungere i test della route)

**Interfaces:**
- Consumes: `upload_tokens.verify`, `article_ops.save_article_image`, `async_session`.
- Produces: route HTTP `POST /upload/immagine?token=<...>` con multipart `file`; 200 `{nome_file, url, bytes}`, 401 token invalido/scaduto, 503 chiave assente, 400 file mancante o errore di validazione (estensione/dimensione).

- [ ] **Step 1: Write the failing test**

Aggiungere in coda a `webapp/tests/test_mcp_upload_url.py`:

```python
import base64

import httpx

# PNG 1x1 valido (stesso usato negli altri test immagini)
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(article_ops, "UPLOADS_DIR", tmp_path / "uploads")
    return tmp_path / "uploads"


async def _post_upload(token: str, filename: str, data: bytes):
    app = server_mod.mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        return await ac.post(
            "/upload/immagine",
            params={"token": token},
            files={"file": (filename, data, "image/png")},
        )


async def test_upload_immagine_happy_path(db, patch_session, uploads_tmp):
    art = await article_ops.create_article(db, titolo="QMX", contenuto_md="![s](x.png)")
    token = upload_tokens.mint(art["id"], "x.png", exp_epoch=2_000_000_000)
    resp = await _post_upload(token, "qualsiasi-nome-locale.png", PNG_BYTES)
    assert resp.status_code == 200
    body = resp.json()
    assert body["nome_file"] == "x.png"
    assert body["url"] == f"/uploads/articoli/{art['id']}/x.png"
    assert (uploads_tmp / "articoli" / str(art["id"]) / "x.png").read_bytes() == PNG_BYTES


async def test_upload_immagine_token_invalido(db, patch_session, uploads_tmp):
    resp = await _post_upload("token.fasullo", "x.png", PNG_BYTES)
    assert resp.status_code == 401


async def test_upload_immagine_file_mancante(db, patch_session, uploads_tmp):
    art = await article_ops.create_article(db, titolo="QMX", contenuto_md="x")
    token = upload_tokens.mint(art["id"], "x.png", exp_epoch=2_000_000_000)
    app = server_mod.mcp.http_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/upload/immagine", params={"token": token})
    assert resp.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_mcp_upload_url.py -k "upload_immagine" -q`
Expected: FAIL — 404 dalla route inesistente (assert 200/400/401 falliscono)

- [ ] **Step 3: Add Starlette imports**

In `webapp/app/mcp/server.py`, aggiungere sotto `from fastmcp import FastMCP`:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse
```

- [ ] **Step 4: Add the route**

In `webapp/app/mcp/server.py`, subito dopo il tool `ottieni_upload_url`, inserire:

```python
@mcp.custom_route("/upload/immagine", methods=["POST"])
async def upload_immagine(request: Request) -> JSONResponse:
    """Riceve un'immagine via multipart e la salva col nome legato nel token.

    Route pubblica (le custom_route FastMCP non passano dal middleware auth):
    l'autenticazione È la firma dell'URL, coniata da `ottieni_upload_url`.
    """
    try:
        claims = upload_tokens.verify(request.query_params.get("token", ""))
    except upload_tokens.TokenError as exc:
        # Chiave server assente → 503; token invalido/scaduto → 401.
        status = 503 if "non configurata" in str(exc) else 401
        return JSONResponse({"error": str(exc)}, status_code=status)

    form = await request.form()
    file = form.get("file")
    if file is None or not hasattr(file, "read"):
        return JSONResponse({"error": "campo 'file' mancante"}, status_code=400)
    content = await file.read()

    try:
        async with async_session() as db:
            res = await article_ops.save_article_image(
                db, claims["aid"], claims["name"], content, sovrascrivi=True
            )
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return JSONResponse(res, status_code=200)
```

> Nota API: in FastMCP v3 `mcp.http_app()` ritorna l'app Starlette con le
> custom_route registrate come route normali (indipendenti dal lifespan MCP),
> quindi i test via `httpx.ASGITransport` le raggiungono senza avviare il
> session manager.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd webapp && source .venv/bin/activate && python -m pytest tests/test_mcp_upload_url.py -q`
Expected: PASS (tutti, tool + route)

- [ ] **Step 6: Commit**

```bash
git add webapp/app/mcp/server.py webapp/tests/test_mcp_upload_url.py
git commit -m "feat(mcp): route pubblica /upload/immagine con auth via firma URL"
```

---

### Task 4: Config env + documentazione

**Files:**
- Modify: `webapp/docker-compose.yml` (env del servizio `geko-mcp`)
- Modify: `webapp/docker-compose.prod.yml` (env del servizio `geko-mcp`)
- Modify: `CLAUDE.md` (sezione "Immagini via MCP")
- Modify: `webapp/README.md` (sezione MCP, se presente)

**Interfaces:**
- Consumes: nulla di nuovo.
- Produces: variabile d'ambiente documentata `GEKO_UPLOAD_SIGNING_KEY` sul container `geko-mcp`.

- [ ] **Step 1: Aggiungere l'env in docker-compose.yml**

Nel blocco `geko-mcp:` → `environment:` di `webapp/docker-compose.yml`, dopo `MCP_PUBLIC_URL`, aggiungere:

```yaml
      - GEKO_UPLOAD_SIGNING_KEY=${GEKO_UPLOAD_SIGNING_KEY:-}
```

- [ ] **Step 2: Aggiungere l'env in docker-compose.prod.yml**

Stessa riga nel blocco `geko-mcp:` → `environment:` di `webapp/docker-compose.prod.yml`, dopo `MCP_PUBLIC_URL`:

```yaml
      - GEKO_UPLOAD_SIGNING_KEY=${GEKO_UPLOAD_SIGNING_KEY:-}
```

- [ ] **Step 3: Documentare in CLAUDE.md**

Nella tabella dei tool MCP aggiungere la riga:

```markdown
| `ottieni_upload_url` | Conia URL firmati per upload immagini via `curl -F` (per Cowork, no base64) |
```

E nella sezione "Immagini via MCP", aggiungere un paragrafo:

```markdown
### Upload da Cowork (URL firmato, no base64)

Quando l'agente ha i file in locale (Cowork) il base64 è impraticabile:
`ottieni_upload_url(articolo_id, nomi_file=[...])` conia un URL firmato HMAC
per nome file; l'agente carica con `curl -F file=@<path> "<url>"` sulla route
pubblica `POST /upload/immagine` del server `geko-mcp` (le custom_route FastMCP
non passano dal middleware auth: la firma È l'auth). La route riusa
`save_article_image` (nome esatto, sovrascrittura, scope articolo). Env
richiesta: `GEKO_UPLOAD_SIGNING_KEY` (secret forte, solo sul container
geko-mcp; se assente il tool dà errore e la route risponde 503). Gli URL
scadono dopo `scadenza_minuti` (default 15). Il tool `carica_immagine` base64
resta per i casi piccoli.
```

- [ ] **Step 4: Documentare in webapp/README.md**

Se il README ha una sezione sui tool MCP, aggiungere una riga equivalente per `ottieni_upload_url`; altrimenti saltare questo step.

- [ ] **Step 5: Verifica sanity + commit**

Run: `grep -n "GEKO_UPLOAD_SIGNING_KEY" webapp/docker-compose.yml webapp/docker-compose.prod.yml`
Expected: una riga per ciascun file.

```bash
git add webapp/docker-compose.yml webapp/docker-compose.prod.yml CLAUDE.md webapp/README.md
git commit -m "docs+config: env GEKO_UPLOAD_SIGNING_KEY e guida upload da Cowork"
```

---

### Task 5: Verifica finale della suite

**Files:** nessuna modifica (gate di verifica).

- [ ] **Step 1: Eseguire l'intera suite**

Run: `cd webapp && source .venv/bin/activate && python -m pytest -q`
Expected: PASS su tutti i test (nuovi + preesistenti), nessuna regressione su `test_mcp_images.py`, `test_article_images.py`, `test_converter_image_base.py`.

- [ ] **Step 2: Commit (solo se servono fix)**

Se emergono fix, committarli con messaggio descrittivo; altrimenti nessun commit.

---

## Self-Review

**Spec coverage:**
- Tool `ottieni_upload_url` (URL firmato) → Task 2. ✓
- Route pubblica `/upload/immagine` + verifica firma → Task 3. ✓
- Modulo firma HMAC + scadenza + binding aid/name → Task 1. ✓
- Riuso `save_article_image` (nome esatto, sovrascrivi, scope) → Task 3 (criteri 1 e 3). ✓
- Formati PNG/JPG/SVG → riuso `ALLOWED_IMAGE_EXTENSIONS`, testato in Task 2 (estensione) e Task 3 (upload PNG). ✓ (criterio 2)
- Config `GEKO_UPLOAD_SIGNING_KEY` + feature-off senza chiave (503/errore) → Task 4 + testato in Task 1 (`test_missing_key_rejected`) e gestito in route (Task 3 branch 503). ✓
- Sicurezza (compare_digest, scadenza, filename dal token) → Task 1 + Task 3 (`happy_path` verifica che il nome salvato = quello del token, non del multipart). ✓
- `carica_immagine` base64 invariato → non toccato. ✓

**Placeholder scan:** nessun TBD/TODO; ogni step di codice mostra il codice completo. Task 4 Step 4 è condizionale (README) ma esplicito. ✓

**Type consistency:** `mint(articolo_id, nome_file, exp_epoch)` / `verify(token, now=)` → usati identici in Task 2 e Task 3. Claim keys `aid`/`name`/`exp` coerenti tra modulo, tool (`scade_a` = `exp`) e route (`claims["aid"]`, `claims["name"]`). Route usa `save_article_image(db, aid, name, content, sovrascrivi=True)`, firma esistente in `article_ops`. ✓
