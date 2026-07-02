"""Logica di servizio condivisa per gli articoli.

Unica fonte di verità usata sia dai router JSON (/api) sia dai tool MCP,
per evitare derive tra i due percorsi.
"""

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import Article, Config, Image, Magazine

# ── Media library per-articolo ─────────────────────────────────────────
# Le immagini caricate via MCP/API sono salvate col loro nome esatto sotto
# UPLOADS_DIR/articoli/<article_id>/, così che i riferimenti nudi
# #figura("nome.png") si risolvano in compilazione (root Typst = webapp/).
UPLOADS_DIR = Path("data/uploads")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
_EXTRA_MIME = {".svg": "image/svg+xml", ".webp": "image/webp"}


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


def article_image_base(article_id: int) -> str:
    """Base path (assoluto dalla root Typst) per le immagini di un articolo."""
    return f"/data/uploads/articoli/{article_id}"


def _guess_mime(nome_file: str) -> str:
    """Deduce il MIME dall'estensione (fallback su mimetypes)."""
    import mimetypes

    ext = os.path.splitext(nome_file)[1].lower()
    if ext in _EXTRA_MIME:
        return _EXTRA_MIME[ext]
    return mimetypes.guess_type(nome_file)[0] or "application/octet-stream"


def _sanitize_nome_file(nome_file: str) -> str:
    """Riduce un nome file al solo basename (niente path/traversal)."""
    name = os.path.basename((nome_file or "").replace("\\", "/")).strip()
    if not name or name in {".", ".."}:
        raise ValueError("nome_file non valido")
    return name


async def _get_article_image(db, article_id: int, nome_file: str) -> Optional[Image]:
    result = await db.execute(
        select(Image).where(
            Image.article_id == article_id, Image.filename == nome_file
        )
    )
    return result.scalar_one_or_none()


async def save_article_image(
    db,
    article_id: int,
    nome_file: str,
    content: bytes,
    *,
    mime: str = "",
    sovrascrivi: bool = True,
) -> dict:
    """Salva un'immagine binaria legata a un articolo.

    Il file viene scritto col nome esatto sotto UPLOADS_DIR/articoli/<id>/
    e tracciato nella tabella images. Ritorna {nome_file, url, bytes, mime}.
    """
    nome_file = _sanitize_nome_file(nome_file)

    ext = os.path.splitext(nome_file)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Estensione non supportata: {ext or '(nessuna)'}. "
            f"Ammesse: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
        )
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"File troppo grande ({len(content)} byte). "
            f"Massimo {MAX_IMAGE_BYTES // (1024 * 1024)} MB"
        )

    article = (
        await db.execute(select(Article).where(Article.id == article_id))
    ).scalar_one_or_none()
    if not article:
        raise ValueError(f"Articolo {article_id} non trovato")

    existing = await _get_article_image(db, article_id, nome_file)
    if existing and not sovrascrivi:
        raise ValueError(
            f"Immagine '{nome_file}' già presente per l'articolo {article_id}: "
            f"usa sovrascrivi=true per rimpiazzarla"
        )

    dest_dir = UPLOADS_DIR / "articoli" / str(article_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / nome_file
    dest_path.write_bytes(content)

    if existing:
        existing.path = str(dest_path)
        image = existing
    else:
        image = Image(
            filename=nome_file,
            original_filename=nome_file,
            path=str(dest_path),
            article_id=article_id,
        )
        db.add(image)
    await db.commit()
    await db.refresh(image)

    return {
        "nome_file": image.filename,
        "url": image.url,
        "bytes": len(content),
        "mime": mime or _guess_mime(nome_file),
    }


async def list_article_images(db, article_id: int) -> list[dict]:
    """Elenca le immagini caricate per un articolo."""
    result = await db.execute(
        select(Image)
        .where(Image.article_id == article_id)
        .order_by(Image.filename)
    )
    images = result.scalars().all()
    out = []
    for img in images:
        try:
            size = os.path.getsize(img.path)
        except OSError:
            size = 0
        out.append(
            {
                "nome_file": img.filename,
                "url": img.url,
                "bytes": size,
                "mime": _guess_mime(img.filename),
            }
        )
    return out


async def delete_article_image(db, article_id: int, nome_file: str) -> bool:
    """Elimina un'immagine (file + record) legata a un articolo."""
    nome_file = _sanitize_nome_file(nome_file)
    image = await _get_article_image(db, article_id, nome_file)
    if not image:
        raise ValueError(
            f"Immagine '{nome_file}' non trovata per l'articolo {article_id}"
        )
    if image.path and os.path.exists(image.path):
        os.remove(image.path)
    await db.delete(image)
    await db.commit()
    return True


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
