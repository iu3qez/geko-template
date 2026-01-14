"""
GEKO Magazine Web App - Entry Point

Applicazione web per generare il GEKO Radio Magazine del Mountain QRP Club.

Funzionalità principali:
    - Gestione articoli in formato Markdown
    - Upload e gestione immagini
    - Generazione automatica sommari con Claude AI
    - Conversione Markdown → Typst
    - Generazione PDF con template GEKO
    - Archivio storico numeri della rivista

Stack tecnologico:
    - FastAPI: Web framework async
    - SQLite + SQLAlchemy: Database
    - Jinja2 + HTMX: Frontend reattivo senza JavaScript complesso
    - Typst: Generazione PDF
    - Claude API: Generazione sommari

Configurazione:
    Le variabili d'ambiente possono essere impostate in un file .env:
    - ANTHROPIC_API_KEY: API key per Claude (opzionale, per sommari AI)
    - DATABASE_URL: Override path database SQLite

Avvio sviluppo:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Avvio produzione:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

Autore: GEKO Magazine Team
Licenza: MIT
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import init_db
from app.routes import articles, magazines, upload

# Directory paths
APP_DIR = Path(__file__).parent
WEBAPP_DIR = APP_DIR.parent
STATIC_DIR = WEBAPP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestione ciclo di vita dell'applicazione.

    All'avvio:
        - Inizializza il database (crea tabelle se non esistono)
        - Crea directory necessarie

    Alla chiusura:
        - Cleanup risorse (se necessario)
    """
    # === STARTUP ===
    print("Inizializzazione GEKO Magazine Web App...")

    # Crea database e tabelle
    await init_db()
    print("Database inizializzato")

    # Crea directory se non esistono
    (WEBAPP_DIR / "data" / "articles").mkdir(parents=True, exist_ok=True)
    (WEBAPP_DIR / "data" / "images").mkdir(parents=True, exist_ok=True)
    (WEBAPP_DIR / "data" / "output").mkdir(parents=True, exist_ok=True)
    (WEBAPP_DIR / "typst" / "generated").mkdir(parents=True, exist_ok=True)
    print("Directory create")

    print("App pronta!")

    yield  # L'app è in esecuzione

    # === SHUTDOWN ===
    print("Chiusura GEKO Magazine Web App...")


# Crea istanza FastAPI
app = FastAPI(
    title="GEKO Magazine",
    description="Web app per generare il GEKO Radio Magazine",
    version="1.0.0",
    lifespan=lifespan,
)

# Monta file statici (CSS, JS, immagini)
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Monta directory immagini per accesso diretto
IMAGES_DIR = WEBAPP_DIR / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# Configura templates Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Rendi templates disponibili globalmente nell'app
app.state.templates = templates

# Registra routers
app.include_router(articles.router)
app.include_router(magazines.router)
app.include_router(upload.router)


# =============================================================================
# ROUTES PRINCIPALI
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Homepage dell'applicazione.

    Mostra:
        - Dashboard con statistiche (numero articoli, numeri pubblicati)
        - Accesso rapido alle funzioni principali
        - Link alla modalità semplice (accessibile)
    """
    return templates.TemplateResponse(
        "standard/home.html",
        {"request": request}
    )


@app.get("/simple", response_class=HTMLResponse)
async def simple_mode(request: Request):
    """
    Homepage modalità semplice (accessibile).

    Interfaccia ottimizzata per:
        - Utenti con difficoltà motorie (es. Parkinson)
        - Bottoni grandi e ben distanziati
        - Una azione per schermata
        - Alto contrasto
    """
    return templates.TemplateResponse(
        "simple/home.html",
        {"request": request}
    )


@app.get("/simple/upload", response_class=HTMLResponse)
async def simple_upload(request: Request):
    """
    Pagina upload articolo - modalità semplice.

    Step 1 del workflow semplificato.
    Un solo bottone grande per caricare il file markdown.
    """
    return templates.TemplateResponse(
        "simple/upload.html",
        {"request": request}
    )


@app.get("/simple/images", response_class=HTMLResponse)
async def simple_images(request: Request):
    """
    Pagina upload immagini - modalità semplice.

    Step 2 del workflow semplificato.
    Drag & drop o click per caricare immagini.
    """
    return templates.TemplateResponse(
        "simple/images.html",
        {"request": request}
    )


@app.get("/simple/generate", response_class=HTMLResponse)
async def simple_generate(request: Request):
    """
    Pagina generazione PDF - modalità semplice.

    Step finale del workflow semplificato.
    Un solo bottone per generare e scaricare il PDF.
    """
    return templates.TemplateResponse(
        "simple/generate.html",
        {"request": request}
    )


@app.get("/health")
async def health_check():
    """
    Endpoint per health check.

    Usato da Docker/orchestratori per verificare che l'app sia attiva.

    Returns:
        JSON con status "ok" e versione
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "app": "GEKO Magazine"
    }


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """
    Handler per errori 404 (pagina non trovata).

    Mostra una pagina user-friendly invece del JSON di default.
    """
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """
    Handler per errori 500 (errore interno).

    Mostra una pagina user-friendly con istruzioni per l'utente.
    """
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500
    )
