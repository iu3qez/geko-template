"""
Markdown → Typst converter for the GEKO Radio Magazine template.

Converts Markdown articles into Typst source code using the custom functions
defined in template.typ (e.g. #box-evidenza, #figura, #tabella-geko, #link-geko).

Conversion pipeline (per-line, single pass):
  1. Block-level structures (stateful, multi-line):
     - Box evidenza (!!! admonitions)
     - Fenced code blocks (``` — content passed through verbatim)
     - Blockquotes (> lines)
     - Tables (| delimited rows)
  2. Block-level elements (single line):
     - Headings (# → =, shifted +1 so article title stays H1)
     - Images: single ![alt](src){width=X} → #figura;
       ≥2 consecutive image lines → #grid a 2 colonne
  3. Inline formatting:
     - Bullet lists (* item → - item, must precede bold/italic)
     - Numbered lists (1. item → + item)
     - Bold (**text** → *text*)
     - Italic (*text* → _text_)
     - Lone asterisk escaping (safety net for malformed markdown)
     - Links ([text](url) → #link-geko)
     - Bare URLs (https://... → #link-geko)

Markdown syntax mapping:
  Markdown                     Typst (GEKO template)
  ─────────────────────────    ─────────────────────────────────
  # Heading                    == Heading  (level shifted +1)
  **bold**                     *bold*
  *italic* / _italic_          _italic_
  [text](url)                  #link-geko("url", testo: "text")
  https://bare.url             #link-geko("https://bare.url")
  ![alt](path){width=80%}     #figura("path", didascalia: "alt", width: 80%)
  ![a](x) + ![b](y) consec.    #grid(columns: (1fr, 1fr), ...figure...)
  ```code fence```             passed through verbatim (Typst raw block)
  * bullet / - bullet          - bullet
  1. numbered                  + numbered
  > blockquote                 #quote[text]
  | table | row |              #tabella-geko(headers, rows)
  !!! / !!! type "title"       #box-evidenza(titolo: "title")[content]
"""

import re
from typing import Optional
import frontmatter
from markdown_it import MarkdownIt


class MarkdownToTypstConverter:
    """
    Converts Markdown content to Typst format compatible with the GEKO template.

    Usage:
        converter = MarkdownToTypstConverter()
        metadata, typst_code = converter.convert(markdown_with_frontmatter)

        # Or generate a full article with title/author wrapper:
        typst_article = converter.generate_article_typst(
            titolo="Titolo", autore="IK2ABC", nome="Mario",
            sottotitolo="Sottotitolo", contenuto=typst_code,
        )
    """

    def __init__(self, grid_gutter: str = "8pt", image_base: Optional[str] = None):
        self.md = MarkdownIt()
        # Gutter (column + row) for the 2-column auto-grid of consecutive images
        self.grid_gutter = grid_gutter
        # Base path for bare image filenames (per-article media library).
        # When set, ![](nome.png) with a bare filename resolves to
        # f"{image_base}/nome.png" (e.g. "/data/uploads/articoli/7").
        self.image_base = image_base.rstrip("/") if image_base else None

    def convert(self, markdown_text: str) -> tuple[dict, str]:
        """
        Convert markdown (with optional YAML frontmatter) to Typst.

        Args:
            markdown_text: Full markdown string, optionally with --- frontmatter.

        Returns:
            (metadata, typst_content) — metadata dict from frontmatter,
            and the converted Typst source string.
        """
        post = frontmatter.loads(markdown_text)
        metadata = dict(post.metadata)
        content = post.content
        typst_content = self._convert_content(content)
        return metadata, typst_content

    # ── Main conversion loop ───────────────────────────────────────────

    def _convert_content(self, content: str) -> str:
        """
        Convert markdown content to Typst syntax, line by line.

        Uses a single-pass state machine to handle multi-line blocks
        (box, blockquote, table) while converting inline formatting
        on regular lines.
        """
        lines = content.split('\n')
        result = []

        # State for multi-line blocks
        in_box = False
        box_title = ""
        box_content: list[str] = []

        in_table = False
        table_headers: list[str] = []
        table_rows: list[list[str]] = []

        in_blockquote = False
        blockquote_lines: list[str] = []

        in_fence = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # ── Box evidenza (admonition) ──────────────────────────
            # Close check MUST come before open check, otherwise a
            # closing "!!!" would be misinterpreted as opening a new box.

            if in_box:
                if line.strip() == '!!!':
                    # Close box — each non-empty line becomes a separate paragraph
                    # (double newline between lines) so Typst renders line breaks
                    content_text = '\n\n'.join(
                        line for line in box_content if line.strip()
                    )
                    result.append(f'#box-evidenza(titolo: "{box_title}")[')
                    result.append(f'  {content_text}')
                    result.append(']')
                    result.append('')
                    in_box = False
                    box_content = []
                else:
                    box_content.append(line)
                i += 1
                continue

            # Open box: bare "!!!", !!! type "title", or !!! "title"
            if line.strip().startswith('!!!'):
                stripped = line.strip()
                if stripped == '!!!':
                    in_box = True
                    box_title = ""
                    box_content = []
                    i += 1
                    continue
                match = re.match(r'!!!\s*(?:\w+\s*)?"([^"]*)"', stripped)
                if match:
                    in_box = True
                    box_title = match.group(1)
                    box_content = []
                i += 1
                continue

            # ── Fenced code blocks ─────────────────────────────────
            # Content inside ``` fences is passed through verbatim:
            # no markdown transform must apply (e.g. #grid must NOT
            # become "== grid"). The fence itself is kept, so Typst
            # renders it as a raw block.

            if in_fence:
                result.append(line)
                if re.match(r'^\s*`{3,}\s*$', line):
                    in_fence = False
                i += 1
                continue

            if re.match(r'^\s*`{3,}', line):
                in_fence = True
                result.append(line)
                i += 1
                continue

            # ── Blockquote ─────────────────────────────────────────
            # Collect consecutive > lines, emit #quote[...] when done.

            if line.strip().startswith('>'):
                if not in_blockquote:
                    in_blockquote = True
                    blockquote_lines = []
                quote_text = re.sub(r'^>\s?', '', line)
                blockquote_lines.append(quote_text)
                i += 1
                continue
            elif in_blockquote:
                # First non-quote line ends the block
                quote_content = '\n'.join(blockquote_lines)
                result.append(f'#quote[{quote_content}]')
                result.append('')
                in_blockquote = False
                blockquote_lines = []
                # Fall through to process current line normally

            # ── Table ──────────────────────────────────────────────
            # Collect | delimited rows, emit #tabella-geko when done.

            if '|' in line and re.match(r'^\|?.+\|', line.strip()):
                if not in_table:
                    # First row = headers
                    in_table = True
                    table_headers = [c.strip() for c in line.strip().strip('|').split('|')]
                    table_rows = []
                    i += 1
                    # Skip separator row (---|---|)
                    if i < len(lines) and re.match(r'^\|?[\s\-:|]+\|', lines[i].strip()):
                        i += 1
                    continue
                else:
                    # Subsequent rows = data
                    cells = [c.strip() for c in line.strip().strip('|').split('|')]
                    table_rows.append(cells)
                    i += 1
                    continue
            elif in_table:
                # First non-table line ends the table
                result.append(self._format_table(table_headers, table_rows))
                result.append('')
                in_table = False
                table_headers = []
                table_rows = []
                # Fall through to process current line normally

            # ── Headings ───────────────────────────────────────────
            # Markdown # = Typst ==  (shifted +1 so article title stays =)

            if line.startswith('#'):
                level = len(re.match(r'^#+', line).group())
                text = line.lstrip('#').strip()
                result.append('=' * (level + 1) + ' ' + text)
                i += 1
                continue

            # ── Images ─────────────────────────────────────────────
            # Single ![alt](path){width=50%} → #figura(...) full width.
            # ≥2 consecutive image-only lines (no blank line or text in
            # between) are grouped into a 2-column #grid so photo-heavy
            # articles don't stack every figure full width.

            images = self._parse_image_line(line)
            if images is not None:
                group = list(images)
                j = i + 1
                while j < len(lines):
                    more = self._parse_image_line(lines[j])
                    if more is None:
                        break
                    group.extend(more)
                    j += 1
                if len(group) == 1:
                    result.append(self._format_figura(*group[0]))
                else:
                    result.append(self._format_figure_grid(group))
                    result.append('')
                i = j
                continue

            # Fallback (historical behavior): image with trailing text
            # on the same line — emit #figura, drop the rest.
            img_match = re.match(
                r'!\[([^\]]*)\]\(([^)]+)\)(?:\{([^}]+)\})?',
                line.strip()
            )
            if img_match:
                result.append(self._format_figura(
                    img_match.group(1), img_match.group(2), img_match.group(3)
                ))
                i += 1
                continue

            # ── Inline formatting ──────────────────────────────────
            # Order matters: bullets → numbered → bold → italic → escape → links

            # Bullet lists: * item → - item
            # MUST run before bold/italic to avoid * being parsed as formatting
            line = re.sub(r'^(\s*)\*\s+', r'\1- ', line)

            # Numbered lists: 1. item → + item
            line = re.sub(r'^(\s*)(\d+)\.\s+', r'\1+ ', line)

            # Bold: **text** → *text* (Typst bold syntax)
            # Use placeholder to prevent italic pass from re-matching
            line = re.sub(r'\*\*([^*]+)\*\*', '\x00BOLD\x00\\1\x00/BOLD\x00', line)

            # Italic: *text* → _text_ (Typst italic syntax)
            line = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', line)

            # Restore bold placeholders to Typst *...*
            line = line.replace('\x00BOLD\x00', '*').replace('\x00/BOLD\x00', '*')

            # Safety: escape any remaining unmatched * to prevent Typst errors
            line = self._escape_lone_asterisks(line)

            # Markdown links: [text](url) → #link-geko("url", testo: "text")
            line = re.sub(
                r'\[([^\]]+)\]\(([^)]+)\)',
                r'#link-geko("\2", testo: "\1")',
                line
            )

            # Bare URLs not already inside a #link-geko or quotes
            line = re.sub(
                r'(?<!")(?<!link-geko\(")(https?://[^\s<>\"\)]+)(?!")',
                r'#link-geko("\1")',
                line
            )

            result.append(line)
            i += 1

        # ── Flush any unclosed blocks at end of input ──────────────
        if in_blockquote:
            quote_content = '\n'.join(blockquote_lines)
            result.append(f'#quote[{quote_content}]')
        if in_table:
            result.append(self._format_table(table_headers, table_rows))

        return '\n'.join(result)

    # ── Helper methods ─────────────────────────────────────────────

    # Alt text may contain one level of nested [brackets]
    _IMG_RE = re.compile(
        r'!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)]+)\)(?:\{([^}]+)\})?'
    )

    def _parse_image_line(self, line: str) -> Optional[list[tuple]]:
        """
        Parse a line consisting ONLY of one or more ![alt](path){attrs}
        images (whitespace-separated).

        Returns a list of (alt, path, attrs) tuples, or None if the line
        contains anything other than images. Multiple images on the same
        line are all kept (previously the second one was dropped).
        """
        stripped = line.strip()
        if not stripped.startswith('!['):
            return None
        images = []
        pos = 0
        while pos < len(stripped):
            match = self._IMG_RE.match(stripped, pos)
            if not match:
                return None
            images.append((match.group(1), match.group(2), match.group(3)))
            pos = match.end()
            while pos < len(stripped) and stripped[pos] in ' \t':
                pos += 1
        return images

    def _remap_path(self, path: str) -> str:
        """Remap image paths for Typst.

        - Web paths `/uploads/…` → Typst filesystem root `/data/uploads/…`.
        - Bare filenames (no path) → per-article media library when
          `image_base` is set, so #figura("nome.png") resolves in compilation.
        """
        if path.startswith('/uploads/'):
            return '/data' + path
        if self.image_base and self._is_bare_filename(path):
            return f"{self.image_base}/{path}"
        return path

    @staticmethod
    def _is_bare_filename(path: str) -> bool:
        """True for a plain filename (no absolute/relative dir, no scheme/data URI)."""
        return (
            not path.startswith('/')
            and not path.startswith('data:')
            and '://' not in path
            and '/' not in path
        )

    def _format_figura(self, alt: str, path: str, attrs: Optional[str]) -> str:
        """Format a single full-width image as a #figura(...) call."""
        width = None
        if attrs:
            width_match = re.search(r'width=(\d+%?)', attrs)
            if width_match:
                width = width_match.group(1)

        parts = [f'"{self._remap_path(path)}"']
        if alt:
            parts.append(f'didascalia: "{alt}"')
        if width:
            parts.append(f'larghezza: {width}')
        return f'#figura({", ".join(parts)})'

    def _format_figure_grid(self, images: list[tuple]) -> str:
        """
        Format ≥2 consecutive images as a 2-column #grid of figure().

        With an odd number of images the last figure spans the full row
        (grid.cell(colspan: 2)) instead of leaving an empty cell.
        """
        cells = []
        for alt, path, _attrs in images:
            fig = f'figure(image("{self._remap_path(path)}", width: 100%)'
            if alt:
                fig += f', caption: [{self._escape_caption(alt)}]'
            fig += ')'
            cells.append(fig)

        if len(cells) % 2 == 1:
            cells[-1] = f'grid.cell(colspan: 2, {cells[-1]})'

        out = [
            '#grid(',
            '  columns: (1fr, 1fr),',
            f'  column-gutter: {self.grid_gutter},',
            f'  row-gutter: {self.grid_gutter},',
        ]
        out.extend(f'  {cell},' for cell in cells)
        out.append(')')
        return '\n'.join(out)

    @staticmethod
    def _escape_caption(text: str) -> str:
        """
        Escape Typst markup characters in a caption content block so the
        alt text renders literally (e.g. # * _ [ ] $ \\).
        """
        return re.sub(r'([\\\[\]#*_$])', r'\\\1', text)

    def _split_paragraphs(self, lines: list[str]) -> list[list[str]]:
        """
        Group consecutive non-empty lines into paragraphs.

        Used to preserve paragraph breaks inside box-evidenza content:
        blank lines in the input become double newlines in the output,
        which Typst renders as separate paragraphs.
        """
        paragraphs = []
        current: list[str] = []
        for line in lines:
            if line.strip() == '':
                if current:
                    paragraphs.append(current)
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(current)
        return paragraphs

    def _escape_lone_asterisks(self, line: str) -> str:
        """
        Escape unmatched * characters that would cause Typst
        "unclosed delimiter" compilation errors.

        This is a safety net for malformed markdown (e.g. "text* more text"
        where the author forgot the opening *). Matched pairs are left intact.
        """
        # Quick check: if all * are in matched pairs, nothing to do
        stripped = re.sub(r'\*[^*]+\*', '', line)
        if '*' not in stripped:
            return line
        # Walk the string, pairing asterisks greedily
        result = []
        i = 0
        while i < len(line):
            if line[i] == '*':
                close = line.find('*', i + 1)
                if close != -1 and close - i > 1:
                    # Matched pair — keep as-is
                    result.append(line[i:close + 1])
                    i = close + 1
                else:
                    # Lone asterisk — escape for Typst
                    result.append('\\*')
                    i += 1
            else:
                result.append(line[i])
                i += 1
        return ''.join(result)

    def _convert_inline(self, text: str) -> str:
        """
        Convert inline Markdown formatting to Typst.

        Used specifically for table cell content where the conversion
        uses #strong[...] (bracket syntax) instead of *...* to avoid
        conflicts with Typst table cell delimiters.
        """
        # Bold: **text** → #strong[text]
        text = re.sub(r'\*\*([^*]+)\*\*', r'#strong[\1]', text)
        # Italic: *text* → _text_
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', text)
        return text

    def _format_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """
        Format a Markdown table as a Typst #tabella-geko() call.

        Uses _convert_inline for cell content (bracket-based bold)
        to avoid delimiter conflicts inside table content blocks.
        """
        headers_str = ', '.join(f'[{self._convert_inline(h)}]' for h in headers)

        rows_strs = []
        for row in rows:
            row_str = ', '.join(f'[{self._convert_inline(c)}]' for c in row)
            rows_strs.append(f'    ({row_str}),')
        rows_content = '\n'.join(rows_strs)

        return f'''#tabella-geko(
  ({headers_str},),
  (
{rows_content}
  )
)'''

    # ── Article wrapper ────────────────────────────────────────────

    def generate_article_typst(
        self,
        titolo: str,
        sottotitolo: Optional[str],
        autore: Optional[str],
        nome: Optional[str],
        contenuto: str
    ) -> str:
        """
        Wrap converted Typst content into a full article structure.

        Generates:
            = Titolo
            #sottotitolo-sezione[...]   (if provided)
            #autore("CALL", nome: "Nome")  (if provided)
            <contenuto>
            #separatore()
        """
        parts = []

        parts.append(f'= {titolo}')
        parts.append('')

        if sottotitolo:
            parts.append(f'#sottotitolo-sezione[{sottotitolo}]')

        if autore:
            if nome:
                parts.append(f'#autore("{autore}", nome: "{nome}")')
            else:
                parts.append(f'#autore("{autore}")')
        parts.append('')

        parts.append(contenuto)
        parts.append('')
        parts.append('#separatore()')

        return '\n'.join(parts)


def convert_markdown_to_typst(
    markdown_text: str, image_base: Optional[str] = None
) -> tuple[dict, str]:
    """Convenience function for converting markdown to typst.

    Pass `image_base` (e.g. "/data/uploads/articoli/7") to resolve bare
    image filenames against an article's media library.
    """
    converter = MarkdownToTypstConverter(image_base=image_base)
    return converter.convert(markdown_text)
