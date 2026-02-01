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

        for line in lines:
            # Handle box evidenza (admonition syntax)
            if line.strip().startswith('!!! '):
                match = re.match(r'!!!\s*\w+\s*"([^"]*)"', line)
                if match:
                    in_box = True
                    box_title = match.group(1)
                    box_content = []
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
                continue

            # Headers: # → =
            if line.startswith('#'):
                level = len(re.match(r'^#+', line).group())
                text = line.lstrip('#').strip()
                result.append('=' * level + ' ' + text)
                continue

            # Images: ![alt](path) → #figura
            img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
            if img_match:
                alt = img_match.group(1)
                path = img_match.group(2)
                # Convert web URL path to Typst filesystem path
                # /uploads/x.png → /data/uploads/x.png (for Typst compilation root)
                if path.startswith('/uploads/'):
                    path = '/data' + path
                if alt:
                    result.append(f'#figura("{path}", didascalia: "{alt}")')
                else:
                    result.append(f'#figura("{path}")')
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

            # Bullet lists: - item → - item (same syntax)
            # Numbered lists: 1. item → + item (typst uses + for enum)
            line = re.sub(r'^(\s*)(\d+)\.\s+', r'\1+ ', line)

            result.append(line)

        return '\n'.join(result)

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
