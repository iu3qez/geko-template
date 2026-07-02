"""Test per la media library per-articolo (upload immagini via servizio/MCP)."""

import base64
from pathlib import Path

import pytest

from app.services import article_ops

# 1x1 PNG trasparente
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


@pytest.fixture
def uploads_tmp(tmp_path, monkeypatch):
    """Redirige lo storage immagini in una cartella temporanea con segmento 'uploads'."""
    base = tmp_path / "uploads"
    monkeypatch.setattr(article_ops, "UPLOADS_DIR", base)
    return base


async def _make_article(db):
    art = await article_ops.create_article(db, titolo="QMX", contenuto_md="x")
    return art["id"]


async def test_save_creates_file_and_record(db, uploads_tmp):
    art_id = await _make_article(db)
    res = await article_ops.save_article_image(db, art_id, "schema.png", PNG_1PX)

    assert res["nome_file"] == "schema.png"
    assert res["bytes"] == len(PNG_1PX)
    assert res["url"] == f"/uploads/articoli/{art_id}/schema.png"
    assert res["mime"] == "image/png"
    assert (uploads_tmp / "articoli" / str(art_id) / "schema.png").read_bytes() == PNG_1PX


async def test_save_deduces_mime_from_extension(db, uploads_tmp):
    art_id = await _make_article(db)
    svg = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
    res = await article_ops.save_article_image(db, art_id, "grafico.svg", svg)
    assert res["mime"] == "image/svg+xml"


async def test_save_accepts_explicit_mime_override(db, uploads_tmp):
    art_id = await _make_article(db)
    res = await article_ops.save_article_image(
        db, art_id, "foto.jpg", PNG_1PX, mime="image/jpeg"
    )
    assert res["mime"] == "image/jpeg"


async def test_save_rejects_unknown_extension(db, uploads_tmp):
    art_id = await _make_article(db)
    with pytest.raises(ValueError):
        await article_ops.save_article_image(db, art_id, "malware.exe", PNG_1PX)


async def test_save_rejects_oversized_file(db, uploads_tmp):
    art_id = await _make_article(db)
    big = b"\x00" * (article_ops.MAX_IMAGE_BYTES + 1)
    with pytest.raises(ValueError):
        await article_ops.save_article_image(db, art_id, "grande.png", big)


async def test_save_strips_path_from_nome_file(db, uploads_tmp):
    """Un nome file con path (o traversal) viene ridotto al solo basename."""
    art_id = await _make_article(db)
    res = await article_ops.save_article_image(db, art_id, "../../etc/x.png", PNG_1PX)
    assert res["nome_file"] == "x.png"
    assert (uploads_tmp / "articoli" / str(art_id) / "x.png").exists()


async def test_save_missing_article_raises(db, uploads_tmp):
    with pytest.raises(ValueError):
        await article_ops.save_article_image(db, 99999, "x.png", PNG_1PX)


async def test_overwrite_true_updates_file(db, uploads_tmp):
    art_id = await _make_article(db)
    await article_ops.save_article_image(db, art_id, "x.png", PNG_1PX)
    new_bytes = PNG_1PX + b"tail"
    res = await article_ops.save_article_image(
        db, art_id, "x.png", new_bytes, sovrascrivi=True
    )
    assert res["bytes"] == len(new_bytes)
    assert (uploads_tmp / "articoli" / str(art_id) / "x.png").read_bytes() == new_bytes
    # nessun duplicato nel DB
    imgs = await article_ops.list_article_images(db, art_id)
    assert len(imgs) == 1


async def test_overwrite_false_raises_when_exists(db, uploads_tmp):
    art_id = await _make_article(db)
    await article_ops.save_article_image(db, art_id, "x.png", PNG_1PX)
    with pytest.raises(ValueError):
        await article_ops.save_article_image(db, art_id, "x.png", PNG_1PX, sovrascrivi=False)


async def test_images_scoped_per_article(db, uploads_tmp):
    a1 = await _make_article(db)
    a2 = await _make_article(db)
    await article_ops.save_article_image(db, a1, "x.png", PNG_1PX)
    await article_ops.save_article_image(db, a2, "x.png", PNG_1PX + b"different")

    l1 = await article_ops.list_article_images(db, a1)
    l2 = await article_ops.list_article_images(db, a2)
    assert [i["nome_file"] for i in l1] == ["x.png"]
    assert [i["nome_file"] for i in l2] == ["x.png"]
    assert l1[0]["url"] == f"/uploads/articoli/{a1}/x.png"
    assert l2[0]["url"] == f"/uploads/articoli/{a2}/x.png"
    assert l1[0]["bytes"] != l2[0]["bytes"]


async def test_list_returns_metadata(db, uploads_tmp):
    art_id = await _make_article(db)
    await article_ops.save_article_image(db, art_id, "a.png", PNG_1PX)
    imgs = await article_ops.list_article_images(db, art_id)
    assert imgs[0].keys() >= {"nome_file", "url", "bytes", "mime"}


async def test_delete_removes_file_and_record(db, uploads_tmp):
    art_id = await _make_article(db)
    await article_ops.save_article_image(db, art_id, "x.png", PNG_1PX)
    ok = await article_ops.delete_article_image(db, art_id, "x.png")
    assert ok is True
    assert not (uploads_tmp / "articoli" / str(art_id) / "x.png").exists()
    assert await article_ops.list_article_images(db, art_id) == []


async def test_delete_missing_raises(db, uploads_tmp):
    art_id = await _make_article(db)
    with pytest.raises(ValueError):
        await article_ops.delete_article_image(db, art_id, "nope.png")
