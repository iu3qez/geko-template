import pytest

from app.services import article_ops


async def test_create_article_returns_serialized_dict(db):
    art = await article_ops.create_article(
        db, titolo="Portatile in vetta", contenuto_md="Testo **grassetto**.",
        autore="IK2ABC", nome_autore="Mario",
    )
    assert art["id"] > 0
    assert art["titolo"] == "Portatile in vetta"
    assert art["autore"] == "IK2ABC"
    assert art["magazines"] == []
    assert art["images"] == []


async def test_get_article_missing_returns_none(db):
    assert await article_ops.get_article(db, 999) is None


async def test_assign_article_to_magazine(db, sample_magazine):
    art = await article_ops.create_article(db, titolo="X", contenuto_md="y")
    updated = await article_ops.assign_article(db, art["id"], [sample_magazine["id"]])
    assert [m["id"] for m in updated["magazines"]] == [sample_magazine["id"]]


async def test_update_article_changes_fields(db):
    art = await article_ops.create_article(db, titolo="Vecchio", contenuto_md="y")
    updated = await article_ops.update_article(db, art["id"], titolo="Nuovo")
    assert updated["titolo"] == "Nuovo"


async def test_list_articles_search(db):
    await article_ops.create_article(db, titolo="Antenna EFHW", contenuto_md="y")
    await article_ops.create_article(db, titolo="Batterie LiFePO4", contenuto_md="y")
    found = await article_ops.list_articles(db, search="antenna")
    assert len(found) == 1
    assert found[0]["titolo"] == "Antenna EFHW"


async def test_list_magazines(db, sample_magazine):
    mags = await article_ops.list_magazines(db)
    assert any(m["id"] == sample_magazine["id"] for m in mags)
