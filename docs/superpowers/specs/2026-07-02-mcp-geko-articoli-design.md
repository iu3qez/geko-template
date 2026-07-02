# Design — MCP "GEKO articoli"

Data: 2026-07-02
Stato: approvato (brainstorming) — pronto per il piano di implementazione

## Obiettivo

Permettere a Claude (client MCP remoti: claude.ai, Claude Desktop, Claude Code)
di **creare e gestire articoli** del GEKO Radio Magazine su un'istanza remota,
scrivendoli **già conformi alle convenzioni** del template Typst.

Il valore non è solo "chiamare l'API": è che l'MCP **insegna a Claude le
convenzioni Markdown** del template (le stesse implementate in
`webapp/app/services/converter.py`) e gli permette di **verificare l'anteprima
Typst** prima di salvare.

## Decisioni prese (brainstorming)

| Tema | Decisione |
|------|-----------|
| Deploy | Server MCP HTTP **integrato nella stessa app FastAPI** della webapp, montato su `/mcp` |
| Accesso dati | **In-process**: riuso diretto di modelli SQLAlchemy e `converter.py`, nessun hop HTTP interno |
| Auth | **OAuth 2.1 con Scalekit** come Authorization Server (l'AS che i client Claude "digeriscono"), MCP come Resource Server che valida i JWT |
| Risorsa Scalekit | **Nuova risorsa dedicata** (`res_...`) solo per questo MCP |
| Perché Scalekit e non Authentik | Authentik protegge la webapp *umana* (forward-auth Traefik). Per l'MCP i client Claude richiedono un flow OAuth 2.1 con discovery/DCR che il setup Scalekit esistente già soddisfa (vedi progetto `../mcp-proxy`). |

## Contesto tecnico verificato

- La webapp è FastAPI async + SQLAlchemy (SQLite), container `geko-webapp` sulla
  rete Docker esterna `traefik`, a `geko.fabris.me` dietro il middleware
  `chain-forwardAuth-authentik@file`.
- Esiste già una REST API completa sotto `/api` (`articles`, `magazines`,
  `images`, `config`) con tutta la logica CRUD, assegnazione a numeri e
  generazione sommari AI. L'MCP **riusa questa logica**, non la duplica.
- Gli articoli sono salvati in Markdown (`Article.contenuto_md`) e convertiti in
  Typst da `MarkdownToTypstConverter` (`converter.py`).
- Riferimento auth: `../mcp-proxy/auth_proxy.py` implementa già la validazione
  token Scalekit (~30 righe) + il discovery `/.well-known/oauth-protected-resource`.
  Riusiamo quel pattern, non il container proxy.
- Dipendenze già presenti: `fastapi`, `httpx`, `anthropic`, `sqlalchemy`,
  `python-frontmatter`, `markdown-it-py`. Da aggiungere: il pacchetto MCP
  (`fastmcp` o `mcp`) e `scalekit-sdk-python`.

## Architettura

```
Client Claude (claude.ai / Desktop / Code)
        │  HTTPS + OAuth 2.1 (JWT Scalekit)
        ▼
Traefik ── router MCP dedicato (host geko-mcp.fabris.me, SENZA middleware Authentik)
        ▼
FastAPI (geko-webapp)
 ├── /api/*         REST API esistente (umani via SPA)   [invariato]
 ├── /health                                             [invariato]
 ├── /mcp           ◀── NUOVO: server MCP montato (ASGI sub-app)
 │     ├── auth: valida JWT Scalekit ad ogni richiesta
 │     ├── discovery: /.well-known/oauth-protected-resource
 │     └── tool/resource → riuso in-process di modelli + converter
 └── /{path}        catch-all SPA Svelte                 [invariato]
```

Il server MCP vive in un nuovo package dentro la webapp, es.
`webapp/app/mcp/` (server, definizione tool, auth, testo convenzioni). Viene
montato in `main.py` come sub-app ASGI accanto ai router esistenti.

### Unità e responsabilità

- **`app/mcp/server.py`** — costruisce l'istanza MCP, registra tool e risorse,
  espone l'app ASGI da montare. *Dipende da*: services (converter, llm),
  models, database session.
- **`app/mcp/auth.py`** — validazione token Scalekit + discovery endpoint
  (adattato da `mcp-proxy/auth_proxy.py`). *Dipende da*: `scalekit-sdk-python`,
  env vars.
- **`app/mcp/tools.py`** — implementazione dei tool: ognuno apre una sessione DB,
  riusa la stessa logica dei router `/api` (estratta in funzioni condivise dove
  utile) e ritorna dati serializzabili. *Dipende da*: models, converter.
- **`app/mcp/conventions.py`** — testo della guida convenzioni (single source,
  derivato dal docstring di `converter.py`), servito come risorsa MCP.

Principio: i tool NON reimplementano la logica di business; dove i router `/api`
contengono logica riutilizzabile (creazione articolo, assegnazione, sommario),
si estrae in funzioni di servizio chiamate sia dai router sia dai tool, per
evitare derive tra i due percorsi.

## Superficie MCP

### Tool

| Tool | Parametri | Azione |
|------|-----------|--------|
| `crea_articolo` | `titolo`, `sottotitolo?`, `autore?` (call), `nome_autore?`, `contenuto_md`, `numero_id?` | Crea l'articolo; se `numero_id` presente, lo assegna al numero. Ritorna id + anteprima. |
| `lista_numeri` | — | Elenca i numeri (id, numero, mese, anno, stato) per dare contesto. |
| `lista_articoli` | `numero_id?`, `search?` | Elenca articoli (id, titolo, autore, numeri). |
| `leggi_articolo` | `id` | Ritorna un articolo completo (md + metadati). |
| `modifica_articolo` | `id`, campi opzionali | Aggiorna contenuto/metadati. |
| `assegna_a_numero` | `id`, `numero_ids[]` | Assegna l'articolo a uno o più numeri. |
| `genera_sommario` | `id` | Genera il sommario AI (riusa `services/llm`). |
| `anteprima_typst` | `contenuto_md` | Converte in Typst via `converter.py` e lo restituisce, senza salvare. |

La *description* di `crea_articolo` (e di `anteprima_typst`) riassume la sintassi
GEKO e rimanda alla risorsa `guida-convenzioni`.

### Risorsa

- **`guida-convenzioni`** — documento che elenca la sintassi Markdown accettata
  dal converter, così Claude la carica come contesto:
  - Heading `#` → sezione (shift +1: il titolo articolo resta H1)
  - `**grassetto**`, `*corsivo*`
  - `[testo](url)` e URL nudi → `#link-geko`
  - `![alt](path){width=80%}` → `#figura` (i path `/uploads/...` sono rimappati)
  - Liste `*`/`-` (punti) e `1.` (numerate)
  - `> citazione` → `#quote`
  - Tabelle `| a | b |` → `#tabella-geko`
  - Admonition (box evidenza):
    ```
    !!! "Titolo del box"
    Contenuto del box su una o più righe.
    !!!
    ```
    → `#box-evidenza(titolo: "Titolo del box")[...]`

## Auth (OAuth 2.1 via Scalekit)

- Il server MCP espone `/.well-known/oauth-protected-resource` che punta alla
  **nuova risorsa Scalekit** dedicata (`authorization_servers`, `resource`, ecc.).
- Ogni richiesta MCP (tranne discovery/health) richiede header
  `Authorization: Bearer <jwt>`; il token è validato con `ScalekitClient.validate_token`
  e `TokenValidationOptions(audience=[RESOURCE_ID])`. In assenza/invalidità →
  `401` con `WWW-Authenticate: Bearer ... resource_metadata="..."` per innescare il flow.
- Env vars nuove (in `.env` / secrets webapp):
  `SCALEKIT_ENVIRONMENT_URL`, `SCALEKIT_CLIENT_ID`, `SCALEKIT_CLIENT_SECRET`,
  `SCALEKIT_RESOURCE_ID`, `MCP_PUBLIC_URL`.
- Le API esatte di FastMCP (montaggio ASGI + hook di validazione token) vanno
  confermate via Context7 e via la skill `mcp-auth:add-auth-fastmcp` in fase di
  implementazione.

## Deploy

- **Traefik**: nuovo router per l'MCP **senza** `chain-forwardAuth-authentik@file`.
  Preferenza: host dedicato `geko-mcp.fabris.me` → servizio `geko-webapp` porta
  interna (8000, o una porta dedicata se il mount lo richiede). L'auth la fa
  Scalekit nell'app, non Traefik.
- **Scalekit**: registrare la nuova risorsa e il client per i client Claude
  (DCR se supportata, altrimenti pre-registrazione una tantum).
- **Client**: Claude si connette a `https://geko-mcp.fabris.me/mcp`.
- Aggiornare `docker-compose.yml` / `docker-compose.prod.yml` con le nuove env
  e le label Traefik del router MCP.

## Gestione errori

- Token mancante/invalido → 401 con `WWW-Authenticate` (flow OAuth).
- Errori di validazione input tool → messaggio d'errore MCP strutturato.
- Articolo/numero inesistente → errore chiaro (404-equivalente nel tool).
- Errori converter/LLM → catturati, restituiti come errore del tool con
  messaggio leggibile (mai crash del server MCP).

## Testing

- Unit: i tool riusano le funzioni di servizio → test sulle funzioni condivise
  (creazione, assegnazione, conversione) su DB SQLite di test.
- `anteprima_typst`: confronto Markdown→Typst su casi noti (admonition, tabelle,
  figure, link) — riusa/estende i test del converter se presenti.
- Auth: 401 senza token; discovery endpoint ritorna il JSON corretto.
- Integrazione manuale: connessione da Claude Desktop/claude.ai all'URL MCP,
  login Scalekit, esecuzione di `crea_articolo` end-to-end.

## Fuori scope (YAGNI)

- Upload immagini via MCP (già gestito dalla UI).
- Creazione/gestione numeri rivista via MCP.
- Generazione PDF via MCP.
- Riuso della risorsa Scalekit del proxy esistente (scelta: risorsa dedicata).

## Follow-up documentazione

Al termine dell'implementazione, aggiungere a `CLAUDE.md` la sezione MCP
(endpoint `/mcp`, tool disponibili, env Scalekit, host Traefik dedicato).
