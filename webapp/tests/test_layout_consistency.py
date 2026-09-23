"""Regressione grafica: editoriale e articoli devono usare lo stesso font.

Prima di `stile-geko` il font era impostato solo dentro `geko-magazine`
(applicato DOPO la copertina): l'editoriale usciva nel font di default di
Typst (Libertinus Serif) e gli articoli in DejaVu Serif, perché "Latin Modern
Roman" non è installato da nessuna parte. Qui compiliamo copertina +
articolo in un unico PDF NON compresso (typst.compile diretto, così i nomi
dei font restano leggibili nei dizionari /BaseFont) e verifichiamo che
compaia una sola famiglia serif, quella del template.
"""

import re
import uuid
from pathlib import Path

import typst

from app.services.md_render import generate_article_typst, render_article_body

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"
GEN_DIR = WEBAPP_DIR / "typst" / "generated"

_BASEFONT_RE = re.compile(rb"/BaseFont\s*/([A-Za-z0-9+\-]+)")


def _font_families(pdf: bytes) -> set[str]:
    """Famiglie font embedded nel PDF (senza prefisso subset e senza stile)."""
    fams = set()
    for m in _BASEFONT_RE.findall(pdf):
        name = m.decode()
        if "+" in name:
            name = name.split("+", 1)[1]
        fams.add(name.split("-", 1)[0])
    return fams


def test_editoriale_e_articoli_stesso_font():
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    editoriale = render_article_body(
        "# Bentornati\n\nTesto dell'editoriale con *enfasi*.\n\n"
        + "Riga lunga per far proseguire l'editoriale su pagina dedicata. " * 60
    )
    articolo = generate_article_typst(
        titolo="Articolo", sottotitolo="Occhiello", autore="IK2ABC", nome="Mario",
        contenuto_md="# Sezione\n\nCorpo.\n\n## Sottosezione\n\nAltro.\n\n### Paragrafo\n\nFine.\n",
    )
    doc = GEN_DIR / f"_layout_{uuid.uuid4().hex}.typ"
    doc.write_text(
        '#import "@preview/cmarker:0.1.10"\n'
        '#import "../src/template.typ": *\n'
        '#copertina(\n'
        '  numero: "1", mese: "Luglio", anno: "2026",\n'
        '  immagine-principale: "/typst/assets/badge-mqc.png",\n'
        '  evidenze: ((titolo: "T", descrizione: "d"),),\n'
        f'  editoriale-testo: [{editoriale}],\n'
        '  editoriale-autore: "IK2ABC",\n'
        ')\n'
        '#sommario(numero: "1", mese: "Luglio", anno: "2026")\n'
        '#show: geko-magazine.with(numero: "1", mese: "Luglio", anno: "2026")\n'
        + articolo,
        encoding="utf-8",
    )
    try:
        pdf = typst.compile(str(doc), root=str(WEBAPP_DIR), package_path=str(PKG_PATH))
    finally:
        doc.unlink(missing_ok=True)

    fams = _font_families(pdf)
    assert fams, "nessun /BaseFont trovato: il test non sta leggendo i font"
    # Un'unica famiglia di testo (Libertinus = font incorporato in Typst,
    # quindi identico su dev/CI/prod); niente fallback DejaVu.
    assert fams == {"LibertinusSerif"}, fams
