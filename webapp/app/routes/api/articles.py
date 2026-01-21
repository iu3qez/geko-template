"""JSON API for articles."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...database import get_db
from ...models import Article, Magazine, article_magazines

router = APIRouter(prefix="/articles")


# Pydantic models for request/response
class ArticleBase(BaseModel):
    titolo: str
    sottotitolo: Optional[str] = ""
    autore: Optional[str] = ""
    nome_autore: Optional[str] = ""
    contenuto_md: Optional[str] = ""
    ordine: Optional[int] = 0


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    titolo: Optional[str] = None
    sottotitolo: Optional[str] = None
    autore: Optional[str] = None
    nome_autore: Optional[str] = None
    contenuto_md: Optional[str] = None
    ordine: Optional[int] = None


class MagazineRef(BaseModel):
    id: int
    numero: str
    mese: str
    anno: str
    stato: str

    class Config:
        from_attributes = True


class ImageRef(BaseModel):
    id: int
    filename: str
    original_filename: str
    url: str
    alt_text: str

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    id: int
    titolo: str
    sottotitolo: str
    autore: str
    nome_autore: str
    contenuto_md: str
    contenuto_typ: str
    sommario_llm: str
    ordine: int
    created_at: datetime
    updated_at: datetime
    magazines: list[MagazineRef]
    images: list[ImageRef]

    class Config:
        from_attributes = True


class AssignRequest(BaseModel):
    magazine_ids: list[int]


def article_to_response(article: Article) -> dict:
    """Convert Article model to response dict."""
    return {
        "id": article.id,
        "titolo": article.titolo,
        "sottotitolo": article.sottotitolo or "",
        "autore": article.autore or "",
        "nome_autore": article.nome_autore or "",
        "contenuto_md": article.contenuto_md or "",
        "contenuto_typ": article.contenuto_typ or "",
        "sommario_llm": article.sommario_llm or "",
        "ordine": article.ordine or 0,
        "created_at": article.created_at.isoformat() if article.created_at else None,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
        "magazines": [
            {
                "id": m.id,
                "numero": m.numero,
                "mese": m.mese,
                "anno": m.anno,
                "stato": m.stato.value if hasattr(m.stato, 'value') else m.stato
            }
            for m in article.magazines
        ],
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "original_filename": img.original_filename,
                "url": img.url,
                "alt_text": img.alt_text or ""
            }
            for img in article.images
        ]
    }


@router.get("")
async def list_articles(
    magazine_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all articles with optional filters."""
    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).order_by(Article.updated_at.desc())

    if magazine_id:
        query = query.join(Article.magazines).where(Magazine.id == magazine_id)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            Article.titolo.ilike(search_term) |
            Article.autore.ilike(search_term) |
            Article.contenuto_md.ilike(search_term)
        )

    result = await db.execute(query)
    articles = result.scalars().unique().all()

    return [article_to_response(a) for a in articles]


@router.get("/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single article by ID."""
    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).where(Article.id == article_id)

    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article_to_response(article)


@router.post("")
async def create_article(data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new article."""
    article = Article(
        titolo=data.titolo,
        sottotitolo=data.sottotitolo or "",
        autore=data.autore or "",
        nome_autore=data.nome_autore or "",
        contenuto_md=data.contenuto_md or "",
        ordine=data.ordine or 0
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Reload with relationships
    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).where(Article.id == article.id)
    result = await db.execute(query)
    article = result.scalar_one()

    return article_to_response(article)


@router.put("/{article_id}")
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing article."""
    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).where(Article.id == article_id)

    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(article, key, value)

    await db.commit()
    await db.refresh(article)

    # Reload with relationships
    result = await db.execute(query)
    article = result.scalar_one()

    return article_to_response(article)


@router.delete("/{article_id}")
async def delete_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an article."""
    query = select(Article).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.delete(article)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{article_id}/summary")
async def generate_summary(article_id: int, db: AsyncSession = Depends(get_db)):
    """Generate AI summary for an article."""
    from ...services.llm import generate_article_summary

    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).where(Article.id == article_id)

    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if not article.contenuto_md:
        raise HTTPException(status_code=400, detail="Article has no content")

    try:
        result = await generate_article_summary(article.contenuto_md, article.titolo)
        article.sommario_llm = result.get("sommario", "")
        await db.commit()
        await db.refresh(article)

        # Reload with relationships
        result = await db.execute(query)
        article = result.scalar_one()

        return article_to_response(article)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/assign")
async def assign_to_magazines(
    article_id: int,
    data: AssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """Assign article to magazines."""
    query = select(Article).options(
        selectinload(Article.magazines),
        selectinload(Article.images)
    ).where(Article.id == article_id)

    result = await db.execute(query)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Clear existing assignments
    await db.execute(
        delete(article_magazines).where(article_magazines.c.article_id == article_id)
    )

    # Add new assignments
    for mag_id in data.magazine_ids:
        mag_result = await db.execute(select(Magazine).where(Magazine.id == mag_id))
        magazine = mag_result.scalar_one_or_none()
        if magazine:
            article.magazines.append(magazine)

    await db.commit()

    # Reload with relationships
    result = await db.execute(query)
    article = result.scalar_one()

    return article_to_response(article)
