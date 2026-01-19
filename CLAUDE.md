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
    │   ├── main.py           # Entry point FastAPI
    │   ├── models.py         # SQLAlchemy models
    │   ├── database.py       # DB setup (SQLite async)
    │   ├── routes/
    │   │   ├── articles.py   # CRUD articoli
    │   │   ├── magazines.py  # Gestione numeri rivista
    │   │   ├── upload.py     # Upload file/immagini
    │   │   └── config.py     # Configurazione
    │   ├── services/
    │   │   ├── builder.py    # Generazione PDF via Typst
    │   │   ├── converter.py  # Conversione Markdown → Typst
    │   │   └── llm.py        # Integrazione Anthropic API
    │   └── templates/        # Jinja2 templates
    ├── static/               # CSS, JS
    ├── data/                 # DB SQLite, uploads
    └── docker-compose.yml
```

## Tech Stack

| Layer | Tecnologia |
|-------|------------|
| Template | Typst |
| Backend | FastAPI, SQLAlchemy (async), aiosqlite |
| Frontend | Jinja2, vanilla JS/CSS |
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

| Endpoint | Descrizione |
|----------|-------------|
| `GET /` | Homepage |
| `GET /simple` | Modalità semplice/accessibile |
| `GET /health` | Health check |
| `/articles/*` | CRUD articoli |
| `/magazines/*` | Gestione numeri rivista |
| `/upload/*` | Upload file |
| `/config/*` | Configurazione |

## Convenzioni Codice

- **Lingua**: Italiano per UI/commenti, inglese per codice
- **Python**: Type hints, async/await per I/O
- **Typst**: Funzioni con parametri named per chiarezza
- **Errori**: Gestiti con try/except, log su console

## File Importanti

| File | Scopo |
|------|-------|
| `template.typ` | Tutti gli stili e funzioni Typst |
| `webapp/app/services/builder.py` | Generazione PDF |
| `webapp/app/services/llm.py` | Chiamate Anthropic API |
| `webapp/app/routes/upload.py` | Logica upload complessa |

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
```
