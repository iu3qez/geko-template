# Debito tecnico

Elenco dei punti noti da sistemare. Voce nuova in cima, con data.

---

## 2026-09-22 — Gli errori di build sono invisibili: 200 OK e nessun log

**Priorità: alta.** Regola: *non possiamo avere errori e non sapere perché.*

### Sintomo
La UI mostra "Errore durante la generazione" e non c'è modo di sapere cosa sia
successo: nei log del container non compare **niente** e la richiesta risulta
`POST /api/magazines/{id}/build HTTP/1.1 200 OK`.

### Cause (tre, sommate)

1. **Status HTTP sbagliato.** `build_pdf()` in
   `webapp/app/routes/api/magazines.py` ritorna `{"status": "error", ...}` con
   codice **200**. Per chiunque guardi i log d'accesso (o un uptime monitor, o
   Traefik) la build è andata a buon fine.
2. **L'eccezione vera viene inghiottita.** Il blocco
   `except Exception:` attorno a `build_magazine_pdf` scarta l'eccezione di
   Typst e lancia al suo posto la diagnostica per-articolo. Il messaggio
   originale (`typst.TypstError: ...`) non viene né loggato né restituito.
3. **La diagnostica copre solo gli articoli.** Se il documento non compila per
   colpa dell'*assemblaggio* (copertina, `editoriale-testo`, evidenze, pagina
   team, pagina finale) ogni articolo compila da solo, la lista `errori` esce
   **vuota** e la risposta è `{"status": "error", "errori": []}`: un errore che
   dichiara di non sapere nulla di sé.

### Come si è manifestato (numero 69)
Build fallita con `errori: []`. Per arrivare alla causa è servito rieseguire a
mano `build_magazine_pdf` dentro il container:

    typst.TypstError: the character `#` is not valid in code

Colpevole: l'**editoriale è Markdown ma viene interpolato grezzo** dentro un
blocco di contenuto Typst (`editoriale-testo: [...]` in
`MagazineBuilder._generate_document`). Le righe `## La fatidica prima domenica
di agosto` e `## E l'Alpe Adria di oggi?` aprono il code mode di Typst sul
primo `#`, e il secondo `#` è un carattere non valido in codice. I corpi degli
articoli passano da `md_render`/cmarker; l'editoriale no. (→ vedi voce
successiva)

### Cosa fare
- Loggare **sempre** l'eccezione originale (`logging.exception`) prima di
  qualunque fallback diagnostico.
- Rispondere **500** (o 422 per un errore di contenuto) invece di 200, e
  includere il messaggio Typst grezzo nel payload.
- Quando la diagnostica per-articolo non trova nulla, dirlo esplicitamente e
  restituire comunque l'errore di compilazione del documento completo, più il
  percorso del `.typ` generato, che resta su disco ed è la cosa più utile da
  guardare. NB: `typst/generated/` **non è montato**, quindi in produzione il
  file vive solo dentro il container (`/app/typst/generated/geko{numero}.typ`):
  di fatto invisibile senza un `docker exec`. Valutare di montarlo, o di
  allegare il sorgente all'errore.
- Estendere la diagnostica ai blocchi non-articolo (editoriale, evidenze, team,
  pagina finale), compilandoli isolati come già si fa per i segmenti.

---

## 2026-09-22 — L'editoriale non passa da cmarker — RISOLTO 2026-09-22

**Risolto**: `_generate_document` ora rende l'editoriale con
`md_render.render_article_body()`, lo stesso percorso dei corpi articolo, e
`md_render` espone `typst_string`/`typst_markup` come unico punto di escaping,
usato anche per evidenze, pagina team, autore editoriale, link e path immagini.
Resta sotto, per memoria, la descrizione del problema.

**Priorità: alta** (rompeva la build, vedi sopra).

`MagazineBuilder._generate_document` inserisce `editoriale` così com'è dentro
`editoriale-testo: [...]`, limitandosi a raddoppiare i newline. Ma nella webapp
l'editoriale si scrive in Markdown come tutto il resto: heading (`##`),
link `[testo](url)`, liste, enfasi. Risultato: gli heading fanno fallire la
compilazione e il resto verrebbe reso male (il link Markdown diventerebbe un
blocco di contenuto seguito da una parentesi).

Va renderizzato con lo stesso percorso dei corpi articolo
(`md_render` → `cmarker.render(...)` con stringa escaped), tenendo conto che
qui il contenuto finisce come *argomento* di `#copertina(...)`.

Stesso sospetto, da verificare, per gli altri campi liberi interpolati grezzi:
- `evidenze` → titolo/descrizione finiscono dentro stringhe `"..."`
  (`_format_evidenze`): una virgoletta o un backslash nel sommario LLM rompe la
  compilazione;
- `team_membri` (nome, ruolo), `editoriale_autore`, i link di configurazione:
  stessa interpolazione non-escaped in stringhe Typst.

Serve una funzione unica di escaping per le stringhe Typst, usata ovunque si
interpoli testo utente.
