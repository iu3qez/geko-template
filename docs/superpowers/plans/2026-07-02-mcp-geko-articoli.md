# MCP "GEKO articoli" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Esporre un server MCP remoto, integrato nella webapp FastAPI GEKO, che permette a Claude di creare/gestire articoli già conformi alle convenzioni Typst, autenticato via OAuth 2.1 (Scalekit).

**Architecture:** Un server FastMCP montato come sub-app ASGI su `/mcp` nella stessa app FastAPI. I tool riusano in-process i modelli SQLAlchemy e il `MarkdownToTypstConverter` tramite un modulo di servizio condiviso (`article_ops.py`), evitando duplicazione con i router `/api`. L'autenticazione è delegata a Scalekit come Authorization Server: un `TokenVerifier` custom valida i JWT riusando la validazione Scalekit già collaudata nel progetto `../mcp-proxy`, e un `RemoteAuthProvider` espone il discovery RFC 9728.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy async (aiosqlite), `fastmcp` (prefecthq), `scalekit-sdk-python`, pytest + pytest-asyncio, Docker/Traefik.

## Global Constraints

- Lingua: italiano per UI/testi/commenti, inglese per identificatori di codice.
- Python: type hints + async/await per I/O. Nessun crash del server MCP su errore di un tool → catturare e restituire messaggio leggibile.
- Non duplicare la logica di business: i tool MCP e i router `/api` devono passare per le stesse funzioni in `app/services/article_ops.py`.
- Auth: il server MCP DEVE validare l'audience del token (`res_...`) e restituire `401` + `WWW-Authenticate` con `resource_metadata` quando manca/è invalido.
- Config sensibile solo via env/secrets: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`, `SCALEKIT_RESOURCE_ID`, `MCP_PUBLIC_URL`, `SCALEKIT_AUTHORIZATION_SERVER` (opzionale).
- Tutti i comandi si eseguono da `webapp/` salvo diversa indicazione.
- Valori di config specifici di Scalekit (JWKS/issuer/AS URL esatti) vanno confermati dalla console Scalekit e/o dalla skill `mcp-auth:add-auth-fastmcp`; nel codice restano parametrizzati via env, mai hardcoded.

## File Structure

- Create: `webapp/app/services/article_ops.py` — funzioni di servizio async condivise (create/list/get/update/assign articoli, list magazines, generate summary) + serializer.
- Create: `webapp/app/mcp/__init__.py` — package MCP.
- Create: `webapp/app/mcp/conventions.py` — testo guida convenzioni + `markdown_preview()`.
- Create: `webapp/app/mcp/auth.py` — `ScalekitTokenVerifier` + `build_auth()`.
- Create: `webapp/app/mcp/server.py` — costruzione istanza FastMCP, tool, risorsa, `mcp_app`.
- Modify: `webapp/app/routes/api/articles.py` — delega ad `article_ops` (rimuove duplicazione).
- Modify: `webapp/app/main.py` — monta `/mcp` e combina i lifespan.
- Modify: `webapp/requirements.txt` — aggiunge dipendenze.
- Create: `webapp/pytest.ini` — config pytest-asyncio.
- Create: `webapp/tests/conftest.py` — fixture DB async in-memory.
- Create: `webapp/tests/test_article_ops.py`, `webapp/tests/test_conventions.py`, `webapp/tests/test_mcp_auth.py`, `webapp/tests/test_mcp_server.py`.
- Modify: `webapp/docker-compose.yml`, `webapp/docker-compose.prod.yml`, `webapp/.env.example` (crea se assente) — env + router Traefik MCP.
- Modify: `CLAUDE.md` (root) — sezione MCP.

---

### Task 1: Dipendenze e harness di test

**Files:**
- Modify: `webapp/requirements.txt`
- Create: `webapp/pytest.ini`
- Create: `webapp/tests/__init__.py`
- Create: `webapp/tests/conftest.py`

**Interfaces:**
- Produces: fixture pytest `db` → `AsyncSession` su SQLite in-memory con schema creato; fixture `sample_magazine(db)` → dict con `id`.

- [ ] **Step 1: Aggiungi le dipendenze**

In `webapp/requirements.txt` aggiungi in fondo:

```
fastmcp>=2.10.0
scalekit-sdk-python>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 2: Installa**

Run: `pip install -r requirements.txt`
Expected: installazione OK di fastmcp, scalekit-sdk-python, pytest, pytest-asyncio.

- [ ] **Step 3: Config pytest**

Create `webapp/pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 4: Package tests**

Create `webapp/tests/__init__.py` (vuoto).

- [ ] **Step 5: Fixture DB**

Create `webapp/tests/conftest.py`:

```python
"""Fixture condivise per i test della webapp GEKO."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base, Magazine, MagazineStatus


@pytest_asyncio.fixture
async def db():
    """Sessione async su SQLite in-memory con schema creato da zero."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def sample_magazine(db):
    """Un numero rivista di prova, ritorna il suo id."""
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    db.add(mag)
    await db.commit()
    await db.refresh(mag)
    return {"id": mag.id, "numero": mag.numero}
```

- [ ] **Step 6: Verifica raccolta test**

Run: `python -m pytest -q`
Expected: `no tests ran` (0 test, nessun errore di import/config).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt pytest.ini tests/__init__.py tests/conftest.py
git commit -m "test: aggiungi harness pytest-asyncio e dipendenze MCP"
```

---

### Task 2: Modulo di servizio condiviso `article_ops.py`

**Files:**
- Create: `webapp/app/services/article_ops.py`
- Test: `webapp/tests/test_article_ops.py`

**Interfaces:**
- Consumes: `app.models` (Article, Magazine, article_magazines), `app.services.llm.generate_article_summary`, `app.models.Config`.
- Produces:
  - `article_to_response(article: Article) -> dict`
  - `magazine_to_response(magazine: Magazine) -> dict`
  - `async list_magazines(db) -> list[dict]`
  - `async create_article(db, *, titolo, contenuto_md, sottotitolo="", autore="", nome_autore="", ordine=0) -> dict`
  - `async list_articles(db, *, magazine_id=None, search=None) -> list[dict]`
  - `async get_article(db, article_id: int) -> dict | None`
  - `async update_article(db, article_id: int, **fields) -> dict | None`
  - `async assign_article(db, article_id: int, magazine_ids: list[int]) -> dict | None`
  - `async generate_summary(db, article_id: int) -> dict | None`

- [ ] **Step 1: Test di creazione e lettura**

Create `webapp/tests/test_article_ops.py`:

```python
import pytest

from app.services import article_ops


async def test_create_article_returns_serialized_dict(db):
    art = await article_ops.create_article(
        db, titolo="Portatile in vetta", contenuto_md="Testo **grassetto**.",
        autore="IK2ABC", nome_autore="Mario",
    )
    assert art["id"] > 0
    assert art["titolo"] == "Portatile in vetta"
    assert art["autore"] == "IK2ABC"
    assert art["magazines"] == []
    assert art["images"] == []


async def test_get_article_missing_returns_none(db):
    assert await article_ops.get_article(db, 999) is None


async def test_assign_article_to_magazine(db, sample_magazine):
    art = await article_ops.create_article(db, titolo="X", contenuto_md="y")
    updated = await article_ops.assign_article(db, art["id"], [sample_magazine["id"]])
    assert [m["id"] for m in updated["magazines"]] == [sample_magazine["id"]]


async def test_update_article_changes_fields(db):
    art = await article_ops.create_article(db, titolo="Vecchio", contenuto_md="y")
    updated = await article_ops.update_article(db, art["id"], titolo="Nuovo")
    assert updated["titolo"] == "Nuovo"


async def test_list_articles_search(db):
    await article_ops.create_article(db, titolo="Antenna EFHW", contenuto_md="y")
    await article_ops.create_article(db, titolo="Batterie LiFePO4", contenuto_md="y")
    found = await article_ops.list_articles(db, search="antenna")
    assert len(found) == 1
    assert found[0]["titolo"] == "Antenna EFHW"


async def test_list_magazines(db, sample_magazine):
    mags = await article_ops.list_magazines(db)
    assert any(m["id"] == sample_magazine["id"] for m in mags)
```

- [ ] **Step 2: Esegui i test (devono fallire)**

Run: `python -m pytest tests/test_article_ops.py -q`
Expected: FAIL con `ModuleNotFoundError: app.services.article_ops`.

- [ ] **Step 3: Implementa il modulo**

Create `webapp/app/services/article_ops.py`:

```python
"""Logica di servizio condivisa per gli articoli.

Unica fonte di verità usata sia dai router JSON (/api) sia dai tool MCP,
per evitare derive tra i due percorsi.
"""

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from ..models import Article, Config, Magazine, article_magazines


def article_to_response(article: Article) -> dict:
    """Serializza un Article in dict JSON-friendly."""
    return {
        "id": article.id,
        "titolo": article.titolo,
        "sottotitolo": article.sottotitolo or "",
        "autore": article.autore or "",
        "nome_autore": article.nome_autore or "",
        "contenuto_md": article.contenuto_md or "",
        "contenuto_typ": article.contenuto_typ or "",
        "sommario_llm": article.sommario_llm or "",
        "ordine": article.ordine or 0,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        "magazines": [
            {
                "id": m.id,
                "numero": m.numero,
                "mese": m.mese,
                "anno": m.anno,
                "stato": m.stato.value if hasattr(m.stato, "value") else m.stato,
            }
            for m in article.magazines
        ],
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "original_filename": img.original_filename,
                "url": img.url,
                "alt_text": img.alt_text or "",
            }
            for img in article.images
        ],
    }


def magazine_to_response(magazine: Magazine) -> dict:
    """Serializza un Magazine (campi essenziali) in dict."""
    return {
        "id": magazine.id,
        "numero": magazine.numero,
        "mese": magazine.mese,
        "anno": magazine.anno,
        "stato": magazine.stato.value if hasattr(magazine.stato, "value") else magazine.stato,
    }


_ARTICLE_LOADED = (selectinload(Article.magazines), selectinload(Article.images))


async def _reload(db, article_id: int) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    return article_to_response(article) if article else None


async def list_magazines(db) -> list[dict]:
    result = await db.execute(select(Magazine).order_by(Magazine.numero.desc()))
    return [magazine_to_response(m) for m in result.scalars().all()]


async def create_article(
    db,
    *,
    titolo: str,
    contenuto_md: str,
    sottotitolo: str = "",
    autore: str = "",
    nome_autore: str = "",
    ordine: int = 0,
) -> dict:
    article = Article(
        titolo=titolo,
        sottotitolo=sottotitolo or "",
        autore=autore or "",
        nome_autore=nome_autore or "",
        contenuto_md=contenuto_md or "",
        ordine=ordine or 0,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return await _reload(db, article.id)


async def list_articles(
    db, *, magazine_id: Optional[int] = None, search: Optional[str] = None
) -> list[dict]:
    query = (
        select(Article)
        .options(*_ARTICLE_LOADED)
        .order_by(Article.updated_at.desc())
    )
    if magazine_id:
        query = query.join(Article.magazines).where(Magazine.id == magazine_id)
    if search:
        term = f"%{search}%"
        query = query.where(
            Article.titolo.ilike(term)
            | Article.autore.ilike(term)
            | Article.contenuto_md.ilike(term)
        )
    result = await db.execute(query)
    return [article_to_response(a) for a in result.scalars().unique().all()]


async def get_article(db, article_id: int) -> Optional[dict]:
    return await _reload(db, article_id)


async def update_article(db, article_id: int, **fields) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    allowed = {
        "titolo", "sottotitolo", "autore", "nome_autore",
        "contenuto_md", "sommario_llm", "ordine",
    }
    for key, value in fields.items():
        if key in allowed and value is not None:
            setattr(article, key, value)
    await db.commit()
    return await _reload(db, article_id)


async def assign_article(db, article_id: int, magazine_ids: list[int]) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    await db.execute(
        delete(article_magazines).where(article_magazines.c.article_id == article_id)
    )
    for mag_id in magazine_ids:
        mag = (await db.execute(select(Magazine).where(Magazine.id == mag_id))).scalar_one_or_none()
        if mag:
            article.magazines.append(mag)
    await db.commit()
    return await _reload(db, article_id)


async def generate_summary(db, article_id: int) -> Optional[dict]:
    from .llm import generate_article_summary

    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    if not article.contenuto_md:
        raise ValueError("L'articolo non ha contenuto da riassumere")
    model = await Config.get(db, "claude_model")
    summary = await generate_article_summary(article.contenuto_md, article.titolo, model=model)
    article.sommario_llm = summary.get("sommario", "")
    await db.commit()
    return await _reload(db, article_id)
```

- [ ] **Step 4: Esegui i test (devono passare)**

Run: `python -m pytest tests/test_article_ops.py -q`
Expected: PASS (6 test). `test_list_magazines` e `test_assign_article_to_magazine` usano `sample_magazine`.

- [ ] **Step 5: Commit**

```bash
git add app/services/article_ops.py tests/test_article_ops.py
git commit -m "feat: modulo di servizio condiviso article_ops"
```

---

### Task 3: Router articoli delega ad `article_ops`

**Files:**
- Modify: `webapp/app/routes/api/articles.py`
- Test: `webapp/tests/test_articles_api.py`

**Interfaces:**
- Consumes: `article_ops` (Task 2).
- Produces: endpoint `/api/articles` invariati nel contratto JSON, ma implementati via `article_ops`.

- [ ] **Step 1: Smoke test dell'API via TestClient**

Create `webapp/tests/test_articles_api.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


@pytest.fixture
def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def test_create_and_get_article(client):
    async with client as c:
        resp = await c.post("/api/articles", json={"titolo": "T", "contenuto_md": "x"})
        assert resp.status_code == 200
        art = resp.json()
        assert art["titolo"] == "T"

        got = await c.get(f"/api/articles/{art['id']}")
        assert got.status_code == 200
        assert got.json()["id"] == art["id"]
```

- [ ] **Step 2: Esegui (deve passare già ORA con il codice esistente)**

Run: `python -m pytest tests/test_articles_api.py -q`
Expected: PASS. (Fissa il comportamento prima del refactor.)

- [ ] **Step 3: Refactor `create_article` e `list_articles` del router**

In `webapp/app/routes/api/articles.py`, sostituisci il corpo degli handler per delegare ad `article_ops`. Sostituisci l'import iniziale e gli handler `create_article`, `list_articles`, `get_article`, `update_article`, `assign_to_magazines`, `generate_summary`. Esempio per `create_article`:

```python
from ...services import article_ops

@router.post("")
async def create_article(data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    return await article_ops.create_article(
        db,
        titolo=data.titolo,
        contenuto_md=data.contenuto_md or "",
        sottotitolo=data.sottotitolo or "",
        autore=data.autore or "",
        nome_autore=data.nome_autore or "",
        ordine=data.ordine or 0,
    )
```

E analogamente:

```python
@router.get("")
async def list_articles(magazine_id: Optional[int] = None, search: Optional[str] = None,
                        db: AsyncSession = Depends(get_db)):
    return await article_ops.list_articles(db, magazine_id=magazine_id, search=search)


@router.get("/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    art = await article_ops.get_article(db, article_id)
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@router.put("/{article_id}")
async def update_article(article_id: int, data: ArticleUpdate, db: AsyncSession = Depends(get_db)):
    art = await article_ops.update_article(db, article_id, **data.model_dump(exclude_unset=True))
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@router.post("/{article_id}/assign")
async def assign_to_magazines(article_id: int, data: AssignRequest, db: AsyncSession = Depends(get_db)):
    art = await article_ops.assign_article(db, article_id, data.magazine_ids)
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@router.post("/{article_id}/summary")
async def generate_summary(article_id: int, db: AsyncSession = Depends(get_db)):
    try:
        art = await article_ops.generate_summary(db, article_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art
```

Rimuovi la funzione locale `article_to_response` dal router (ora vive in `article_ops`); se serve altrove importala da lì. La `delete_article` resta invariata.

- [ ] **Step 4: Esegui gli smoke test (devono ancora passare)**

Run: `python -m pytest tests/test_articles_api.py -q`
Expected: PASS (contratto invariato).

- [ ] **Step 5: Commit**

```bash
git add app/routes/api/articles.py tests/test_articles_api.py
git commit -m "refactor: router articoli delega ad article_ops"
```

---

### Task 4: Convenzioni + anteprima Typst

**Files:**
- Create: `webapp/app/mcp/__init__.py`
- Create: `webapp/app/mcp/conventions.py`
- Test: `webapp/tests/test_conventions.py`

**Interfaces:**
- Consumes: `app.services.converter.MarkdownToTypstConverter`.
- Produces: `CONVENZIONI: str`; `markdown_preview(md: str) -> str`.

- [ ] **Step 1: Test anteprima**

Create `webapp/tests/test_conventions.py`:

```python
from app.mcp.conventions import CONVENZIONI, markdown_preview


def test_conventions_text_mentions_box_evidenza():
    assert "box-evidenza" in CONVENZIONI
    assert "!!!" in CONVENZIONI


def test_preview_converts_bold_and_admonition():
    md = "Testo **grassetto**.\n\n!!! \"Nota\"\nRiga uno.\n!!!"
    typ = markdown_preview(md)
    assert "*grassetto*" in typ
    assert '#box-evidenza(titolo: "Nota")' in typ
```

- [ ] **Step 2: Esegui (deve fallire)**

Run: `python -m pytest tests/test_conventions.py -q`
Expected: FAIL con `ModuleNotFoundError: app.mcp`.

- [ ] **Step 3: Crea il package e il modulo**

Create `webapp/app/mcp/__init__.py` (vuoto).

Create `webapp/app/mcp/conventions.py`:

```python
"""Guida convenzioni Markdown → Typst e helper di anteprima per l'MCP."""

from ..services.converter import MarkdownToTypstConverter

CONVENZIONI = """\
# Convenzioni Markdown del GEKO Radio Magazine

Scrivi gli articoli in Markdown. Il template li converte in Typst così:

- `# Titolo` → sezione (il titolo dell'articolo resta di primo livello).
- `**grassetto**` → grassetto; `*corsivo*` o `_corsivo_` → corsivo.
- `[testo](url)` e URL nudi → link stilizzato `#link-geko`.
- `![descrizione](/uploads/foto.jpg){width=80%}` → figura con didascalia.
  I path `/uploads/...` vengono rimappati automaticamente.
- Liste puntate con `*` o `-`; liste numerate con `1.`.
- `> citazione` → blocco citazione.
- Tabelle Markdown `| a | b |` con riga separatrice → tabella GEKO.
- Box evidenza (admonition), con titolo tra virgolette:

  !!! "Attenzione alla batteria"
  In portatile QRP porta sempre una batteria di scorta.
  Il freddo riduce la capacità del 20-30%.
  !!!

Usa il tool `anteprima_typst` per vedere il Typst generato prima di salvare.
"""


def markdown_preview(md: str) -> str:
    """Converte Markdown GEKO in Typst e restituisce il sorgente Typst."""
    converter = MarkdownToTypstConverter()
    _metadata, typst = converter.convert(md)
    return typst
```

- [ ] **Step 4: Esegui (deve passare)**

Run: `python -m pytest tests/test_conventions.py -q`
Expected: PASS (2 test).

- [ ] **Step 5: Commit**

```bash
git add app/mcp/__init__.py app/mcp/conventions.py tests/test_conventions.py
git commit -m "feat: guida convenzioni MCP e anteprima Typst"
```

---

### Task 5: Auth Scalekit (`TokenVerifier` custom)

**Files:**
- Create: `webapp/app/mcp/auth.py`
- Test: `webapp/tests/test_mcp_auth.py`

**Interfaces:**
- Consumes: `scalekit` SDK, env vars.
- Produces:
  - `ScalekitTokenVerifier(TokenVerifier)` con `async verify_token(token) -> AccessToken | None`.
  - `build_auth() -> RemoteAuthProvider | None` (None se le env Scalekit non sono configurate).

- [ ] **Step 1: Test del verifier**

Create `webapp/tests/test_mcp_auth.py`:

```python
import pytest

from app.mcp import auth as auth_mod


class _FakeScalekit:
    def __init__(self, ok: bool):
        self._ok = ok

    def validate_token(self, token, options=None):
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


def test_build_auth_none_without_env(monkeypatch):
    for var in ("SCALEKIT_ENVIRONMENT_URL", "SCALEKIT_CLIENT_ID",
                "SCALEKIT_CLIENT_SECRET", "SCALEKIT_RESOURCE_ID"):
        monkeypatch.delenv(var, raising=False)
    assert auth_mod.build_auth() is None
```

- [ ] **Step 2: Esegui (deve fallire)**

Run: `python -m pytest tests/test_mcp_auth.py -q`
Expected: FAIL con `ModuleNotFoundError: app.mcp.auth`.

- [ ] **Step 3: Implementa auth**

Create `webapp/app/mcp/auth.py`:

```python
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

        claims = claims if isinstance(claims, dict) else {}
        scope = claims.get("scope", "")
        scopes = claims.get("scopes") or (scope.split() if scope else [])
        return AccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("sub") or "unknown",
            scopes=list(scopes),
            expires_at=claims.get("exp"),
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

    as_url = os.environ.get(
        "SCALEKIT_AUTHORIZATION_SERVER", f"{env_url}/resources/{resource_id}"
    )
    return RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[AnyHttpUrl(as_url)],
        base_url=public_url,
    )
```

Nota: la firma di `ScalekitClient(...)` e il ritorno di `validate_token` vanno confermati con la skill `mcp-auth:add-auth-fastmcp` / SDK installato; `../mcp-proxy/auth_proxy.py` usa `env_url=`, `client_id=`, `client_secret=`. Se `validate_token` non ritorna i claim, sostituire con `validate_token_and_get_claims`.

- [ ] **Step 4: Esegui (deve passare)**

Run: `python -m pytest tests/test_mcp_auth.py -q`
Expected: PASS (3 test).

- [ ] **Step 5: Commit**

```bash
git add app/mcp/auth.py tests/test_mcp_auth.py
git commit -m "feat: verifier token Scalekit per l'MCP"
```

---

### Task 6: Server FastMCP (tool + risorsa) e app ASGI

**Files:**
- Create: `webapp/app/mcp/server.py`
- Test: `webapp/tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `article_ops` (Task 2), `conventions` (Task 4), `build_auth` (Task 5), `app.database.async_session`.
- Produces: `mcp: FastMCP`; `mcp_app` (ASGI app via `mcp.http_app(path="/")`).

- [ ] **Step 1: Test tool in-memory**

Create `webapp/tests/test_mcp_server.py`:

```python
import json

import pytest
from fastmcp import Client

from app.database import async_session
import app.mcp.server as server_mod


@pytest.fixture
def patch_session(db, monkeypatch):
    """Fa usare ai tool la sessione di test invece del DB reale."""
    class _CtxSession:
        async def __aenter__(self):
            return db
        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(server_mod, "async_session", lambda: _CtxSession())


async def test_crea_articolo_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        result = await client.call_tool(
            "crea_articolo",
            {"titolo": "Antenna", "contenuto_md": "Testo **bold**."},
        )
        data = result.data
        assert data["titolo"] == "Antenna"
        assert data["id"] > 0


async def test_anteprima_typst_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        result = await client.call_tool(
            "anteprima_typst", {"contenuto_md": "Testo **bold**."}
        )
        assert "*bold*" in result.data


async def test_guida_convenzioni_resource(patch_session):
    async with Client(server_mod.mcp) as client:
        content = await client.read_resource("guida://convenzioni")
        assert "box-evidenza" in content[0].text
```

- [ ] **Step 2: Esegui (deve fallire)**

Run: `python -m pytest tests/test_mcp_server.py -q`
Expected: FAIL con `ModuleNotFoundError: app.mcp.server`.

- [ ] **Step 3: Implementa il server**

Create `webapp/app/mcp/server.py`:

```python
"""Server MCP GEKO: tool per creare/gestire articoli conformi al template."""

from typing import Optional

from fastmcp import FastMCP

from ..database import async_session
from ..services import article_ops
from .auth import build_auth
from .conventions import CONVENZIONI, markdown_preview

mcp = FastMCP(name="GEKO Articoli", auth=build_auth())


@mcp.tool
async def crea_articolo(
    titolo: str,
    contenuto_md: str,
    sottotitolo: str = "",
    autore: str = "",
    nome_autore: str = "",
    numero_id: Optional[int] = None,
) -> dict:
    """Crea un articolo GEKO da Markdown (vedi risorsa guida://convenzioni).

    `autore` è il nominativo radio (call), `nome_autore` il nome reale.
    Se `numero_id` è indicato, assegna l'articolo a quel numero.
    """
    async with async_session() as db:
        art = await article_ops.create_article(
            db, titolo=titolo, contenuto_md=contenuto_md,
            sottotitolo=sottotitolo, autore=autore, nome_autore=nome_autore,
        )
        if numero_id is not None:
            art = await article_ops.assign_article(db, art["id"], [numero_id])
        return art


@mcp.tool
async def lista_numeri() -> list[dict]:
    """Elenca i numeri della rivista (id, numero, mese, anno, stato)."""
    async with async_session() as db:
        return await article_ops.list_magazines(db)


@mcp.tool
async def lista_articoli(numero_id: Optional[int] = None, search: Optional[str] = None) -> list[dict]:
    """Elenca gli articoli, opzionalmente filtrati per numero o ricerca testo."""
    async with async_session() as db:
        return await article_ops.list_articles(db, magazine_id=numero_id, search=search)


@mcp.tool
async def leggi_articolo(id: int) -> dict:
    """Restituisce un articolo completo (Markdown + metadati)."""
    async with async_session() as db:
        art = await article_ops.get_article(db, id)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def modifica_articolo(
    id: int,
    titolo: Optional[str] = None,
    sottotitolo: Optional[str] = None,
    autore: Optional[str] = None,
    nome_autore: Optional[str] = None,
    contenuto_md: Optional[str] = None,
) -> dict:
    """Aggiorna i campi indicati di un articolo esistente."""
    async with async_session() as db:
        art = await article_ops.update_article(
            db, id, titolo=titolo, sottotitolo=sottotitolo, autore=autore,
            nome_autore=nome_autore, contenuto_md=contenuto_md,
        )
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def assegna_a_numero(id: int, numero_ids: list[int]) -> dict:
    """Assegna l'articolo a uno o più numeri (sostituisce le assegnazioni)."""
    async with async_session() as db:
        art = await article_ops.assign_article(db, id, numero_ids)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def genera_sommario(id: int) -> dict:
    """Genera il sommario AI dell'articolo (richiede ANTHROPIC_API_KEY)."""
    async with async_session() as db:
        art = await article_ops.generate_summary(db, id)
        if art is None:
            raise ValueError(f"Articolo {id} non trovato")
        return art


@mcp.tool
async def anteprima_typst(contenuto_md: str) -> str:
    """Converte il Markdown in Typst e lo restituisce, senza salvare nulla."""
    return markdown_preview(contenuto_md)


@mcp.resource("guida://convenzioni")
def guida_convenzioni() -> str:
    """Guida alle convenzioni Markdown del template GEKO."""
    return CONVENZIONI


mcp_app = mcp.http_app(path="/")
```

- [ ] **Step 4: Esegui (deve passare)**

Run: `python -m pytest tests/test_mcp_server.py -q`
Expected: PASS (3 test). Se `result.data`/`read_resource` differiscono per versione di fastmcp, adegua l'accesso al payload confermando l'API del `Client` via Context7 (`/prefecthq/fastmcp`).

- [ ] **Step 5: Commit**

```bash
git add app/mcp/server.py tests/test_mcp_server.py
git commit -m "feat: server MCP GEKO con tool articoli e risorsa convenzioni"
```

---

### Task 7: Montaggio in FastAPI + lifespan combinato

**Files:**
- Modify: `webapp/app/main.py`
- Test: `webapp/tests/test_mcp_mount.py`

**Interfaces:**
- Consumes: `app.mcp.server.mcp_app`.
- Produces: endpoint `/mcp` montato; discovery su `/.well-known/oauth-protected-resource` (quando auth attiva).

- [ ] **Step 1: Test di montaggio**

Create `webapp/tests/test_mcp_mount.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_mcp_endpoint_requires_auth_or_mounted():
    """Con auth attiva: 401. Senza env (test): l'endpoint /mcp esiste (non 404 catch-all SPA)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        resp = await c.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        assert resp.status_code != 404
```

- [ ] **Step 2: Esegui (deve fallire)**

Run: `python -m pytest tests/test_mcp_mount.py -q`
Expected: FAIL (il catch-all SPA risponde 404/JSON, `/mcp` non ancora montato).

- [ ] **Step 3: Monta l'MCP e combina i lifespan**

In `webapp/app/main.py`:

1. Importa il sub-app MCP dopo gli altri import:

```python
from app.mcp.server import mcp_app
```

2. Sostituisci il decoratore del lifespan esistente con una versione che entra anche nel lifespan dell'MCP (necessario per il session manager di FastMCP). Modifica la funzione `lifespan` così:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # === STARTUP ===
    print("Inizializzazione GEKO Magazine Web App...")
    await init_db()
    print("Database inizializzato")
    (WEBAPP_DIR / "data" / "uploads").mkdir(parents=True, exist_ok=True)
    (WEBAPP_DIR / "data" / "output").mkdir(parents=True, exist_ok=True)
    (WEBAPP_DIR / "typst" / "generated").mkdir(parents=True, exist_ok=True)
    print("Directory create")
    async with mcp_app.lifespan(app):
        print("App pronta!")
        yield
    # === SHUTDOWN ===
    print("Chiusura GEKO Magazine Web App...")
```

3. Monta il sub-app MCP **prima** del catch-all SPA. Subito dopo `app.include_router(api_router)` aggiungi:

```python
# Server MCP (OAuth 2.1 via Scalekit) — montato prima del catch-all SPA
app.mount("/mcp", mcp_app)
```

- [ ] **Step 4: Esegui (deve passare)**

Run: `python -m pytest tests/test_mcp_mount.py -q`
Expected: PASS (`/mcp/` non è più 404).

- [ ] **Step 5: Suite completa**

Run: `python -m pytest -q`
Expected: PASS tutti i test.

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_mcp_mount.py
git commit -m "feat: monta il server MCP su /mcp con lifespan combinato"
```

---

### Task 8: Config di deploy (Docker + Traefik + env)

**Files:**
- Modify: `webapp/docker-compose.yml`
- Modify: `webapp/docker-compose.prod.yml`
- Create/Modify: `webapp/.env.example`

**Interfaces:**
- Produces: router Traefik `geko-mcp.fabris.me` → `geko-webapp:8000`, senza middleware Authentik; env Scalekit passate al container.

- [ ] **Step 1: Env di esempio**

Create/Modify `webapp/.env.example`, aggiungi:

```
# --- MCP / Scalekit (OAuth 2.1 per client Claude) ---
SCALEKIT_ENVIRONMENT_URL=https://<org>.scalekit.com
SCALEKIT_CLIENT_ID=skc_...
SCALEKIT_CLIENT_SECRET=...
SCALEKIT_RESOURCE_ID=res_...
MCP_PUBLIC_URL=https://geko-mcp.fabris.me
# Opzionale: override dell'Authorization Server annunciato nel discovery
# SCALEKIT_AUTHORIZATION_SERVER=https://<org>.scalekit.com/resources/res_...
```

- [ ] **Step 2: Passa le env al container (dev e prod)**

In `webapp/docker-compose.yml` e `webapp/docker-compose.prod.yml`, nella sezione `environment:` del servizio `webapp`, aggiungi:

```yaml
      - SCALEKIT_ENVIRONMENT_URL=${SCALEKIT_ENVIRONMENT_URL:-}
      - SCALEKIT_CLIENT_ID=${SCALEKIT_CLIENT_ID:-}
      - SCALEKIT_CLIENT_SECRET=${SCALEKIT_CLIENT_SECRET:-}
      - SCALEKIT_RESOURCE_ID=${SCALEKIT_RESOURCE_ID:-}
      - MCP_PUBLIC_URL=${MCP_PUBLIC_URL:-https://geko-mcp.fabris.me}
      - SCALEKIT_AUTHORIZATION_SERVER=${SCALEKIT_AUTHORIZATION_SERVER:-}
```

- [ ] **Step 3: Router Traefik MCP senza Authentik**

Nella sezione `labels:` del servizio `webapp` (in entrambi i compose), aggiungi un router dedicato per l'host MCP che **non** usa `chain-forwardAuth-authentik@file` (l'auth la fa Scalekit nell'app). Serve anche una definizione di servizio con la porta interna:

```yaml
        # Router MCP — host dedicato, SENZA middleware Authentik (auth = Scalekit)
        - "traefik.http.routers.geko-mcp-rtr.rule=Host(`geko-mcp.fabris.me`)"
        - "traefik.http.routers.geko-mcp-rtr.entrypoints=websecure"
        - "traefik.http.routers.geko-mcp-rtr.service=geko-svc"
        - "traefik.http.services.geko-svc.loadbalancer.server.port=8000"
```

(Il router umano `geko-rtr` esistente resta con l'Authentik middleware e ora deve puntare esplicitamente a `geko-svc`: aggiungi `- "traefik.http.routers.geko-rtr.service=geko-svc"` se non presente.)

- [ ] **Step 4: Verifica sintassi compose**

Run: `docker compose -f docker-compose.yml config >/dev/null && echo OK`
Expected: `OK` (nessun errore di parsing YAML).

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml docker-compose.prod.yml .env.example
git commit -m "chore: deploy MCP — env Scalekit e router Traefik dedicato"
```

- [ ] **Step 6: Passi manuali di deploy (fuori dal codice — richiedono l'utente)**

Documenta/esegui (non automatizzabili qui):
1. In Scalekit: crea una **nuova risorsa** MCP (`res_...`), ottieni env URL/client id/secret, registra il redirect per i client Claude (DCR se supportata).
2. DNS: `geko-mcp.fabris.me` → stesso IP del reverse proxy Traefik; certificato TLS via Traefik.
3. Popola `.env`/secrets sul server con i valori Scalekit.
4. `docker compose up -d --build`.
5. Verifiche:
   - `curl -s https://geko-mcp.fabris.me/.well-known/oauth-protected-resource | jq` → JSON con `authorization_servers` e `resource`.
   - `curl -si https://geko-mcp.fabris.me/mcp/ | head` → `401` con header `WWW-Authenticate`.
   - Da Claude Desktop/claude.ai: aggiungi il server MCP `https://geko-mcp.fabris.me/mcp`, completa il login Scalekit, esegui `crea_articolo` end-to-end.

---

### Task 9: Documentazione — sezione MCP in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (root)

- [ ] **Step 1: Aggiungi la sezione MCP**

In `CLAUDE.md`, dopo la sezione "Webapp Routes", aggiungi:

```markdown
## Server MCP (articoli via Claude)

Server MCP montato su `/mcp` nella stessa FastAPI (`app/mcp/`), auth OAuth 2.1
via Scalekit (Resource Server → valida JWT; Authentik NON è usato per l'MCP).
Host Traefik dedicato `geko-mcp.fabris.me` senza middleware Authentik.

| Tool | Azione |
|------|--------|
| `crea_articolo` | Crea articolo da Markdown (opz. assegna a un numero) |
| `lista_numeri` / `lista_articoli` / `leggi_articolo` | Lettura/contesto |
| `modifica_articolo` / `assegna_a_numero` / `genera_sommario` | Modifica/assegnazione/AI |
| `anteprima_typst` | Converte Markdown→Typst senza salvare |
| risorsa `guida://convenzioni` | Sintassi Markdown del template |

I tool riusano `app/services/article_ops.py` (stessa logica dei router `/api`).
Env richieste: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`,
`SCALEKIT_CLIENT_SECRET`, `SCALEKIT_RESOURCE_ID`, `MCP_PUBLIC_URL`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documenta il server MCP in CLAUDE.md"
```

---

## Self-Review

**Spec coverage:**
- Deploy integrato in FastAPI → Task 6-7. ✓
- Accesso dati in-process (converter + DB) → Task 2, 4, 6. ✓
- Auth OAuth 2.1 Scalekit (Resource Server, discovery, 401) → Task 5, 7, 8. ✓
- Risorsa Scalekit dedicata → Task 8 step 6. ✓
- Tool (crea/lista/leggi/modifica/assegna/sommario/anteprima) + risorsa convenzioni → Task 6. ✓
- Estrazione logica condivisa per evitare drift → Task 2-3. ✓
- Router Traefik dedicato senza Authentik → Task 8. ✓
- Gestione errori senza crash → tool sollevano `ValueError` con messaggi leggibili (Task 6). ✓
- Testing (unit article_ops/conventions/auth, e2e tool in-memory, mount) → Task 2,4,5,6,7. ✓
- Follow-up doc CLAUDE.md → Task 9. ✓

**Placeholder scan:** nessun TBD/TODO nel codice; i valori Scalekit sono config via env (non placeholder di codice) con nota di verifica via skill `mcp-auth:add-auth-fastmcp`.

**Type consistency:** i nomi delle funzioni `article_ops` (create_article/list_articles/get_article/update_article/assign_article/list_magazines/generate_summary) sono usati coerentemente in Task 3 e Task 6; `ScalekitTokenVerifier`/`build_auth` coerenti tra Task 5 e Task 6; `mcp`/`mcp_app` coerenti tra Task 6 e Task 7.

**Rischi noti da confermare in implementazione (via Context7 `/prefecthq/fastmcp` e skill `mcp-auth:add-auth-fastmcp`):**
- API esatta del `Client` di fastmcp per leggere `result.data` / `read_resource` (Task 6 step 4).
- Firma di `ScalekitClient(...)` e ritorno di `validate_token` vs `validate_token_and_get_claims` (Task 5).
- Path esatto del discovery quando l'MCP è montato su `/mcp` con host dedicato (Task 8 verifica).
