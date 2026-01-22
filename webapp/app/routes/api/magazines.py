"""JSON API for magazines."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os

from ...database import get_db
from ...models import Magazine, MagazineStatus, Article, Image, article_magazines

router = APIRouter(prefix="/magazines")


class MagazineBase(BaseModel):
    numero: str
    mese: str
    anno: str
    stato: Optional[str] = "bozza"
    editoriale: Optional[str] = ""
    editoriale_autore: Optional[str] = ""
    copertina_id: Optional[int] = None


class MagazineCreate(MagazineBase):
    pass


class MagazineUpdate(BaseModel):
    numero: Optional[str] = None
    mese: Optional[str] = None
    anno: Optional[str] = None
    stato: Optional[str] = None
    editoriale: Optional[str] = None
    editoriale_autore: Optional[str] = None
    copertina_id: Optional[int] = None


class ArticleRef(BaseModel):
    id: int
    titolo: str
    sottotitolo: str
    autore: str
    ordine: int

    class Config:
        from_attributes = True


class ImageRef(BaseModel):
    id: int
    filename: str
    url: str
    alt_text: str

    class Config:
        from_attributes = True


class MagazineResponse(BaseModel):
    id: int
    numero: str
    mese: str
    anno: str
    stato: str
    editoriale: str
    editoriale_autore: str
    copertina_id: Optional[int]
    copertina: Optional[ImageRef]
    created_at: datetime
    updated_at: datetime
    articles: list[ArticleRef]
    article_count: int

    class Config:
        from_attributes = True


class ReorderRequest(BaseModel):
    article_ids: list[int]


class AddArticleRequest(BaseModel):
    ordine: Optional[int] = None


def magazine_to_response(magazine: Magazine) -> dict:
    """Convert Magazine model to response dict."""
    return {
        "id": magazine.id,
        "numero": magazine.numero,
        "mese": magazine.mese,
        "anno": magazine.anno,
        "stato": magazine.stato.value if hasattr(magazine.stato, 'value') else magazine.stato,
        "editoriale": magazine.editoriale or "",
        "editoriale_autore": magazine.editoriale_autore or "",
        "copertina_id": magazine.copertina_id,
        "copertina": {
            "id": magazine.copertina.id,
            "filename": magazine.copertina.filename,
            "url": magazine.copertina.url,
            "alt_text": magazine.copertina.alt_text or ""
        } if magazine.copertina else None,
        "created_at": magazine.created_at.isoformat() if magazine.created_at else None,
        "updated_at": magazine.updated_at.isoformat() if magazine.updated_at else None,
        "articles": [
            {
                "id": a.id,
                "titolo": a.titolo,
                "sottotitolo": a.sottotitolo or "",
                "autore": a.autore or "",
                "ordine": a.ordine or 0
            }
            for a in sorted(magazine.articles, key=lambda x: x.ordine or 0)
        ],
        "article_count": len(magazine.articles)
    }


@router.get("")
async def list_magazines(db: AsyncSession = Depends(get_db)):
    """List all magazines."""
    query = select(Magazine).options(
        selectinload(Magazine.articles),
        selectinload(Magazine.copertina)
    ).order_by(Magazine.anno.desc(), Magazine.numero.desc())

    result = await db.execute(query)
    magazines = result.scalars().unique().all()

    return [magazine_to_response(m) for m in magazines]


@router.get("/{magazine_id}")
async def get_magazine(magazine_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single magazine by ID."""
    query = select(Magazine).options(
        selectinload(Magazine.articles),
        selectinload(Magazine.copertina)
    ).where(Magazine.id == magazine_id)

    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    return magazine_to_response(magazine)


@router.post("")
async def create_magazine(data: MagazineCreate, db: AsyncSession = Depends(get_db)):
    """Create a new magazine."""
    stato = MagazineStatus(data.stato) if data.stato else MagazineStatus.BOZZA

    magazine = Magazine(
        numero=data.numero,
        mese=data.mese,
        anno=data.anno,
        stato=stato,
        editoriale=data.editoriale or "",
        editoriale_autore=data.editoriale_autore or "",
        copertina_id=data.copertina_id
    )
    db.add(magazine)
    await db.commit()
    await db.refresh(magazine)

    # Reload with relationships
    query = select(Magazine).options(
        selectinload(Magazine.articles),
        selectinload(Magazine.copertina)
    ).where(Magazine.id == magazine.id)
    result = await db.execute(query)
    magazine = result.scalar_one()

    return magazine_to_response(magazine)


@router.put("/{magazine_id}")
async def update_magazine(
    magazine_id: int,
    data: MagazineUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing magazine."""
    query = select(Magazine).options(
        selectinload(Magazine.articles),
        selectinload(Magazine.copertina)
    ).where(Magazine.id == magazine_id)

    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "stato" and value:
            value = MagazineStatus(value)
        setattr(magazine, key, value)

    await db.commit()
    await db.refresh(magazine)

    # Reload with relationships
    result = await db.execute(query)
    magazine = result.scalar_one()

    return magazine_to_response(magazine)


@router.delete("/{magazine_id}")
async def delete_magazine(magazine_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a magazine."""
    query = select(Magazine).where(Magazine.id == magazine_id)
    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    await db.delete(magazine)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{magazine_id}/build")
async def build_pdf(magazine_id: int, db: AsyncSession = Depends(get_db)):
    """Build PDF for a magazine."""
    from ...services.builder import build_magazine_pdf
    from ...services.converter import convert_markdown_to_typst

    query = select(Magazine).options(
        selectinload(Magazine.articles).selectinload(Article.images),
        selectinload(Magazine.copertina)
    ).where(Magazine.id == magazine_id)

    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    if not magazine.articles:
        raise HTTPException(status_code=400, detail="Magazine has no articles")

    try:
        # Prepare articles typst content
        # If contenuto_typ exists, use it; otherwise convert markdown to typst
        articles_typst = []
        for article in magazine.articles:
            if article.contenuto_typ:
                articles_typst.append(article.contenuto_typ)
            elif article.contenuto_md:
                # Convert markdown to typst on-the-fly
                # convert_markdown_to_typst returns (metadata, typst_content)
                _, converted = convert_markdown_to_typst(article.contenuto_md)
                articles_typst.append(converted)
            else:
                articles_typst.append("")

        # Build evidenze (highlights) from article summaries
        evidenze = [
            {
                "titolo": article.titolo,
                "descrizione": article.sommario_llm or ""
            }
            for article in magazine.articles
            if article.sommario_llm  # Only include articles with AI summaries
        ]

        # Get cover image path if exists
        copertina_path = None
        if magazine.copertina:
            copertina_path = magazine.copertina.path

        # Build PDF (not async)
        pdf_path = build_magazine_pdf(
            numero=magazine.numero,
            mese=magazine.mese,
            anno=magazine.anno,
            articles_typst=articles_typst,
            editoriale=magazine.editoriale,
            editoriale_autore=magazine.editoriale_autore,
            copertina_path=copertina_path,
            evidenze=evidenze,
        )

        # Update magazine status
        magazine.stato = MagazineStatus.PUBBLICATO
        await db.commit()

        return {
            "status": "success",
            "pdf_url": f"/api/magazines/{magazine_id}/pdf"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/{magazine_id}/pdf")
async def download_pdf(magazine_id: int, db: AsyncSession = Depends(get_db)):
    """Download PDF for a magazine."""
    query = select(Magazine).where(Magazine.id == magazine_id)
    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    # Check if PDF exists
    pdf_filename = f"geko{magazine.numero}.pdf"
    pdf_path = os.path.join("data", "output", pdf_filename)

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found. Build the magazine first.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename
    )


@router.post("/{magazine_id}/articles/reorder")
async def reorder_articles(
    magazine_id: int,
    data: ReorderRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reorder articles in a magazine."""
    query = select(Magazine).where(Magazine.id == magazine_id)
    result = await db.execute(query)
    magazine = result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    # Update order for each article
    for idx, article_id in enumerate(data.article_ids):
        await db.execute(
            article_magazines.update()
            .where(article_magazines.c.article_id == article_id)
            .where(article_magazines.c.magazine_id == magazine_id)
            .values(ordine=idx)
        )

    await db.commit()

    return {"status": "reordered"}


@router.post("/{magazine_id}/articles/{article_id}")
async def add_article(
    magazine_id: int,
    article_id: int,
    data: AddArticleRequest = AddArticleRequest(),
    db: AsyncSession = Depends(get_db)
):
    """Add an article to a magazine."""
    # Get magazine
    mag_query = select(Magazine).options(selectinload(Magazine.articles)).where(Magazine.id == magazine_id)
    mag_result = await db.execute(mag_query)
    magazine = mag_result.scalar_one_or_none()

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")

    # Get article
    art_query = select(Article).where(Article.id == article_id)
    art_result = await db.execute(art_query)
    article = art_result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check if already assigned
    if article in magazine.articles:
        return {"status": "already_assigned", "ordine": article.ordine}

    # Determine order
    if data.ordine is not None:
        ordine = data.ordine
    else:
        # Get max order + 1
        max_ordine = max((a.ordine or 0 for a in magazine.articles), default=0)
        ordine = max_ordine + 1

    # Add to magazine
    magazine.articles.append(article)

    # Update order in junction table
    await db.execute(
        article_magazines.update()
        .where(article_magazines.c.article_id == article_id)
        .where(article_magazines.c.magazine_id == magazine_id)
        .values(ordine=ordine)
    )

    await db.commit()

    return {"status": "added", "ordine": ordine}


@router.delete("/{magazine_id}/articles/{article_id}")
async def remove_article(
    magazine_id: int,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Remove an article from a magazine."""
    # Delete from junction table
    result = await db.execute(
        delete(article_magazines)
        .where(article_magazines.c.article_id == article_id)
        .where(article_magazines.c.magazine_id == magazine_id)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Article not in magazine")

    await db.commit()

    return {"status": "removed"}
