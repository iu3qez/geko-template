"""JSON API for articles."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...database import get_db
from ...models import Article
from ...services import article_ops

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
    sommario_llm: Optional[str] = None
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


@router.get("")
async def list_articles(
    magazine_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all articles with optional filters."""
    return await article_ops.list_articles(db, magazine_id=magazine_id, search=search)


@router.get("/{article_id}")
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single article by ID."""
    art = await article_ops.get_article(db, article_id)
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@router.post("")
async def create_article(data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    """Create a new article."""
    return await article_ops.create_article(
        db,
        titolo=data.titolo,
        contenuto_md=data.contenuto_md or "",
        sottotitolo=data.sottotitolo or "",
        autore=data.autore or "",
        nome_autore=data.nome_autore or "",
        ordine=data.ordine or 0,
    )


@router.put("/{article_id}")
async def update_article(
    article_id: int,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing article."""
    art = await article_ops.update_article(db, article_id, **data.model_dump(exclude_unset=True))
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


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
    try:
        art = await article_ops.generate_summary(db, article_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art


@router.post("/{article_id}/assign")
async def assign_to_magazines(
    article_id: int,
    data: AssignRequest,
    db: AsyncSession = Depends(get_db)
):
    """Assign article to magazines."""
    art = await article_ops.assign_article(db, article_id, data.magazine_ids)
    if art is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return art
