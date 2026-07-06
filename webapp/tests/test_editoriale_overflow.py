"""Regressione layout: un editoriale lungo non deve essere troncato in copertina,
ma proseguire su una pagina dedicata (teaser + "continua a pag. N")."""

import uuid
from pathlib import Path

import typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"
GEN_DIR = WEBAPP_DIR / "typst" / "generated"


def _pagine_copertina(editoriale: str) -> int:
    """Compila una copertina (seguita da una pagina segnaposto) col dato
    editoriale e ritorna il numero di pagine renderizzate."""
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    doc = GEN_DIR / f"_edit_{uuid.uuid4().hex}.typ"
    doc.write_text(
        '#import "/template.typ": *\n'
        '#copertina(\n'
        '  numero: "1", mese: "Luglio", anno: "2026",\n'
        '  immagine-principale: "/assets/badge-mqc.png",\n'
        '  evidenze: ((titolo: "T", descrizione: "d"),),\n'
        f'  editoriale-testo: [{editoriale}],\n'
        '  editoriale-autore: "IK2ABC",\n'
        ')\n'
        # pagina segnaposto: "consuma" il pagebreak finale della copertina
        '#pagina-logo(numero: "1", mese: "Luglio", anno: "2026")\n',
        encoding="utf-8",
    )
    try:
        pages = typst.compile(
            str(doc), root=str(REPO_DIR), package_path=str(PKG_PATH),
            format="png", ppi=72,
        )
        return len(pages)
    finally:
        doc.unlink(missing_ok=True)


def test_editoriale_corto_non_aggiunge_pagine():
    # Un editoriale corto entra in copertina: stesso numero di pagine di uno
    # minimale (nessuna pagina editoriale dedicata emessa).
    minimale = _pagine_copertina("Breve.")
    corto = _pagine_copertina(
        "Benvenuti nel nuovo numero. Buona lettura a tutti i soci del club."
    )
    assert corto == minimale


def test_editoriale_lungo_prosegue_su_pagina_dedicata():
    # Un editoriale lungo NON viene troncato: prosegue su una pagina dedicata,
    # quindi produce strettamente più pagine di uno corto.
    lungo = " ".join(
        ["Questo editoriale è volutamente molto lungo per superare lo spazio "
         "disponibile nella colonna della copertina."] * 25
    )
    assert _pagine_copertina(lungo) > _pagine_copertina("Breve.")
