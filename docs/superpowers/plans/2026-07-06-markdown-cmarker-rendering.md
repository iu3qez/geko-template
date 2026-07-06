# Rendering Markdown→PDF via cmarker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sostituire il converter Markdown→Typst fatto a mano (fragile, causa `unclosed delimiter`) con un rendering CommonMark robusto via cmarker, mantenendo lo stile GEKO e aggiungendo errori attribuibili per-segmento.

**Architecture:** Un segmenter Python a livello di riga spezza il corpo articolo in prosa / box-evidenza / immagini. La prosa (anche dentro i box) è renderizzata **dentro Typst** da `cmarker.render` (parser CommonMark Rust/WASM), passata come stringa Typst escaped (solo `\ " \n \t`) → la classe `unclosed delimiter` da prosa sparisce per costruzione. Lo stile GEKO si inietta via `scope` + show-rule. Immagini e box restano Typst nativo (`#figura`/`#grid`/`#box-evidenza`).

**Tech Stack:** Python 3 (FastAPI, SQLAlchemy async), Typst via `typst` (typst-py 0.15.0), package `@preview/cmarker:0.1.10` vendorizzato offline, pytest (asyncio_mode=auto).

## Global Constraints

- Package Typst pinnato: **`@preview/cmarker:0.1.10`** (richiede compiler 0.15.0 = typst-py installato). Import nei doc generati: `#import "@preview/cmarker:0.1.10": *`.
- Ogni `typst.compile(...)` DEVE ricevere `package_path=<PKG_PATH>` dove `PKG_PATH = WEBAPP_DIR / "typst" / "packages"`.
- Markdown embeddato come **stringa Typst literal**: escapare `\`→`\\`, `"`→`\"`, newline→`\n`, tab→`\t`, e rimuovere `\r`. Nessun'altra trasformazione della semantica markdown.
- Heading del corpo articolo: `cmarker.render(..., h1-level: 2)` (il titolo articolo resta `=` livello 1, emesso dal wrapper).
- Tipi alert box: `note | tip | warning | important | caution` (lowercase).
- Lingua: italiano per UI/commenti/convenzioni, inglese per codice.
- Commit: **niente trailer `Co-Authored-By`** (regola utente globale).
- Test con `.venv` locale: `cd webapp && source .venv/bin/activate` già configurato; eseguire `python -m pytest` (config in `pytest.ini`, asyncio_mode=auto).

---

## File Structure

- **Create** `webapp/typst/packages/preview/cmarker/0.1.10/{lib.typ,plugin.wasm,typst.toml,LICENSE}` — package cmarker vendorizzato (offline).
- **Create** `webapp/app/services/md_render.py` — segmenter + rendering Typst (sostituisce il ruolo di `MarkdownToTypstConverter`).
- **Modify** `template.typ` — estende `box-evidenza` con `tipo`; aggiunge `geko-md-scope`; aggiunge styling tabelle in `geko-magazine`.
- **Modify** `webapp/app/services/builder.py` — import cmarker nel doc generato + `package_path` in `typst.compile`.
- **Modify** `webapp/app/routes/api/magazines.py` — usa `md_render`, elimina il ramo `contenuto_typ`, aggiunge attribuzione errori per-segmento.
- **Modify** `webapp/app/mcp/conventions.py` — `CONVENZIONI` aggiornate + `markdown_preview` via `md_render`.
- **Create** `webapp/app/services/esempio_convenzioni.md` — articolo-esempio canonico (base della guida).
- **Modify** `webapp/Dockerfile` (+ verificare `docker-compose*.yml`) — includere `typst/packages` nell'immagine.
- **Create** `webapp/tests/test_md_render.py` — unit segmenter + escaping + compile.
- **Create** `webapp/tests/test_build_regression.py` — compile di tutti gli articoli reali.
- **Remove** (task finale) `webapp/app/services/converter.py` + export in `__init__.py`; portare i test `test_converter_grid.py` / `test_converter_image_base.py`.

---

## Task 1: Vendorizzare il package cmarker (offline)

**Files:**
- Create: `webapp/typst/packages/preview/cmarker/0.1.10/lib.typ` (+ `plugin.wasm`, `typst.toml`, `LICENSE`)
- Test: `webapp/tests/test_cmarker_vendored.py`

**Interfaces:**
- Produces: package risolvibile come `@preview/cmarker:0.1.10` passando `package_path=WEBAPP_DIR/"typst"/"packages"` a `typst.compile`.

- [ ] **Step 1: Scaricare ed estrarre il package pubblicato (include il `plugin.wasm` compilato)**

```bash
cd webapp
mkdir -p typst/packages/preview/cmarker/0.1.10
curl -fsSL "https://packages.typst.org/preview/cmarker-0.1.10.tar.gz" \
  | tar xz -C typst/packages/preview/cmarker/0.1.10
ls typst/packages/preview/cmarker/0.1.10
# Atteso: LICENSE  README.md  lib.typ  plugin.wasm  typst.toml
```

- [ ] **Step 2: Scrivere il test che compila offline importando cmarker vendorizzato**

```python
# webapp/tests/test_cmarker_vendored.py
from pathlib import Path
import typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"


def test_cmarker_renders_offline(tmp_path):
    doc = tmp_path / "doc.typ"
    doc.write_text(
        '#import "@preview/cmarker:0.1.10": *\n'
        '#set page(width: 12cm, height: auto)\n'
        # casi che oggi rompono il vecchio converter:
        '#render("Costo 5$ per il file `pippo_pluto`, con _enfasi_, #radio e **grassetto**.")\n',
        encoding="utf-8",
    )
    pdf = typst.compile(str(doc), package_path=str(PKG_PATH))
    assert isinstance(pdf, (bytes, bytearray)) and len(pdf) > 1000
```

- [ ] **Step 3: Eseguire il test — deve passare (prova che il vendoring risolve offline e che i caratteri speciali non rompono)**

Run: `cd webapp && python -m pytest tests/test_cmarker_vendored.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add webapp/typst/packages/preview/cmarker/0.1.10 webapp/tests/test_cmarker_vendored.py
git commit -m "feat(typst): vendorizza package cmarker 0.1.10 per rendering offline"
```

---

## Task 2: Estendere `template.typ` (box tipo, scope GEKO, tabelle)

**Files:**
- Modify: `template.typ` (box-evidenza ~84-99; nuove definizioni dopo `figura`; show-rule in `geko-magazine`)
- Test: `webapp/tests/test_template_smoke.py`

**Interfaces:**
- Produces:
  - `box-evidenza(titolo: none, tipo: "note", contenuto)` — retro-compatibile (chiamate senza `tipo` invariate).
  - `geko-md-scope` — dizionario scope per `cmarker.render` (`link`→`link-geko`, `image`→`figura`).
  - styling tabelle native (cmarker) dentro `geko-magazine`.

- [ ] **Step 1: Estendere `box-evidenza` con parametro `tipo` e mappa colori**

Sostituire `template.typ:84-99` con:

```typst
// Colori bordo/titolo per tipo di alert (GitHub-style)
#let _alert-colori = (
  note:      (bordo: geko-gold,        titolo: geko-magenta),
  tip:       (bordo: rgb("#2E7D32"),   titolo: rgb("#2E7D32")),
  warning:   (bordo: rgb("#ED6C02"),   titolo: rgb("#ED6C02")),
  important: (bordo: geko-magenta,     titolo: geko-magenta),
  caution:   (bordo: rgb("#D32F2F"),   titolo: rgb("#D32F2F")),
)

#let box-evidenza(titolo: none, tipo: "note", contenuto) = {
  let c = _alert-colori.at(tipo, default: _alert-colori.note)
  block(
    width: 100%,
    fill: geko-light,
    inset: 12pt,
    radius: 3pt,
    stroke: 0.5pt + c.bordo,
    [
      #if titolo != none and titolo != "" {
        text(weight: "bold", fill: c.titolo, size: 11pt)[#titolo]
        v(0.4em)
      }
      #contenuto
    ]
  )
}
```

- [ ] **Step 2: Aggiungere `geko-md-scope` subito dopo la funzione `figura` (dopo `template.typ:683`)**

```typst
// ============================================
// SCOPE per cmarker.render: reindirizza gli elementi markdown
// alle funzioni di stile GEKO senza toccare la prosa.
// ============================================

#let geko-md-scope = (
  // Link markdown -> #link-geko. dest può essere una label (anchor interni): in
  // quel caso si usa il link nativo.
  link: (dest, body) => if type(dest) == str {
    link-geko(dest, testo: body)
  } else {
    link(dest, body)
  },
  // Fallback per immagini dentro la prosa (le immagini "da sole" le gestisce il
  // segmenter Python emettendo #figura/#grid direttamente).
  image: (src, alt: none, ..args) => figura(src, didascalia: alt),
)
```

- [ ] **Step 3: Aggiungere lo styling delle tabelle native dentro `geko-magazine`**

Individuare in `geko-magazine` il blocco `set heading(numbering: none)` (≈ `template.typ:...`) e subito dopo aggiungere:

```typst
  // Tabelle da markdown (cmarker emette #table nativo) con look GEKO
  set table(
    fill: (x, y) => if y == 0 { geko-gold } else if calc.odd(y) { geko-light } else { white },
    stroke: 0.5pt + geko-dark.lighten(60%),
    inset: 6pt,
  )
  show table.cell.where(y: 0): set text(fill: white, weight: "bold", size: 9pt)
  show table: set text(size: 9pt)
```

- [ ] **Step 4: Scrivere lo smoke test del template**

```python
# webapp/tests/test_template_smoke.py
from pathlib import Path
import typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"


def test_box_evidenza_tipi_e_scope(tmp_path):
    doc = tmp_path / "doc.typ"
    doc.write_text(
        f'#import "{REPO_DIR / "template.typ"}": *\n'
        '#set page(width: 12cm, height: auto)\n'
        '#box-evidenza(titolo: "T", tipo: "warning")[corpo]\n'
        '#box-evidenza(titolo: "Vecchia")[retro-compatibile]\n'
        '#assert(type(geko-md-scope) == dictionary)\n',
        encoding="utf-8",
    )
    pdf = typst.compile(str(doc), root=str(REPO_DIR), package_path=str(PKG_PATH))
    assert len(pdf) > 1000
```

- [ ] **Step 5: Eseguire il test — deve passare**

Run: `cd webapp && python -m pytest tests/test_template_smoke.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add template.typ webapp/tests/test_template_smoke.py
git commit -m "feat(template): box-evidenza per tipo alert + geko-md-scope + tabelle markdown"
```

---

## Task 3: Segmenter (`md_render.segment_markdown`)

**Files:**
- Create: `webapp/app/services/md_render.py`
- Test: `webapp/tests/test_md_render.py`

**Interfaces:**
- Produces:
  - `@dataclass Segment(kind: str, start_line: int, end_line: int, text: str = "", titolo: str = "", tipo: str = "", images: list = [])` — `kind ∈ {"prose","box","images"}`; righe 0-based inclusive.
  - `segment_markdown(md: str) -> list[Segment]`

- [ ] **Step 1: Scrivere i test del segmenter**

```python
# webapp/tests/test_md_render.py
from app.services.md_render import segment_markdown, Segment


def test_prosa_semplice_un_segmento():
    segs = segment_markdown("Riga uno\nRiga due")
    assert len(segs) == 1
    assert segs[0].kind == "prose"
    assert segs[0].text == "Riga uno\nRiga due"
    assert (segs[0].start_line, segs[0].end_line) == (0, 1)


def test_alert_github_diventa_box():
    md = (
        "Intro\n"
        "\n"
        "> [!WARNING] Attenzione batteria\n"
        "> Porta una **scorta**.\n"
        "> Il freddo scarica.\n"
        "\n"
        "Coda"
    )
    segs = segment_markdown(md)
    kinds = [s.kind for s in segs]
    assert kinds == ["prose", "box", "prose"]
    box = segs[1]
    assert box.tipo == "warning"
    assert box.titolo == "Attenzione batteria"
    assert box.text == "Porta una **scorta**.\nIl freddo scarica."
    assert (box.start_line, box.end_line) == (2, 4)


def test_run_immagini_consecutive_un_segmento():
    md = "![a](a.png)\n![b](b.png)\ntesto"
    segs = segment_markdown(md)
    assert [s.kind for s in segs] == ["images", "prose"]
    assert segs[0].images == [("a", "a.png", None), ("b", "b.png", None)]
    assert (segs[0].start_line, segs[0].end_line) == (0, 1)


def test_immagine_singola_con_width():
    segs = segment_markdown("![Schema](s.png){width=60%}")
    assert segs[0].kind == "images"
    assert segs[0].images == [("Schema", "s.png", "width=60%")]


def test_blockquote_normale_resta_prosa():
    segs = segment_markdown("> solo una citazione\n> seconda riga")
    assert len(segs) == 1 and segs[0].kind == "prose"
```

- [ ] **Step 2: Eseguire i test — devono fallire (modulo assente)**

Run: `cd webapp && python -m pytest tests/test_md_render.py -v`
Expected: FAIL con `ModuleNotFoundError: app.services.md_render`

- [ ] **Step 3: Implementare dataclass + segmenter**

```python
# webapp/app/services/md_render.py
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
```

- [ ] **Step 4: Eseguire i test — devono passare**

Run: `cd webapp && python -m pytest tests/test_md_render.py -v`
Expected: PASS (5 test)

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/md_render.py webapp/tests/test_md_render.py
git commit -m "feat(md_render): segmenter markdown per riga (prosa/box/immagini) con range righe"
```

---

## Task 4: Rendering dei segmenti in Typst (escaping, figura/grid, box, prosa)

**Files:**
- Modify: `webapp/app/services/md_render.py`
- Test: `webapp/tests/test_md_render.py` (aggiunte)

**Interfaces:**
- Consumes: `Segment`, `segment_markdown` (Task 3).
- Produces:
  - `_typ_str(s: str) -> str` — escaping per stringa Typst literal (senza virgolette).
  - `render_segments(md: str, image_base: Optional[str] = None) -> list[tuple[Segment, str]]`
  - `render_article_body(md: str, image_base: Optional[str] = None) -> str`

- [ ] **Step 1: Aggiungere i test di rendering**

```python
# append a webapp/tests/test_md_render.py
from app.services.md_render import (
    _typ_str, render_article_body, render_segments,
)


def test_typ_str_escaping():
    assert _typ_str('a"b\\c') == 'a\\"b\\\\c'
    assert _typ_str('r1\nr2') == 'r1\\nr2'
    assert _typ_str('t\tx\r') == 't\\tx'


def test_render_prosa_usa_cmarker_con_dollaro_letterale():
    out = render_article_body("Costo 5$ e _enfasi_")
    assert '#cmarker.render(' in out
    assert 'h1-level: 2' in out
    assert 'scope: geko-md-scope' in out
    assert 'Costo 5$ e _enfasi_' in out  # embeddato, non trasformato


def test_render_box_annidato():
    md = "> [!TIP] Consiglio\n> testo **forte**"
    out = render_article_body(md)
    assert '#box-evidenza(titolo: "Consiglio", tipo: "tip")[' in out
    assert 'label-prefix:' in out  # cmarker annidato con prefix


def test_render_immagine_singola_con_width():
    out = render_article_body("![Schema](s.png){width=60%}")
    assert '#figura("s.png"' in out
    assert 'larghezza: 60%' in out


def test_render_griglia_due_immagini():
    out = render_article_body("![a](a.png)\n![b](b.png)")
    assert '#grid(' in out and 'columns: (1fr, 1fr)' in out


def test_render_image_base_nome_nudo():
    out = render_article_body("![x](foto.png)", image_base="/data/uploads/articoli/7")
    assert '"/data/uploads/articoli/7/foto.png"' in out


def test_render_segments_ritorna_range():
    segs = render_segments("Intro\n\n> [!NOTE] N\n> corpo")
    assert [s.kind for s, _ in segs] == ["prose", "box"]
    assert all(isinstance(typ, str) and typ for _, typ in segs)
```

- [ ] **Step 2: Eseguire — i nuovi test falliscono**

Run: `cd webapp && python -m pytest tests/test_md_render.py -k "typ_str or render_" -v`
Expected: FAIL (funzioni assenti)

- [ ] **Step 3: Implementare escaping, helper immagini e rendering**

Aggiungere in fondo a `webapp/app/services/md_render.py`:

```python
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
    parts = [f'"{_remap_path(path, image_base)}"']
    if alt:
        parts.append(f'didascalia: "{_typ_str(alt)}"')
    if width:
        parts.append(f'larghezza: {width}')
    return f'#figura({", ".join(parts)})'


def _render_grid(images: list[tuple], image_base: Optional[str]) -> str:
    cells = []
    for alt, path, _attrs in images:
        fig = f'figure(image("{_remap_path(path, image_base)}", width: 100%)'
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
```

- [ ] **Step 4: Eseguire i test — devono passare**

Run: `cd webapp && python -m pytest tests/test_md_render.py -v`
Expected: PASS (tutti)

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/md_render.py webapp/tests/test_md_render.py
git commit -m "feat(md_render): rendering segmenti in Typst (cmarker/figura/grid/box) + escaping totale"
```

---

## Task 5: Wrapper articolo (`generate_article_typst`) + compile-check integrato

**Files:**
- Modify: `webapp/app/services/md_render.py`
- Test: `webapp/tests/test_md_render.py` (aggiunte)

**Interfaces:**
- Consumes: `render_article_body` (Task 4).
- Produces: `generate_article_typst(titolo, sottotitolo, autore, nome, contenuto_md, image_base=None) -> str` — Typst completo di un articolo (`= Titolo`, sottotitolo, autore, corpo, `#separatore()`).

- [ ] **Step 1: Test del wrapper + compile end-to-end di un articolo**

```python
# append a webapp/tests/test_md_render.py
from pathlib import Path
import typst
from app.services.md_render import generate_article_typst

WEBAPP_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = WEBAPP_DIR.parent
PKG_PATH = WEBAPP_DIR / "typst" / "packages"


def test_generate_article_typst_struttura():
    out = generate_article_typst(
        titolo="Il mio articolo", sottotitolo="sub",
        autore="IK2ABC", nome="Mario",
        contenuto_md="Testo con 5$ e _enfasi_.",
    )
    assert out.startswith("= Il mio articolo")
    assert '#sottotitolo-sezione[sub]' in out
    assert '#autore("IK2ABC", nome: "Mario")' in out
    assert '#separatore()' in out


def test_articolo_completo_compila(tmp_path):
    body = generate_article_typst(
        titolo="Test", sottotitolo=None, autore=None, nome=None,
        contenuto_md=(
            "Costo 5$, file `pippo_pluto`, canale #3.\n\n"
            "> [!WARNING] Occhio\n> Testo **forte**.\n\n"
            "| A | B |\n| - | - |\n| 1 | 2 |\n\n"
            "![Foto](https://example.org/x.png)\n"
        ),
    )
    doc = tmp_path / "art.typ"
    doc.write_text(
        '#import "@preview/cmarker:0.1.10": *\n'
        f'#import "{REPO_DIR / "template.typ"}": *\n'
        '#show: geko-magazine.with(numero: "1", mese: "Luglio", anno: "2026")\n'
        + body,
        encoding="utf-8",
    )
    pdf = typst.compile(str(doc), root=str(REPO_DIR), package_path=str(PKG_PATH))
    assert len(pdf) > 1000
```

- [ ] **Step 2: Eseguire — falliscono (funzione assente)**

Run: `cd webapp && python -m pytest tests/test_md_render.py -k "generate_article or articolo_completo" -v`
Expected: FAIL

- [ ] **Step 3: Implementare il wrapper**

Aggiungere in fondo a `webapp/app/services/md_render.py`:

```python
def generate_article_typst(
    titolo: str,
    sottotitolo: Optional[str],
    autore: Optional[str],
    nome: Optional[str],
    contenuto_md: str,
    image_base: Optional[str] = None,
) -> str:
    """Articolo Typst completo: titolo (H1), sottotitolo, autore, corpo, separatore."""
    parts = [f'= {titolo}', '']
    if sottotitolo:
        parts.append(f'#sottotitolo-sezione[{sottotitolo}]')
    if autore:
        if nome:
            parts.append(f'#autore("{autore}", nome: "{nome}")')
        else:
            parts.append(f'#autore("{autore}")')
    parts.append('')
    parts.append(render_article_body(contenuto_md, image_base))
    parts.append('')
    parts.append('#separatore()')
    return '\n'.join(parts)
```

- [ ] **Step 4: Eseguire i test — devono passare**

Run: `cd webapp && python -m pytest tests/test_md_render.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/md_render.py webapp/tests/test_md_render.py
git commit -m "feat(md_render): wrapper generate_article_typst + compile end-to-end verificato"
```

---

## Task 6: Integrare `builder.py` (import cmarker + package_path)

**Files:**
- Modify: `webapp/app/services/builder.py` (`_generate_document` ~118-120; `build_magazine` compile ~93-95; add `PKG_PATH`)
- Test: `webapp/tests/test_build_regression.py` (smoke minimo qui; regressione piena in Task 9)

**Interfaces:**
- Consumes: package vendorizzato (Task 1), `md_render.generate_article_typst` (Task 5).
- Produces: `build_magazine(...)` che compila con cmarker offline.

- [ ] **Step 1: Aggiungere `PKG_PATH`, l'import cmarker nel doc, e `package_path` al compile**

In `webapp/app/services/builder.py`, dopo `OUTPUT_DIR = WEBAPP_DIR / "data" / "output"` aggiungere:

```python
PKG_PATH = WEBAPP_DIR / "typst" / "packages"
```

In `_generate_document`, dove costruisce l'header (attuale `parts.append('#import "../template.typ": *')`), anteporre l'import di cmarker:

```python
        # Import cmarker (rendering markdown) + template
        parts.append('#import "@preview/cmarker:0.1.10": *')
        parts.append('#import "../template.typ": *')
        parts.append('')
```

In `build_magazine`, sostituire la riga di compile:

```python
        pdf_bytes = typst.compile(
            str(typ_path), root=str(WEBAPP_DIR), package_path=str(PKG_PATH)
        )
```

- [ ] **Step 2: Scrivere lo smoke test del builder**

```python
# webapp/tests/test_build_regression.py
from app.services.builder import MagazineBuilder
from app.services.md_render import generate_article_typst


def test_build_magazine_minimo(tmp_path, monkeypatch):
    b = MagazineBuilder()
    art = generate_article_typst(
        titolo="Uno", sottotitolo=None, autore="IK2XYZ", nome=None,
        contenuto_md="Testo con 5$ e `codice` inline e _enfasi_.\n",
    )
    pdf_path = b.build_magazine(
        numero="99", mese="Luglio", anno="2026", articles_typst=[art],
    )
    assert pdf_path.exists() and pdf_path.stat().st_size > 1000
```

- [ ] **Step 3: Eseguire — deve passare**

Run: `cd webapp && python -m pytest tests/test_build_regression.py::test_build_magazine_minimo -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add webapp/app/services/builder.py webapp/tests/test_build_regression.py
git commit -m "feat(builder): import cmarker nel doc generato + package_path offline"
```

---

## Task 7: Route `/build` — md_render, niente `contenuto_typ`, errori per-segmento

**Files:**
- Modify: `webapp/app/routes/api/magazines.py` (`build_pdf` ~233-333)
- Test: `webapp/tests/test_build_errors.py`

**Interfaces:**
- Consumes: `md_render.generate_article_typst`, `md_render.render_segments`; `builder.MagazineBuilder` (per il probe isolato).
- Produces: risposta `/build`:
  - successo: `{"status":"success","pdf_url": "..."}` (invariato)
  - errore: `{"status":"error","errori":[{"articolo_id","titolo","segmento","righe","errore"}]}`

- [ ] **Step 1: Aggiungere in `builder.py` un helper di compile isolato per il probe**

In `MagazineBuilder` aggiungere:

```python
    def try_compile_snippet(self, typst_body: str) -> Optional[str]:
        """Compila un frammento isolato (import cmarker+template+show geko).
        Ritorna None se ok, oppure il messaggio d'errore Typst."""
        import tempfile
        doc = (
            '#import "@preview/cmarker:0.1.10": *\n'
            '#import "../template.typ": *\n'
            '#show: geko-magazine.with(numero: "0", mese: "Test", anno: "2026")\n'
            + typst_body
        )
        tmp = TYPST_DIR / "generated" / "_probe.typ"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(doc, encoding="utf-8")
        try:
            typst.compile(str(tmp), root=str(WEBAPP_DIR), package_path=str(PKG_PATH))
            return None
        except Exception as e:
            return str(e)
```

- [ ] **Step 2: Riscrivere il corpo di `build_pdf` — usare md_render, togliere il ramo `contenuto_typ`, e diagnosticare per-segmento sul fallimento**

Sostituire il blocco `try:` di `build_pdf` (da `articles_typst = []` fino al `return {"status":"success", ...}`) con la logica:

```python
    from ...services.md_render import generate_article_typst, render_segments

    # Prepara il Typst di ogni articolo SEMPRE dal markdown (niente contenuto_typ)
    articles_typst = []
    for article in magazine.articles:
        image_base = article_ops.article_image_base(article.id)
        art_typ = generate_article_typst(
            titolo=article.titolo,
            sottotitolo=getattr(article, "sottotitolo", None),
            autore=getattr(article, "autore", None),
            nome=getattr(article, "autore_nome", None),
            contenuto_md=article.contenuto_md or "",
            image_base=image_base,
        )
        articles_typst.append(art_typ)

    # ... (evidenze, copertina, config team/finale come prima) ...

    try:
        pdf_path = build_magazine_pdf(numero=magazine.numero, ... , articles_typst=articles_typst, ...)
    except Exception:
        # Diagnostica: individua articolo + segmento che non compila
        builder = MagazineBuilder()
        errori = []
        for article in magazine.articles:
            image_base = article_ops.article_image_base(article.id)
            for seg, typ in render_segments(article.contenuto_md or "", image_base):
                msg = builder.try_compile_snippet(typ)
                if msg:
                    errori.append({
                        "articolo_id": article.id,
                        "titolo": article.titolo,
                        "segmento": seg.kind,
                        "righe": [seg.start_line + 1, seg.end_line + 1],
                        "errore": msg,
                    })
        return {"status": "error", "errori": errori}

    magazine.stato = MagazineStatus.PUBBLICATO
    await db.commit()
    return {"status": "success", "pdf_url": f"/api/magazines/{magazine_id}/pdf"}
```

> Nota: `MagazineBuilder` e `build_magazine_pdf` sono già importati nella funzione; aggiungere `from ...services.builder import MagazineBuilder`. I nomi campo `sottotitolo/autore/autore_nome` usano `getattr` per tollerare l'assenza nel model (verificare i nomi reali in `models.py` e sostituirli se differiscono).

- [ ] **Step 3: Test dell'attribuzione errori per-segmento**

```python
# webapp/tests/test_build_errors.py
from app.services.builder import MagazineBuilder


def test_probe_isola_segmento_buono():
    b = MagazineBuilder()
    # figura verso file inesistente -> errore attribuibile a quel segmento
    msg = b.try_compile_snippet('#figura("/data/uploads/inesistente_xyz.png")')
    assert msg is not None and isinstance(msg, str)


def test_probe_prosa_valida_ok():
    b = MagazineBuilder()
    from app.services.md_render import render_segments
    segs = render_segments("Testo con 5$ e _enfasi_ e `codice`.")
    assert b.try_compile_snippet(segs[0][1]) is None
```

- [ ] **Step 4: Eseguire — devono passare**

Run: `cd webapp && python -m pytest tests/test_build_errors.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/builder.py webapp/app/routes/api/magazines.py webapp/tests/test_build_errors.py
git commit -m "feat(magazines): build da markdown via cmarker + errori attribuiti per-segmento"
```

---

## Task 8: MCP `conventions.py` — CONVENZIONI aggiornate + preview via md_render

**Files:**
- Modify: `webapp/app/mcp/conventions.py`
- Test: `webapp/tests/test_conventions.py` (aggiornare)

**Interfaces:**
- Consumes: `md_render.render_article_body`.
- Produces: `markdown_preview(md, articolo_id=None) -> str` (Typst cmarker-based); `CONVENZIONI` con la nuova sintassi.

- [ ] **Step 1: Riscrivere `markdown_preview` e la stringa `CONVENZIONI`**

In `webapp/app/mcp/conventions.py`:

```python
from ..services.article_ops import article_image_base
from ..services.md_render import render_article_body


def markdown_preview(md: str, articolo_id: Optional[int] = None) -> str:
    """Renderizza il Markdown GEKO in Typst (via cmarker) e lo restituisce."""
    image_base = article_image_base(articolo_id) if articolo_id is not None else None
    return render_article_body(md, image_base=image_base)
```

E aggiornare `CONVENZIONI` (sezione box e note figure), in particolare sostituire il blocco `!!!` con:

```
- Box evidenza (GitHub-alert): riga `> [!TIPO] Titolo`, poi il corpo su righe `>`.
  Tipi: NOTE, TIP, WARNING, IMPORTANT, CAUTION. Il corpo resta Markdown.

  > [!WARNING] Attenzione alla batteria
  > In portatile QRP porta sempre una batteria di scorta.
  > Il **freddo** riduce la capacità del 20-30%.

- Immagini: `![alt](file.png)` a piena larghezza; `{width=60%}` per una figura
  più piccola centrata; due o più immagini su righe consecutive → griglia 2 colonne.
- URL: usare `[testo](url)` o `<url>` (gli URL nudi non vengono più auto-linkati).
```

- [ ] **Step 2: Aggiornare i test delle convenzioni**

Sostituire in `webapp/tests/test_conventions.py` le asserzioni che verificavano il vecchio `#box-evidenza` da `!!!` con:

```python
from app.mcp.conventions import markdown_preview, CONVENZIONI


def test_preview_alert_diventa_box():
    out = markdown_preview("> [!TIP] Consiglio\n> corpo **forte**")
    assert '#box-evidenza(titolo: "Consiglio", tipo: "tip")[' in out


def test_convenzioni_menziona_github_alert():
    assert "[!WARNING]" in CONVENZIONI or "[!TIPO]" in CONVENZIONI
```

- [ ] **Step 3: Eseguire — devono passare**

Run: `cd webapp && python -m pytest tests/test_conventions.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add webapp/app/mcp/conventions.py webapp/tests/test_conventions.py
git commit -m "feat(mcp): convenzioni GitHub-alert + anteprima_typst via md_render/cmarker"
```

---

## Task 9: Regressione — tutti gli articoli reali compilano

**Files:**
- Create: `webapp/tests/fixtures/articoli_reali/` (dump `.md` degli articoli dal DB)
- Modify: `webapp/tests/test_build_regression.py` (aggiunta parametrizzata)

**Interfaces:**
- Consumes: `md_render.generate_article_typst`, `builder.MagazineBuilder.try_compile_snippet`.

- [ ] **Step 1: Esportare i markdown reali come fixture**

```bash
cd webapp
mkdir -p tests/fixtures/articoli_reali
.venv/bin/python - <<'PY'
import sqlite3, pathlib
con = sqlite3.connect("data/geko.db")
rows = con.execute(
    "SELECT id, contenuto_md FROM articles "
    "WHERE contenuto_md IS NOT NULL AND length(contenuto_md) > 0"
).fetchall()
d = pathlib.Path("tests/fixtures/articoli_reali")
for aid, md in rows:
    (d / f"art_{aid}.md").write_text(md, encoding="utf-8")
print("scritti", len(rows), "articoli")
PY
```

- [ ] **Step 2: Test di regressione parametrizzato (ogni articolo reale deve compilare)**

```python
# append a webapp/tests/test_build_regression.py
from pathlib import Path
import pytest
from app.services.builder import MagazineBuilder
from app.services.md_render import generate_article_typst

FIX = Path(__file__).parent / "fixtures" / "articoli_reali"


@pytest.mark.parametrize("md_file", sorted(FIX.glob("art_*.md")), ids=lambda p: p.stem)
def test_articolo_reale_compila(md_file):
    md = md_file.read_text(encoding="utf-8")
    body = generate_article_typst(
        titolo="Regressione", sottotitolo=None, autore=None, nome=None,
        contenuto_md=md,
    )
    msg = MagazineBuilder().try_compile_snippet(body)
    assert msg is None, f"{md_file.stem} non compila: {msg}"
```

- [ ] **Step 3: Eseguire — tutti gli articoli devono compilare**

Run: `cd webapp && python -m pytest tests/test_build_regression.py -v`
Expected: PASS per ogni `art_*` (se qualcuno fallisce per path immagine mancante, marcare quell'id come noto in Task 10, non è un bug del renderer).

- [ ] **Step 4: Commit**

```bash
git add webapp/tests/fixtures/articoli_reali webapp/tests/test_build_regression.py
git commit -m "test(regression): compile di tutti gli articoli markdown reali"
```

---

## Task 10: Migrazione dati — articolo con `!!!` → GitHub-alert

**Files:**
- Create: `webapp/scripts/migra_alert.py`

**Interfaces:**
- Consumes: DB `data/geko.db`.

- [ ] **Step 1: Script di migrazione idempotente `!!!` → `> [!TIPO]`**

```python
# webapp/scripts/migra_alert.py
"""Converte i box '!!!' del vecchio formato in GitHub-alert '> [!NOTE]'.
Idempotente: se non trova '!!!' non tocca nulla."""
import re
import sqlite3

BLOCK = re.compile(r'^!!!\s*(?:\w+\s*)?"([^"]*)"?\s*\n(.*?)^!!!\s*$',
                   re.MULTILINE | re.DOTALL)


def convert(md: str) -> str:
    def repl(m):
        titolo = m.group(1) or ""
        corpo = m.group(2).rstrip('\n')
        righe = '\n'.join('> ' + l if l.strip() else '>'
                          for l in corpo.split('\n'))
        return f'> [!NOTE] {titolo}\n{righe}\n'
    return BLOCK.sub(repl, md)


def main():
    con = sqlite3.connect("data/geko.db")
    rows = con.execute(
        "SELECT id, contenuto_md FROM articles WHERE contenuto_md LIKE '%!!!%'"
    ).fetchall()
    for aid, md in rows:
        new = convert(md)
        if new != md:
            con.execute("UPDATE articles SET contenuto_md=? WHERE id=?", (new, aid))
            print("migrato articolo", aid)
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Eseguire la migrazione e verificare col renderer**

```bash
cd webapp && .venv/bin/python scripts/migra_alert.py
# rigenera le fixture e rilancia la regressione
.venv/bin/python - <<'PY'
import sqlite3, pathlib
con = sqlite3.connect("data/geko.db")
d = pathlib.Path("tests/fixtures/articoli_reali")
for aid, md in con.execute("SELECT id, contenuto_md FROM articles WHERE contenuto_md IS NOT NULL AND length(contenuto_md)>0"):
    (d / f"art_{aid}.md").write_text(md, encoding="utf-8")
PY
python -m pytest tests/test_build_regression.py -v
```
Expected: PASS (incluso l'articolo migrato, ora con `> [!NOTE]`)

- [ ] **Step 3: Commit**

```bash
git add webapp/scripts/migra_alert.py webapp/tests/fixtures/articoli_reali
git commit -m "chore(data): migra box !!! a GitHub-alert + fixture aggiornate"
```

---

## Task 11: Articolo-esempio canonico + guida

**Files:**
- Create: `webapp/app/services/esempio_convenzioni.md`
- Modify: `webapp/app/mcp/conventions.py` (usare il file come base della guida) + `webapp/tests/test_build_regression.py`

**Interfaces:**
- Produces: un markdown che esercita ogni convenzione; usato come smoke-test e riferimento della guida.

- [ ] **Step 1: Scrivere l'articolo-esempio**

```markdown
<!-- webapp/app/services/esempio_convenzioni.md -->
# Sezione principale

Testo con **grassetto**, _corsivo_, `codice inline`, un [link](https://mountainqrp.it)
e caratteri che prima rompevano: prezzo 5$, canale #3, file `pippo_pluto`.

## Sottosezione

- primo
- secondo

1. uno
2. due

> [!NOTE] Nota informativa
> Contenuto **Markdown** con [link](https://example.com).

> [!WARNING] Attenzione
> Testo di avviso.

| Banda | MHz |
| ----- | --- |
| 40m   | 7   |
| 20m   | 14  |

![Schema stazione](https://example.org/schema.png){width=60%}

![Foto uno](https://example.org/a.png)
![Foto due](https://example.org/b.png)
```

- [ ] **Step 2: Test: l'esempio compila e copre i costrutti**

```python
# append a webapp/tests/test_build_regression.py
from app.services.md_render import render_article_body
from app.services.builder import MagazineBuilder

ESEMPIO = Path(__file__).resolve().parent.parent / "app" / "services" / "esempio_convenzioni.md"


def test_esempio_convenzioni_compila():
    md = ESEMPIO.read_text(encoding="utf-8")
    out = render_article_body(md)
    assert '#box-evidenza' in out and '#grid(' in out and '#figura(' in out
    assert MagazineBuilder().try_compile_snippet(out) is None
```

- [ ] **Step 3: Far puntare `CONVENZIONI` all'esempio (append del sorgente markdown)**

In `conventions.py`, dopo la stringa `CONVENZIONI`, aggiungere:

```python
import pathlib
_ESEMPIO = pathlib.Path(__file__).resolve().parent.parent / "services" / "esempio_convenzioni.md"
if _ESEMPIO.exists():
    CONVENZIONI += "\n\n## Esempio completo\n\n```markdown\n" + _ESEMPIO.read_text(encoding="utf-8") + "\n```\n"
```

- [ ] **Step 4: Eseguire i test**

Run: `cd webapp && python -m pytest tests/test_build_regression.py::test_esempio_convenzioni_compila tests/test_conventions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add webapp/app/services/esempio_convenzioni.md webapp/app/mcp/conventions.py webapp/tests/test_build_regression.py
git commit -m "docs(mcp): articolo-esempio canonico come guida convenzioni"
```

---

## Task 12: Docker offline + rimozione converter legacy

**Files:**
- Modify: `webapp/Dockerfile` (+ verificare `docker-compose.yml` / `docker-compose.prod.yml`)
- Remove: `webapp/app/services/converter.py`; export in `webapp/app/services/__init__.py`
- Remove/porta: `webapp/tests/test_converter_grid.py`, `webapp/tests/test_converter_image_base.py`

**Interfaces:**
- Consumes: nessuno nuovo; rimuove il vecchio converter dopo che tutti i call`er usano `md_render`.

- [ ] **Step 1: Verificare che `typst/packages` finisca nell'immagine**

Ispezionare `webapp/Dockerfile`: assicurarsi che `typst/` (che ora contiene `packages/`) sia copiato nell'immagine. Se il Dockerfile fa `COPY . .` o `COPY typst/ ./typst/`, è già incluso. Altrimenti aggiungere:

```dockerfile
COPY typst/ ./typst/
```

Aggiungere un commento nel Dockerfile:

```dockerfile
# Package Typst vendorizzati (cmarker) per compilazione offline: NON rimuovere
```

- [ ] **Step 2: Rimuovere i riferimenti al vecchio converter**

Controllare che nessun modulo importi più `converter`:

```bash
cd webapp && grep -rn "services.converter\|convert_markdown_to_typst\|MarkdownToTypstConverter\|from .converter\|import converter" app/ tests/
```
Expected: nessun risultato in `app/` (solo eventuali test converter da rimuovere).

Rimuovere da `webapp/app/services/__init__.py` le righe che esportano `convert_markdown_to_typst` / `MarkdownToTypstConverter`.

- [ ] **Step 3: Rimuovere converter e i suoi test dedicati**

```bash
cd webapp
git rm app/services/converter.py tests/test_converter_grid.py tests/test_converter_image_base.py
```

(La copertura grid/image_base è ora in `tests/test_md_render.py`, Task 4.)

- [ ] **Step 4: Suite completa verde**

Run: `cd webapp && python -m pytest -q`
Expected: PASS (nessun import rotto, nessun riferimento a converter)

- [ ] **Step 5: Commit**

```bash
git add webapp/Dockerfile webapp/app/services/__init__.py
git commit -m "chore: rimuove converter legacy, vendoring cmarker nell'immagine Docker"
```

---

## Self-Review (svolto in fase di scrittura)

**Spec coverage:** Segmenter+cmarker → Task 3-5; stile GEKO (scope/show/h1-level) → Task 2,4; immagini width/grid → Task 3-4; admonition GitHub-alert → Task 3-4,8; error handling per-segmento → Task 7; Docker offline → Task 1,12; migrazione `!!!`/`contenuto_typ` → Task 7,10; anteprima MCP → Task 8; test regressione 18 articoli → Task 9; articolo-esempio/guida → Task 11. **Fase 2 (flottante, math LaTeX)** esclusa come da spec.

**Type consistency:** `Segment` (Task 3) usato invariato in Task 4,7,9; `render_segments`/`render_article_body`/`generate_article_typst` firme coerenti tra Task 4,5,6,7,8,11; `try_compile_snippet` definita Task 7 e riusata Task 9,11; `PKG_PATH` definita Task 6 e riusata Task 7.

**Punti da verificare in esecuzione (non placeholder, ma dipendenze dal codice esistente):**
- Nomi campo del model `Article` per sottotitolo/autore/nome (Task 7 usa `getattr` con fallback; sostituire coi nomi reali da `models.py`).
- Forma esatta dell'header in `_generate_document` di `builder.py` (Task 6) e del blocco `try:` in `build_pdf` (Task 7) — seguire il codice attuale, i frammenti mostrano le sostituzioni chiave.
