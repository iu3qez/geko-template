from app.services.md_render import (
    segment_markdown, Segment,
    _typ_str, render_article_body, render_segments,
)


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
