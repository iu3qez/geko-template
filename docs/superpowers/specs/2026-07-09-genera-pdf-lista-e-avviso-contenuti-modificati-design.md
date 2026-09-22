# Genera PDF dalla lista numeri + avviso "contenuti modificati"

Data: 2026-07-09

## Obiettivo

Due modifiche alla webapp GEKO:

1. **Genera PDF dalla lista** — la pagina `/magazines` permette di vedere i
   dettagli e scaricare il PDF, ma non di rigenerare un numero. Solo la pagina
   di dettaglio (`/magazines/{id}`) ha il pulsante "Genera PDF". Aggiungere il
   pulsante anche alle card della lista.

2. **Avviso contenuti modificati** — segnalare quando i contenuti di un numero
   sono cambiati dopo l'ultima generazione del PDF, così l'utente sa che il PDF
   scaricabile potrebbe non essere allineato ai contenuti e va rigenerato.

## Decisioni prese

- **Rilevamento staleness**: confronto timestamp. Salvo `pdf_built_at` alla
  generazione riuscita e lo confronto con l'ultima modifica dei contenuti del
  numero. Scope: **numero + articoli** (incluse immagini degli articoli). La
  **config globale** (team MQC, link, immagini pagina finale) NON conta ai fini
  della staleness.
- **PDF obsoleto**: quando un numero è stale il download del PDF esistente
  **resta disponibile**, ma affiancato da un avviso evidente.

## Architettura

### Backend — rilevamento staleness (timestamp)

**Modello** (`app/models.py`): nuovo campo su `Magazine`:

```python
pdf_built_at = Column(DateTime, nullable=True)
```

**Migration** (`app/database.py`, funzione `run_migrations`): seguendo il
pattern esistente per `images.alt_text`, aggiungere la colonna se manca:

```python
# PRAGMA table_info(magazines) → se "pdf_built_at" non c'è:
conn.execute(text("ALTER TABLE magazines ADD COLUMN pdf_built_at DATETIME"))
```

`run_migrations` va esteso per ispezionare anche la tabella `magazines` (oggi
guarda solo `images`).

**Marker di generazione** (`app/routes/api/magazines.py`, `build_pdf`): su build
riuscita, oltre a `magazine.stato = MagazineStatus.PUBBLICATO`, impostare
`magazine.pdf_built_at = utcnow()` prima del commit.

**Calcolo staleness** — helper che confronta `pdf_built_at` con l'ultima
modifica dei contenuti:

```
content_updated_at = max(
    magazine.updated_at,
    max(article.updated_at for article in magazine.articles)  # se articoli
)
pdf_stale = (pdf_built_at is not None) and (content_updated_at > pdf_built_at)
```

Note implementative:
- Se non ci sono articoli, `content_updated_at = magazine.updated_at`.
- Confronto timezone-safe: `updated_at`/`pdf_built_at` sono `DateTime` naive nel
  DB (SQLite). `utcnow()` è tz-aware. Normalizzare i due lati allo stesso tipo
  prima di confrontare (es. rendere entrambi naive UTC) per evitare
  `TypeError: can't compare offset-naive and offset-aware datetimes`.

**Copertura dei casi di modifica** — perché il confronto timestamp è sufficiente:
- Editoriale / copertina / dati numero → `Magazine.updated_at` (già
  `onupdate=utcnow`).
- Testo/metadati articolo → `Article.updated_at` (già `onupdate=utcnow`).
- Aggiungi / rimuovi / riordina articoli → questi endpoint modificano la
  junction table `article_magazines` **senza** toccare `Magazine.updated_at`.
  Aggiungere `magazine.updated_at = utcnow()` esplicito in `add_article`,
  `remove_article`, `reorder_articles`.
- Upload / rimozione immagine di un articolo → in
  `app/services/article_ops.py` (`save_article_image`, `delete_article_image`)
  toccare `article.updated_at = utcnow()` dell'articolo interessato, così la
  modifica si propaga alla staleness dei numeri che lo contengono.

**Risposta API** (`magazine_to_response`): esporre due campi nuovi, sia in
`list_magazines` che in `get_magazine`:
- `pdf_built_at`: ISO string | null
- `pdf_stale`: bool

`list_magazines` e `get_magazine` già fanno `selectinload(Magazine.articles)`,
quindi `article.updated_at` è disponibile senza query extra.

### Frontend — tipi (`src/lib/api.ts`)

Aggiungere all'interface `Magazine`:

```ts
pdf_built_at: string | null;
pdf_stale?: boolean;
```

### Frontend — pulsante "Genera PDF" nella lista (`src/routes/magazines/+page.svelte`)

- Nel footer di ogni card, pulsante **"Genera PDF"** che chiama
  `magazines.build(magazine.id)`.
- Stato di loading **per-card**: un `Set<number>` (o `Record<number, ...>`) di
  id in build, così più card possono avere stati indipendenti.
- `disabled` se `article_count === 0`.
- Al successo: ricaricare la lista (`loadMagazines()`) per aggiornare stato e
  `pdf_stale`.
- Esito inline sulla card: successo o messaggio d'errore (riusare lo stile
  `build-result` del dettaglio).
- Visibile per **tutti** i numeri con articoli (bozza e pubblicato).
- Ordine bottoni card: `Dettagli` · `Genera PDF` · `PDF` (download, se
  pubblicato) · elimina (🗑).

### Frontend — avviso "contenuti modificati"

Quando `magazine.pdf_stale === true`:

- **Lista** (`magazines/+page.svelte`): sulla card, un avviso in stile warning,
  es. ⚠️ *"Contenuti modificati — rigenera"*, vicino ai bottoni azione.
- **Dettaglio** (`magazines/[id]/+page.svelte`): banner di avviso nella Card
  "Azioni", **sopra** i bottoni: ⚠️ *"I contenuti sono cambiati dopo l'ultima
  generazione del PDF. Rigenera per allineare il PDF."* Il pulsante "Scarica
  PDF" resta disponibile.

## Fuori scope

- Staleness da modifica della **config globale** (team, link, immagini pagina
  finale): esplicitamente esclusa.
- Correzione del caso pre-esistente in cui un numero viene messo manualmente su
  `pubblicato` senza mai buildare (il download mostra 404 perché il file PDF non
  esiste). Non introdotto né peggiorato da questa modifica.

## Testing

- Test backend (`webapp/tests/`, pytest-asyncio):
  - `pdf_stale` è `false` subito dopo una build riuscita.
  - `pdf_stale` diventa `true` dopo aver modificato un articolo del numero.
  - `pdf_stale` diventa `true` dopo add/remove/reorder articoli.
  - `pdf_stale` è `false` quando `pdf_built_at` è null (mai buildato).
  - `pdf_built_at` viene valorizzato dalla build.
- Verifica frontend: build della SPA senza errori TS; smoke test manuale del
  pulsante nella lista e dell'avviso.
