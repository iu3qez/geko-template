"""
Article management routes.

Questo modulo gestisce tutte le operazioni CRUD per gli articoli della rivista.
Gli articoli vengono salvati in formato Markdown e convertiti automaticamente
in Typst per la generazione del PDF.

Routes disponibili:
    GET  /articles/          - Lista tutti gli articoli
    GET  /articles/new       - Form per nuovo articolo
    POST /articles/          - Crea nuovo articolo
    GET  /articles/{id}      - Dettaglio articolo
    GET  /articles/{id}/edit - Form modifica articolo
    PUT  /articles/{id}      - Aggiorna articolo
    DELETE /articles/{id}    - Elimina articolo
    POST /articles/{id}/summary - Genera sommario con Claude AI

Formato Markdown supportato:
    - Headers: # ## ###
    - Bold: **testo**
    - Italic: *testo*
    - Links: [testo](url)
    - Images: ![alt](path)
    - Box evidenza: !!! nota "Titolo" ... !!!
"""

from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from typing import List

from app.database import get_db
from app.models import Article, Magazine
from app.services.converter import MarkdownToTypstConverter
from app.services.llm import generate_article_summary

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_class=HTMLResponse)
async def list_articles(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List all articles."""
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.magazines))
        .order_by(Article.created_at.desc())
    )
    articles = result.scalars().all()

    # Get templates from request.app.state
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/list.html",
        {"request": request, "articles": articles}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_article_form(request: Request):
    """Show form for creating new article."""
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/form.html",
        {"request": request, "article": None}
    )


@router.post("/", response_class=HTMLResponse)
async def create_article(
    request: Request,
    titolo: str = Form(...),
    sottotitolo: str = Form(""),
    autore: str = Form(""),
    nome_autore: str = Form(""),
    contenuto_md: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """Create a new article."""
    # Convert markdown to typst
    converter = MarkdownToTypstConverter()
    _, typst_content = converter.convert(contenuto_md)

    # Generate full article typst
    contenuto_typ = converter.generate_article_typst(
        titolo=titolo,
        sottotitolo=sottotitolo if sottotitolo else None,
        autore=autore if autore else None,
        nome=nome_autore if nome_autore else None,
        contenuto=typst_content
    )

    article = Article(
        titolo=titolo,
        sottotitolo=sottotitolo,
        autore=autore,
        nome_autore=nome_autore,
        contenuto_md=contenuto_md,
        contenuto_typ=contenuto_typ,
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

    # Return updated list (for HTMX)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/list_item.html",
        {"request": request, "article": article},
        headers={"HX-Trigger": "articleCreated"}
    )


@router.get("/{article_id}", response_class=HTMLResponse)
async def get_article(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get single article."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/detail.html",
        {"request": request, "article": article}
    )


@router.get("/{article_id}/edit", response_class=HTMLResponse)
async def edit_article_form(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Show edit form for article."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/form.html",
        {"request": request, "article": article}
    )


@router.put("/{article_id}", response_class=HTMLResponse)
async def update_article(
    request: Request,
    article_id: int,
    titolo: str = Form(...),
    sottotitolo: str = Form(""),
    autore: str = Form(""),
    nome_autore: str = Form(""),
    contenuto_md: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    """Update an article."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    # Convert markdown to typst
    converter = MarkdownToTypstConverter()
    _, typst_content = converter.convert(contenuto_md)

    # Generate full article typst
    contenuto_typ = converter.generate_article_typst(
        titolo=titolo,
        sottotitolo=sottotitolo if sottotitolo else None,
        autore=autore if autore else None,
        nome=nome_autore if nome_autore else None,
        contenuto=typst_content
    )

    article.titolo = titolo
    article.sottotitolo = sottotitolo
    article.autore = autore
    article.nome_autore = nome_autore
    article.contenuto_md = contenuto_md
    article.contenuto_typ = contenuto_typ

    await db.commit()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/detail.html",
        {"request": request, "article": article}
    )


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete an article."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    await db.delete(article)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{article_id}/summary", response_class=HTMLResponse)
async def generate_summary(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI summary for article."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    # Generate summary using Claude
    summary_data = await generate_article_summary(
        article.contenuto_md,
        article.titolo
    )

    article.sommario_llm = summary_data.get("sommario", "")
    await db.commit()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/summary_badge.html",
        {"request": request, "article": article, "summary": summary_data}
    )


@router.get("/{article_id}/assign", response_class=HTMLResponse)
async def assign_article_form(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Show form to assign article to magazines."""
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.magazines))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    # Get all magazines
    magazines_result = await db.execute(
        select(Magazine).order_by(Magazine.numero.desc())
    )
    magazines = magazines_result.scalars().all()

    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/assign_form.html",
        {"request": request, "article": article, "magazines": magazines}
    )


@router.post("/{article_id}/assign", response_class=HTMLResponse)
async def assign_article(
    request: Request,
    article_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Assign article to selected magazines."""
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.magazines))
        .where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    # Get form data (multiple checkbox values)
    form_data = await request.form()
    magazine_ids = form_data.getlist("magazine_ids")

    # Clear existing assignments and add new ones
    article.magazines.clear()

    if magazine_ids:
        magazines_result = await db.execute(
            select(Magazine).where(Magazine.id.in_([int(mid) for mid in magazine_ids]))
        )
        magazines = magazines_result.scalars().all()
        article.magazines.extend(magazines)

    await db.commit()

    # Re-query with eager loading to ensure magazines is loaded
    result = await db.execute(
        select(Article)
        .options(selectinload(Article.magazines))
        .where(Article.id == article.id)
    )
    article = result.scalar_one()

    # Return updated article card
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "standard/articles/list_item.html",
        {"request": request, "article": article}
    )
