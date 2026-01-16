"""Build PDF from Typst files using the GEKO template."""

from pathlib import Path
from typing import Optional
import typst

# Paths
WEBAPP_DIR = Path(__file__).parent.parent.parent
TYPST_DIR = WEBAPP_DIR / "typst"
OUTPUT_DIR = WEBAPP_DIR / "data" / "output"

# Determina dove cercare template.typ:
# - In Docker: /app/typst/template.typ (montato via volume)
# - In locale: ../template.typ (nella root del progetto)
if (TYPST_DIR / "template.typ").exists():
    TEMPLATE_DIR = TYPST_DIR  # Docker: template montato in typst/
else:
    TEMPLATE_DIR = WEBAPP_DIR.parent  # Locale: template nella root progetto


class MagazineBuilder:
    """Builds GEKO Magazine PDF from articles."""

    def __init__(self):
        self.template_path = TEMPLATE_DIR / "template.typ"
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_magazine(
        self,
        numero: str,
        mese: str,
        anno: str,
        articles_typst: list[str],
        editoriale: Optional[str] = None,
        editoriale_autore: Optional[str] = None,
        copertina_path: Optional[str] = None,
        evidenze: Optional[list[dict]] = None,
    ) -> Path:
        """
        Build complete magazine PDF.

        Args:
            numero: Magazine number (e.g., "68")
            mese: Month name (e.g., "Gennaio")
            anno: Year (e.g., "2025")
            articles_typst: List of article content in Typst format
            editoriale: Editorial text
            editoriale_autore: Editorial author
            copertina_path: Path to cover image
            evidenze: List of highlights for cover {"titolo": ..., "descrizione": ...}

        Returns:
            Path to generated PDF
        """
        # Generate document
        document = self._generate_document(
            numero=numero,
            mese=mese,
            anno=anno,
            articles=articles_typst,
            editoriale=editoriale,
            editoriale_autore=editoriale_autore,
            copertina_path=copertina_path,
            evidenze=evidenze,
        )

        # Write .typ file
        typ_path = TYPST_DIR / "generated" / f"geko{numero}.typ"
        typ_path.parent.mkdir(parents=True, exist_ok=True)
        typ_path.write_text(document, encoding='utf-8')

        # Compile to PDF
        pdf_path = self.output_dir / f"geko{numero}.pdf"
        pdf_bytes = typst.compile(str(typ_path), root=str(TEMPLATE_DIR))
        pdf_path.write_bytes(pdf_bytes)

        return pdf_path

    def _generate_document(
        self,
        numero: str,
        mese: str,
        anno: str,
        articles: list[str],
        editoriale: Optional[str],
        editoriale_autore: Optional[str],
        copertina_path: Optional[str],
        evidenze: Optional[list[dict]],
    ) -> str:
        """Generate complete Typst document."""
        parts = []

        # Import template
        parts.append('#import "template.typ": *')
        parts.append('')

        # Cover page (if we have highlights)
        if evidenze and copertina_path:
            evidenze_typst = self._format_evidenze(evidenze)
            parts.append(f'''#copertina(
  numero: "{numero}",
  mese: "{mese}",
  anno: "{anno}",
  immagine-principale: "{copertina_path}",
  evidenze: {evidenze_typst},
  editoriale-testo: [{editoriale or ""}],
  editoriale-autore: "{editoriale_autore or ""}",
)''')
            parts.append('')

        # Logo page
        parts.append('''#pagina-logo(
  logo-grande: "assets/logo-mqc-grande.png",
  sottotitolo: "Rivista aperiodica del Mountain QRP Club",
)''')
        parts.append('')

        # Main content setup
        parts.append(f'''#show: geko-magazine.with(
  numero: "{numero}",
  mese: "{mese}",
  anno: "{anno}",
)''')
        parts.append('')

        # Table of contents
        parts.append('#sommario()')
        parts.append('')

        # Articles
        for article in articles:
            parts.append(article)
            parts.append('')

        return '\n'.join(parts)

    def _format_evidenze(self, evidenze: list[dict]) -> str:
        """Format highlights list for Typst."""
        items = []
        for ev in evidenze:
            titolo = ev.get('titolo', '')
            descrizione = ev.get('descrizione', '')
            items.append(f'(titolo: "{titolo}", descrizione: "{descrizione}")')
        return '(\n    ' + ',\n    '.join(items) + ',\n  )'


def build_magazine_pdf(
    numero: str,
    mese: str,
    anno: str,
    articles_typst: list[str],
    **kwargs
) -> Path:
    """Convenience function for building magazine PDF."""
    builder = MagazineBuilder()
    return builder.build_magazine(numero, mese, anno, articles_typst, **kwargs)
