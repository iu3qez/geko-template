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


# ── Escaping stringa Typst ──────────────────────────────────────────
def _typ_str(s: str) -> str:
    """Escapa una stringa per un literal Typst "..." (senza le virgolette).
    Trasformazione totale su soli 4 caratteri: la ragione per cui la prosa
    non può più rompere la compilazione."""
    return (
        s.replace('\\', '\\\\')
         .replace('"', '\\"')
         .replace('\r', '')
         .replace('\t', '\\t')
         .replace('\n', '\\n')
    )


# ── Helper immagini (path remap + media library nomi nudi) ──────────
def _is_bare_filename(path: str) -> bool:
    return (
        not path.startswith('/')
        and not path.startswith('data:')
        and '://' not in path
        and '/' not in path
    )


def _remap_path(path: str, image_base: Optional[str]) -> str:
    if path.startswith('/uploads/'):
        return '/data' + path
    if image_base and _is_bare_filename(path):
        return f"{image_base}/{path}"
    return path


def _parse_width(attrs: Optional[str]) -> Optional[str]:
    if not attrs:
        return None
    m = re.search(r'width=(\d+%?)', attrs)
    return m.group(1) if m else None


def _render_figura(alt: str, path: str, attrs: Optional[str],
                   image_base: Optional[str]) -> str:
    width = _parse_width(attrs)
    parts = [f'"{_typ_str(_remap_path(path, image_base))}"']
    if alt:
        parts.append(f'didascalia: "{_typ_str(alt)}"')
    if width:
        parts.append(f'larghezza: {width}')
    return f'#figura({", ".join(parts)})'


def _render_grid(images: list[tuple], image_base: Optional[str]) -> str:
    cells = []
    for alt, path, _attrs in images:
        fig = f'figure(image("{_typ_str(_remap_path(path, image_base))}", width: 100%)'
        if alt:
            fig += f', caption: [{_typ_str(alt)}]'
        fig += ')'
        cells.append(fig)
    if len(cells) % 2 == 1:
        cells[-1] = f'grid.cell(colspan: 2, {cells[-1]})'
    out = [
        '#grid(',
        '  columns: (1fr, 1fr),',
        '  column-gutter: 8pt,',
        '  row-gutter: 8pt,',
    ]
    out.extend(f'  {c},' for c in cells)
    out.append(')')
    return '\n'.join(out)


def _render_cmarker(md_text: str, label_prefix: str) -> str:
    return (
        f'#cmarker.render("{_typ_str(md_text)}", '
        f'h1-level: 2, scope: geko-md-scope, label-prefix: "{label_prefix}")'
    )


# ── Rendering dei segmenti ──────────────────────────────────────────
def render_segments(md: str, image_base: Optional[str] = None) -> list[tuple[Segment, str]]:
    """Ritorna [(segmento, typst)] preservando l'ordine. Usato anche dalla
    diagnostica errori per-segmento (ogni typst è compilabile isolatamente)."""
    out: list[tuple[Segment, str]] = []
    for idx, seg in enumerate(segment_markdown(md)):
        if seg.kind == "prose":
            typ = _render_cmarker(seg.text, f"seg{idx}-")
        elif seg.kind == "box":
            inner = _render_cmarker(seg.text, f"box{idx}-")
            titolo = _typ_str(seg.titolo)
            typ = (
                f'#box-evidenza(titolo: "{titolo}", tipo: "{seg.tipo}")'
                f'[{inner}]'
            )
        elif seg.kind == "images":
            if len(seg.images) == 1:
                typ = _render_figura(*seg.images[0], image_base=image_base)
            else:
                typ = _render_grid(seg.images, image_base)
        else:  # pragma: no cover
            typ = ""
        out.append((seg, typ))
    return out


def render_article_body(md: str, image_base: Optional[str] = None) -> str:
    """Renderizza il corpo di un articolo in Typst (concatenazione dei segmenti)."""
    return '\n\n'.join(typ for _seg, typ in render_segments(md, image_base))
