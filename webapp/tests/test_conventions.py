from app.mcp.conventions import CONVENZIONI, markdown_preview


def test_conventions_text_mentions_box_evidenza():
    assert "box-evidenza" in CONVENZIONI
    assert "!!!" in CONVENZIONI


def test_preview_converts_bold_and_admonition():
    md = "Testo **grassetto**.\n\n!!! \"Nota\"\nRiga uno.\n!!!"
    typ = markdown_preview(md)
    assert "*grassetto*" in typ
    assert '#box-evidenza(titolo: "Nota")' in typ
