"""Convert Markdown to Typst format for GEKO template."""

import re
from typing import Optional
import frontmatter
from markdown_it import MarkdownIt


class MarkdownToTypstConverter:
    """Converts Markdown content to Typst format compatible with GEKO template."""

    def __init__(self):
        self.md = MarkdownIt()

    def convert(self, markdown_text: str) -> tuple[dict, str]:
        """
        Convert markdown to typst.

        Returns:
            tuple: (metadata dict, typst content string)
        """
        # Parse frontmatter
        post = frontmatter.loads(markdown_text)
        metadata = dict(post.metadata)
        content = post.content

        # Convert content
        typst_content = self._convert_content(content)

        return metadata, typst_content

    def _convert_content(self, content: str) -> str:
        """Convert markdown content to typst syntax."""
        lines = content.split('\n')
        result = []
        in_box = False
        box_title = ""
        box_content = []
        in_table = False
        table_headers = []
        table_rows = []
        in_blockquote = False
        blockquote_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Handle box evidenza (admonition syntax)
            if line.strip().startswith('!!! '):
                match = re.match(r'!!!\s*\w+\s*"([^"]*)"', line)
                if match:
                    in_box = True
                    box_title = match.group(1)
                    box_content = []
                i += 1
                continue

            if in_box:
                if line.strip() == '!!!':
                    # Close box
                    content_text = '\n'.join(box_content)
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

            # Handle blockquotes: > text → #quote[text]
            if line.strip().startswith('>'):
                if not in_blockquote:
                    in_blockquote = True
                    blockquote_lines = []
                # Remove > prefix and add to blockquote
                quote_text = re.sub(r'^>\s?', '', line)
                blockquote_lines.append(quote_text)
                i += 1
                continue
            elif in_blockquote:
                # End of blockquote
                quote_content = '\n'.join(blockquote_lines)
                result.append(f'#quote[{quote_content}]')
                result.append('')
                in_blockquote = False
                blockquote_lines = []
                # Don't increment i, process current line

            # Handle tables
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_headers = []
                    table_rows = []
                    # Parse header row
                    cells = [c.strip() for c in line.strip().strip('|').split('|')]
                    table_headers = cells
                    i += 1
                    # Skip separator row (|---|---|)
                    if i < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i].strip()):
                        i += 1
                    continue
                else:
                    # Parse data row
                    cells = [c.strip() for c in line.strip().strip('|').split('|')]
                    table_rows.append(cells)
                    i += 1
                    continue
            elif in_table:
                # End of table, output it
                result.append(self._format_table(table_headers, table_rows))
                result.append('')
                in_table = False
                table_headers = []
                table_rows = []
                # Don't increment i, process current line

            # Headers: # → == (shifted down one level so only article title is H1)
            if line.startswith('#'):
                level = len(re.match(r'^#+', line).group())
                text = line.lstrip('#').strip()
                result.append('=' * (level + 1) + ' ' + text)
                i += 1
                continue

            # Images with dimensions: ![alt](path){width=50%} → #figura with width
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

                # Convert web URL path to Typst filesystem path
                # /uploads/x.png → /data/uploads/x.png (for Typst compilation root)
                if path.startswith('/uploads/'):
                    path = '/data' + path

                parts = [f'"{path}"']
                if alt:
                    parts.append(f'didascalia: "{alt}"')
                if width:
                    parts.append(f'width: {width}')
                result.append(f'#figura({", ".join(parts)})')
                i += 1
                continue

            # Bold: **text** → *text*
            line = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', line)

            # Italic: *text* or _text_ → _text_
            # Note: need to be careful not to replace bold markers
            line = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', line)
            line = re.sub(r'_([^_]+)_', r'_\1_', line)

            # Links: [text](url) → #link-geko("url", testo: "text")
            line = re.sub(
                r'\[([^\]]+)\]\(([^)]+)\)',
                r'#link-geko("\2", testo: "\1")',
                line
            )

            # Bare URLs: https://... or http://... → #link-geko("url")
            # Only match URLs not already inside quotes or link-geko
            line = re.sub(
                r'(?<!")(?<!link-geko\(")(https?://[^\s<>\"\)]+)(?!")',
                r'#link-geko("\1")',
                line
            )

            # Bullet lists: - item → - item (same syntax)
            # Numbered lists: 1. item → + item (typst uses + for enum)
            line = re.sub(r'^(\s*)(\d+)\.\s+', r'\1+ ', line)

            result.append(line)
            i += 1

        # Handle any remaining open blocks
        if in_blockquote:
            quote_content = '\n'.join(blockquote_lines)
            result.append(f'#quote[{quote_content}]')
        if in_table:
            result.append(self._format_table(table_headers, table_rows))

        return '\n'.join(result)

    def _convert_inline(self, text: str) -> str:
        """Convert Markdown inline formatting to Typst."""
        # Bold: **text** → *text*
        text = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', text)
        # Italic: *text* or _text_ → _text_
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', text)
        return text

    def _format_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Format a table as Typst #tabella-geko."""
        # Format headers with content brackets to support inline formatting
        headers_str = ', '.join(f'[{self._convert_inline(h)}]' for h in headers)

        # Format rows with content brackets
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

    def generate_article_typst(
        self,
        titolo: str,
        sottotitolo: Optional[str],
        autore: Optional[str],
        nome: Optional[str],
        contenuto: str
    ) -> str:
        """Generate complete article in Typst format."""
        parts = []

        # Title (heading level 1)
        parts.append(f'= {titolo}')
        parts.append('')

        # Subtitle
        if sottotitolo:
            parts.append(f'#sottotitolo-sezione[{sottotitolo}]')

        # Author
        if autore:
            if nome:
                parts.append(f'#autore("{autore}", nome: "{nome}")')
            else:
                parts.append(f'#autore("{autore}")')
        parts.append('')

        # Content
        parts.append(contenuto)
        parts.append('')
        parts.append('#separatore()')

        return '\n'.join(parts)


def convert_markdown_to_typst(markdown_text: str) -> tuple[dict, str]:
    """Convenience function for converting markdown to typst."""
    converter = MarkdownToTypstConverter()
    return converter.convert(markdown_text)
