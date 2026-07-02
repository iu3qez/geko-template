# GEKO Magazine Web App

Web app per generare il **GEKO Radio Magazine** del Mountain QRP Club.

## Funzionalità

- **Upload articoli** in formato Markdown
- **Generazione sommari** automatici con Claude AI
- **Conversione** Markdown → Typst → PDF
- **Archivio** storico numeri rivista
- **Modalità accessibile** per utenti con difficoltà motorie
- **Server MCP** per creare/gestire articoli e caricare immagini da Claude

## Quick Start

### Con Docker (raccomandato)

```bash
# 1. Configura API key Claude (opzionale)
cp .env.example .env
# Modifica .env con la tua ANTHROPIC_API_KEY

# 2. Avvia
docker-compose up -d

# 3. Apri nel browser
open http://localhost:8000
```

### Sviluppo locale

```bash
# 1. Crea virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia server sviluppo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Struttura

```
webapp/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── models.py            # Modelli SQLAlchemy
│   ├── database.py          # Configurazione DB
│   ├── routes/              # API endpoints
│   │   ├── articles.py      # CRUD articoli
│   │   ├── magazines.py     # Gestione numeri
│   │   └── upload.py        # Upload file
│   ├── services/            # Business logic
│   │   ├── converter.py     # MD → Typst
│   │   ├── builder.py       # Typst → PDF
│   │   └── llm.py           # Claude API
│   └── templates/           # HTML (Jinja2)
│       ├── standard/        # UI completa
│       └── simple/          # UI accessibile
├── static/css/              # Stili
├── data/                    # Database e file
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Modalità Semplice (Accessibile)

L'app include una modalità semplificata ottimizzata per utenti con difficoltà motorie:

- Bottoni grandi (60px+)
- Alto contrasto
- Una azione per schermata
- Nessuno scroll necessario

Accedi da: `http://localhost:8000/simple`

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/` | Homepage |
| GET | `/simple` | Modalità accessibile |
| GET | `/articles/` | Lista articoli |
| POST | `/articles/` | Crea articolo |
| POST | `/articles/{id}/summary` | Genera sommario AI |
| GET | `/magazines/` | Archivio numeri |
| POST | `/magazines/` | Crea numero |
| POST | `/magazines/{id}/build` | Genera PDF |
| GET | `/magazines/{id}/pdf` | Scarica PDF |
| POST | `/upload/markdown` | Importa file MD |
| POST | `/upload/image` | Carica immagine |

## Server MCP (articoli via Claude)

L'app espone un server MCP (Model Context Protocol) con auth OAuth 2.1 via
Scalekit, che permette a Claude di creare e gestire articoli conformi al
template. Tool disponibili:

| Tool | Azione |
|------|--------|
| `crea_articolo` | Crea articolo da Markdown (opz. assegna a un numero) |
| `lista_numeri` / `lista_articoli` / `leggi_articolo` | Lettura/contesto |
| `modifica_articolo` / `assegna_a_numero` / `genera_sommario` | Modifica / assegnazione / sommario AI |
| `carica_immagine` / `lista_immagini` / `elimina_immagine` | Media library per-articolo (immagini) |
| `ottieni_upload_url` | Conia URL firmati per upload immagini via `curl -F` (per Cowork, no base64) |
| `anteprima_typst` | Converte Markdown → Typst senza salvare |

### Pubblicare un articolo con figure

Nel Markdown referenzia le immagini col **solo nome file**, poi caricane i byte:

```
crea_articolo(titolo="Come funziona il QMX",
              contenuto_md="![Schema finale](QMX_schema_finale.png)\n...")
# → restituisce l'id dell'articolo, es. 42
carica_immagine(articolo_id=42, nome_file="QMX_schema_finale.png",
                contenuto_base64="<byte del file in base64>")
anteprima_typst(contenuto_md="...", articolo_id=42)   # figure risolte
```

- Le immagini sono salvate col nome esatto sotto
  `data/uploads/articoli/{id}/{nome_file}` (scoping per articolo, così due
  articoli possono usare lo stesso nome file senza collisioni).
- Formati: **PNG, JPG/JPEG, GIF, WEBP, SVG** (max 10 MB); MIME dedotto
  dall'estensione se non fornito.
- `sovrascrivi=true` (default) rimpiazza un file con lo stesso nome;
  `sovrascrivi=false` dà errore se esiste già.
- I riferimenti col nome file nudo si risolvono nella media library
  dell'articolo in anteprima (`anteprima_typst(..., articolo_id=…)`) e in fase
  di build del numero.

## Configurazione

### Variabili Ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key Claude per sommari | (nessuno) |
| `ENVIRONMENT` | `development` o `production` | `production` |

### Integrazione Authentik

L'app non include autenticazione interna. Configura Authentik come reverse proxy:

```nginx
location / {
    auth_request /outpost.goauthentik.io/auth/nginx;
    proxy_pass http://localhost:8000;
}
```

## Formato Markdown

Gli articoli supportano questo formato:

```markdown
---
titolo: "Titolo Articolo"
autore: "IU3XYZ"
nome: "Nome Autore"
sottotitolo: "Sottotitolo opzionale"
---

Contenuto dell'articolo...

## Sezione

Testo con **grassetto** e *corsivo*.

![Descrizione](percorso/immagine.jpg)

!!! nota "Titolo Box"
Contenuto del box evidenza
!!!
```

## Licenza

MIT License - Mountain QRP Club
