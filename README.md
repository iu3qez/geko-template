# GEKO Radio Magazine - Template Typst

Template per generare automaticamente il **GEKO Radio Magazine** del Mountain QRP Club.

Layout a **due colonne** con supporto per copertina, sommario automatico, tabelle stile GEKO, box evidenza e gestione immagini.

![Esempio output](output/preview.png)

## 🚀 Quick Start

```bash
# Installa dipendenza
pip install typst

# Compila l'esempio
python build.py geko67-completo.typ -o output/geko67.pdf
```

## 📁 Struttura

```
geko-template/
├── template.typ          # Template principale (stili, funzioni)
├── geko67-completo.typ   # Esempio completo con copertina e sommario
├── esempio-geko67.typ    # Esempio semplificato
├── build.py              # Script per compilare in PDF
├── assets/               # Immagini, loghi
│   ├── copertina-contest.jpg
│   ├── logo-mqc-grande.png
│   └── ...
├── output/               # PDF generati
├── README.md
├── LICENSE
└── .gitignore
```

## 📝 Creare un nuovo numero

### 1. Struttura base

```typst
#import "template.typ": *

// COPERTINA (opzionale)
#copertina(
  numero: "68",
  mese: "Ottobre",
  anno: "2025",
  immagine-principale: "assets/mia-immagine.jpg",
  evidenze: (
    (titolo: "Articolo 1", descrizione: "Descrizione..."),
    (titolo: "Articolo 2", descrizione: "Descrizione..."),
  ),
  editoriale-testo: [Testo editoriale...],
  editoriale-autore: "Nominativo",
)

// PAGINA LOGO (opzionale)
#pagina-logo(
  logo-grande: "assets/logo-mqc-grande.png",
  sottotitolo: "Rivista aperiodica del Mountain QRP Club",
)

// CONTENUTO PRINCIPALE
#show: geko-magazine.with(
  numero: "68",
  mese: "Ottobre",
  anno: "2025",
)

// SOMMARIO (automatico)
#sommario()

// ARTICOLI
= Titolo Articolo

Contenuto...
```

### 2. Funzioni disponibili

#### Titoli e metadati
```typst
= Titolo Principale        // heading level 1 → stile GEKO
== Sottosezione            // heading level 2
=== Sotto-sottosezione     // heading level 3

#sottotitolo[Testo in corsivo magenta]
#autore("IU3QEZ", nome: "Simone")
```

#### Box evidenza
```typst
#box-evidenza(titolo: "Nota importante")[
  Contenuto con sfondo grigio e bordo oro.
]
```

#### Immagini con didascalia
```typst
#figura("assets/foto.jpg", didascalia: "Descrizione", width: 80%)
```

#### Tabelle stile GEKO
```typst
#tabella-geko(
  ("Col1", "Col2", "Col3"),      // intestazioni
  (
    ("A1", "B1", "C1"),          // righe
    ("A2", "B2", "C2"),
  )
)
```

#### Link stilizzati
```typst
#link-geko("https://www.mqc.it", testo: "Sito MQC")
```

#### Separatore tra articoli
```typst
#separatore()
```

## 🎨 Palette colori

| Nome | Valore | Uso |
|------|--------|-----|
| `geko-gold` | `#C4A35A` | Titoli, accenti, header tabelle |
| `geko-magenta` | `#C7338C` | Link, sottotitoli, evidenze |
| `geko-dark` | `#333333` | Testo principale |
| `geko-light` | `#F5F5F5` | Sfondi box |

## 📐 Layout

- **Formato:** A4
- **Colonne:** 2 (automatico)
- **Margini:** 1.8cm laterali, 2.5cm top, 2cm bottom
- **Font:** Linux Libertine (serif)
- **Header:** da pagina 3 in poi
- **Footer:** numero pagina in box oro

## 🔧 Personalizzazione

### Cambiare i colori
Modifica le variabili all'inizio di `template.typ`:

```typst
#let geko-gold = rgb("#C4A35A")
#let geko-magenta = rgb("#C7338C")
```

### Cambiare il font
```typst
set text(
  font: "Libertinus Serif",  // o altro font installato
  size: 10pt,
)
```

## ❓ Troubleshooting

**Errore font non trovato:**
```bash
# Ubuntu/Debian
sudo apt install fonts-linuxlibertine
```

**Import non funziona:**
Assicurati che `template.typ` sia nella stessa cartella del documento.

**Immagine non trovata:**
Usa path relativi alla cartella del documento: `assets/foto.jpg`

## 📄 Licenza

MIT License - Vedi [LICENSE](LICENSE)

---

**72 de Mountain QRP Club** 🦎

[www.mqc.it](https://www.mqc.it)
