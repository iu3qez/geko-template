# GEKO Radio Magazine - Project Guide

Template Typst + webapp FastAPI per generare il GEKO Radio Magazine del Mountain QRP Club.

## Struttura Progetto

```
geko-template/
├── template.typ          # Template Typst principale (stili, funzioni)
├── geko67-completo.typ   # Esempio completo con copertina
├── esempio-geko67.typ    # Esempio semplificato
├── build.py              # Script CLI per compilare .typ → PDF
├── assets/               # Immagini, loghi
├── output/               # PDF generati
└── webapp/               # Applicazione web FastAPI
    ├── app/
    │   ├── main.py           # Entry point FastAPI (JSON API + serve SPA Svelte)
    │   ├── models.py         # SQLAlchemy models
    │   ├── database.py       # DB setup (SQLite async)
    │   ├── routes/
    │   │   └── api/          # Router JSON montato su /api
    │   │       ├── articles.py    # CRUD articoli (/api/articles)
    │   │       ├── magazines.py   # Gestione numeri rivista (/api/magazines)
    │   │       ├── images.py      # Upload/gestione immagini (/api/images)
    │   │       └── config.py      # Configurazione (/api/config)
    │   └── services/
    │       ├── builder.py    # Generazione PDF via Typst
    │       ├── converter.py  # Conversione Markdown → Typst
    │       └── llm.py        # Integrazione Anthropic API
    ├── frontend/             # SPA SvelteKit (Svelte 5 + TS, adapter-static)
    │   └── build/            # Output build servito dalla FastAPI
    ├── static/               # Asset statici legacy
    ├── data/                 # DB SQLite, uploads, output PDF
    ├── docker-compose.yml         # Sviluppo
    └── docker-compose.prod.yml    # Produzione
```

## Tech Stack

| Layer | Tecnologia |
|-------|------------|
| Template | Typst |
| Backend | FastAPI, SQLAlchemy (async), aiosqlite |
| Frontend | SvelteKit (Svelte 5, TypeScript), adapter-static |
| LLM | Anthropic Claude API |
| Build | Python typst package |
| Deploy | Docker |

## Comandi

### Compilazione diretta
```bash
# Installa dipendenze
pip install typst

# Compila PDF
python build.py geko67-completo.typ -o output/geko67.pdf
```

### Webapp (sviluppo)
```bash
cd webapp
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Webapp (Docker)
```bash
cd webapp
docker-compose up -d        # sviluppo
docker-compose -f docker-compose.prod.yml up -d  # produzione
```

## Template Typst

### Colori definiti
- `geko-gold` (#C4A35A) - Titoli, bordi, header tabelle
- `geko-magenta` (#C7338C) - Link, sottotitoli, evidenze
- `geko-dark` (#333333) - Testo principale
- `geko-light` (#F5F5F5) - Sfondi box

### Funzioni principali
```typst
#copertina(numero, mese, anno, immagine-principale, evidenze, ...)
#pagina-logo(logo-grande, sottotitolo)
#geko-magazine.with(numero, mese, anno)  // show rule
#sommario()
#titolo-articolo(testo)
#sottotitolo[testo]
#autore("CALL", nome: "Nome")
#box-evidenza(titolo: "...")[contenuto]
#figura("path", didascalia: "...", width: 80%)
#tabella-geko(headers, rows)
#link-geko("url", testo: "...")
#separatore()
```

## Webapp Routes

JSON API sotto il prefisso `/api` (vedi `app/routes/api/`). Tutte le altre
route servono la SPA SvelteKit (catch-all in `main.py`).

| Endpoint | Descrizione |
|----------|-------------|
| `GET /health` | Health check |
| `/api/articles/*` | CRUD articoli, sommari AI, assegnazione a numeri |
| `/api/magazines/*` | Gestione numeri rivista |
| `/api/images/*` | Upload/gestione immagini |
| `/api/config/*` | Configurazione |
| `GET /{path}` | Catch-all: serve la SPA Svelte (`frontend/build`) |

## Server MCP (articoli via Claude)

Server MCP montato su `/mcp` nella stessa FastAPI (`app/mcp/`), auth OAuth 2.1
via Scalekit (Resource Server → valida JWT; Authentik NON è usato per l'MCP).
Host Traefik dedicato `geko-mcp.fabris.me` senza middleware Authentik.

| Tool | Azione |
|------|--------|
| `crea_articolo` | Crea articolo da Markdown (opz. assegna a un numero) |
| `lista_numeri` / `lista_articoli` / `leggi_articolo` | Lettura/contesto |
| `modifica_articolo` / `assegna_a_numero` / `genera_sommario` | Modifica/assegnazione/AI |
| `carica_immagine` / `lista_immagini` / `elimina_immagine` | Media library per-articolo (upload/lista/eliminazione immagini, max 10 MB) |
| `anteprima_typst` | Converte Markdown→Typst senza salvare (opz. `articolo_id` per risolvere le figure) |
| risorsa `guida://convenzioni` | Sintassi Markdown del template |

### Immagini via MCP (media library per-articolo)

`carica_immagine(articolo_id, nome_file, contenuto_base64, mime="", sovrascrivi=true)`
salva l'immagine col **nome esatto** sotto `data/uploads/articoli/{id}/{nome_file}`
(scoping per articolo, servita da `/uploads/articoli/{id}/{nome}`). Nel Markdown le
figure si referenziano col **solo nome file** (`![Schema](x.png)`): i nomi nudi si
risolvono nella media library dell'articolo tramite il parametro `image_base` di
`MarkdownToTypstConverter` (`article_ops.article_image_base(id)`), sia in
`anteprima_typst(..., articolo_id=…)` sia nella build del numero. Formati: PNG,
JPG/JPEG, GIF, WEBP, SVG. Senza `image_base`/`articolo_id` il comportamento resta
invariato (nome nudo non rimappato). Logica in `article_ops.save_article_image` /
`list_article_images` / `delete_article_image`.

I tool riusano `app/services/article_ops.py` (stessa logica dei router `/api`).
Env richieste: `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`,
`SCALEKIT_CLIENT_SECRET`, `SCALEKIT_RESOURCE_ID`, `MCP_PUBLIC_URL`.

## Convenzioni Codice

- **Lingua**: Italiano per UI/commenti, inglese per codice
- **Python**: Type hints, async/await per I/O
- **Typst**: Funzioni con parametri named per chiarezza
- **Errori**: Gestiti con try/except, log su console
- **Logica articoli**: router `/api` e tool MCP delegano entrambi a `app/services/article_ops.py` (fonte unica, no duplicazione)

## File Importanti

| File | Scopo |
|------|-------|
| `template.typ` | Tutti gli stili e funzioni Typst |
| `webapp/app/services/builder.py` | Generazione PDF |
| `webapp/app/services/llm.py` | Chiamate Anthropic API |
| `webapp/app/services/converter.py` | Convenzioni Markdown → Typst (admonition, tabelle, figure, link; `image_base` risolve i nomi file nudi) |
| `webapp/app/services/article_ops.py` | Fonte unica logica articoli + media library per-articolo (`save/list/delete_article_image`) |
| `webapp/app/routes/api/images.py` | Logica upload immagini web (flusso separato, prefisso uuid) |

## Environment Variables (webapp)

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=sqlite+aiosqlite:///./data/geko.db
SECRET_KEY=...
```

## Testing

```bash
# Compila esempio per verificare template
python build.py esempio-geko67.typ

# Verifica webapp
curl http://localhost:8000/health

# Test webapp (pytest-asyncio). NB: Python di sistema è PEP 668 → serve venv locale
cd webapp
python -m venv .venv && source .venv/bin/activate   # .venv è gitignorato
pip install -r requirements.txt
python -m pytest          # test in webapp/tests/, asyncio_mode=auto (pytest.ini)
```
