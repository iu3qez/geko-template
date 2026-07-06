# Compressione PDF via Ghostscript — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ridurre la dimensione del PDF finale del magazine (ora >48 MB) ricomprimendolo con Ghostscript (preset `/ebook`, 150 dpi) come passo post-build, in modo fail-safe.

**Architecture:** Un nuovo modulo `pdf_compress.py` esegue Ghostscript sul PDF appena scritto da Typst, sostituendo l'originale col compresso solo se più piccolo; se `gs` manca o fallisce, tiene l'originale senza rompere la build. `build_magazine` lo richiama dopo aver scritto il PDF. Il pacchetto `ghostscript` viene aggiunto all'immagine Docker.

**Tech Stack:** Python 3 (subprocess, shutil), Ghostscript (`gs`), Pillow (solo nei test, già dipendenza), pytest.

## Global Constraints

- Preset Ghostscript fisso: **`/ebook`** (150 dpi).
- Comando gs: `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH -dQUIET -sOutputFile=<tmp> <src>`.
- `compress_pdf` **non solleva mai** eccezioni; sostituisce l'originale **solo se strettamente più piccolo** (mai ingrandire il file).
- Fail-safe: `gs` assente (`shutil.which("gs") is None`) → no-op con `compressed: False`.
- Tests con il venv locale: `cd webapp && .venv/bin/python -m pytest`.
- Italiano per commenti/log, inglese per il codice. Commit: **niente trailer `Co-Authored-By`**.

---

## File Structure

- **Create** `webapp/app/services/pdf_compress.py` — `compress_pdf(path, preset="ebook") -> dict`, con guardie e fail-safe.
- **Modify** `webapp/app/services/builder.py` — in `build_magazine`, dopo `pdf_path.write_bytes(...)`, chiama `compress_pdf(pdf_path)`.
- **Modify** `webapp/Dockerfile` — aggiunge `ghostscript` all'`apt-get install` dello stage runtime.
- **Create** `webapp/tests/test_pdf_compress.py` — riduzione con gs, no-op senza gs, mai ingrandire.

---

## Task 1: Modulo `pdf_compress`

**Files:**
- Create: `webapp/app/services/pdf_compress.py`
- Test: `webapp/tests/test_pdf_compress.py`

**Interfaces:**
- Produces: `compress_pdf(path: pathlib.Path, preset: str = "ebook") -> dict` — ricomprime in-place; ritorna `{"compressed": bool, "before": int, "after": int, "preset": str, "reason": str?}`. Non solleva eccezioni; non ingrandisce mai il file.

- [ ] **Step 1: Scrivere i test**

```python
# webapp/tests/test_pdf_compress.py
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
```

- [ ] **Step 2: Eseguire — falliscono (modulo assente)**

Run: `cd webapp && .venv/bin/python -m pytest tests/test_pdf_compress.py -v`
Expected: FAIL con `ModuleNotFoundError: app.services.pdf_compress`

- [ ] **Step 3: Implementare il modulo**

```python
# webapp/app/services/pdf_compress.py
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
```

- [ ] **Step 4: Eseguire — devono passare (il primo è skippato solo se manca gs)**

Run: `cd webapp && .venv/bin/python -m pytest tests/test_pdf_compress.py -v`
Expected: PASS (3 test; `test_compress_riduce_pdf_pesante` SKIPPED se `gs` non installato)

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/pdf_compress.py webapp/tests/test_pdf_compress.py
git commit -m "feat(pdf): compressione PDF via Ghostscript (fail-safe, solo se riduce)"
```

---

## Task 2: Integrazione in `build_magazine` + Ghostscript nell'immagine Docker

**Files:**
- Modify: `webapp/app/services/builder.py` (`build_magazine`, subito dopo `pdf_path.write_bytes(pdf_bytes)`)
- Modify: `webapp/Dockerfile` (apt-get install dello stage runtime)
- Test: `webapp/tests/test_build_regression.py` (asserzione aggiuntiva)

**Interfaces:**
- Consumes: `pdf_compress.compress_pdf` (Task 1).

- [ ] **Step 1: Richiamare `compress_pdf` in `build_magazine`**

In `webapp/app/services/builder.py`, nel metodo `build_magazine`, il blocco attuale è:
```python
        pdf_path = self.output_dir / f"geko{numero}.pdf"
        pdf_bytes = typst.compile(
            str(typ_path), root=str(WEBAPP_DIR), package_path=str(PKG_PATH)
        )
        pdf_path.write_bytes(pdf_bytes)

        return pdf_path
```
Sostituirlo con (aggiunta della compressione dopo la scrittura):
```python
        pdf_path = self.output_dir / f"geko{numero}.pdf"
        pdf_bytes = typst.compile(
            str(typ_path), root=str(WEBAPP_DIR), package_path=str(PKG_PATH)
        )
        pdf_path.write_bytes(pdf_bytes)

        # Post-processing: comprime il PDF (fail-safe, non rompe la build)
        from .pdf_compress import compress_pdf
        info = compress_pdf(pdf_path)
        if info["compressed"]:
            print(
                f"PDF compresso: {info['before'] / 1048576:.1f} MB -> "
                f"{info['after'] / 1048576:.1f} MB"
            )
        else:
            print(f"Compressione PDF saltata: {info.get('reason', '?')}")

        return pdf_path
```

- [ ] **Step 2: Aggiungere `ghostscript` all'immagine Docker**

In `webapp/Dockerfile`, nello stage runtime, il blocco attuale (righe ~78-85) è:
```dockerfile
# Installa dipendenze runtime
# - fonts-linuxlibertine: font per Typst
# - fontconfig: gestione font
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-linuxlibertine \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv
```
Sostituirlo con (aggiunta di `ghostscript`):
```dockerfile
# Installa dipendenze runtime
# - fonts-linuxlibertine: font per Typst
# - fontconfig: gestione font
# - ghostscript: compressione PDF post-build (app/services/pdf_compress.py)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-linuxlibertine \
    fontconfig \
    ghostscript \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv
```

- [ ] **Step 3: Estendere il test di build per verificare l'integrazione (build valida a prescindere da gs)**

In `webapp/tests/test_build_regression.py`, aggiungere in fondo:
```python
def test_build_magazine_comprime_se_gs_presente(tmp_path):
    import shutil
    from app.services.builder import MagazineBuilder
    from app.services.md_render import generate_article_typst

    art = generate_article_typst(
        titolo="Foto", sottotitolo=None, autore="IK2X", nome=None,
        contenuto_md="![Vetta](/typst/assets/corno-grande-1.jpg)\n"
                     "![Cresta](/typst/assets/corno-grande-2.jpg)\n",
    )
    pdf = MagazineBuilder().build_magazine(
        numero="93", mese="Luglio", anno="2026", articles_typst=[art],
    )
    # La build produce sempre un PDF valido, con o senza Ghostscript.
    assert pdf.exists() and pdf.read_bytes()[:5] == b"%PDF-"
```

- [ ] **Step 4: Eseguire i test + suite**

Run: `cd webapp && .venv/bin/python -m pytest tests/test_build_regression.py -v && .venv/bin/python -m pytest -q`
Expected: PASS (build valida; se `gs` è presente nell'ambiente il PDF risulta compresso)

- [ ] **Step 5: (Facoltativo, se Docker disponibile) verificare che l'immagine includa gs**

Run: `cd webapp && docker build -t geko-gs-check . >/dev/null 2>&1 && docker run --rm geko-gs-check gs --version`
Expected: stampa una versione (es. `10.0x`). Se `docker` non è disponibile, saltare — non bloccante.

- [ ] **Step 6: Commit**

```bash
git add webapp/app/services/builder.py webapp/Dockerfile webapp/tests/test_build_regression.py
git commit -m "feat(builder): comprime il PDF dopo la build + ghostscript nell'immagine"
```

---

## Self-Review

**Spec coverage:** modulo `pdf_compress` con fail-safe + guardia "solo se più piccolo" → Task 1; integrazione in `build_magazine` → Task 2 Step 1; `ghostscript` nell'immagine → Task 2 Step 2; testing (riduzione con gs, no-op senza gs, build valida) → Task 1 + Task 2 Step 3. Preset `/ebook` fisso e non-goal (configurabilità, Pillow, soglia) rispettati.

**Placeholder scan:** nessun TBD/TODO; ogni step ha codice completo e comandi con output atteso.

**Type consistency:** `compress_pdf(path, preset="ebook") -> dict` con chiavi `compressed/before/after/preset/reason` usata coerentemente tra Task 1 (definizione/test) e Task 2 (consumo in builder). Comando gs identico tra spec, modulo e global constraints.
