"""Guida convenzioni Markdown → Typst e helper di anteprima per l'MCP."""

from typing import Optional

from ..services.article_ops import article_image_base
from ..services.converter import MarkdownToTypstConverter

CONVENZIONI = """\
# Convenzioni Markdown del GEKO Radio Magazine

Scrivi gli articoli in Markdown. Il template li converte in Typst così:

- `# Titolo` → sezione (il titolo dell'articolo resta di primo livello).
- `**grassetto**` → grassetto; `*corsivo*` o `_corsivo_` → corsivo.
- `[testo](url)` e URL nudi → link stilizzato `#link-geko`.
- `![descrizione](/uploads/foto.jpg){width=80%}` → figura con didascalia.
  I path `/uploads/...` vengono rimappati automaticamente.
- Per pubblicare figure da MCP: nel Markdown usa il **solo nome file**
  (`![Schema](x.png)`), poi carica i byte con `carica_immagine(articolo_id,
  "x.png", <base64>)`. I nomi nudi si risolvono nelle immagini di quell'articolo
  in anteprima (`anteprima_typst(..., articolo_id=...)`) e in compilazione.
  Formati: PNG, JPG/JPEG, GIF, WEBP, SVG (vettoriale, ideale per schemi).
- Due o più immagini su righe consecutive (senza testo o righe vuote in
  mezzo) → griglia a 2 colonne con didascalie. Con numero dispari l'ultima
  foto occupa tutta la riga. Utile per articoli con molte foto.
  Una singola immagine isolata resta a piena larghezza.
- I blocchi di codice ``` restano letterali (nessuna conversione).
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


def markdown_preview(md: str, articolo_id: Optional[int] = None) -> str:
    """Converte Markdown GEKO in Typst e restituisce il sorgente Typst.

    Con `articolo_id`, i riferimenti a immagini con nome file nudo
    (`![](nome.png)`) si risolvono nella media library di quell'articolo.
    """
    image_base = article_image_base(articolo_id) if articolo_id is not None else None
    converter = MarkdownToTypstConverter(image_base=image_base)
    _metadata, typst = converter.convert(md)
    return typst
