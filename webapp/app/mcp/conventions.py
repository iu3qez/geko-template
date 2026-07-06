"""Guida convenzioni Markdown → Typst e helper di anteprima per l'MCP."""

import pathlib
from typing import Optional

from ..services.article_ops import article_image_base
from ..services.md_render import render_article_body

CONVENZIONI = """\
# Convenzioni Markdown del GEKO Radio Magazine

Scrivi gli articoli in Markdown. Il template li converte in Typst così:

- `# Titolo` → sezione (il titolo dell'articolo resta di primo livello).
- `**grassetto**` → grassetto; `*corsivo*` o `_corsivo_` → corsivo.
- `[testo](url)` → link stilizzato `#link-geko` (gli URL nudi non vengono più
  auto-linkati: usa `<url>` per un link esplicito).
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
- Box evidenza (GitHub-alert) → funzione `#box-evidenza`: riga `> [!TIPO] Titolo`,
  poi il corpo su righe `>`. Tipi: NOTE, TIP, WARNING, IMPORTANT, CAUTION.
  Il corpo resta Markdown.

  > [!WARNING] Attenzione alla batteria
  > In portatile QRP porta sempre una batteria di scorta.
  > Il **freddo** riduce la capacità del 20-30%.

- Immagini: `![alt](file.png)` a piena larghezza; `{width=60%}` per una figura
  più piccola centrata; due o più immagini su righe consecutive → griglia 2 colonne.
- URL: usare `[testo](url)` o `<url>` (gli URL nudi non vengono più auto-linkati).

Usa il tool `anteprima_typst` per vedere il Typst generato prima di salvare.
"""

_ESEMPIO = pathlib.Path(__file__).resolve().parent.parent / "services" / "esempio_convenzioni.md"
if _ESEMPIO.exists():
    CONVENZIONI += (
        "\n\n## Esempio completo\n\n```markdown\n"
        + _ESEMPIO.read_text(encoding="utf-8")
        + "\n```\n"
    )


def markdown_preview(md: str, articolo_id: Optional[int] = None) -> str:
    """Renderizza il Markdown GEKO in Typst (via cmarker) e lo restituisce."""
    image_base = article_image_base(articolo_id) if articolo_id is not None else None
    return render_article_body(md, image_base=image_base)
