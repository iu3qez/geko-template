"""Test del probe di compilazione per-segmento usato dalla diagnostica
errori di `/magazines/{id}/build` (Task 7).
"""

from app.services.builder import MagazineBuilder
from app.services.md_render import render_segments


def test_probe_isola_segmento_buono():
    b = MagazineBuilder()
    # figura verso file inesistente -> errore attribuibile a quel segmento
    msg = b.try_compile_snippet('#figura("/data/uploads/inesistente_xyz.png")')
    assert msg is not None and isinstance(msg, str)


def test_probe_prosa_valida_ok():
    b = MagazineBuilder()
    segs = render_segments("Testo con 5$ e _enfasi_ e `codice`.")
    assert b.try_compile_snippet(segs[0][1]) is None
