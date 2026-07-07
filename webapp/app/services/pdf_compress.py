"""Compressione del PDF finale del magazine via Ghostscript.

Typst incorpora le immagini alla risoluzione originale: un numero con molte foto
può superare decine di MB. Questo passo post-build ricampiona/ricomprime le
immagini interne al PDF (preset /ebook, 150 dpi) mantenendo il testo vettoriale.
Fail-safe: se Ghostscript non è disponibile o fallisce, l'originale resta intatto.
"""

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# /ebook = 150 dpi: buon compromesso qualità/dimensione per lettura a schermo.
_GS_PRESET = "ebook"


def compress_pdf(path: Path, preset: str = _GS_PRESET) -> dict:
    """Ricomprime in-place il PDF con Ghostscript. Non solleva mai eccezioni.

    Sostituisce l'originale col compresso SOLO se strettamente più piccolo.
    Ritorna: {"compressed": bool, "before": int, "after": int, "preset": str,
              "reason": str (solo se non compresso)}.
    """
    path = Path(path)
    before = path.stat().st_size

    def _skip(reason: str) -> dict:
        return {"compressed": False, "before": before, "after": before,
                "preset": preset, "reason": reason}

    gs = shutil.which("gs")
    if gs is None:
        logger.warning("Compressione PDF saltata: Ghostscript (gs) non disponibile")
        return _skip("ghostscript non disponibile")

    tmp = path.with_suffix(".compressed.pdf")
    cmd = [
        gs, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5",
        f"-dPDFSETTINGS=/{preset}", "-dNOPAUSE", "-dBATCH", "-dQUIET",
        f"-sOutputFile={tmp}", str(path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Compressione PDF fallita (%s): tengo l'originale", e)
        if tmp.exists():
            tmp.unlink()
        return _skip("ghostscript ha fallito")

    if not tmp.exists() or tmp.stat().st_size == 0:
        if tmp.exists():
            tmp.unlink()
        return _skip("output vuoto")

    after = tmp.stat().st_size
    if after < before:
        tmp.replace(path)
        logger.info("PDF compresso: %.1f MB -> %.1f MB (-%.0f%%)",
                    before / 1048576, after / 1048576, 100 * (before - after) / before)
        return {"compressed": True, "before": before, "after": after, "preset": preset}

    tmp.unlink()  # nessuna riduzione: tieni l'originale
    return _skip("nessuna riduzione")
