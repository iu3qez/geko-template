# Rendering Markdown→PDF robusto via cmarker — Design

Data: 2026-07-06

## Problema

Generando un numero dalla UI si ottiene l'errore Typst **`unclosed delimiter`**,
mostrato grezzo e non attribuibile a un articolo/riga.

La causa è **strutturale**, non un singolo carattere. `converter.py`
(`MarkdownToTypstConverter`) è un traduttore markup scritto a mano che emette la
prosa nel *markup mode* di Typst escapando **solo `*`**
(`_escape_lone_asterisks`). Ogni altro carattere speciale di Typst passa
verbatim e rompe la compilazione. Verificato compilando i casi reali:

| Testo nell'articolo | Errore Typst |
|---|---|
| `5$ per il kit` | **unclosed delimiter** (apre math mode) |
| `` `comando` `` inline (backtick singolo, non fence) | **unclosed raw text** |
| `pippo_pluto`, `_enfasi` spaiata | **unclosed delimiter** |
| `#radio`, `canale #3` | unknown variable |

In più `magazines.py:329` (`except Exception: return {"error": str(e)}`)
restituisce il messaggio grezzo del compilatore, senza dire **quale articolo**
né **quale riga**.

## Obiettivo reale

Rendere il rendering markdown→PDF **robusto per costruzione** (non a forza di
rattoppi di escaping) e **diagnostico** (errori attribuibili). La strada
markdown→typst è corretta; è l'implementazione a mano a essere fragile.

## Decisione architetturale: **Segmenter + cmarker**

Sostituire il traduttore markup a mano con un rendering markdown che avviene
**dentro Typst** tramite [`cmarker`](https://typst.app/universe/package/cmarker/)
(transpiler CommonMark→Typst, parser Rust `pulldown-cmark` compilato in WASM).
L'escaping dei delimitatori è corretto *per costruzione*: la classe
`unclosed delimiter` da prosa sparisce.

### Perché non solo "indurire il converter attuale"
Aggiungere escaping di *tutti* i caratteri speciali in markup mode interagisce
male con i pass emphasis (regex a più passate su una macchina a stati per riga):
è la strada "continuare a rattoppare i sintomi". cmarker sposta il parsing su un
parser CommonMark maturo e testato.

### Perché non Pandoc
Writer Typst di Pandoc è maturo ma aggiunge un **binario esterno** nell'immagine
Docker e le convenzioni GEKO custom richiederebbero filtri Lua. cmarker resta
**tutto dentro la compilazione Typst** (single-step, nessun binario nuovo).

## Pipeline

Un nuovo modulo `md_render.py` sostituisce `MarkdownToTypstConverter`. Produce
Typst il cui corpo articolo è reso da cmarker. Un **segmenter a livello di riga**
(mai a livello di carattere → **non può corrompere la prosa**) spezza il corpo
dell'articolo in una lista ordinata di segmenti:

| Segmento | Riconoscimento (per riga) | Output Typst |
|---|---|---|
| **prosa** | tutto ciò che non è box/immagine | `#cmarker.render("…md…", h1-level: 2, scope: GEKO, label-prefix: "segN-")` |
| **box-evidenza** | blocco `> [!TIPO] Titolo` … | `#box-evidenza(titolo:"Titolo", tipo:"note")[#cmarker.render("corpo", label-prefix:"boxN-")]` |
| **immagini** | run di righe *solo* `![](...)` | 1 → `#figura(...)` · N → `#grid(…figure…)`, con `{width=N%}` |

- La prosa (top-level **e** dentro i box, via cmarker annidato con
  `label-prefix` univoco per evitare collisioni di label) passa **tutta** da
  cmarker.
- Il markdown viaggia come **stringa Typst escaped**: la sola trasformazione è
  escapare `\` e `"` (e i newline come `\n`). È un escaping **totale e sicuro**
  su due soli caratteri — la ragione per cui il bug muore. NON si tocca la
  semantica markdown.
- I segmenti prosa/box/immagini sono emessi nell'ordine originale così il flusso
  del testo è preservato.

### Metadati (titolo/sottotitolo/autore)
Restano **campi strutturati** del DB, emessi da `generate_article_typst` /
builder **attorno** al corpo (`= Titolo`, `#sottotitolo-sezione`, `#autore`,
`#separatore`). Non sono sintassi markdown → nessun impatto.

## Stile GEKO (via `scope` + show-rule, prosa intatta)

cmarker genera markup Typst e lo valuta in uno `scope`. Aggancio dello stile
GEKO senza toccare la prosa:

| Elemento | Meccanismo | Note (verificate su sorgente cmarker) |
|---|---|---|
| Link | `scope: (link: (dest, body) => link-geko(dest, testo: body))` | cmarker emette `#link("url")[body]` (`lib.rs:342`) |
| Tabelle | `#show table` → look GEKO (header oro, bordi) | cmarker emette `#table(align:…, table.header(…), …)` nativo (`lib.rs:257`); si stila la table nativa, niente reroute a `tabella-geko` |
| Heading | opzione nativa `h1-level: 2` | markdown `#` → Typst `==`; titolo articolo resta `=` (`lib.rs:147`) |
| Immagini | `scope: (image: …→figura)` come **fallback** | le immagini reali le gestisce il segmenter; il fallback copre immagini dentro prosa |

## Convenzioni immagini

Motivazione: servono **tre taglie** — a piena larghezza distrae troppo per
schemi/figure piccole. Il controllo taglia non è esprimibile in CommonMark (il
`title` dell'immagine viene **scartato** da cmarker, `lib.rs:364`), ma il
segmenter gestisce già le righe-immagine per la griglia → la larghezza ci viaggia
dentro allo stesso passo, a costo ~zero.

| Cosa scrive l'autore | Risultato |
|---|---|
| `![Vetta](foto.jpg)` da sola | `#figura` a piena larghezza |
| `![Schema](s.png){width=60%}` | `#figura` ridotta, centrata (anti-distrazione) |
| 2+ righe `![](...)` consecutive | griglia 2 colonne (dispari → ultima full-row) |

- Path remap e media library **invariati**: `/uploads/…`→`/data/uploads/…`;
  nomi-file nudi risolti via `image_base` (`article_ops.article_image_base`).
- La grammatica delle annotazioni `{...}` è **estensibile**: `{width=N%}` in v1;
  `{inline width=50 align=left|right|center}` **riservata** ma non implementata.

### Fase 2 (fuori da questo spec)
Due feature rimandate a fast-follow dopo la verifica del core in produzione:

1. **Immagine flottante** — `{inline …}` → `wrap-content` di
   [`wrap-it:0.1.1`](https://typst.app/universe/package/wrap-it) (testo che
   scorre attorno). È l'**unica** modalità che accoppia immagine + testo seguente
   (richiede cattura del paragrafo successivo + cmarker annidato). Oggi usata da
   **0/172** immagini. Grammatica già riservata nel parser.
2. **Formule LaTeX** — cmarker ha già `ENABLE_MATH` + callback `math:`; si abilita
   con `math: (block, src) => mitex(src)` (package
   [`mitex`](https://typst.app/universe/package/mitex), da vendorizzare offline).
   Cablaggio ~mezza giornata. Tenuta OFF nel v1 per un **tradeoff sul `$`**: con
   math OFF cmarker escapa *ogni* `$` (→ "30$" sempre sicuro, parte del fix bug);
   con math ON le coppie `$…$` diventano math. Se attivata, valutare opt-in
   per-articolo. `mitex` copre un sottoinsieme di LaTeX.

## Admonition (GitHub-alert)

Sintassi: `> [!TIPO] Titolo` (standard GitHub/Obsidian/VS Code), corpo su righe
`>` successive.

```markdown
> [!WARNING] Attenzione alla batteria
> In portatile QRP porta sempre una batteria di scorta.
> Il **freddo** riduce la capacità del 20-30%.
```

Tipi mappati agli stili `box-evidenza`: `NOTE | TIP | WARNING | IMPORTANT |
CAUTION`. La funzione template attuale è `box-evidenza(titolo: none, contenuto)`
**senza** parametro tipo → va **estesa** con un parametro `tipo`/`stile` (colore
bordo/icona per ciascun tipo alert), retro-compatibile (default = stile attuale).
**cmarker NON gestisce nativamente gli alert** (verificato: `lib.rs:195`
scarta il `BlockQuoteKind`; `lib.rs:68` non abilita `ENABLE_GFM` → `[!NOTE]`
arriva come testo letterale). Quindi il **segmenter** riconosce il blocco a
livello di riga e ne rende il corpo con cmarker annidato. La scelta di sintassi
è editoriale (standard/familiare); il costo tecnico è identico a `!!!`.

## Error handling

- **Happy path** (`POST /{magazine_id}/build`): invariato — build completo.
- **Su fallimento**: attribuzione **a livello di segmento**. Il segmenter
  conosce il range di righe markdown originali di ogni segmento (prosa/box/
  immagini): su errore si compilano i segmenti isolatamente per individuare
  quello che fallisce e riportarne il **range di righe** del markdown. Risposta
  strutturata:
  ```json
  {"status":"error","errori":[
    {"articolo_id":7,"titolo":"…","segmento":"box","righe":[41,45],"errore":"…"}
  ]}
  ```
  La UI mostra *"Articolo «Titolo», box alle righe 41–45: <messaggio>"* invece di
  `unclosed delimiter` nudo.
- Fattibile senza dipendenze nuove perché **il segmenter è nostro** (possediamo i
  range di riga). Con cmarker gran parte degli errori di delimitatore da prosa
  sparisce; i residui sono strutturali (path immagine errato, alert malformato) →
  l'attribuzione per-segmento porta praticamente sul blocco colpevole.
- **Non in scope**: riga/colonna *esatta* dentro un segmento di prosa — Typst
  riporta la posizione nel Typst generato da cmarker (WASM), che non espone un
  sourcemap verso gli offset del markdown; richiederebbe patchare cmarker in
  Rust, sproporzionato. Il livello-segmento è il punto dolce.

## Docker offline

La compilazione gira nel container prod **senza rete**. cmarker (e wrap-it in
fase 2) vanno **vendorizzati** nell'immagine: copiare i pacchetti nel namespace
`@local` di Typst (o pre-popolare la cache pacchetti) e referenziarli in modo
risolvibile offline. Modifica a `Dockerfile` / immagine + verifica che
`typst.compile` risolva il pacchetto senza accesso a `packages.typst.org`.

## Migrazione (materiale ridotto: 18 articoli, 2 numeri)

- **1 articolo** usa `!!!` (art. 13) → riscrivere a `> [!TIPO]`.
- **`contenuto_typ` deprecato come input di build**: il build renderizza
  **sempre** da `contenuto_md` via la nuova pipeline. I `.typ` esistenti (5
  articoli) sono output del vecchio converter, potenzialmente già buggati. Si
  rimuove il doppio percorso `if article.contenuto_typ` in `magazines.py:259`.
  (Valutare se svuotare/ignorare la colonna; non necessariamente droppare lo
  schema.)
- **`anteprima_typst`** (MCP): continua a restituire il Typst generato, ora
  cmarker-based (`markdown_preview` in `mcp/conventions.py` aggiornato).

## Componenti e confini

| Unità | Responsabilità | Dipende da |
|---|---|---|
| `md_render.py` — **segmenter** | spezza il corpo md in prosa/box/immagini a livello di riga; emette Typst con `cmarker.render` + `box-evidenza`/`figura`/`grid`; escaping stringa totale | — |
| `template.typ` — **scope GEKO + show-rule** | `link`→`link-geko`, `#show table`, **estendere `box-evidenza` con param `tipo`** (stile per alert) | cmarker, wrap-it (fase 2) |
| `builder.py` | invariato salvo import cmarker + rendering da `md_render` | `md_render`, `template.typ` |
| `magazines.py` `/build` | probe per-articolo + risposta errori strutturata; niente più `contenuto_typ` | `md_render`, `builder` |
| `mcp/conventions.py` | `CONVENZIONI` aggiornate (nuove convenzioni) + `markdown_preview` cmarker-based | `md_render` |
| Dockerfile | vendoring pacchetti Typst offline | — |
| Articolo-esempio canonico | mostra tutti i tag → base di `guida://convenzioni` + sample | — |

## Test

- **Unit** sul segmenter: prosa pura, blocco `> [!TIPO]`, run immagini
  (singola/multipla/dispari), `{width=N%}`, interleaving prosa/box/immagini,
  escaping di `\` e `"` nelle stringhe.
- **Regressione golden**: i **18 articoli reali** dal DB devono **compilare a
  PDF** senza errori (corpus di regressione già disponibile). Include i casi che
  oggi rompono (`$`, backtick inline, `_`, `#parola`).
- **Error handling**: articolo volutamente malformato → il `/build` risponde con
  `errori[].articolo_id` corretto.

## Deliverable extra

**Articolo-esempio canonico** che mostra ogni tag/convenzione (heading, enfasi,
link, liste, quote, code, tabella, tutti i tipi di box, figura singola/width,
griglia). Diventa il testo di `guida://convenzioni` (MCP) e un sample compilabile
usato anche come smoke-test.

## Non-goal (v1)

- Immagine flottante `{inline}` → **fase 2**.
- Supporto math LaTeX (cmarker `math:` callback + `mitex`) → **fase 2** (tradeoff
  `$`, vedi sopra).
- Mapping errore→**riga/colonna esatta** del markdown (l'attribuzione a livello
  di *segmento* È in scope v1; l'esatta no — niente sourcemap da cmarker).
- Autolink di URL nudi non racchiusi (cmarker senza GFM non li autolinka; le
  convenzioni useranno `[testo](url)` o `<url>`). Comportamento documentato.
