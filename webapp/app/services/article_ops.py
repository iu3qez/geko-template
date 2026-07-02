"""Logica di servizio condivisa per gli articoli.

Unica fonte di verità usata sia dai router JSON (/api) sia dai tool MCP,
per evitare derive tra i due percorsi.
"""

import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import Article, Config, Magazine, MagazineStatus


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


_MESI_IT = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]
_MESI_LOOKUP = {m.lower(): m for m in _MESI_IT}
_STATI_VALIDI = {s.value for s in MagazineStatus}


def _validate_magazine_fields(*, numero=None, mese=None, anno=None, stato=None) -> dict:
    """Valida i campi passati (non-None) di un numero e li normalizza.

    Ritorna un dict coi soli campi passati; `stato` diventa MagazineStatus.
    Solleva ValueError con messaggio italiano su input non valido.
    """
    cleaned = {}
    if numero is not None:
        numero = str(numero).strip()
        if not numero:
            raise ValueError("Il numero non può essere vuoto")
        cleaned["numero"] = numero
    if mese is not None:
        normalizzato = _MESI_LOOKUP.get(str(mese).strip().lower())
        if normalizzato is None:
            raise ValueError(
                f"Mese non valido: '{mese}'. Valori ammessi: {', '.join(_MESI_IT)}"
            )
        cleaned["mese"] = normalizzato
    if anno is not None:
        anno = str(anno).strip()
        if not re.fullmatch(r"\d{4}", anno):
            raise ValueError(f"Anno non valido: '{anno}' (devono essere 4 cifre)")
        cleaned["anno"] = anno
    if stato is not None:
        stato = str(stato).strip().lower()
        if stato not in _STATI_VALIDI:
            raise ValueError(
                f"Stato non valido: '{stato}'. Valori ammessi: {', '.join(sorted(_STATI_VALIDI))}"
            )
        cleaned["stato"] = MagazineStatus(stato)
    return cleaned


async def create_magazine(db, *, numero: str, mese: str, anno: str, stato: str = "bozza") -> dict:
    """Crea un numero della rivista. Solleva ValueError su validazione/duplicato."""
    cleaned = _validate_magazine_fields(numero=numero, mese=mese, anno=anno, stato=stato)
    existing = await db.execute(select(Magazine).where(Magazine.numero == cleaned["numero"]))
    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"Numero già esistente: {cleaned['numero']}")
    magazine = Magazine(
        numero=cleaned["numero"],
        mese=cleaned["mese"],
        anno=cleaned["anno"],
        stato=cleaned["stato"],
    )
    db.add(magazine)
    await db.commit()
    await db.refresh(magazine)
    return magazine_to_response(magazine)


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
        if key in allowed:
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
