from pathlib import Path
import typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"


def test_cmarker_renders_offline(tmp_path):
    doc = tmp_path / "doc.typ"
    doc.write_text(
        '#import "@preview/cmarker:0.1.10": *\n'
        '#set page(width: 12cm, height: auto)\n'
        # casi che oggi rompono il vecchio converter:
        '#render("Costo 5$ per il file `pippo_pluto`, con _enfasi_, #radio e **grassetto**.")\n',
        encoding="utf-8",
    )
    pdf = typst.compile(str(doc), package_path=str(PKG_PATH))
    assert isinstance(pdf, (bytes, bytearray)) and len(pdf) > 1000
