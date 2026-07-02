# Design — GEKO MCP: gestione dei numeri della rivista

Data: 2026-07-02

## Contesto

Il connettore MCP GEKO oggi espone `lista_numeri` (sola lettura) e
`assegna_a_numero` (associa un articolo a numeri esistenti). Manca qualsiasi
strumento per **creare** o **gestire** un numero: non è quindi possibile
preparare, ad es., il numero di Luglio e assegnarvi un articolo finché il numero
non viene creato a mano nel DB.

## Obiettivo

Aggiungere gli strumenti MCP per creare, modificare ed eliminare i numeri della
rivista, mantenendo stile e convenzioni degli strumenti esistenti (nomi in
italiano, snake_case, delega alla logica condivisa).

## Vincoli architetturali (dallo stato attuale del codice)

- **Fonte unica di verità**: `webapp/app/services/article_ops.py`. Sia i router
  `/api` sia i tool MCP delegano qui. I nuovi strumenti seguono lo stesso schema.
- **Tool MCP sottili**: in `webapp/app/mcp/server.py` i tool sono wrapper che
  aprono `async_session()` e chiamano `article_ops`.
- **Serializzazione**: esiste già `article_ops.magazine_to_response(m)` che
  ritorna `{id, numero, mese, anno, stato}` — esattamente lo schema richiesto.
- **Convenzione errori**: tutti i tool GEKO esistenti segnalano gli errori
  **sollevando `ValueError`** (FastMCP lo converte in `ToolError` lato client).
  I nuovi tool fanno lo stesso — decisione confermata dall'utente.
- **Modello**: `Magazine(numero, mese, anno, stato: MagazineStatus{BOZZA,
  PUBBLICATO}, editoriale, editoriale_autore, copertina_id, ...)`. La relazione
  M2M con gli articoli usa la tabella `article_magazines` (secondary).

## Modello dati di un "numero" (output, invariato)

```json
{ "id": 5, "numero": "67", "mese": "Febbraio", "anno": "2026", "stato": "pubblicato" }
```

## Componenti

### 1. Service layer — `article_ops.py`

Helper di validazione (privato):

```
_MESI_IT = [Gennaio, Febbraio, Marzo, Aprile, Maggio, Giugno,
            Luglio, Agosto, Settembre, Ottobre, Novembre, Dicembre]

_validate_magazine_fields(*, numero=None, mese=None, anno=None, stato=None)
    -> dict con i soli campi passati, normalizzati
```

Regole (valida solo i campi non-`None`, così è riusabile in create e update):

1. `mese`: confronto case-insensitive contro `_MESI_IT`; normalizzato a
   iniziale maiuscola (es. "luglio" → "Luglio"). Non valido → `ValueError`
   ("Mese non valido: '<x>'. Valori ammessi: Gennaio…Dicembre").
2. `anno`: deve corrispondere a `^\d{4}$`. Altrimenti `ValueError`
   ("Anno non valido: deve essere di 4 cifre").
3. `stato`: deve appartenere a `{"bozza", "pubblicato"}`. Altrimenti
   `ValueError`. Ritorna il valore `MagazineStatus` corrispondente.
4. `numero`: non vuoto (per create). L'unicità è verificata separatamente con
   una query (non è un vincolo DB).

Funzioni:

```
async def create_magazine(db, *, numero, mese, anno, stato="bozza") -> dict
```
- Valida i campi. Verifica che non esista già un `Magazine` con lo stesso
  `numero` → altrimenti `ValueError("Numero già esistente: <numero>")`.
- Inserisce, commit, refresh; ritorna `magazine_to_response`.

```
async def update_magazine(db, magazine_id, **fields) -> Optional[dict]
```
- Carica il magazine; se assente → `None` (il tool tradurrà in `ValueError`,
  come fa `update_article`).
- Valida i soli campi passati. Se `numero` cambia, verifica l'unicità
  **escludendo se stesso** → `ValueError` se collide.
- Applica i campi ammessi (`numero, mese, anno, stato`), commit, ritorna
  `magazine_to_response`.

```
async def delete_magazine(db, magazine_id, *, forza=False) -> bool | None
```
- Carica il magazine (con `selectinload(Magazine.articles)`); se assente →
  `None`.
- Se ha articoli associati e `forza` è `False` → `ValueError`
  ("Il numero <n> ha N articoli associati; usa forza=True per eliminarlo").
- Elimina il magazine: SQLAlchemy rimuove solo le righe della tabella di
  associazione `article_magazines`, **gli articoli restano**. Ritorna `True`.

Modifica minore correlata: allineare l'ordinamento di `list_magazines` a
`ORDER BY anno DESC, numero DESC` (oggi solo `numero DESC`), coerente col router
`/api/magazines` e con "ordinamento sensato" richiesto.

### 2. Tool MCP — `server.py`

```
@mcp.tool
async def crea_numero(numero, mese, anno, stato="bozza") -> dict
    """Crea un nuovo numero della rivista (id, numero, mese, anno, stato)."""

@mcp.tool
async def modifica_numero(id, numero=None, mese=None, anno=None, stato=None) -> dict
    """Aggiorna i campi indicati di un numero esistente."""
    # se article_ops.update_magazine ritorna None -> raise ValueError(f"Numero {id} non trovato")

@mcp.tool
async def elimina_numero(id, forza=False) -> dict
    """Elimina un numero. Fallisce se ha articoli associati (usa forza=True)."""
    # ritorna {"eliminato": id}; None -> raise ValueError(f"Numero {id} non trovato")
```

Docstring in italiano, parametri named, coerenti con i tool esistenti.

## Flusso dati

Client MCP → tool (`server.py`) → `async_session()` → `article_ops.*` →
SQLAlchemy → `magazine_to_response` → dict → client. Nessuna logica duplicata:
i tool sono wrapper.

## Gestione errori

- Validazione fallita / duplicato / vincolo eliminazione → `ValueError` con
  messaggio italiano leggibile (→ `ToolError` lato client).
- Numero inesistente (modifica/elimina) → `article_ops` ritorna `None`, il tool
  solleva `ValueError(f"Numero {id} non trovato")` (stesso pattern di
  `leggi_articolo`/`modifica_articolo`).

## Coerenza con `assegna_a_numero`

`create_magazine` fa commit e ritorna il nuovo `id` immediatamente utilizzabile
come elemento di `numero_ids` in `assegna_a_numero`. `list_numeri` riflette
subito creazioni/modifiche/eliminazioni (stessa sessione/DB condiviso).

## Testing

`webapp/tests/test_article_ops.py` (service-level):
- `create_magazine` → record con `stato="bozza"` di default e `id` valido.
- `create_magazine` con `numero` duplicato → `ValueError`, nessun doppione.
- `create_magazine`/validazione con `mese="Luglioo"` → `ValueError`.
- `create_magazine` con `anno` non a 4 cifre → `ValueError`.
- normalizzazione `mese` ("luglio" → "Luglio").
- `update_magazine(id, stato="pubblicato")` → stato aggiornato.
- `update_magazine` con `numero` che collide con altro → `ValueError`.
- `delete_magazine` con articoli associati e `forza=False` → `ValueError`.
- `delete_magazine(forza=True)` → elimina numero, l'articolo sopravvive.

`webapp/tests/test_mcp_server.py` (tool-level, via `Client(mcp)`):
- `crea_numero(numero="68", mese="Luglio", anno="2026")` → `stato="bozza"`, id valido.
- nuovo `id` usabile con `assegna_a_numero` (crea articolo → assegna → verifica).
- `crea_numero` con numero duplicato → `ToolError`.
- `crea_numero` con `mese="Luglioo"` → `ToolError`.
- `modifica_numero(id, stato="pubblicato")` → visibile in `lista_numeri`.
- `elimina_numero` su numero con articoli → `ToolError`; con `forza=True` → ok.

## Criteri di accettazione (dal committente)

- [ ] `crea_numero(numero:"68", mese:"Luglio", anno:"2026")` → record con
      `stato:"bozza"` e `id` valido.
- [ ] Il nuovo `id` funziona con `assegna_a_numero(id_articolo, [nuovo_id])`.
- [ ] `crea_numero` con `numero` già esistente → errore, nessun doppione.
- [ ] `crea_numero` con `mese:"Luglioo"` → errore di validazione.
- [ ] `modifica_numero(id, stato:"pubblicato")` → stato aggiornato in `lista_numeri`.
- [ ] `elimina_numero` su numero con articoli associati → errore (o `forza`).

## Fuori scope (YAGNI)

- Nessuna modifica ai campi `editoriale`, `editoriale_autore`, `copertina_id`
  via MCP (non richiesti).
- Nessun vincolo di unicità a livello DB (mantenuto come check applicativo,
  coerente con `/api`).
- Nessuna gestione del riordino articoli o build PDF (già coperti altrove).
