"""Smoke test di regressione per la build completa del magazine (Task 6).

Verifica che MagazineBuilder compili un numero minimo con un articolo generato
da md_render.generate_article_typst (che usa #cmarker.render), con il package
cmarker vendorizzato risolto offline via package_path.
"""

from app.services.builder import MagazineBuilder
from app.services.md_render import generate_article_typst


def test_build_magazine_minimo(tmp_path, monkeypatch):
    b = MagazineBuilder()
    art = generate_article_typst(
        titolo="Uno", sottotitolo=None, autore="IK2XYZ", nome=None,
        contenuto_md="Testo con 5$ e `codice` inline e _enfasi_.\n",
    )
    pdf_path = b.build_magazine(
        numero="99", mese="Luglio", anno="2026", articles_typst=[art],
    )
    assert pdf_path.exists() and pdf_path.stat().st_size > 1000
