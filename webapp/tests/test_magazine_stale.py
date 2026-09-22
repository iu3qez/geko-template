"""Test staleness PDF dei numeri (pdf_built_at / pdf_stale)."""

import base64

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models import Article, Image, Magazine, MagazineStatus, utcnow

# 1x1 PNG trasparente (stesso fixture usato in test_article_images.py)
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


async def test_new_magazine_has_no_pdf_built_at(db):
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    db.add(mag)
    await db.commit()
    await db.refresh(mag)
    assert mag.pdf_built_at is None


@pytest.fixture
def client(db):
    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


async def _make_mag_with_article(db):
    mag = Magazine(numero="99", mese="Gennaio", anno="2026", stato=MagazineStatus.BOZZA)
    art = Article(titolo="A", contenuto_md="ciao")
    db.add(mag)
    db.add(art)
    await db.commit()
    # `mag.articles` non è ancora stato caricato in memoria (nessun accesso
    # prima del commit): un append diretto qui scatenerebbe una lazy-load
    # sincrona fuori dal contesto greenlet di AsyncSession (MissingGreenlet).
    # Il refresh esplicito lo evita, come già fanno gli endpoint reali con
    # selectinload(Magazine.articles).
    await db.refresh(mag, attribute_names=["articles"])
    mag.articles.append(art)
    await db.commit()
    await db.refresh(mag)
    await db.refresh(art)
    return mag.id, art.id


async def test_pdf_stale_false_when_never_built(client, db):
    mag_id, _ = await _make_mag_with_article(db)
    async with client as c:
        resp = await c.get(f"/api/magazines/{mag_id}")
    body = resp.json()
    assert body["pdf_built_at"] is None
    assert body["pdf_stale"] is False


async def test_pdf_stale_true_after_article_change(client, db):
    mag_id, art_id = await _make_mag_with_article(db)
    # Simula una build riuscita nel passato. Impostiamo anche updated_at allo
    # stesso istante: Magazine.updated_at ha onupdate=utcnow, che altrimenti
    # scatterebbe comunque su questo UPDATE con un timestamp calcolato pochi
    # microsecondi dopo pdf_built_at, rendendo il numero "stale" da subito
    # (come fa build_pdf nel codice di produzione, per lo stesso motivo).
    mag = await db.get(Magazine, mag_id)
    built_at = utcnow()
    mag.pdf_built_at = built_at
    mag.updated_at = built_at
    await db.commit()
    async with client as c:
        before = (await c.get(f"/api/magazines/{mag_id}")).json()
        assert before["pdf_stale"] is False
        # Modifica l'articolo -> updated_at avanza
        art = await db.get(Article, art_id)
        art.titolo = "Modificato"
        await db.commit()
        after = (await c.get(f"/api/magazines/{mag_id}")).json()
    assert after["pdf_stale"] is True


async def test_pdf_stale_true_after_reorder(client, db):
    mag_id, art_id = await _make_mag_with_article(db)
    # Vedi commento in test_pdf_stale_true_after_article_change: fissiamo
    # updated_at allo stesso istante di pdf_built_at per simulare un numero
    # appena costruito e non ancora stale.
    mag = await db.get(Magazine, mag_id)
    built_at = utcnow()
    mag.pdf_built_at = built_at
    mag.updated_at = built_at
    await db.commit()
    async with client as c:
        resp = await c.post(
            f"/api/magazines/{mag_id}/articles/reorder",
            json={"article_ids": [art_id]},
        )
        assert resp.status_code == 200
        after = (await c.get(f"/api/magazines/{mag_id}")).json()
    assert after["pdf_stale"] is True


# ── Finding 1: le mutazioni sul flusso web-immagini devono marcare stale ──


async def test_delete_web_image_bumps_owning_article_updated_at(client, db):
    """DELETE /api/images/{id} deve avanzare updated_at dell'articolo che la
    referenzia (le immagini web sono embeddate nel markdown e finiscono nel
    PDF: cancellarle cambia il contenuto renderizzato)."""
    art = Article(titolo="Con immagine", contenuto_md="![x](/uploads/abc_x.png)")
    db.add(art)
    await db.commit()
    await db.refresh(art)

    img = Image(
        filename="abc_x.png",
        original_filename="x.png",
        path="data/uploads/abc_x.png",
        article_id=art.id,
    )
    db.add(img)
    await db.commit()
    await db.refresh(img)

    before = art.updated_at

    async with client as c:
        resp = await c.delete(f"/api/images/{img.id}")
    assert resp.status_code == 200

    await db.refresh(art)
    assert art.updated_at != before


async def test_upload_web_image_bumps_owning_article_updated_at(client, db):
    """POST /api/images con article_id deve avanzare updated_at dell'articolo."""
    art = Article(titolo="Senza immagine", contenuto_md="ciao")
    db.add(art)
    await db.commit()
    await db.refresh(art)
    before = art.updated_at

    async with client as c:
        resp = await c.post(
            "/api/images",
            data={"article_id": str(art.id)},
            files={"file": ("foto.png", PNG_1PX, "image/png")},
        )
    assert resp.status_code == 200

    await db.refresh(art)
    assert art.updated_at != before


# ── Finding 2: regressione sul "pin" di updated_at nella build reale ──


async def test_build_pdf_endpoint_not_stale_immediately_after_build(client, db, monkeypatch):
    """POST /api/magazines/{id}/build (con la compilazione Typst/GS mockata)
    non deve lasciare il numero stale nell'istante stesso in cui la build
    termina (vedi commento su build_completed_at in build_pdf)."""
    mag_id, art_id = await _make_mag_with_article(db)

    def fake_build_magazine_pdf(*args, **kwargs):
        return "data/output/fake.pdf"

    import app.services.builder as builder_module

    monkeypatch.setattr(builder_module, "build_magazine_pdf", fake_build_magazine_pdf)

    async with client as c:
        resp = await c.post(f"/api/magazines/{mag_id}/build")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        after = (await c.get(f"/api/magazines/{mag_id}")).json()

    assert after["pdf_built_at"] is not None
    assert after["pdf_stale"] is False
