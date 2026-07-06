"""
Rendering Markdown → Typst per il GEKO Magazine, basato su cmarker.

Il corpo dell'articolo è spezzato da un segmenter a livello di riga in:
  - prosa    → #cmarker.render(...) (parser CommonMark, escaping corretto)
  - box      → #box-evidenza(...)[#cmarker.render(corpo)]  (GitHub-alert)
  - immagini → #figura / #grid (righe di sole immagini)

La prosa viaggia come stringa Typst escaped: niente più "unclosed delimiter".
"""

import re
from dataclasses import dataclass, field
from typing import Optional

# Alert GitHub: "> [!TIPO] Titolo"
_ALERT_RE = re.compile(
    r'^\s*>\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*(.*)$',
    re.IGNORECASE,
)
# Alt text con un livello di [parentesi] annidate, path, e {attributi} opzionali
_IMG_RE = re.compile(
    r'!\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)]+)\)(?:\{([^}]+)\})?'
)


@dataclass
class Segment:
    kind: str                 # "prose" | "box" | "images"
    start_line: int           # 0-based inclusive (riga nel markdown originale)
    end_line: int             # 0-based inclusive
    text: str = ""            # prose: markdown grezzo | box: corpo markdown
    titolo: str = ""          # box
    tipo: str = ""            # box: note|tip|warning|important|caution
    images: list = field(default_factory=list)  # images: [(alt, path, attrs)]


def _parse_image_line(line: str) -> Optional[list[tuple]]:
    """Se la riga è composta SOLO da una o più immagini, ritorna la lista di
    (alt, path, attrs); altrimenti None."""
    stripped = line.strip()
    if not stripped.startswith('!['):
        return None
    images = []
    pos = 0
    while pos < len(stripped):
        m = _IMG_RE.match(stripped, pos)
        if not m:
            return None
        images.append((m.group(1), m.group(2), m.group(3)))
        pos = m.end()
        while pos < len(stripped) and stripped[pos] in ' \t':
            pos += 1
    return images


def segment_markdown(md: str) -> list[Segment]:
    """Spezza il markdown in segmenti prosa / box / immagini, a livello di riga."""
    lines = md.split('\n')
    segments: list[Segment] = []
    prose_buf: list[str] = []
    prose_start = 0

    def flush_prose(end_line: int):
        nonlocal prose_buf, prose_start
        if prose_buf:
            segments.append(Segment(
                kind="prose",
                start_line=prose_start,
                end_line=end_line,
                text='\n'.join(prose_buf),
            ))
            prose_buf = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # --- Alert GitHub -> box ---
        m = _ALERT_RE.match(line)
        if m:
            flush_prose(i - 1)
            start = i
            tipo = m.group(1).lower()
            titolo = m.group(2).strip()
            body: list[str] = []
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith('>'):
                body.append(re.sub(r'^\s*>\s?', '', lines[i]))
                i += 1
            segments.append(Segment(
                kind="box",
                start_line=start,
                end_line=i - 1,
                text='\n'.join(body).strip('\n'),
                titolo=titolo,
                tipo=tipo,
            ))
            prose_start = i
            continue

        # --- Run di righe di sole immagini -> figura/grid ---
        imgs = _parse_image_line(line)
        if imgs is not None:
            flush_prose(i - 1)
            start = i
            group = list(imgs)
            i += 1
            while i < len(lines):
                more = _parse_image_line(lines[i])
                if more is None:
                    break
                group.extend(more)
                i += 1
            segments.append(Segment(
                kind="images",
                start_line=start,
                end_line=i - 1,
                images=group,
            ))
            prose_start = i
            continue

        # --- Prosa ---
        if not prose_buf:
            prose_start = i
        prose_buf.append(line)
        i += 1

    flush_prose(len(lines) - 1)
    return segments
