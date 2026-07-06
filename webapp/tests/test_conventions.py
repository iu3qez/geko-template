from app.mcp.conventions import CONVENZIONI, markdown_preview


def test_conventions_text_mentions_box_evidenza():
    assert "box-evidenza" in CONVENZIONI


def test_convenzioni_menziona_github_alert():
    assert "[!WARNING]" in CONVENZIONI or "[!TIPO]" in CONVENZIONI


def test_preview_alert_diventa_box():
    out = markdown_preview("> [!TIP] Consiglio\n> corpo **forte**")
    assert '#box-evidenza(titolo: "Consiglio", tipo: "tip")[' in out
