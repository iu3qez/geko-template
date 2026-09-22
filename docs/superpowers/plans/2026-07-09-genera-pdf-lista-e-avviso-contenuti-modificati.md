# Genera PDF da lista + avviso contenuti modificati — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere il pulsante "Genera PDF" alla lista numeri e segnalare quando i contenuti di un numero sono cambiati dopo l'ultima generazione del PDF.

**Architecture:** Backend: nuovo campo `Magazine.pdf_built_at` valorizzato alla build; staleness calcolata confrontando `pdf_built_at` col max `updated_at` di numero+articoli; `updated_at` toccato esplicitamente sulle mutazioni che non passano dall'ORM update del numero (add/remove/reorder articoli, upload/delete immagini articolo). Frontend: pulsante build per-card + avviso ⚠️ su lista e dettaglio.

**Tech Stack:** FastAPI, SQLAlchemy async, aiosqlite, pytest-asyncio, httpx AsyncClient; SvelteKit (Svelte 5, TypeScript).

## Global Constraints

- Python: type hints, async/await per I/O.
- Lingua: italiano per UI/commenti, inglese per codice.
- Migration schema SQLite: pattern `ALTER TABLE ... ADD COLUMN` in `app/database.py::run_migrations` (niente Alembic).
- Test webapp: `webapp/tests/`, `asyncio_mode=auto`, girano da `webapp/` con venv locale.
- Confronto datetime: `Magazine.updated_at`/`pdf_built_at` sono naive nel DB SQLite; `models.utcnow()` è tz-aware. Normalizzare entrambi a naive-UTC prima di confrontare.
- Fonte unica logica articoli in `app/services/article_ops.py`.

---

### Task 1: Campo `pdf_built_at` sul modello Magazine + migration

**Files:**
- Modify: `webapp/app/models.py` (classe `Magazine`, ~riga 42-44)
- Modify: `webapp/app/database.py` (`run_migrations`, righe 17-33)
- Test: `webapp/tests/test_magazine_stale.py` (create)

**Interfaces:**
- Produces: `Magazine.pdf_built_at` (`Column(DateTime, nullable=True)`), default `None`.

- [ ] **Step 1: Scrivere il test che fallisce** (create `webapp/tests/test_magazine_stale.py`)

```python
"""Test staleness PDF dei numeri (pdf_built_at / pdf_stale)."""

from app.models import Magazine, MagazineStatus


async def test_new_magazine_has_no_pdf_built_at(db):
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    db.add(mag)
    await db.commit()
    await db.refresh(mag)
    assert mag.pdf_built_at is None
```

- [ ] **Step 2: Eseguire il test e verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_magazine_stale.py -v`
Expected: FAIL — `AttributeError: ... 'pdf_built_at'` (colonna inesistente).

- [ ] **Step 3: Aggiungere la colonna al modello** (`webapp/app/models.py`, dentro `class Magazine`, dopo `copertina_id`):

```python
    copertina_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    pdf_built_at = Column(DateTime, nullable=True)  # ultima generazione PDF riuscita
    created_at = Column(DateTime, default=utcnow)
```

- [ ] **Step 4: Aggiungere la migration** (`webapp/app/database.py`). Sostituire il corpo di `run_migrations` per ispezionare sia `images` sia `magazines`:

```python
def run_migrations(conn):
    """Run schema migrations for existing databases (sync, called via run_sync)."""
    def columns(table):
        try:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            return {row[1] for row in result.fetchall()}
        except Exception:
            return None

    images_cols = columns("images")
    if images_cols is not None and "alt_text" not in images_cols:
        try:
            conn.execute(text("ALTER TABLE images ADD COLUMN alt_text TEXT DEFAULT ''"))
            print("Migration: added alt_text column to images")
        except Exception as e:
            print(f"Migration warning: {e}")

    magazines_cols = columns("magazines")
    if magazines_cols is not None and "pdf_built_at" not in magazines_cols:
        try:
            conn.execute(text("ALTER TABLE magazines ADD COLUMN pdf_built_at DATETIME"))
            print("Migration: added pdf_built_at column to magazines")
        except Exception as e:
            print(f"Migration warning: {e}")
```

- [ ] **Step 5: Eseguire il test e verificarne il passaggio**

Run: `cd webapp && python -m pytest tests/test_magazine_stale.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add webapp/app/models.py webapp/app/database.py webapp/tests/test_magazine_stale.py
git commit -m "feat(magazines): aggiungi campo pdf_built_at + migration"
```

---

### Task 2: Staleness backend — helper, campi API, marker build, touch mutazioni

**Files:**
- Modify: `webapp/app/routes/api/magazines.py` (`magazine_to_response` righe 90-120; `build_pdf` righe 358-360; `reorder_articles` righe 397-422; `add_article` righe 425-474; `remove_article` righe 477-496)
- Test: `webapp/tests/test_magazine_stale.py` (append)

**Interfaces:**
- Consumes: `Magazine.pdf_built_at` (Task 1).
- Produces:
  - `magazine_pdf_stale(magazine: Magazine) -> bool` in `app/routes/api/magazines.py`.
  - `magazine_to_response` include `"pdf_built_at": str|None` (ISO) e `"pdf_stale": bool`.
  - `build_pdf` imposta `magazine.pdf_built_at = utcnow()` su successo.
  - `add_article`/`remove_article`/`reorder_articles` impostano `magazine.updated_at = utcnow()`.

- [ ] **Step 1: Scrivere i test che falliscono** (append a `webapp/tests/test_magazine_stale.py`). Usano il `client` httpx come `test_articles_api.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import Article, utcnow


@pytest.fixture
def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def _make_mag_with_article(db):
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    art = Article(titolo="A", contenuto_md="ciao")
    db.add(mag)
    db.add(art)
    await db.commit()
    mag.articles.append(art)
    await db.commit()
    await db.refresh(mag)
    await db.refresh(art)
    return mag.id, art.id


async def test_pdf_stale_false_when_never_built(client, db):
    mag_id, _ = await _make_mag_with_article(db)
    async with client as c:
        resp = await c.get(f"/api/magazines/{mag_id}")
    body = resp.json()
    assert body["pdf_built_at"] is None
    assert body["pdf_stale"] is False


async def test_pdf_stale_true_after_article_change(client, db):
    mag_id, art_id = await _make_mag_with_article(db)
    # Simula una build riuscita nel passato
    mag = await db.get(Magazine, mag_id)
    mag.pdf_built_at = utcnow()
    await db.commit()
    async with client as c:
        before = (await c.get(f"/api/magazines/{mag_id}")).json()
        assert before["pdf_stale"] is False
        # Modifica l'articolo -> updated_at avanza
        art = await db.get(Article, art_id)
        art.titolo = "Modificato"
        await db.commit()
        after = (await c.get(f"/api/magazines/{mag_id}")).json()
    assert after["pdf_stale"] is True


async def test_pdf_stale_true_after_reorder(client, db):
    mag_id, art_id = await _make_mag_with_article(db)
    mag = await db.get(Magazine, mag_id)
    mag.pdf_built_at = utcnow()
    await db.commit()
    async with client as c:
        resp = await c.post(
            f"/api/magazines/{mag_id}/articles/reorder",
            json={"article_ids": [art_id]},
        )
        assert resp.status_code == 200
        after = (await c.get(f"/api/magazines/{mag_id}")).json()
    assert after["pdf_stale"] is True
```

- [ ] **Step 2: Eseguire i test e verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_magazine_stale.py -v`
Expected: FAIL — `KeyError: 'pdf_built_at'` / `pdf_stale` mancanti, e reorder non rende stale.

- [ ] **Step 3: Aggiungere l'helper staleness** (`webapp/app/routes/api/magazines.py`, dopo gli import e prima di `magazine_to_response`):

```python
def _as_naive_utc(dt):
    """Normalizza un datetime a naive-UTC per confronti sicuri (SQLite li salva naive)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        from datetime import timezone
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def magazine_pdf_stale(magazine: Magazine) -> bool:
    """True se i contenuti (numero + articoli) sono cambiati dopo l'ultima build."""
    built = _as_naive_utc(magazine.pdf_built_at)
    if built is None:
        return False
    candidates = [magazine.updated_at]
    candidates.extend(a.updated_at for a in magazine.articles)
    content_updated = max(_as_naive_utc(c) for c in candidates if c is not None)
    return content_updated > built
```

- [ ] **Step 4: Esporre i campi in `magazine_to_response`** — aggiungere, nel dict ritornato (dopo `"updated_at": ...`):

```python
        "updated_at": magazine.updated_at.isoformat() if magazine.updated_at else None,
        "pdf_built_at": magazine.pdf_built_at.isoformat() if magazine.pdf_built_at else None,
        "pdf_stale": magazine_pdf_stale(magazine),
```

- [ ] **Step 5: Marcare la build** — in `build_pdf`, dove imposta lo stato (righe ~358-360):

```python
        # Update magazine status
        magazine.stato = MagazineStatus.PUBBLICATO
        magazine.pdf_built_at = utcnow()
        await db.commit()
```

Aggiungere `utcnow` all'import dei models in cima al file:
`from ...models import Magazine, MagazineStatus, Article, Image, article_magazines, Config, utcnow`

- [ ] **Step 6: Toccare `updated_at` sulle mutazioni junction** — in `reorder_articles`, prima di `await db.commit()` (riga ~420):

```python
    magazine.updated_at = utcnow()
    await db.commit()
```

In `add_article`, prima del `await db.commit()` finale (riga ~472):

```python
    magazine.updated_at = utcnow()
    await db.commit()
```

In `remove_article`, la funzione oggi non carica il `Magazine` (usa `delete(...)` diretto). Sostituire il corpo per caricare il numero e toccarlo:

```python
@router.delete("/{magazine_id}/articles/{article_id}")
async def remove_article(
    magazine_id: int,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove an article from a magazine."""
    # Delete from junction table
    result = await db.execute(
        delete(article_magazines)
        .where(article_magazines.c.article_id == article_id)
        .where(article_magazines.c.magazine_id == magazine_id)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Article not in magazine")

    magazine = (
        await db.execute(select(Magazine).where(Magazine.id == magazine_id))
    ).scalar_one_or_none()
    if magazine:
        magazine.updated_at = utcnow()

    await db.commit()

    return {"status": "removed"}
```

- [ ] **Step 7: Eseguire i test e verificarne il passaggio**

Run: `cd webapp && python -m pytest tests/test_magazine_stale.py -v`
Expected: PASS (tutti).

- [ ] **Step 8: Non-regressione API numeri**

Run: `cd webapp && python -m pytest tests/test_articles_api.py -q`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add webapp/app/routes/api/magazines.py webapp/tests/test_magazine_stale.py
git commit -m "feat(magazines): calcolo pdf_stale, pdf_built_at su build, touch updated_at su add/remove/reorder"
```

---

### Task 3: Touch `article.updated_at` su upload/delete immagini articolo

**Files:**
- Modify: `webapp/app/services/article_ops.py` (`save_article_image` righe 363-375; `delete_article_image` righe 410-422)
- Test: `webapp/tests/test_article_images.py` (append) — verificare quale fixture `db` usa (riusa `conftest.py`).

**Interfaces:**
- Consumes: `Article.updated_at` (già esistente), `models.utcnow`.
- Produces: `save_article_image`/`delete_article_image` avanzano `article.updated_at` dell'articolo interessato.

- [ ] **Step 1: Scrivere il test che fallisce** (append a `webapp/tests/test_article_images.py`). Import in cima al file se assenti: `from app.models import Article, utcnow` e `from app.services import article_ops`.

```python
async def test_save_image_bumps_article_updated_at(db):
    art = Article(titolo="Img", contenuto_md="x")
    db.add(art)
    await db.commit()
    await db.refresh(art)
    before = art.updated_at

    png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    await article_ops.save_article_image(db, art.id, "foto.png", png)

    await db.refresh(art)
    assert art.updated_at is not None
    assert art.updated_at >= before
```

(Nota: se un test analogo di upload esiste già nel file, riusare il PNG/fixture di quel test per coerenza.)

- [ ] **Step 2: Eseguire il test e verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_article_images.py::test_save_image_bumps_article_updated_at -v`
Expected: FAIL — `updated_at` invariato (l'articolo non viene ri-UPDATEd).

- [ ] **Step 3: Toccare l'articolo in `save_article_image`** — prima di `await db.commit()` (riga ~374), dopo aver aggiunto/aggiornato `image`:

```python
        db.add(image)
    article.updated_at = utcnow()
    await db.commit()
    await db.refresh(image)
```

(`article` è già in scope, caricato a riga ~345.) Assicurarsi che `utcnow` sia importato: in cima al file, `from ..models import ..., utcnow` (o `from app.models import utcnow` secondo lo stile del file).

- [ ] **Step 4: Toccare l'articolo in `delete_article_image`** — la funzione oggi non carica l'`Article`. Prima di `await db.commit()` (riga ~421):

```python
    if image.path and os.path.exists(image.path):
        os.remove(image.path)
    await db.delete(image)
    article = (
        await db.execute(select(Article).where(Article.id == article_id))
    ).scalar_one_or_none()
    if article:
        article.updated_at = utcnow()
    await db.commit()
    return True
```

(`select` e `Article` sono già importati nel modulo — verificare in cima al file; se manca `Article`, aggiungerlo all'import esistente dei models.)

- [ ] **Step 5: Eseguire i test e verificarne il passaggio**

Run: `cd webapp && python -m pytest tests/test_article_images.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add webapp/app/services/article_ops.py webapp/tests/test_article_images.py
git commit -m "feat(article_ops): avanza article.updated_at su upload/delete immagini"
```

---

### Task 4: Frontend — tipi + pulsante "Genera PDF" nella lista

**Files:**
- Modify: `webapp/frontend/src/lib/api.ts` (interface `Magazine`, righe 24-38)
- Modify: `webapp/frontend/src/routes/magazines/+page.svelte`

**Interfaces:**
- Consumes: `magazines.build(id)` (già esistente, `api.ts:145`), campi `pdf_built_at`/`pdf_stale` dalla risposta (Task 2).
- Produces: card lista con pulsante build per-card e stato di esito.

- [ ] **Step 1: Aggiornare i tipi** (`api.ts`, interface `Magazine`, dopo `updated_at`):

```ts
	created_at: string;
	updated_at: string;
	pdf_built_at: string | null;
	pdf_stale?: boolean;
	articles: Article[];
	article_count?: number;
```

- [ ] **Step 2: Aggiungere stato e handler build per-card** (`magazines/+page.svelte`, blocco `<script>`). `FileText` è già importato (riga 3); aggiungere stato:

```ts
	let buildingIds = $state<Set<number>>(new Set());
	let buildResults = $state<Record<number, { status: string; error?: string }>>({});

	async function handleBuild(magazine: Magazine) {
		if (magazine.article_count === 0) return;
		buildingIds = new Set(buildingIds).add(magazine.id);
		buildResults = { ...buildResults, [magazine.id]: undefined as any };
		try {
			const result = await magazines.build(magazine.id);
			buildResults = { ...buildResults, [magazine.id]: result };
			if (result.status === 'success') {
				await loadMagazines();
			}
		} catch (e) {
			buildResults = {
				...buildResults,
				[magazine.id]: { status: 'error', error: e instanceof Error ? e.message : 'Errore' }
			};
		} finally {
			const next = new Set(buildingIds);
			next.delete(magazine.id);
			buildingIds = next;
		}
	}
```

- [ ] **Step 3: Aggiungere il pulsante nel footer della card** (`magazines/+page.svelte`, snippet `footer`, dopo il bottone "Dettagli" e prima del bottone PDF download):

```svelte
				<Button
					size="sm"
					onclick={() => handleBuild(magazine)}
					loading={buildingIds.has(magazine.id)}
					disabled={magazine.article_count === 0}
				>
					<FileText size={14} />
					Genera PDF
				</Button>
```

(Il dettaglio usa `<Button>` senza `variant` per il build: manteniamo lo stesso stile di default.)

E sotto il gruppo bottoni, l'esito inline (dentro il footer, dopo la `div.magazine-actions`):

```svelte
				{#if buildResults[magazine.id]}
					<div class="build-result build-{buildResults[magazine.id].status}">
						{#if buildResults[magazine.id].status === 'success'}
							PDF generato con successo!
						{:else}
							{buildResults[magazine.id].error || 'Errore durante la generazione'}
						{/if}
					</div>
				{/if}
```

Aggiungere gli stili `.build-result`/`.build-success`/`.build-error` (copiare da `magazines/[id]/+page.svelte` righe 597-615) nel blocco `<style>`.

- [ ] **Step 4: Verificare i tipi e la build della SPA**

Run: `cd webapp/frontend && npm run check && npm run build`
Expected: nessun errore TypeScript/Svelte; build completata.

- [ ] **Step 5: Commit**

```bash
git add webapp/frontend/src/lib/api.ts webapp/frontend/src/routes/magazines/+page.svelte
git commit -m "feat(frontend): pulsante Genera PDF per-card nella lista numeri"
```

---

### Task 5: Frontend — avviso "contenuti modificati" (lista + dettaglio)

**Files:**
- Modify: `webapp/frontend/src/routes/magazines/+page.svelte`
- Modify: `webapp/frontend/src/routes/magazines/[id]/+page.svelte`

**Interfaces:**
- Consumes: `magazine.pdf_stale` (Task 2/4).

- [ ] **Step 1: Avviso nella lista** (`magazines/+page.svelte`, snippet `footer`, sopra `div.magazine-actions`):

```svelte
				{#if magazine.pdf_stale}
					<div class="stale-warning">
						<AlertTriangle size={14} />
						<span>Contenuti modificati — rigenera</span>
					</div>
				{/if}
```

Aggiungere `AlertTriangle` all'import da `lucide-svelte` (riga 3). Aggiungere gli stili:

```css
	.stale-warning {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		color: var(--color-warning, #b45309);
		font-size: var(--text-sm);
		margin-bottom: var(--space-2);
	}
```

- [ ] **Step 2: Avviso nel dettaglio** (`magazines/[id]/+page.svelte`, Card "Azioni", dentro `.actions-list` o subito prima, sopra il bottone "Genera PDF" alla riga ~338):

```svelte
					{#if magazine.pdf_stale}
						<div class="stale-warning">
							<AlertTriangle size={18} />
							<span>I contenuti sono cambiati dopo l'ultima generazione del PDF. Rigenera per allineare il PDF.</span>
						</div>
					{/if}
```

Aggiungere `AlertTriangle` all'import `lucide-svelte` (righe 6-8). Aggiungere gli stili nel blocco `<style>`:

```css
	.stale-warning {
		display: flex;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-3);
		border-radius: var(--radius-md);
		background: var(--color-warning-light, #fef3c7);
		color: var(--color-warning, #b45309);
		font-size: var(--text-sm);
	}
```

- [ ] **Step 3: Verificare i tipi e la build della SPA**

Run: `cd webapp/frontend && npm run check && npm run build`
Expected: nessun errore; build completata.

- [ ] **Step 4: Commit**

```bash
git add webapp/frontend/src/routes/magazines/+page.svelte webapp/frontend/src/routes/magazines/[id]/+page.svelte
git commit -m "feat(frontend): avviso contenuti modificati su lista e dettaglio numero"
```

---

## Note di verifica finale (dopo tutti i task)

- Backend: `cd webapp && python -m pytest -q` (nessuna regressione).
- Frontend: `cd webapp/frontend && npm run check && npm run build`.
- Smoke manuale (opzionale, se ambiente disponibile): genera PDF di un numero dalla lista; poi modifica un articolo del numero e verifica la comparsa dell'avviso ⚠️ in lista e in dettaglio.

## Verifica copertura spec

- Genera PDF da lista → Task 4.
- Avviso contenuti modificati (lista + dettaglio) → Task 5.
- Rilevamento staleness timestamp (`pdf_built_at`, `pdf_stale`) → Task 1 (colonna+migration) + Task 2 (calcolo, marker, touch mutazioni) + Task 3 (touch immagini).
- Download PDF resta disponibile quando stale → nessuna modifica al bottone download (comportamento invariato per design); Task 5 aggiunge solo l'avviso.
- Config globale fuori scope → nessun task, coerente con lo spec.
