# Compressione PDF post-build via Ghostscript — Design

Data: 2026-07-06

## Problema

Il PDF di un numero con molte foto supera i **48 MB** (impraticabile da
distribuire via email/web). Causa: Typst incorpora le immagini alla risoluzione
originale. Nel numero corrente ci sono ~180 immagini in `data/uploads`, molte da
0.5–1.5 MB ciascuna (es. le ~148 foto dell'articolo 17 "Settimana SOTA").

## Obiettivo

Ridurre drasticamente la dimensione del PDF finale senza toccare gli originali né
la pipeline Typst, con un passo di post-processing.

## Misura (dati reali)

Test su un PDF di 30 foto grandi dell'articolo 17 (15.3 MB originali):

| Metodo | Dimensione | Riduzione |
|---|---|---|
| Originale (Typst) | 15.3 MB | — |
| Ghostscript `/ebook` (150 dpi) | 1.4 MB | **−91%** |
| Ghostscript `/screen` (72 dpi) | 0.2 MB | −98% |

Un numero da ~48 MB → **~4–5 MB** con `/ebook`. **Scelta: `/ebook` (150 dpi)** —
miglior compromesso qualità/dimensione per una rivista letta a schermo/tablet.

## Decisione architetturale

Post-processare il **PDF generato** con **Ghostscript** (non ricomprimere le
immagini sorgente con Pillow). Motivi:
- Un solo passo alla fine di `build_magazine`, gestisce uniformemente copertina +
  articoli + team + pagina finale.
- Non tocca upload, media library, né gli originali (PDF sempre rigenerabile).
- Qualità regolabile con un preset; il **testo resta vettoriale** (nitido), solo
  le immagini vengono ricampionate.

Costo: aggiungere il pacchetto `ghostscript` all'immagine Docker (attualmente
assente; presente sull'host di sviluppo).

## Componenti

### `webapp/app/services/pdf_compress.py` (nuovo)
`compress_pdf(path: Path, preset: str = "ebook") -> dict`
- Esegue:
  ```
  gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/ebook \
     -dNOPAUSE -dBATCH -dQUIET -sOutputFile=<tmp> <path>
  ```
  (scrive su un file temporaneo nella stessa directory).
- Sostituisce l'originale col compresso **solo se più piccolo** (guardia: se gs
  producesse un file uguale/più grande, tiene l'originale).
- **Fail-safe**: se `shutil.which("gs")` è None → no-op (ritorna
  `{"compressed": False, "reason": "ghostscript non disponibile"}`); se gs esce
  con errore o il file temp è vuoto/mancante → no-op, tiene l'originale, logga un
  warning. Non solleva mai: la build non deve rompersi per la compressione.
- Ritorna info per il log: `{"compressed": bool, "before": int, "after": int,
  "preset": str, "reason"?: str}`.

### `webapp/app/services/builder.py` (modifica)
In `build_magazine`, dopo `pdf_path.write_bytes(pdf_bytes)`:
```python
from .pdf_compress import compress_pdf
info = compress_pdf(pdf_path)
# log: compresso da X a Y (-Z%) oppure "compressione saltata: <reason>"
```
Il valore di ritorno resta `pdf_path` (invariato per i chiamanti).

### `webapp/Dockerfile` (modifica)
Aggiungere `ghostscript` all'`apt-get install` dello stage runtime (con
`--no-install-recommends` per contenere la dimensione), pulendo la apt cache.

## Gestione errori

- gs assente (dev locale senza gs, o immagine non ancora aggiornata) → PDF non
  compresso, warning nel log, build OK.
- gs fallisce / output anomalo → tiene l'originale, warning, build OK.
- Nessun percorso solleva eccezioni verso `build_magazine`.

## Testing

- **`compress_pdf` riduce** un PDF ricco di immagini quando gs è presente
  (generato al volo da alcune foto reali); asserisce `after < before` e PDF
  valido. `@pytest.mark.skipif(shutil.which("gs") is None)`.
- **No-op senza gs**: monkeypatch `shutil.which`→None → `compressed False`,
  file invariato, nessuna eccezione.
- **Guardia "solo se più piccolo"**: su un PDF già minuscolo (testo puro) la
  funzione non deve ingrandirlo (mantiene l'originale se gs non riduce).
- **`build_magazine`** produce un PDF valido con e senza gs (il test esistente
  `test_build_magazine_minimo` copre il caso; nell'ambiente di test gs può
  esserci o no — la build deve passare comunque).

## Non-goal

- Preset configurabile per numero (scelto `/ebook` fisso; eventuale
  configurazione è un follow-up).
- Ricompressione delle immagini sorgente / della media library.
- Compressione condizionale a soglia di dimensione (si comprime sempre: `/ebook`
  è adeguato anche per numeri piccoli).
