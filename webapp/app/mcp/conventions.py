"""Guida convenzioni Markdown → Typst e helper di anteprima per l'MCP."""

from ..services.converter import MarkdownToTypstConverter

CONVENZIONI = """\
# Convenzioni Markdown del GEKO Radio Magazine

Scrivi gli articoli in Markdown. Il template li converte in Typst così:

- `# Titolo` → sezione (il titolo dell'articolo resta di primo livello).
- `**grassetto**` → grassetto; `*corsivo*` o `_corsivo_` → corsivo.
- `[testo](url)` e URL nudi → link stilizzato `#link-geko`.
- `![descrizione](/uploads/foto.jpg){width=80%}` → figura con didascalia.
  I path `/uploads/...` vengono rimappati automaticamente.
- Liste puntate con `*` o `-`; liste numerate con `1.`.
- `> citazione` → blocco citazione.
- Tabelle Markdown `| a | b |` con riga separatrice → tabella GEKO.
- Box evidenza (admonition), con titolo tra virgolette → funzione `#box-evidenza`:

  !!! "Attenzione alla batteria"
  In portatile QRP porta sempre una batteria di scorta.
  Il freddo riduce la capacità del 20-30%.
  !!!

Usa il tool `anteprima_typst` per vedere il Typst generato prima di salvare.
"""


def markdown_preview(md: str) -> str:
    """Converte Markdown GEKO in Typst e restituisce il sorgente Typst."""
    converter = MarkdownToTypstConverter()
    _metadata, typst = converter.convert(md)
    return typst
