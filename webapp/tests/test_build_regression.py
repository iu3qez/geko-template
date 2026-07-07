"""Smoke test di regressione per la build completa del magazine (Task 6).

Verifica che MagazineBuilder compili un numero minimo con un articolo generato
da md_render.generate_article_typst (che usa #cmarker.render), con il package
cmarker vendorizzato risolto offline via package_path.

Task 9 aggiunge una regressione parametrizzata sui markdown REALI esportati
dal DB (`tests/fixtures/articoli_reali/art_<id>.md`): la loro prosa contiene
`$`, backtick, `_`, `#parola` che rompevano il vecchio converter basato su
regex. Le immagini per-articolo referenziate nei markdown reali non sono
garantite presenti su disco/CI, quindi vengono riscritte deterministicamente
verso un asset noto (`/typst/assets/logo_rivista.jpg`, risolto offline via il
symlink creato da `ensure_docker_like_typst_layout` in conftest.py) prima
della compilazione: l'obiettivo è verificare il rendering di prosa/box/
tabelle/figure, non la disponibilità dei file immagine originali.
"""

import re
from pathlib import Path

import pytest

from app.services.builder import MagazineBuilder
from app.services.md_render import generate_article_typst, render_article_body


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


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "articoli_reali"

# Path di un asset noto, sempre presente e risolvibile offline (root=WEBAPP_DIR
# nella compilazione, vedi builder.py). Sostituisce SOLO il path dentro
# `![alt](path)`, lasciando intatti alt text e `{attrs}` successivi, così la
# grid/figura viene comunque esercitata sul contenuto reale.
_KNOWN_GOOD_IMAGE = "/typst/assets/logo_rivista.jpg"
_MD_IMAGE_PATH_RE = re.compile(r'(!\[[^\]]*\]\()([^)]+)(\))')


def _make_images_deterministic(md: str) -> str:
    """Rimappa ogni path immagine del markdown su un asset noto e offline."""
    return _MD_IMAGE_PATH_RE.sub(rf'\g<1>{_KNOWN_GOOD_IMAGE}\g<3>', md)


@pytest.mark.parametrize(
    "md_file", sorted(FIXTURES_DIR.glob("art_*.md")), ids=lambda p: p.stem
)
def test_articolo_reale_compila(md_file):
    """Ogni articolo reale esportato dal DB deve compilare senza errori.

    Le immagini vengono rimappate su un asset noto e offline (vedi
    `_make_images_deterministic`): un fallimento qui riguarda quindi SEMPRE
    prosa/delimitatori/tabelle/box, mai un file immagine mancante.
    """
    md = md_file.read_text(encoding="utf-8")
    md = _make_images_deterministic(md)
    body = generate_article_typst(
        titolo="Regressione", sottotitolo=None, autore=None, nome=None,
        contenuto_md=md,
    )
    msg = MagazineBuilder().try_compile_snippet(body)
    assert msg is None, f"{md_file.stem} non compila: {msg}"


ESEMPIO = Path(__file__).resolve().parent.parent / "app" / "services" / "esempio_convenzioni.md"


def test_esempio_convenzioni_compila():
    """L'articolo-esempio canonico (guida CONVENZIONI) copre ogni costrutto
    (prosa, box GitHub-alert, tabella, figura singola con width, griglia di
    immagini) e deve compilare per davvero, con asset locali su disco."""
    md = ESEMPIO.read_text(encoding="utf-8")
    out = render_article_body(md)
    assert '#box-evidenza' in out and '#grid(' in out and '#figura(' in out
    assert MagazineBuilder().try_compile_snippet(out) is None


def test_build_magazine_comprime_se_gs_presente(tmp_path):
    import shutil
    from app.services.builder import MagazineBuilder
    from app.services.md_render import generate_article_typst

    art = generate_article_typst(
        titolo="Foto", sottotitolo=None, autore="IK2X", nome=None,
        contenuto_md="![Vetta](/typst/assets/corno-grande-1.jpg)\n"
                     "![Cresta](/typst/assets/corno-grande-2.jpg)\n",
    )
    pdf = MagazineBuilder().build_magazine(
        numero="93", mese="Luglio", anno="2026", articles_typst=[art],
    )
    # La build produce sempre un PDF valido, con o senza Ghostscript.
    assert pdf.exists() and pdf.read_bytes()[:5] == b"%PDF-"
