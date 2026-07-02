"""Logica di servizio condivisa per gli articoli.

Unica fonte di verità usata sia dai router JSON (/api) sia dai tool MCP,
per evitare derive tra i due percorsi.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import Article, Config, Magazine


def article_to_response(article: Article) -> dict:
    """Serializza un Article in dict JSON-friendly."""
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
                "stato": m.stato.value if hasattr(m.stato, "value") else m.stato,
            }
            for m in article.magazines
        ],
        "images": [
            {
                "id": img.id,
                "filename": img.filename,
                "original_filename": img.original_filename,
                "url": img.url,
                "alt_text": img.alt_text or "",
            }
            for img in article.images
        ],
    }


def magazine_to_response(magazine: Magazine) -> dict:
    """Serializza un Magazine (campi essenziali) in dict."""
    return {
        "id": magazine.id,
        "numero": magazine.numero,
        "mese": magazine.mese,
        "anno": magazine.anno,
        "stato": magazine.stato.value if hasattr(magazine.stato, "value") else magazine.stato,
    }


_ARTICLE_LOADED = (selectinload(Article.magazines), selectinload(Article.images))


async def _reload(db, article_id: int) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    return article_to_response(article) if article else None


async def list_magazines(db) -> list[dict]:
    result = await db.execute(select(Magazine).order_by(Magazine.numero.desc()))
    return [magazine_to_response(m) for m in result.scalars().all()]


async def create_article(
    db,
    *,
    titolo: str,
    contenuto_md: str,
    sottotitolo: str = "",
    autore: str = "",
    nome_autore: str = "",
    ordine: int = 0,
) -> dict:
    article = Article(
        titolo=titolo,
        sottotitolo=sottotitolo or "",
        autore=autore or "",
        nome_autore=nome_autore or "",
        contenuto_md=contenuto_md or "",
        ordine=ordine or 0,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return await _reload(db, article.id)


async def list_articles(
    db, *, magazine_id: Optional[int] = None, search: Optional[str] = None
) -> list[dict]:
    query = (
        select(Article)
        .options(*_ARTICLE_LOADED)
        .order_by(Article.updated_at.desc())
    )
    if magazine_id is not None:
        query = query.join(Article.magazines).where(Magazine.id == magazine_id)
    if search:
        term = f"%{search}%"
        query = query.where(
            Article.titolo.ilike(term)
            | Article.autore.ilike(term)
            | Article.contenuto_md.ilike(term)
        )
    result = await db.execute(query)
    return [article_to_response(a) for a in result.scalars().unique().all()]


async def get_article(db, article_id: int) -> Optional[dict]:
    return await _reload(db, article_id)


async def update_article(db, article_id: int, **fields) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    allowed = {
        "titolo", "sottotitolo", "autore", "nome_autore",
        "contenuto_md", "sommario_llm", "ordine",
    }
    for key, value in fields.items():
        if key in allowed and value is not None:
            setattr(article, key, value)
    await db.commit()
    return await _reload(db, article_id)


async def assign_article(db, article_id: int, magazine_ids: list[int]) -> Optional[dict]:
    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    article.magazines.clear()
    unique_ids = list(dict.fromkeys(magazine_ids))
    if unique_ids:
        mags = (await db.execute(select(Magazine).where(Magazine.id.in_(unique_ids)))).scalars().all()
        by_id = {m.id: m for m in mags}
        for mid in unique_ids:
            if mid in by_id:
                article.magazines.append(by_id[mid])
    await db.commit()
    return await _reload(db, article_id)


async def generate_summary(db, article_id: int) -> Optional[dict]:
    from .llm import generate_article_summary

    query = select(Article).options(*_ARTICLE_LOADED).where(Article.id == article_id)
    result = await db.execute(query)
    article = result.scalar_one_or_none()
    if not article:
        return None
    if not article.contenuto_md:
        raise ValueError("L'articolo non ha contenuto da riassumere")
    model = await Config.get(db, "claude_model")
    summary = await generate_article_summary(article.contenuto_md, article.titolo, model=model)
    article.sommario_llm = summary.get("sommario", "")
    await db.commit()
    return await _reload(db, article_id)
