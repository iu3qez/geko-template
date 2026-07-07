import shutil
from pathlib import Path

import pytest
from PIL import Image

from app.services import pdf_compress
from app.services.pdf_compress import compress_pdf

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
GEN_DIR = WEBAPP_DIR / "typst" / "generated"
ASSET = REPO_DIR / "assets" / "corno-grande-1.jpg"


def _pdf_pesante(dst: Path, pagine: int = 6):
    """PDF ricco di immagini ad alta dpi (gs /ebook lo ricampiona a 150 dpi)."""
    img = Image.open(ASSET).convert("RGB")
    img.save(dst, "PDF", save_all=True,
             append_images=[img] * (pagine - 1), resolution=300)


@pytest.mark.skipif(shutil.which("gs") is None, reason="Ghostscript non installato")
def test_compress_riduce_pdf_pesante(tmp_path):
    pdf = tmp_path / "pesante.pdf"
    _pdf_pesante(pdf)
    before = pdf.stat().st_size
    info = compress_pdf(pdf)
    assert info["compressed"] is True
    assert info["after"] < before
    assert pdf.stat().st_size == info["after"]
    # è ancora un PDF valido
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_compress_noop_senza_gs(tmp_path, monkeypatch):
    pdf = tmp_path / "x.pdf"
    _pdf_pesante(pdf, pagine=2)
    prima = pdf.read_bytes()
    monkeypatch.setattr(pdf_compress.shutil, "which", lambda _: None)
    info = compress_pdf(pdf)
    assert info["compressed"] is False
    assert "reason" in info
    assert pdf.read_bytes() == prima  # file intatto


def test_compress_non_ingrandisce_mai(tmp_path):
    # Invariante: dopo compress_pdf il file non è mai più grande di prima,
    # indipendentemente dalla presenza/efficacia di gs.
    pdf = tmp_path / "y.pdf"
    _pdf_pesante(pdf, pagine=2)
    before = pdf.stat().st_size
    compress_pdf(pdf)
    assert pdf.stat().st_size <= before
