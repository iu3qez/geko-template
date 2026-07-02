# MCP: gestione dei numeri della rivista — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere i tool MCP `crea_numero`, `modifica_numero`, `elimina_numero` per creare e gestire i numeri della rivista GEKO, con validazione e delega alla logica condivisa.

**Architecture:** La logica vive in `article_ops.py` (fonte unica di verità), i tool MCP in `server.py` sono wrapper sottili che aprono `async_session()` e delegano. Gli errori sono segnalati sollevando `ValueError` (FastMCP → `ToolError` lato client), coerente con i tool esistenti.

**Tech Stack:** Python async, SQLAlchemy (async), FastMCP, pytest (asyncio_mode=auto).

## Global Constraints

- Lingua: italiano per docstring/messaggi/UI, inglese per identificatori di codice.
- Errori: **raise `ValueError`** con messaggio italiano leggibile. Mai ritornare `{"success": false}`.
- Nessuna duplicazione: i tool MCP NON contengono logica DB, delegano ad `article_ops`.
- Mesi validi (12, italiano): Gennaio, Febbraio, Marzo, Aprile, Maggio, Giugno, Luglio, Agosto, Settembre, Ottobre, Novembre, Dicembre.
- `anno`: esattamente 4 cifre (`^\d{4}$`). `stato` ∈ {`bozza`, `pubblicato`}, default `bozza`.
- `numero` univoco: verificato a livello applicativo (non vincolo DB).
- Test in `webapp/tests/`, eseguiti da `webapp/` con `python -m pytest`. Fixture disponibili: `db`, `sample_magazine` (ritorna `{"id", "numero"}` per un numero "99"/Gennaio/2026), `patch_session` (in `test_mcp_server.py`).
- Serializzazione output: `article_ops.magazine_to_response(m)` → `{id, numero, mese, anno, stato}`.

---

### Task 1: Validation helper + `create_magazine`

**Files:**
- Modify: `webapp/app/services/article_ops.py` (import `re` e `MagazineStatus`; aggiungi helper e funzione)
- Test: `webapp/tests/test_article_ops.py`

**Interfaces:**
- Consumes: `Magazine`, `MagazineStatus` da `..models`; `magazine_to_response` (già presente).
- Produces:
  - `_validate_magazine_fields(*, numero=None, mese=None, anno=None, stato=None) -> dict` — ritorna i campi passati normalizzati (`stato` → `MagazineStatus`); solleva `ValueError` su input non valido.
  - `create_magazine(db, *, numero: str, mese: str, anno: str, stato: str = "bozza") -> dict`.

- [ ] **Step 1: Scrivi i test che falliscono**

Aggiungi in fondo a `webapp/tests/test_article_ops.py`:

```python
async def test_create_magazine_defaults_to_bozza(db):
    mag = await article_ops.create_magazine(db, numero="68", mese="Luglio", anno="2026")
    assert mag["id"] > 0
    assert mag["numero"] == "68"
    assert mag["mese"] == "Luglio"
    assert mag["stato"] == "bozza"


async def test_create_magazine_normalizes_month(db):
    mag = await article_ops.create_magazine(db, numero="70", mese="luglio", anno="2026")
    assert mag["mese"] == "Luglio"


async def test_create_magazine_rejects_invalid_month(db):
    with pytest.raises(ValueError):
        await article_ops.create_magazine(db, numero="71", mese="Luglioo", anno="2026")


async def test_create_magazine_rejects_invalid_year(db):
    with pytest.raises(ValueError):
        await article_ops.create_magazine(db, numero="72", mese="Luglio", anno="26")


async def test_create_magazine_rejects_duplicate_numero(db):
    await article_ops.create_magazine(db, numero="73", mese="Luglio", anno="2026")
    with pytest.raises(ValueError):
        await article_ops.create_magazine(db, numero="73", mese="Agosto", anno="2026")
    mags = await article_ops.list_magazines(db)
    assert sum(1 for m in mags if m["numero"] == "73") == 1
```

- [ ] **Step 2: Esegui i test per verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -k magazine -v`
Expected: FAIL con `AttributeError: module 'app.services.article_ops' has no attribute 'create_magazine'`.

- [ ] **Step 3: Implementa helper e funzione**

In `webapp/app/services/article_ops.py`, aggiungi `import re` in cima (con gli altri import) e cambia l'import dei modelli in:

```python
from ..models import Article, Config, Magazine, MagazineStatus
```

Poi aggiungi (dopo `magazine_to_response`):

```python
_MESI_IT = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]
_MESI_LOOKUP = {m.lower(): m for m in _MESI_IT}
_STATI_VALIDI = {s.value for s in MagazineStatus}


def _validate_magazine_fields(*, numero=None, mese=None, anno=None, stato=None) -> dict:
    """Valida i campi passati (non-None) di un numero e li normalizza.

    Ritorna un dict coi soli campi passati; `stato` diventa MagazineStatus.
    Solleva ValueError con messaggio italiano su input non valido.
    """
    cleaned = {}
    if numero is not None:
        numero = str(numero).strip()
        if not numero:
            raise ValueError("Il numero non può essere vuoto")
        cleaned["numero"] = numero
    if mese is not None:
        normalizzato = _MESI_LOOKUP.get(str(mese).strip().lower())
        if normalizzato is None:
            raise ValueError(
                f"Mese non valido: '{mese}'. Valori ammessi: {', '.join(_MESI_IT)}"
            )
        cleaned["mese"] = normalizzato
    if anno is not None:
        anno = str(anno).strip()
        if not re.fullmatch(r"\d{4}", anno):
            raise ValueError(f"Anno non valido: '{anno}' (devono essere 4 cifre)")
        cleaned["anno"] = anno
    if stato is not None:
        stato = str(stato).strip().lower()
        if stato not in _STATI_VALIDI:
            raise ValueError(
                f"Stato non valido: '{stato}'. Valori ammessi: {', '.join(sorted(_STATI_VALIDI))}"
            )
        cleaned["stato"] = MagazineStatus(stato)
    return cleaned


async def create_magazine(db, *, numero: str, mese: str, anno: str, stato: str = "bozza") -> dict:
    """Crea un numero della rivista. Solleva ValueError su validazione/duplicato."""
    cleaned = _validate_magazine_fields(numero=numero, mese=mese, anno=anno, stato=stato)
    existing = await db.execute(select(Magazine).where(Magazine.numero == cleaned["numero"]))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Numero già esistente: {cleaned['numero']}")
    magazine = Magazine(
        numero=cleaned["numero"],
        mese=cleaned["mese"],
        anno=cleaned["anno"],
        stato=cleaned["stato"],
    )
    db.add(magazine)
    await db.commit()
    await db.refresh(magazine)
    return magazine_to_response(magazine)
```

- [ ] **Step 4: Esegui i test per verificarne il successo**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -k magazine -v`
Expected: PASS (i 5 nuovi test + `test_list_magazines` esistente).

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/article_ops.py webapp/tests/test_article_ops.py
git commit -m "feat(article_ops): create_magazine con validazione e unicità numero"
```

---

### Task 2: `update_magazine` + ordinamento `list_magazines`

**Files:**
- Modify: `webapp/app/services/article_ops.py` (aggiungi `update_magazine`; cambia ordinamento in `list_magazines`)
- Test: `webapp/tests/test_article_ops.py`

**Interfaces:**
- Consumes: `_validate_magazine_fields`, `create_magazine` (Task 1), `magazine_to_response`.
- Produces: `update_magazine(db, magazine_id: int, **fields) -> Optional[dict]` — ritorna `None` se il numero non esiste; `ValueError` su validazione o numero duplicato.

- [ ] **Step 1: Scrivi i test che falliscono**

Aggiungi in fondo a `webapp/tests/test_article_ops.py`:

```python
async def test_update_magazine_changes_stato(db, sample_magazine):
    updated = await article_ops.update_magazine(db, sample_magazine["id"], stato="pubblicato")
    assert updated["stato"] == "pubblicato"
    mags = await article_ops.list_magazines(db)
    assert next(m for m in mags if m["id"] == sample_magazine["id"])["stato"] == "pubblicato"


async def test_update_magazine_missing_returns_none(db):
    assert await article_ops.update_magazine(db, 999, stato="pubblicato") is None


async def test_update_magazine_rejects_duplicate_numero(db):
    await article_ops.create_magazine(db, numero="80", mese="Gennaio", anno="2026")
    b = await article_ops.create_magazine(db, numero="81", mese="Febbraio", anno="2026")
    with pytest.raises(ValueError):
        await article_ops.update_magazine(db, b["id"], numero="80")


async def test_list_magazines_orders_by_year_desc(db):
    await article_ops.create_magazine(db, numero="60", mese="Gennaio", anno="2025")
    await article_ops.create_magazine(db, numero="61", mese="Gennaio", anno="2026")
    mags = await article_ops.list_magazines(db)
    annos = [m["anno"] for m in mags]
    assert annos == sorted(annos, reverse=True)
```

- [ ] **Step 2: Esegui i test per verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -k "update_magazine or orders_by_year" -v`
Expected: FAIL (`update_magazine` inesistente; l'ordinamento potrebbe già passare per caso ma i test `update_magazine` falliscono).

- [ ] **Step 3: Implementa `update_magazine` e cambia l'ordinamento**

In `webapp/app/services/article_ops.py`, sostituisci la funzione `list_magazines` esistente con:

```python
async def list_magazines(db) -> list[dict]:
    result = await db.execute(
        select(Magazine).order_by(Magazine.anno.desc(), Magazine.numero.desc())
    )
    return [magazine_to_response(m) for m in result.scalars().all()]
```

E aggiungi (dopo `create_magazine`):

```python
async def update_magazine(db, magazine_id: int, **fields) -> Optional[dict]:
    """Aggiorna i campi passati di un numero. None se non esiste."""
    result = await db.execute(select(Magazine).where(Magazine.id == magazine_id))
    magazine = result.scalar_one_or_none()
    if not magazine:
        return None
    to_validate = {
        k: v for k, v in fields.items()
        if k in {"numero", "mese", "anno", "stato"} and v is not None
    }
    cleaned = _validate_magazine_fields(**to_validate)
    if "numero" in cleaned and cleaned["numero"] != magazine.numero:
        dup = await db.execute(
            select(Magazine).where(
                Magazine.numero == cleaned["numero"], Magazine.id != magazine_id
            )
        )
        if dup.scalar_one_or_none() is not None:
            raise ValueError(f"Numero già esistente: {cleaned['numero']}")
    for key, value in cleaned.items():
        setattr(magazine, key, value)
    await db.commit()
    await db.refresh(magazine)
    return magazine_to_response(magazine)
```

- [ ] **Step 4: Esegui i test per verificarne il successo**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -k magazine -v`
Expected: PASS (nuovi test + quelli di Task 1 + `test_list_magazines`).

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/article_ops.py webapp/tests/test_article_ops.py
git commit -m "feat(article_ops): update_magazine + ordinamento anno,numero"
```

---

### Task 3: `delete_magazine` (guardia articoli associati)

**Files:**
- Modify: `webapp/app/services/article_ops.py` (aggiungi `delete_magazine`)
- Test: `webapp/tests/test_article_ops.py`

**Interfaces:**
- Consumes: `Magazine`, `selectinload` (già importato), `create_article`, `assign_article`, `get_article`.
- Produces: `delete_magazine(db, magazine_id: int, *, forza: bool = False) -> Optional[bool]` — `None` se non esiste, `True` se eliminato; `ValueError` se ha articoli e `forza` è `False`.

- [ ] **Step 1: Scrivi i test che falliscono**

Aggiungi in fondo a `webapp/tests/test_article_ops.py`:

```python
async def test_delete_magazine_without_articles(db, sample_magazine):
    assert await article_ops.delete_magazine(db, sample_magazine["id"]) is True
    mags = await article_ops.list_magazines(db)
    assert all(m["id"] != sample_magazine["id"] for m in mags)


async def test_delete_magazine_missing_returns_none(db):
    assert await article_ops.delete_magazine(db, 999) is None


async def test_delete_magazine_with_articles_requires_forza(db, sample_magazine):
    art = await article_ops.create_article(db, titolo="X", contenuto_md="y")
    await article_ops.assign_article(db, art["id"], [sample_magazine["id"]])
    with pytest.raises(ValueError):
        await article_ops.delete_magazine(db, sample_magazine["id"])


async def test_delete_magazine_forza_keeps_article(db, sample_magazine):
    art = await article_ops.create_article(db, titolo="X", contenuto_md="y")
    await article_ops.assign_article(db, art["id"], [sample_magazine["id"]])
    assert await article_ops.delete_magazine(db, sample_magazine["id"], forza=True) is True
    assert await article_ops.get_article(db, art["id"]) is not None
```

- [ ] **Step 2: Esegui i test per verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -k delete_magazine -v`
Expected: FAIL (`delete_magazine` inesistente).

- [ ] **Step 3: Implementa `delete_magazine`**

In `webapp/app/services/article_ops.py`, aggiungi (dopo `update_magazine`):

```python
async def delete_magazine(db, magazine_id: int, *, forza: bool = False) -> Optional[bool]:
    """Elimina un numero. None se non esiste. ValueError se ha articoli e non `forza`.

    Non elimina a cascata gli articoli: rimuove solo le associazioni M2M.
    """
    result = await db.execute(
        select(Magazine)
        .options(selectinload(Magazine.articles))
        .where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()
    if not magazine:
        return None
    if magazine.articles and not forza:
        raise ValueError(
            f"Il numero {magazine.numero} ha {len(magazine.articles)} articoli associati; "
            "usa forza=True per eliminarlo"
        )
    await db.delete(magazine)
    await db.commit()
    return True
```

- [ ] **Step 4: Esegui i test per verificarne il successo**

Run: `cd webapp && python -m pytest tests/test_article_ops.py -v`
Expected: PASS (tutti i test del file, inclusi quelli preesistenti sugli articoli).

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/article_ops.py webapp/tests/test_article_ops.py
git commit -m "feat(article_ops): delete_magazine con guardia articoli associati"
```

---

### Task 4: Tool MCP `crea_numero`, `modifica_numero`, `elimina_numero`

**Files:**
- Modify: `webapp/app/mcp/server.py` (aggiungi 3 tool)
- Test: `webapp/tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `article_ops.create_magazine`, `article_ops.update_magazine`, `article_ops.delete_magazine` (Task 1-3); `async_session`; fixture `patch_session` esistente.
- Produces: tool MCP `crea_numero`, `modifica_numero`, `elimina_numero` (registrati su `server_mod.mcp`).

- [ ] **Step 1: Scrivi i test che falliscono**

Aggiungi in fondo a `webapp/tests/test_mcp_server.py`:

```python
async def test_crea_numero_tool(patch_session):
    async with Client(server_mod.mcp) as client:
        data = (await client.call_tool(
            "crea_numero", {"numero": "68", "mese": "Luglio", "anno": "2026"}
        )).data
        assert data["id"] > 0
        assert data["stato"] == "bozza"


async def test_crea_numero_id_usable_with_assegna(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "69", "mese": "Agosto", "anno": "2026"}
        )).data
        art = (await client.call_tool(
            "crea_articolo", {"titolo": "T", "contenuto_md": "y"}
        )).data
        assigned = (await client.call_tool(
            "assegna_a_numero", {"id": art["id"], "numero_ids": [num["id"]]}
        )).data
        assert [m["id"] for m in assigned["magazines"]] == [num["id"]]


async def test_crea_numero_duplicate_raises(patch_session):
    async with Client(server_mod.mcp) as client:
        await client.call_tool("crea_numero", {"numero": "70", "mese": "Luglio", "anno": "2026"})
        with pytest.raises(ToolError):
            await client.call_tool("crea_numero", {"numero": "70", "mese": "Agosto", "anno": "2026"})


async def test_crea_numero_invalid_month_raises(patch_session):
    async with Client(server_mod.mcp) as client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "crea_numero", {"numero": "71", "mese": "Luglioo", "anno": "2026"}
            )


async def test_modifica_numero_updates_stato(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "72", "mese": "Luglio", "anno": "2026"}
        )).data
        await client.call_tool("modifica_numero", {"id": num["id"], "stato": "pubblicato"})
        numeri = (await client.call_tool("lista_numeri", {})).data
        assert next(n for n in numeri if n["id"] == num["id"])["stato"] == "pubblicato"


async def test_elimina_numero_with_articles_then_forza(patch_session):
    async with Client(server_mod.mcp) as client:
        num = (await client.call_tool(
            "crea_numero", {"numero": "73", "mese": "Luglio", "anno": "2026"}
        )).data
        art = (await client.call_tool(
            "crea_articolo", {"titolo": "T", "contenuto_md": "y"}
        )).data
        await client.call_tool("assegna_a_numero", {"id": art["id"], "numero_ids": [num["id"]]})
        with pytest.raises(ToolError):
            await client.call_tool("elimina_numero", {"id": num["id"]})
        res = (await client.call_tool(
            "elimina_numero", {"id": num["id"], "forza": True}
        )).data
        assert res["eliminato"] == num["id"]
```

- [ ] **Step 2: Esegui i test per verificarne il fallimento**

Run: `cd webapp && python -m pytest tests/test_mcp_server.py -k numero -v`
Expected: FAIL (`Unknown tool: crea_numero`).

- [ ] **Step 3: Implementa i tool**

In `webapp/app/mcp/server.py`, aggiungi (dopo `assegna_a_numero`, prima di `genera_sommario`):

```python
@mcp.tool
async def crea_numero(numero: str, mese: str, anno: str, stato: str = "bozza") -> dict:
    """Crea un nuovo numero della rivista.

    `mese` in italiano (es. "Luglio"), `anno` a 4 cifre, `stato` = bozza|pubblicato
    (default bozza). Ritorna il record creato (id, numero, mese, anno, stato).
    """
    async with async_session() as db:
        return await article_ops.create_magazine(
            db, numero=numero, mese=mese, anno=anno, stato=stato
        )


@mcp.tool
async def modifica_numero(
    id: int,
    numero: Optional[str] = None,
    mese: Optional[str] = None,
    anno: Optional[str] = None,
    stato: Optional[str] = None,
) -> dict:
    """Aggiorna i campi indicati di un numero esistente (id, numero, mese, anno, stato)."""
    fields = {k: v for k, v in {
        "numero": numero, "mese": mese, "anno": anno, "stato": stato,
    }.items() if v is not None}
    async with async_session() as db:
        mag = await article_ops.update_magazine(db, id, **fields)
        if mag is None:
            raise ValueError(f"Numero {id} non trovato")
        return mag


@mcp.tool
async def elimina_numero(id: int, forza: bool = False) -> dict:
    """Elimina un numero. Fallisce se ha articoli associati (usa forza=True).

    Non elimina gli articoli, solo le associazioni al numero.
    """
    async with async_session() as db:
        ok = await article_ops.delete_magazine(db, id, forza=forza)
        if ok is None:
            raise ValueError(f"Numero {id} non trovato")
        return {"eliminato": id}
```

- [ ] **Step 4: Esegui i test per verificarne il successo**

Run: `cd webapp && python -m pytest tests/test_mcp_server.py -v`
Expected: PASS (nuovi test + quelli preesistenti sugli articoli).

- [ ] **Step 5: Esegui l'intera suite**

Run: `cd webapp && python -m pytest -q`
Expected: PASS su tutti i file di test.

- [ ] **Step 6: Commit**

```bash
git add webapp/app/mcp/server.py webapp/tests/test_mcp_server.py
git commit -m "feat(mcp): tool crea_numero, modifica_numero, elimina_numero"
```

---

## Note di aggiornamento documentazione (opzionale, non bloccante)

Dopo il merge, aggiornare la tabella dei tool MCP in `CLAUDE.md` (sezione "Server MCP") aggiungendo `crea_numero` / `modifica_numero` / `elimina_numero`. Non incluso come task perché non testabile; farlo nel commit finale o in un commit docs separato.
