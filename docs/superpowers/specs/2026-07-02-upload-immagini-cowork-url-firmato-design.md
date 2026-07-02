# Upload immagini da Cowork via URL firmato — Design

Data: 2026-07-02

## Problema

`crea_articolo` (MCP) converte `![alt](x.png)` in `#figura("x.png", …)`, ma non
esiste un canale pratico per **caricare i byte** di `x.png` sul server: la
compilazione Typst non trova il file e mostra un placeholder.

Il tool MCP `carica_immagine(contenuto_base64=…)` esiste già, ma il base64 come
argomento di una tool-call è impraticabile: per 7 PNG da decine/centinaia di KB
significa che *il modello* deve emettere 50k–240k caratteri esatti per figura.
Non è riproducibile in modo affidabile, né da un umano né da un agente.

## Obiettivo reale

Il flusso finale è **Claude Cowork**: gira sul desktop, ha i file immagine sul
proprio filesystem locale, ha shell + rete ("Claude Code power for knowledge
work"), e parla con Geko tramite il **connettore MCP** (OAuth 2.1 Scalekit).
Serve un canale binario **affidabile** (i byte non passano dal modello) e
**autenticabile** con ciò che Cowork già possiede.

## Vincoli di infrastruttura (accertati)

| Host | Auth | Autenticabile da curl headless? |
|------|------|---------------------------------|
| `geko.fabris.me` (webapp FastAPI) | Authentik (`chain-forwardAuth-authentik@file`, SSO browser) | ❌ SSO interattivo |
| `geko-mcp.fabris.me` (container `geko-mcp`, FastMCP) | Scalekit OAuth (JWT) sul solo endpoint `/mcp` | canale MCP di Cowork |

- Il container `geko-mcp` monta **solo** `./data` come `/app/data`: non vede il
  laptop di Cowork né i file della chat. Un parametro `percorso_file` che punti
  al filesystem di Cowork **non funzionerebbe mai** (filesystem separati) e, se
  scritto ingenuamente, aprirebbe una lettura di file arbitrari sul host.
  → **`percorso_file` è scartato.**
- L'upload web esistente (`POST /api/images`) rinomina i file con prefisso uuid
  (`{uuid}_{nome}`) e li scrive in `data/uploads/`, **non** in
  `data/uploads/articoli/{id}/` col nome esatto → non risolve le figure e sta
  dietro Authentik. → non riutilizzabile per questo flusso.
- Il token OAuth Scalekit del connettore MCP è gestito dal layer host di Cowork,
  **non** è esposto alla shell dell'agente → curl non può presentarlo.
- **Accertato via Context7**: le route `@mcp.custom_route` di FastMCP **non**
  sono protette dal middleware di auth ("This endpoint is not protected by
  authentication middleware"). Una route custom è quindi pubblica a livello
  OAuth: la sua autenticazione va implementata nel handler.

## Design scelto: URL firmato coniato via tool MCP

Due componenti sullo stesso processo `geko-mcp` (in-process, condividono il
volume `./data` e `article_ops`):

1. **Tool MCP `ottieni_upload_url`** — Cowork è già autenticato all'MCP via
   OAuth, quindi *questo* è il gate di autorizzazione. Il tool conia un URL
   firmato a scadenza breve per ciascun nome file e lo restituisce all'agente.
2. **Route custom pubblica `POST /upload/immagine`** — riceve il multipart da
   `curl -F`, **verifica la firma** (che è l'auth), e salva col nome esatto
   riusando `article_ops.save_article_image`.

L'auth vive nella firma HMAC, non in un secret statico dentro Cowork.

### Flusso end-to-end

```
Cowork ──(MCP, OAuth)──▶ ottieni_upload_url(articolo_id=7,
                                            nomi_file=["a.png","schema.svg", …])
        ◀── [{nome_file, url, scade_a}, …]         # URL firmati, uno per file

Cowork ──(curl -F file=@/local/a.png "<url a.png>")──▶ POST /upload/immagine
        route: verifica firma → save_article_image(7,"a.png",bytes,sovrascrivi=True)
        ◀── {nome_file:"a.png", url:"/uploads/articoli/7/a.png", bytes:34122}

Nel Markdown dell'articolo:  ![Schema](schema.svg)
build/anteprima: image_base = /data/uploads/articoli/7 → #figura risolve ✓
```

## Componenti

### 1. `app/mcp/upload_tokens.py` (nuovo)

Firma/verifica dei token, stdlib `hmac` + `hashlib` (nessuna nuova dipendenza).

- `SIGNING_KEY = os.environ["GEKO_UPLOAD_SIGNING_KEY"]` (vedi Config). Se
  assente → feature disattivata (tool solleva `ValueError`, route risponde 503),
  coerente con `build_auth()` che ritorna `None` se non configurato.
- `mint(articolo_id: int, nome_file: str, exp_epoch: int) -> str`
  - payload = `base64url(json({"aid":…, "name":…, "exp":…}))`
  - sig = `base64url(HMAC_SHA256(SIGNING_KEY, payload_bytes))`
  - token = `f"{payload}.{sig}"`
- `verify(token: str) -> dict` → `{"aid","name","exp"}` oppure solleva
  `ValueError` se: formato errato, `hmac.compare_digest` fallisce (confronto
  a tempo costante), o `exp` passato (scadenza).
- Il token **lega `nome_file`**: la route userà il nome dal token, non quello
  del multipart. Così Cowork può fare `curl -F file=@/qualsiasi/path.png` e il
  file viene salvato col nome canonico previsto nel Markdown.

Nota sull'orologio: `Date.now`/`time` a runtime va bene nel processo server
(non è un workflow deterministico); usare `int(time.time())`.

### 2. Tool MCP `ottieni_upload_url` (in `app/mcp/server.py`)

```python
@mcp.tool
async def ottieni_upload_url(
    articolo_id: int,
    nomi_file: list[str],
    scadenza_minuti: int = 15,
) -> list[dict]:
    """Conia URL di upload firmati per le immagini di un articolo.

    Cowork poi carica ogni file con:
      curl -F file=@<path-locale> "<url>"
    I byte non passano dal modello. Formati: PNG, JPG/JPEG, GIF, WEBP, SVG.
    Ritorna [{nome_file, url, scade_a}, …].
    """
```

Validazioni (fail-fast, prima che Cowork carichi):
- l'articolo esiste (`article_ops` / query su `Article`);
- ogni `nome_file` ha estensione in `ALLOWED_IMAGE_EXTENSIONS` e passa
  `_sanitize_nome_file` (no path/traversal);
- `scadenza_minuti` in un range ragionevole (es. 1–60);
- URL assoluto costruito da `MCP_PUBLIC_URL` +
  `/upload/immagine?token=<mint(...)>`.

### 3. Route custom `POST /upload/immagine` (in `app/mcp/server.py`)

```python
@mcp.custom_route("/upload/immagine", methods=["POST"])
async def upload_immagine(request: Request) -> JSONResponse:
    ...
```

Logica:
1. `token = request.query_params["token"]`; `claims = upload_tokens.verify(token)`
   (401 su fallimento/scadenza).
2. `form = await request.form()`; `file = form["file"]` (Starlette `UploadFile`);
   `content = await file.read()` (400 se manca `file`).
3. `async with async_session() as db:`
   `res = await article_ops.save_article_image(db, claims["aid"],
   claims["name"], content, sovrascrivi=True)` — riusa validazione estensione,
   dimensione (10 MB), esistenza articolo, sanitizzazione nome, scrittura in
   `data/uploads/articoli/{id}/` e record `images`.
4. `ValueError` da `save_article_image` → 400 con messaggio; successo → 200
   `{nome_file, url, bytes}`.

Nessuna dipendenza dall'auth OAuth: la firma È l'auth (route pubblica, accertato).

### 4. Config / deploy

- Nuova env **`GEKO_UPLOAD_SIGNING_KEY`** (secret forte) aggiunta al servizio
  `geko-mcp` in `docker-compose.yml` e `docker-compose.prod.yml`. Solo il
  processo `geko-mcp` la usa (conia *e* verifica nello stesso processo): il
  secret non lascia mai il server, e non entra in Cowork.
- Se non impostata: `ottieni_upload_url` solleva `ValueError` esplicito e
  `/upload/immagine` risponde 503 → feature semplicemente assente in dev/test
  finché non si configura la chiave.
- Documentare in `CLAUDE.md` (sezione MCP) e `README`.

### 5. Invariato

- Tool `carica_immagine` (base64): resta com'è, utile per casi piccoli.
- `article_ops.save_article_image / list_article_images / delete_article_image`:
  nessuna modifica — sono la fonte unica riusata anche qui.
- Converter / `image_base`: già risolvono i nomi nudi.

## Mappatura criteri di accettazione

1. *Dopo crea + upload, l'anteprima mostra l'immagine* → `save_article_image`
   scrive in `data/uploads/articoli/{id}/` col nome esatto; `image_base` già
   risolve `#figura("x.png")`. ✓
2. *Formati PNG, JPG, SVG* → `ALLOWED_IMAGE_EXTENSIONS` include già
   `.png .jpg .jpeg .gif .webp .svg`. ✓
3. *Ricaricare lo stesso nome sovrascrive; scope per articolo* →
   `save_article_image(..., sovrascrivi=True)`, path per-articolo. ✓

## Sicurezza

- Firma HMAC-SHA256 con confronto a tempo costante (`hmac.compare_digest`).
- Scadenza breve (default 15 min) → URL non riusabili a lungo.
- `nome_file` e `articolo_id` legati nel token → un URL non può essere dirottato
  su un altro file/articolo; la route ignora il filename del multipart.
- `save_article_image` applica: estensione whitelist, dimensione ≤ 10 MB,
  esistenza articolo, `_sanitize_nome_file` (no traversal).
- Route pubblica ma inerte senza firma valida; nessun listing/enumerazione.

## Testing (pytest-asyncio, `webapp/tests/`)

- `upload_tokens`: mint→verify valido; token manomesso → `ValueError`; scaduto
  → `ValueError`; formato errato → `ValueError`.
- Tool `ottieni_upload_url`: articolo inesistente → errore; estensione non
  ammessa → errore; ritorna un URL per nome; senza `GEKO_UPLOAD_SIGNING_KEY`
  → errore esplicito.
- Route `/upload/immagine`: happy path (200, file scritto nel path atteso, record
  `images` creato); token assente/invalid/scaduto → 401; `file` mancante → 400;
  estensione/oversize → 400; ri-upload stesso nome → sovrascrive.
- Integrazione: crea articolo → mint → POST → converter con
  `image_base=article_image_base(id)` produce `#figura` che punta al file
  esistente.
- Test impostano una `GEKO_UPLOAD_SIGNING_KEY` fittizia via fixture/env.

## Fuori scope

- Widget drag-drop nel frontend SvelteKit (aggiungibile dopo).
- Modifiche al tool base64 o all'upload web `/api/images`.
- Carve-out di Authentik sulla webapp.
