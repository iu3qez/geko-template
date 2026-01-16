"""
Configuration panel routes.

Gestisce il pannello di configurazione globale dell'applicazione.
Permette di modificare parametri che valgono per tutti i numeri della rivista.

Routes disponibili:
    GET  /config/          - Mostra pannello configurazione
    POST /config/          - Salva configurazioni
    GET  /config/{key}     - Ottiene singolo valore (JSON)
"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Config

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/", response_class=HTMLResponse)
async def config_panel(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Mostra il pannello di configurazione."""
    configs = await Config.get_all(db)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/config/panel.html",
        {"request": request, "configs": configs}
    )


@router.post("/", response_class=HTMLResponse)
async def save_config(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Salva le configurazioni modificate."""
    form_data = await request.form()

    # Salva ogni configurazione
    for key in Config.DEFAULTS.keys():
        if key in form_data:
            value = form_data.get(key, "")
            await Config.set(db, key, value)

    # Ritorna feedback
    configs = await Config.get_all(db)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/config/panel.html",
        {
            "request": request,
            "configs": configs,
            "message": "Configurazione salvata con successo!"
        }
    )


@router.get("/{key}")
async def get_config_value(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """Ottiene un singolo valore di configurazione (API JSON)."""
    value = await Config.get(db, key)
    return JSONResponse({"key": key, "value": value})
