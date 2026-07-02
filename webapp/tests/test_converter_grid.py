"""Test per l'auto-griglia figure a 2 colonne e la gestione dei fence nel converter."""

from app.services.converter import MarkdownToTypstConverter


def convert(md: str) -> str:
    converter = MarkdownToTypstConverter()
    _, typst = converter.convert(md)
    return typst


# ── Auto-griglia: immagini consecutive ──────────────────────────────


def test_two_consecutive_images_become_grid():
    md = "![Foto A](immagini/a.jpg)\n![Foto B](immagini/b.jpg)"
    typ = convert(md)
    assert "#grid(" in typ
    assert "columns: (1fr, 1fr)" in typ
    assert 'figure(image("immagini/a.jpg", width: 100%), caption: [Foto A])' in typ
    assert 'figure(image("immagini/b.jpg", width: 100%), caption: [Foto B])' in typ
    assert "#figura" not in typ


def test_four_consecutive_images_all_present():
    md = "\n".join(f"![Foto {c}](immagini/{c.lower()}.jpg)" for c in "ABCD")
    typ = convert(md)
    assert typ.count("#grid(") == 1
    for c in "ABCD":
        assert f"caption: [Foto {c}]" in typ
    assert "column-gutter: 8pt" in typ
    assert "row-gutter: 8pt" in typ


def test_three_images_last_spans_full_row():
    md = "\n".join(f"![Foto {c}](immagini/{c.lower()}.jpg)" for c in "ABC")
    typ = convert(md)
    assert typ.count("#grid(") == 1
    # Cella dispari: l'ultima figura occupa tutta la riga
    assert 'grid.cell(colspan: 2, figure(image("immagini/c.jpg"' in typ


def test_single_image_stays_full_width_figura():
    md = "Testo prima.\n\n![Didascalia](immagini/a.jpg)\n\nTesto dopo."
    typ = convert(md)
    assert '#figura("immagini/a.jpg", didascalia: "Didascalia")' in typ
    assert "#grid(" not in typ


def test_blank_line_splits_image_groups():
    md = (
        "![A](immagini/a.jpg)\n![B](immagini/b.jpg)\n"
        "\n"
        "![C](immagini/c.jpg)"
    )
    typ = convert(md)
    assert typ.count("#grid(") == 1
    assert '#figura("immagini/c.jpg", didascalia: "C")' in typ


def test_text_line_closes_group():
    md = "![A](immagini/a.jpg)\nTesto in mezzo.\n![B](immagini/b.jpg)"
    typ = convert(md)
    assert "#grid(" not in typ
    assert typ.count("#figura") == 2
    assert "Testo in mezzo." in typ


def test_two_images_same_line_both_kept():
    md = "![A](immagini/a.jpg) ![B](immagini/b.jpg)"
    typ = convert(md)
    assert "#grid(" in typ
    assert "caption: [A]" in typ
    assert "caption: [B]" in typ


def test_caption_special_chars_escaped():
    md = '![Antenna #1 [test] a "V" *45°*](immagini/a.jpg)\n![B](immagini/b.jpg)'
    typ = convert(md)
    # I caratteri speciali Typst nel caption devono essere escapati
    assert r"Antenna \#1 \[test\]" in typ
    assert r"\*45°\*" in typ


def test_grid_images_remap_uploads_path():
    md = "![A](/uploads/a.jpg)\n![B](/uploads/b.jpg)"
    typ = convert(md)
    assert 'image("/data/uploads/a.jpg"' in typ
    assert 'image("/data/uploads/b.jpg"' in typ


def test_image_without_alt_has_no_caption():
    md = "![](immagini/a.jpg)\n![B](immagini/b.jpg)"
    typ = convert(md)
    assert 'figure(image("immagini/a.jpg", width: 100%)),' in typ


def test_custom_gutter():
    converter = MarkdownToTypstConverter(grid_gutter="12pt")
    _, typ = converter.convert("![A](a.jpg)\n![B](b.jpg)")
    assert "column-gutter: 12pt" in typ
    assert "row-gutter: 12pt" in typ


# ── Fence: contenuto letterale, nessuna trasformazione ──────────────


def test_typst_fence_content_untouched():
    md = (
        "Prima del codice.\n"
        "```typst\n"
        "#grid(\n"
        "  columns: (1fr, 1fr),\n"
        ")\n"
        "```\n"
        "Dopo il codice."
    )
    typ = convert(md)
    assert "#grid(" in typ
    assert "== grid" not in typ
    assert "```typst" in typ
    assert "```" in typ.split("#grid(")[1]  # fence di chiusura preservato


def test_fence_content_skips_markdown_transforms():
    md = "```\n**non grassetto**\n![non immagine](x.jpg)\n# non titolo\n```"
    typ = convert(md)
    assert "**non grassetto**" in typ
    assert "![non immagine](x.jpg)" in typ
    assert "# non titolo" in typ
    assert "#figura" not in typ
    assert "== " not in typ
