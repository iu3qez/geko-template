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
    - Svelte: Frontend SPA
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

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import init_db
from app.routes.api import router as api_router

# Directory paths
APP_DIR = Path(__file__).parent
WEBAPP_DIR = APP_DIR.parent
STATIC_DIR = WEBAPP_DIR / "static"
FRONTEND_DIR = WEBAPP_DIR / "frontend" / "build"


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
    (WEBAPP_DIR / "data" / "uploads").mkdir(parents=True, exist_ok=True)
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
    version="2.0.0",
    lifespan=lifespan,
)

# Monta file statici legacy (CSS, JS)
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Monta directory immagini caricate per accesso diretto
UPLOADS_DIR = WEBAPP_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Monta immagini con path legacy /images
IMAGES_DIR = WEBAPP_DIR / "data" / "images"
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# JSON API routes
app.include_router(api_router)

# Mount Svelte frontend build assets
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "_app").exists():
    app.mount("/_app", StaticFiles(directory=str(FRONTEND_DIR / "_app")), name="svelte_app")


# =============================================================================
# HEALTH CHECK
# =============================================================================

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
        "version": "2.0.0",
        "app": "GEKO Magazine"
    }


# =============================================================================
# SVELTE SPA
# =============================================================================

@app.get("/favicon.png")
async def favicon():
    """Serve favicon."""
    favicon_path = FRONTEND_DIR / "favicon.png"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return FileResponse(STATIC_DIR / "favicon.png")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve la Single Page Application Svelte.

    Tutte le route vengono gestite dal router Svelte lato client.
    Questo catch-all deve essere l'ultimo route handler.
    """
    # Serve static files from frontend build if they exist
    if full_path:
        static_file = FRONTEND_DIR / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)

    # Default: serve index.html for SPA routing
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Fallback if frontend not built
    return {"error": "Frontend not built. Run 'npm run build' in frontend/"}
