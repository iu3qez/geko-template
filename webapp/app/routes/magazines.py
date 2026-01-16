"""
Magazine management routes.

Questo modulo gestisce i numeri della rivista GEKO Radio Magazine.
Ogni numero (Magazine) contiene più articoli e può essere in stato
"bozza" (in lavorazione) o "pubblicato" (PDF generato).

Routes disponibili:
    GET  /magazines/           - Lista tutti i numeri
    GET  /magazines/new        - Form per nuovo numero
    POST /magazines/           - Crea nuovo numero
    GET  /magazines/{id}       - Dettaglio numero con articoli
    PUT  /magazines/{id}       - Aggiorna metadati numero
    DELETE /magazines/{id}     - Elimina numero (solo bozze)
    POST /magazines/{id}/build - Genera PDF finale
    GET  /magazines/{id}/pdf   - Scarica PDF generato

Workflow tipico:
    1. Crea nuovo numero (POST /magazines/)
    2. Aggiungi articoli (POST /articles/ con magazine_id)
    3. Genera sommari AI per ogni articolo
    4. Seleziona copertina e scrivi editoriale
    5. Genera PDF (POST /magazines/{id}/build)
    6. Scarica e distribuisci (GET /magazines/{id}/pdf)
"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Magazine, Article, MagazineStatus
from app.services.builder import MagazineBuilder

router = APIRouter(prefix="/magazines", tags=["magazines"])

# Directory per i PDF generati
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "output"


@router.get("/", response_class=HTMLResponse)
async def list_magazines(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista tutti i numeri della rivista.

    Ordina per numero decrescente (più recenti prima).
    Mostra stato (bozza/pubblicato) e conteggio articoli.
    """
    result = await db.execute(
        select(Magazine)
        .options(selectinload(Magazine.articles))
        .order_by(Magazine.anno.desc(), Magazine.numero.desc())
    )
    magazines = result.scalars().all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/magazines/list.html",
        {"request": request, "magazines": magazines}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_magazine_form(request: Request):
    """
    Mostra form per creare un nuovo numero.

    Suggerisce automaticamente il prossimo numero basandosi
    sull'ultimo numero esistente.
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/magazines/form.html",
        {"request": request, "magazine": None}
    )


@router.post("/", response_class=HTMLResponse)
async def create_magazine(
    request: Request,
    numero: str = Form(...),
    mese: str = Form(...),
    anno: str = Form(...),
    editoriale: str = Form(""),
    editoriale_autore: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuovo numero della rivista.

    Il numero viene creato in stato "bozza" e può essere
    modificato fino alla pubblicazione.

    Args:
        numero: Numero progressivo della rivista (es. "68")
        mese: Mese di pubblicazione (es. "Gennaio")
        anno: Anno di pubblicazione (es. "2025")
        editoriale: Testo dell'editoriale (opzionale)
        editoriale_autore: Autore dell'editoriale (opzionale)
    """
    magazine = Magazine(
        numero=numero,
        mese=mese,
        anno=anno,
        editoriale=editoriale,
        editoriale_autore=editoriale_autore,
        stato=MagazineStatus.BOZZA,
    )

    db.add(magazine)
    await db.commit()
    await db.refresh(magazine)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/magazines/detail.html",
        {"request": request, "magazine": magazine},
        headers={"HX-Trigger": "magazineCreated"}
    )


@router.get("/{magazine_id}", response_class=HTMLResponse)
async def get_magazine(
    request: Request,
    magazine_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mostra dettaglio di un numero con tutti i suoi articoli.

    Include:
    - Metadati del numero (mese, anno, stato)
    - Lista articoli ordinata per posizione
    - Pulsanti per generare PDF (se bozza)
    - Link download PDF (se pubblicato)
    """
    result = await db.execute(
        select(Magazine)
        .options(selectinload(Magazine.articles))
        .where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/magazines/detail.html",
        {"request": request, "magazine": magazine}
    )


@router.put("/{magazine_id}", response_class=HTMLResponse)
async def update_magazine(
    request: Request,
    magazine_id: int,
    mese: str = Form(...),
    anno: str = Form(...),
    editoriale: str = Form(""),
    editoriale_autore: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggiorna i metadati di un numero.

    Il numero (progressivo) non può essere modificato dopo la creazione.
    I metadati possono essere modificati anche dopo la pubblicazione
    (sarà necessario rigenerare il PDF).
    """
    result = await db.execute(
        select(Magazine).where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    magazine.mese = mese
    magazine.anno = anno
    magazine.editoriale = editoriale
    magazine.editoriale_autore = editoriale_autore

    await db.commit()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/magazines/detail.html",
        {"request": request, "magazine": magazine}
    )


@router.delete("/{magazine_id}")
async def delete_magazine(
    magazine_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un numero della rivista.

    ATTENZIONE: Solo i numeri in stato "bozza" possono essere eliminati.
    I numeri pubblicati sono archiviati permanentemente.

    Elimina anche tutti gli articoli associati.
    """
    result = await db.execute(
        select(Magazine)
        .options(selectinload(Magazine.articles))
        .where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    if magazine.stato == MagazineStatus.PUBBLICATO:
        raise HTTPException(
            status_code=400,
            detail="Non puoi eliminare un numero già pubblicato"
        )

    # Elimina articoli associati
    for article in magazine.articles:
        await db.delete(article)

    await db.delete(magazine)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{magazine_id}/build", response_class=HTMLResponse)
async def build_magazine_pdf(
    request: Request,
    magazine_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Genera (o rigenera) il PDF finale della rivista.

    Questo processo:
    1. Raccoglie tutti gli articoli in ordine
    2. Genera la copertina con evidenze (sommari AI)
    3. Assembla il documento Typst completo
    4. Compila in PDF usando il template GEKO
    5. Salva il PDF e aggiorna lo stato a "pubblicato"

    Può essere eseguito più volte per rigenerare il PDF dopo modifiche.
    """
    result = await db.execute(
        select(Magazine)
        .options(selectinload(Magazine.articles))
        .where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    if not magazine.articles:
        raise HTTPException(
            status_code=400,
            detail="Aggiungi almeno un articolo prima di generare il PDF"
        )

    # Prepara contenuto articoli in Typst
    articles_typst = [
        article.contenuto_typ
        for article in sorted(magazine.articles, key=lambda a: a.ordine)
    ]

    # Prepara evidenze per copertina (usa sommari AI)
    evidenze = [
        {
            "titolo": article.titolo,
            "descrizione": article.sommario_llm or article.sottotitolo or ""
        }
        for article in magazine.articles[:4]  # Max 4 evidenze in copertina
        if article.sommario_llm or article.sottotitolo
    ]

    # Genera PDF
    try:
        builder = MagazineBuilder()
        pdf_path = builder.build_magazine(
            numero=magazine.numero,
            mese=magazine.mese,
            anno=magazine.anno,
            articles_typst=articles_typst,
            editoriale=magazine.editoriale,
            editoriale_autore=magazine.editoriale_autore,
            evidenze=evidenze if evidenze else None,
        )

        # Aggiorna stato
        magazine.stato = MagazineStatus.PUBBLICATO
        await db.commit()

        templates = request.app.state.templates
        return templates.TemplateResponse(
            "standard/magazines/build_success.html",
            {
                "request": request,
                "magazine": magazine,
                "pdf_path": str(pdf_path),
            }
        )

    except Exception as e:
        import traceback
        print(f"ERRORE BUILD PDF: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante la generazione del PDF: {str(e)}"
        )


@router.get("/{magazine_id}/pdf")
async def download_magazine_pdf(
    magazine_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Scarica il PDF generato di un numero.

    Il PDF deve essere stato generato in precedenza con POST /build.
    Restituisce il file PDF con header appropriati per il download.
    """
    result = await db.execute(
        select(Magazine).where(Magazine.id == magazine_id)
    )
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    pdf_path = OUTPUT_DIR / f"geko{magazine.numero}.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="PDF non ancora generato. Usa prima il pulsante 'Genera PDF'."
        )

    return FileResponse(
        path=str(pdf_path),
        filename=f"GEKO-{magazine.numero}-{magazine.mese}-{magazine.anno}.pdf",
        media_type="application/pdf"
    )


@router.post("/{magazine_id}/articles/{article_id}/add")
async def add_article_to_magazine(
    magazine_id: int,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Aggiunge un articolo esistente a questo numero.

    L'articolo viene posizionato in fondo alla lista.
    Usa PUT /magazines/{id}/articles/reorder per riordinare.
    """
    # Verifica magazine
    mag_result = await db.execute(
        select(Magazine).where(Magazine.id == magazine_id)
    )
    magazine = mag_result.scalar_one_or_none()
    if not magazine:
        raise HTTPException(status_code=404, detail="Numero non trovato")

    # Verifica articolo
    art_result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = art_result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    # Trova prossimo ordine
    max_order_result = await db.execute(
        select(Article.ordine)
        .where(Article.magazine_id == magazine_id)
        .order_by(Article.ordine.desc())
        .limit(1)
    )
    max_order = max_order_result.scalar() or 0

    article.magazine_id = magazine_id
    article.ordine = max_order + 1

    await db.commit()

    return {"status": "added", "ordine": article.ordine}
