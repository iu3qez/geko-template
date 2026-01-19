"""
File upload routes.

Questo modulo gestisce il caricamento di file:
- Immagini (JPG, PNG, GIF) per articoli e copertine
- File Markdown per importazione articoli

Le immagini vengono:
1. Validate (tipo, dimensione)
2. Ridimensionate se troppo grandi (max 2000px lato lungo)
3. Salvate con nome univoco in data/images/
4. Registrate nel database

Routes disponibili:
    POST /upload/image              - Carica singola immagine
    POST /upload/images             - Carica multiple immagini
    POST /upload/markdown           - Importa articolo da file MD
    DELETE /upload/image/{image_id} - Elimina immagine

Limiti:
    - Max dimensione file: 10MB
    - Formati immagine: JPG, PNG, GIF, WebP
    - Formato markdown: UTF-8
"""

import uuid
import base64
import re
import unicodedata
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from PIL import Image as PILImage  # Alias per evitare conflitto con app.models.Image

from datetime import datetime, timedelta

from app.database import get_db
from app.models import Image as ImageModel, Article, Magazine, MagazineStatus
from app.services.converter import MarkdownToTypstConverter
from app.services.llm import generate_image_caption

router = APIRouter(prefix="/upload", tags=["upload"])

# Directory per le immagini
IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Configurazione upload
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_DIMENSION = 2000  # pixel
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def slugify(text: str) -> str:
    """
    Converte un testo in slug per nome file.

    Es: "RTX QRP autocostruito per i 40m" -> "rtx-qrp-autocostruito-per-i-40m"
    """
    # Normalizza unicode (è -> e)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Minuscolo
    text = text.lower()
    # Sostituisci spazi e caratteri non alfanumerici con trattini
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Rimuovi trattini multipli e agli estremi
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:50] if text else "immagine"  # Max 50 caratteri


def validate_image_file(file: UploadFile) -> None:
    """
    Valida un file immagine caricato.

    Args:
        file: Il file caricato da validare

    Raises:
        HTTPException: Se il file non è valido

    Controlli effettuati:
        - Content-type deve essere un'immagine supportata
        - Estensione deve corrispondere al tipo
    """
    # Controlla content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo file non supportato: {file.content_type}. "
                   f"Usa: JPG, PNG, GIF o WebP."
        )

    # Controlla estensione
    if file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Estensione file non supportata: {ext}"
            )


def resize_image_if_needed(image_path: Path) -> None:
    """
    Ridimensiona l'immagine se supera le dimensioni massime.

    Mantiene l'aspect ratio. Modifica il file in-place.

    Args:
        image_path: Path al file immagine da ridimensionare
    """
    with PILImage.open(image_path) as img:
        # Calcola se serve ridimensionare
        width, height = img.size
        if width <= MAX_IMAGE_DIMENSION and height <= MAX_IMAGE_DIMENSION:
            return  # Nessun ridimensionamento necessario

        # Calcola nuove dimensioni mantenendo aspect ratio
        if width > height:
            new_width = MAX_IMAGE_DIMENSION
            new_height = int(height * (MAX_IMAGE_DIMENSION / width))
        else:
            new_height = MAX_IMAGE_DIMENSION
            new_width = int(width * (MAX_IMAGE_DIMENSION / height))

        # Ridimensiona e salva
        img_resized = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

        # Converti RGBA in RGB se necessario (per JPEG)
        if img_resized.mode == 'RGBA' and image_path.suffix.lower() in ['.jpg', '.jpeg']:
            img_resized = img_resized.convert('RGB')

        img_resized.save(image_path, quality=85, optimize=True)


@router.post("/image", response_class=HTMLResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    article_id: Optional[int] = Form(None),
    auto_caption: bool = Form(True),
    db: AsyncSession = Depends(get_db)
):
    """
    Carica una singola immagine con didascalia automatica.

    L'immagine viene validata, eventualmente ridimensionata,
    e la didascalia generata da Claude viene usata per il nome file.

    Args:
        file: Il file immagine da caricare
        article_id: ID articolo a cui associare l'immagine (opzionale)
        auto_caption: Se True, genera didascalia con Claude Vision

    Returns:
        HTML partial con l'immagine caricata (per HTMX)
    """
    validate_image_file(file)

    original_filename = file.filename or "image"
    ext = Path(original_filename).suffix.lower()

    # Leggi contenuto file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File troppo grande. Massimo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Genera didascalia automatica con Claude Vision
    caption = ""
    if auto_caption:
        try:
            image_base64 = base64.b64encode(content).decode('utf-8')
            media_type = file.content_type or "image/jpeg"
            caption_result = await generate_image_caption(image_base64, media_type)
            caption = caption_result.get("caption", "")
            caption_slug = caption_result.get("caption_slug", "")

            # Usa la didascalia come nome file se disponibile
            if caption_slug:
                # Aggiungi suffisso univoco per evitare collisioni
                unique_suffix = uuid.uuid4().hex[:8]
                unique_filename = f"{caption_slug}-{unique_suffix}{ext}"
            else:
                unique_filename = f"{uuid.uuid4()}{ext}"
        except Exception as e:
            print(f"Errore generazione didascalia: {e}")
            unique_filename = f"{uuid.uuid4()}{ext}"
    else:
        unique_filename = f"{uuid.uuid4()}{ext}"

    file_path = IMAGES_DIR / unique_filename

    # Salva file
    file_path.write_bytes(content)

    # Ridimensiona se necessario
    try:
        resize_image_if_needed(file_path)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Errore elaborazione immagine: {str(e)}"
        )

    # Salva nel database con didascalia
    image = ImageModel(
        filename=unique_filename,
        original_filename=original_filename,
        path=str(file_path.relative_to(IMAGES_DIR.parent.parent)),
        article_id=article_id,
        alt_text=caption,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/upload/image_item.html",
        {"request": request, "image": image}
    )


@router.post("/image/editor")
async def upload_image_editor(
    file: UploadFile = File(...),
    article_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Carica immagine dall'editor Markdown con didascalia automatica.

    Endpoint JSON per integrazione con EasyMDE.
    Genera automaticamente una didascalia per l'immagine.

    Returns:
        JSON: {"url": "/images/filename.jpg", "caption": "Didascalia generata"}
    """
    validate_image_file(file)

    original_filename = file.filename or "image"
    ext = Path(original_filename).suffix.lower()

    # Leggi contenuto file
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File troppo grande. Massimo: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

    # Genera didascalia automatica con Claude Vision
    caption = ""
    try:
        image_base64 = base64.b64encode(content).decode('utf-8')
        media_type = file.content_type or "image/jpeg"
        caption_result = await generate_image_caption(image_base64, media_type)
        caption = caption_result.get("caption", "")
        caption_slug = caption_result.get("caption_slug", "")

        if caption_slug:
            unique_suffix = uuid.uuid4().hex[:8]
            unique_filename = f"{caption_slug}-{unique_suffix}{ext}"
        else:
            unique_filename = f"{uuid.uuid4()}{ext}"
    except Exception as e:
        print(f"Errore generazione didascalia: {e}")
        unique_filename = f"{uuid.uuid4()}{ext}"

    file_path = IMAGES_DIR / unique_filename

    # Salva file
    file_path.write_bytes(content)

    # Ridimensiona se necessario
    try:
        resize_image_if_needed(file_path)
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Errore elaborazione immagine: {str(e)}"
        )

    # Salva nel database con didascalia
    image = ImageModel(
        filename=unique_filename,
        original_filename=original_filename,
        path=str(file_path.relative_to(IMAGES_DIR.parent.parent)),
        article_id=article_id,
        alt_text=caption,
    )
    db.add(image)
    await db.commit()

    # Ritorna URL e didascalia per l'editor
    return JSONResponse({
        "url": f"/images/{unique_filename}",
        "filename": unique_filename,
        "original": original_filename,
        "caption": caption
    })


@router.post("/images", response_class=HTMLResponse)
async def upload_multiple_images(
    request: Request,
    files: list[UploadFile] = File(...),
    article_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Carica multiple immagini in una sola richiesta.

    Utile per l'upload batch. Ogni immagine viene processata
    individualmente - se una fallisce, le altre vengono comunque caricate.

    Args:
        files: Lista di file immagine da caricare
        article_id: ID articolo a cui associare le immagini (opzionale)

    Returns:
        HTML partial con tutte le immagini caricate
    """
    uploaded_images = []
    errors = []

    for file in files:
        try:
            validate_image_file(file)

            # Genera nome univoco
            original_filename = file.filename or "image"
            ext = Path(original_filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{ext}"
            file_path = IMAGES_DIR / unique_filename

            # Salva file
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                errors.append(f"{original_filename}: troppo grande")
                continue

            file_path.write_bytes(content)
            resize_image_if_needed(file_path)

            # Salva nel database
            image = ImageModel(
                filename=unique_filename,
                original_filename=original_filename,
                path=str(file_path.relative_to(IMAGES_DIR.parent.parent)),
                article_id=article_id,
            )
            db.add(image)
            uploaded_images.append(image)

        except HTTPException as e:
            errors.append(f"{file.filename}: {e.detail}")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    await db.commit()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/upload/images_list.html",
        {
            "request": request,
            "images": uploaded_images,
            "errors": errors,
        }
    )


@router.post("/markdown", response_class=HTMLResponse)
async def upload_markdown(
    request: Request,
    file: UploadFile = File(...),
    magazine_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Importa un articolo da file Markdown.

    Il file MD può contenere un frontmatter YAML con metadati:

    ```markdown
    ---
    titolo: "Il mio articolo"
    autore: "IU3XYZ"
    nome: "Mario Rossi"
    sottotitolo: "Un sottotitolo opzionale"
    ---

    Contenuto dell'articolo...
    ```

    Se il frontmatter non è presente, il titolo viene estratto
    dal primo heading del documento.

    Args:
        file: File markdown da importare
        magazine_id: ID numero a cui aggiungere l'articolo (opzionale)

    Returns:
        HTML partial con l'articolo creato
    """
    # Verifica estensione
    if file.filename and not file.filename.endswith('.md'):
        raise HTTPException(
            status_code=400,
            detail="Il file deve avere estensione .md"
        )

    # Leggi contenuto
    content = await file.read()
    try:
        markdown_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Il file deve essere in formato UTF-8"
        )

    # Converti markdown
    converter = MarkdownToTypstConverter()
    metadata, typst_content = converter.convert(markdown_text)

    # Estrai metadati dal frontmatter o dal contenuto
    titolo = metadata.get('titolo', metadata.get('title', ''))
    if not titolo:
        # Prova a estrarre dal primo heading
        lines = markdown_text.split('\n')
        for line in lines:
            if line.startswith('# '):
                titolo = line[2:].strip()
                break
        if not titolo:
            titolo = Path(file.filename or "articolo").stem

    # Genera typst completo dell'articolo
    contenuto_typ = converter.generate_article_typst(
        titolo=titolo,
        sottotitolo=metadata.get('sottotitolo', metadata.get('subtitle')),
        autore=metadata.get('autore', metadata.get('author')),
        nome=metadata.get('nome', metadata.get('name')),
        contenuto=typst_content
    )

    # Crea articolo
    article = Article(
        titolo=titolo,
        sottotitolo=metadata.get('sottotitolo', ''),
        autore=metadata.get('autore', ''),
        nome_autore=metadata.get('nome', ''),
        contenuto_md=markdown_text,
        contenuto_typ=contenuto_typ,
        magazine_id=magazine_id,
    )

    db.add(article)
    await db.commit()

    # Re-query with eager loading to avoid lazy-load in template
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.magazines))
        .where(Article.id == article.id)
    )
    article = result.scalar_one()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/list_item.html",
        {"request": request, "article": article},
        headers={"HX-Trigger": "articleImported"}
    )


@router.delete("/image/{image_id}")
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un'immagine caricata.

    Rimuove sia il file dal disco che il record dal database.

    Args:
        image_id: ID dell'immagine da eliminare

    Returns:
        JSON con status dell'operazione
    """
    result = await db.execute(
        select(ImageModel).where(ImageModel.id == image_id)
    )
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(status_code=404, detail="Immagine non trovata")

    # Elimina file dal disco
    file_path = IMAGES_DIR / image.filename
    file_path.unlink(missing_ok=True)

    # Elimina dal database
    await db.delete(image)
    await db.commit()

    return {"status": "deleted"}


@router.get("/library", response_class=HTMLResponse)
async def image_library(
    request: Request,
    filter: str = "all",  # all, today, published, magazine_id
    magazine_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Libreria immagini con filtri.

    Filtri disponibili:
    - all: tutte le immagini
    - today: caricate oggi
    - published: in articoli pubblicati
    - magazine: in articoli di un numero specifico (richiede magazine_id)

    Returns:
        HTML partial con griglia immagini
    """
    # Eager load article and article.magazines for is_published property
    query = (
        select(ImageModel)
        .options(
            selectinload(ImageModel.article)
            .selectinload(Article.magazines)
        )
        .order_by(ImageModel.uploaded_at.desc())
    )

    if filter == "today":
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(ImageModel.uploaded_at >= today_start)

    result = await db.execute(query)
    images = result.scalars().all()

    # Filtri post-query (per relazioni complesse)
    if filter == "published":
        images = [img for img in images if img.is_published]
    elif filter == "magazine" and magazine_id:
        images = [
            img for img in images
            if img.article and any(mag.id == magazine_id for mag in img.article.magazines)
        ]

    # Get all magazines for filter dropdown
    magazines_result = await db.execute(
        select(Magazine).order_by(Magazine.numero.desc())
    )
    magazines = magazines_result.scalars().all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/upload/library.html",
        {
            "request": request,
            "images": images,
            "magazines": magazines,
            "current_filter": filter,
            "current_magazine_id": magazine_id
        }
    )


@router.get("/library/grid", response_class=HTMLResponse)
async def image_library_grid(
    request: Request,
    filter: str = "all",
    magazine_id: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Solo la griglia immagini (per aggiornamento HTMX).
    """
    # Eager load for is_published property
    query = (
        select(ImageModel)
        .options(
            selectinload(ImageModel.article)
            .selectinload(Article.magazines)
        )
        .order_by(ImageModel.uploaded_at.desc())
    )

    if filter == "today":
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.where(ImageModel.uploaded_at >= today_start)

    result = await db.execute(query)
    images = result.scalars().all()

    if filter == "published":
        images = [img for img in images if img.is_published]
    elif filter == "magazine" and magazine_id:
        images = [
            img for img in images
            if img.article and any(mag.id == magazine_id for mag in img.article.magazines)
        ]

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/upload/library_grid.html",
        {"request": request, "images": images}
    )


@router.post("/regenerate-captions")
async def regenerate_all_captions(
    db: AsyncSession = Depends(get_db)
):
    """
    Rigenera le didascalie per tutte le immagini esistenti.

    Utile per aggiornare immagini caricate prima dell'introduzione
    della funzionalità di auto-captioning.

    Returns:
        JSON con statistiche: totale, successi, errori
    """
    # Recupera tutte le immagini
    result = await db.execute(select(ImageModel))
    images = result.scalars().all()

    stats = {"total": len(images), "success": 0, "errors": 0, "skipped": 0}
    updated_images = []

    for image in images:
        try:
            # Leggi file immagine
            file_path = IMAGES_DIR / image.filename
            if not file_path.exists():
                stats["skipped"] += 1
                continue

            content = file_path.read_bytes()
            image_base64 = base64.b64encode(content).decode('utf-8')

            # Determina media type dall'estensione
            ext = file_path.suffix.lower()
            media_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            media_type = media_types.get(ext, "image/jpeg")

            # Genera nuova didascalia
            caption_result = await generate_image_caption(image_base64, media_type)
            caption = caption_result.get("caption", "")
            caption_slug = caption_result.get("caption_slug", "")

            if caption:
                # Aggiorna alt_text nel database
                image.alt_text = caption

                # Rinomina file se abbiamo uno slug
                if caption_slug:
                    unique_suffix = uuid.uuid4().hex[:8]
                    new_filename = f"{caption_slug}-{unique_suffix}{ext}"
                    new_path = IMAGES_DIR / new_filename

                    # Rinomina file su disco
                    file_path.rename(new_path)

                    # Aggiorna database
                    image.filename = new_filename
                    image.path = str(new_path.relative_to(IMAGES_DIR.parent.parent))

                updated_images.append({
                    "id": image.id,
                    "old_filename": file_path.name,
                    "new_filename": image.filename,
                    "caption": caption
                })
                stats["success"] += 1
            else:
                stats["skipped"] += 1

        except Exception as e:
            print(f"Errore rigenerazione didascalia per {image.filename}: {e}")
            stats["errors"] += 1

    # Salva tutte le modifiche
    await db.commit()

    return JSONResponse({
        "status": "completed",
        "stats": stats,
        "updated": updated_images
    })
