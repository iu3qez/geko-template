import uuid
from pathlib import Path

import typst

from app.services.md_render import (
    segment_markdown, Segment,
    _typ_str, render_article_body, render_segments,
    generate_article_typst,
)

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"
# typst richiede che il file di ingresso sia contenuto in `root`: usiamo
# typst/generated/ (già gitignorato, vedi webapp/.gitignore) invece del
# tmp_path di pytest, che vive fuori dal repo e farebbe fallire il compile.
GENERATED_DIR = WEBAPP_DIR / "typst" / "generated"


def test_prosa_semplice_un_segmento():
    segs = segment_markdown("Riga uno\nRiga due")
    assert len(segs) == 1
    assert segs[0].kind == "prose"
    assert segs[0].text == "Riga uno\nRiga due"
    assert (segs[0].start_line, segs[0].end_line) == (0, 1)


def test_alert_github_diventa_box():
    md = (
        "Intro\n"
        "\n"
        "> [!WARNING] Attenzione batteria\n"
        "> Porta una **scorta**.\n"
        "> Il freddo scarica.\n"
        "\n"
        "Coda"
    )
    segs = segment_markdown(md)
    kinds = [s.kind for s in segs]
    assert kinds == ["prose", "box", "prose"]
    box = segs[1]
    assert box.tipo == "warning"
    assert box.titolo == "Attenzione batteria"
    assert box.text == "Porta una **scorta**.\nIl freddo scarica."
    assert (box.start_line, box.end_line) == (2, 4)


def test_run_immagini_consecutive_un_segmento():
    md = "![a](a.png)\n![b](b.png)\ntesto"
    segs = segment_markdown(md)
    assert [s.kind for s in segs] == ["images", "prose"]
    assert segs[0].images == [("a", "a.png", None), ("b", "b.png", None)]
    assert (segs[0].start_line, segs[0].end_line) == (0, 1)


def test_immagine_singola_con_width():
    segs = segment_markdown("![Schema](s.png){width=60%}")
    assert segs[0].kind == "images"
    assert segs[0].images == [("Schema", "s.png", "width=60%")]


def test_blockquote_normale_resta_prosa():
    segs = segment_markdown("> solo una citazione\n> seconda riga")
    assert len(segs) == 1 and segs[0].kind == "prose"


def test_typ_str_escaping():
    assert _typ_str('a"b\\c') == 'a\\"b\\\\c'
    assert _typ_str('r1\nr2') == 'r1\\nr2'
    assert _typ_str('t\tx\r') == 't\\tx'


def test_render_prosa_usa_cmarker_con_dollaro_letterale():
    out = render_article_body("Costo 5$ e _enfasi_")
    assert '#cmarker.render(' in out
    assert 'h1-level: 2' in out
    assert 'scope: geko-md-scope' in out
    assert 'Costo 5$ e _enfasi_' in out  # embeddato, non trasformato


def test_render_box_annidato():
    md = "> [!TIP] Consiglio\n> testo **forte**"
    out = render_article_body(md)
    assert '#box-evidenza(titolo: "Consiglio", tipo: "tip")[' in out
    assert 'label-prefix:' in out  # cmarker annidato con prefix


def test_render_immagine_singola_con_width():
    out = render_article_body("![Schema](s.png){width=60%}")
    assert '#figura("s.png"' in out
    assert 'larghezza: 60%' in out


def test_render_griglia_due_immagini():
    out = render_article_body("![a](a.png)\n![b](b.png)")
    assert '#grid(' in out and 'columns: (1fr, 1fr)' in out


def test_render_image_base_nome_nudo():
    out = render_article_body("![x](foto.png)", image_base="/data/uploads/articoli/7")
    assert '"/data/uploads/articoli/7/foto.png"' in out


def test_render_segments_ritorna_range():
    segs = render_segments("Intro\n\n> [!NOTE] N\n> corpo")
    assert [s.kind for s, _ in segs] == ["prose", "box"]
    assert all(isinstance(typ, str) and typ for _, typ in segs)


def test_render_immagine_path_con_virgolette_escapato():
    out = render_article_body('![img](weird"quote.png)')
    assert '\\"' in out            # la virgoletta nel path è escapata
    assert 'weird"quote.png"' not in out  # non termina la stringa in anticipo


def test_generate_article_typst_struttura():
    out = generate_article_typst(
        titolo="Il mio articolo", sottotitolo="sub",
        autore="IK2ABC", nome="Mario",
        contenuto_md="Testo con 5$ e _enfasi_.",
    )
    assert out.startswith("= Il mio articolo")
    assert '#sottotitolo-sezione[sub]' in out
    assert '#autore("IK2ABC", nome: "Mario")' in out
    assert '#separatore()' in out


def test_articolo_completo_compila():
    # NB rispetto al brief: con `root=REPO_DIR` un `#import` con path assoluto
    # filesystem del template fallisce (typst tratta "/x" come root-relative,
    # quindi il path assoluto double-risolve). Scriviamo il .typ generato sotto
    # typst/generated/ (gitignorato, vedi test_template_smoke.py) e importiamo
    # il template come "/template.typ" (root-relative). Per lo stesso motivo
    # l'immagine di esempio usa un file locale root-relative
    # ("/assets/logo-mqc.png") invece di un URL remoto: typst#image() legge da
    # disco, non fa fetch di rete.
    body = generate_article_typst(
        titolo="Test", sottotitolo=None, autore=None, nome=None,
        contenuto_md=(
            "Costo 5$, file `pippo_pluto`, canale #3.\n\n"
            "> [!WARNING] Occhio\n> Testo **forte**.\n\n"
            "| A | B |\n| - | - |\n| 1 | 2 |\n\n"
            "![Foto](/assets/logo-mqc.png)\n"
        ),
    )
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    doc = GENERATED_DIR / f"test_articolo_{uuid.uuid4().hex}.typ"
    try:
        doc.write_text(
            # NB: senza ": *" — il corpo generato usa `#cmarker.render(...)`
            # (namespace del modulo), non `#render(...)` come nell'import
            # wildcard usato in altri smoke test (es. test_cmarker_vendored.py).
            '#import "@preview/cmarker:0.1.10"\n'
            '#import "/template.typ": *\n'
            '#show: geko-magazine.with(numero: "1", mese: "Luglio", anno: "2026")\n'
            + body,
            encoding="utf-8",
        )
        pdf = typst.compile(str(doc), root=str(REPO_DIR), package_path=str(PKG_PATH))
        assert len(pdf) > 1000
    finally:
        doc.unlink(missing_ok=True)
