"""Test risoluzione riferimenti immagine 'nudi' via image_base (media library per-articolo)."""

from app.services.converter import MarkdownToTypstConverter, convert_markdown_to_typst


def _convert(md, **kwargs):
    _meta, typ = MarkdownToTypstConverter(**kwargs).convert(md)
    return typ


def test_bare_filename_resolved_with_image_base():
    typ = _convert("![Schema](schema.png)", image_base="/data/uploads/articoli/7")
    assert '#figura("/data/uploads/articoli/7/schema.png"' in typ


def test_bare_filename_unchanged_without_image_base():
    # Retro-compatibilità: senza image_base il nome nudo resta invariato.
    typ = _convert("![Schema](schema.png)")
    assert '#figura("schema.png"' in typ


def test_uploads_path_still_remapped_with_image_base():
    # Un path /uploads/... esplicito non viene toccato dalla logica image_base.
    typ = _convert("![x](/uploads/foto.png)", image_base="/data/uploads/articoli/7")
    assert '#figura("/data/uploads/foto.png"' in typ


def test_grid_uses_image_base_for_bare_filenames():
    md = "![A](a.png)\n![B](b.png)"
    typ = _convert(md, image_base="/data/uploads/articoli/3")
    assert 'image("/data/uploads/articoli/3/a.png"' in typ
    assert 'image("/data/uploads/articoli/3/b.png"' in typ


def test_convenience_function_accepts_image_base():
    _meta, typ = convert_markdown_to_typst(
        "![x](y.png)", image_base="/data/uploads/articoli/1"
    )
    assert '#figura("/data/uploads/articoli/1/y.png"' in typ
