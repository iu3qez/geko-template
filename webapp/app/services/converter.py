"""
Markdown → Typst converter for the GEKO Radio Magazine template.

Converts Markdown articles into Typst source code using the custom functions
defined in template.typ (e.g. #box-evidenza, #figura, #tabella-geko, #link-geko).

Conversion pipeline (per-line, single pass):
  1. Block-level structures (stateful, multi-line):
     - Box evidenza (!!! admonitions)
     - Blockquotes (> lines)
     - Tables (| delimited rows)
  2. Block-level elements (single line):
     - Headings (# → =, shifted +1 so article title stays H1)
     - Images (![alt](src){width=X} → #figura)
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

    def __init__(self):
        self.md = MarkdownIt()

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
                    table_headers = [c.strip() for c in line.strip().strip('|').split('|') if c.strip()]
                    table_rows = []
                    i += 1
                    # Skip separator row (---|---|)
                    if i < len(lines) and re.match(r'^\|?[\s\-:|]+\|', lines[i].strip()):
                        i += 1
                    continue
                else:
                    # Subsequent rows = data
                    cells = [c.strip() for c in line.strip().strip('|').split('|') if c.strip()]
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
            # ![alt](path){width=50%} → #figura("path", didascalia: "alt", width: 50%)

            img_match = re.match(
                r'!\[([^\]]*)\]\(([^)]+)\)(?:\{([^}]+)\})?',
                line.strip()
            )
            if img_match:
                alt = img_match.group(1)
                path = img_match.group(2)
                attrs = img_match.group(3)
                width = None
                if attrs:
                    width_match = re.search(r'width=(\d+%?)', attrs)
                    if width_match:
                        width = width_match.group(1)

                # Remap web paths to Typst filesystem root
                # /uploads/x.png → /data/uploads/x.png
                if path.startswith('/uploads/'):
                    path = '/data' + path

                parts = [f'"{path}"']
                if alt:
                    parts.append(f'didascalia: "{alt}"')
                if width:
                    parts.append(f'larghezza: {width}')
                result.append(f'#figura({", ".join(parts)})')
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


def convert_markdown_to_typst(markdown_text: str) -> tuple[dict, str]:
    """Convenience function for converting markdown to typst."""
    converter = MarkdownToTypstConverter()
    return converter.convert(markdown_text)
