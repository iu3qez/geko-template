from app.services.md_render import segment_markdown, Segment


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
