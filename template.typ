// GEKO Radio Magazine Template - Layout 2 colonne
// Mountain QRP Club

// ============================================
// CONFIGURAZIONE
// ============================================

#let geko-gold = rgb("#C4A35A")
#let geko-magenta = rgb("#C7338C")
#let geko-dark = rgb("#333333")
#let geko-light = rgb("#F5F5F5")

#let config = (
  numero: "67",
  mese: "Settembre",
  anno: "2025",
  titolo: "Geko Radio Magazine",
)

// ============================================
// FUNZIONI LAYOUT
// ============================================

// Header pagina
#let page-header(numero, mese, anno) = {
  set text(size: 9pt, fill: geko-dark)
  [Geko Radio Magazine – Nr. #numero | #mese - #anno]
}

// Footer con numero pagina
#let page-footer() = {
  context {
    let page-num = counter(page).get().first()
    if page-num > 1 {
      align(right)[
        #box(
          fill: geko-gold,
          inset: (x: 8pt, y: 4pt),
          radius: 2pt,
          text(fill: white, weight: "bold", size: 10pt)[#page-num]
        )
      ]
    }
  }
}

// Titolo articolo
#let titolo-articolo(testo) = {
  v(1em)
  block(
    width: 100%,
    below: 0.8em,
    [
      #line(length: 4pt, stroke: 3pt + geko-gold)
      #v(-0.3em)
      #text(
        size: 18pt,
        weight: "bold",
        fill: geko-gold,
        upper(testo)
      )
    ]
  )
}

// Sottotitolo
#let sottotitolo(testo) = {
  text(size: 12pt, style: "italic", fill: geko-magenta, testo)
  v(0.5em)
}

// Autore
#let autore(nominativo, nome: none) = {
  v(0.3em)
  text(size: 10pt, weight: "bold")[
    #if nome != none [#nome ]
    #nominativo
  ]
  v(0.8em)
}

// Immagine con didascalia
#let figura(path, didascalia: none, width: 100%) = {
  figure(
    image(path, width: width),
    caption: if didascalia != none { text(size: 9pt, didascalia) },
    supplement: none,
    numbering: none,
  )
}

// Box evidenza
#let box-evidenza(titolo: none, contenuto) = {
  block(
    width: 100%,
    fill: geko-light,
    inset: 12pt,
    radius: 4pt,
    stroke: 0.5pt + geko-gold,
    [
      #if titolo != none {
        text(weight: "bold", fill: geko-magenta, size: 11pt, titolo)
        v(0.5em)
      }
      #contenuto
    ]
  )
}

// Tabella stile GEKO
#let tabella-geko(intestazioni, righe) = {
  table(
    columns: intestazioni.len(),
    fill: (col, row) => if row == 0 { geko-gold } else if calc.odd(row) { geko-light } else { white },
    stroke: 0.5pt + geko-dark.lighten(50%),
    inset: 8pt,
    align: (col, row) => if row == 0 { center } else { left },
    ..intestazioni.map(h => text(fill: white, weight: "bold", size: 9pt, h)),
    ..righe.flatten().map(c => text(size: 9pt, c))
  )
}

// Sezione a colonna singola (per tabelle larghe, immagini grandi)
#let colonna-singola(contenuto) = {
  block(width: 100%, breakable: true)[
    #columns(1)[#contenuto]
  ]
}

// Link stilizzato
#let link-geko(url, testo: none) = {
  let display = if testo != none { testo } else { url }
  link(url, text(fill: geko-magenta, display))
}

// Separatore articoli
#let separatore() = {
  v(1em)
  line(length: 100%, stroke: 0.5pt + geko-gold.lighten(50%))
  v(1em)
}

// ============================================
// COPERTINA
// ============================================

#let copertina(
  numero: "XX",
  mese: "Mese",
  anno: "2025",
  immagine-principale: none,
  logo: none,
  evidenze: (),
  editoriale-titolo: none,
  editoriale-testo: none,
  editoriale-autore: none,
) = {
  // Reset a singola colonna per copertina
  set page(
    margin: (top: 1.5cm, bottom: 1.5cm, left: 1.8cm, right: 1.8cm),
    header: none,
    footer: none,
    columns: 1,
  )
  
  // Layout copertina
  grid(
    columns: (1.8fr, 1.2fr),
    gutter: 1.2em,
    
    // === COLONNA SINISTRA ===
    [
      // Logo e immagine principale
      #if logo != none {
        align(left)[#image(logo, width: 60pt)]
        v(0.5em)
      }
      
      #if immagine-principale != none {
        box(
          clip: true,
          radius: 4pt,
          image(immagine-principale, width: 100%)
        )
      }
      
      v(1em)
      
      // Box editoriale
      #block(
        width: 100%,
        fill: white,
        stroke: (left: 3pt + geko-gold),
        inset: (left: 12pt, y: 8pt, right: 8pt),
        [
          #text(size: 16pt, weight: "bold", fill: geko-gold)[EDITORIALE]
          #v(0.6em)
          
          #if editoriale-testo != none {
            set text(size: 9.5pt)
            set par(justify: true, leading: 0.55em)
            editoriale-testo
          }
          
          #v(0.8em)
          
          #if editoriale-autore != none {
            text(size: 9pt, weight: "bold")[72 e buone ferie a tutti!]
            v(0.3em)
            text(size: 9pt)[#editoriale-autore]
          }
        ]
      )
    ],
    
    // === COLONNA DESTRA ===
    [
      // Header
      align(right)[
        #text(size: 11pt, fill: geko-dark)[Nr. #numero | #mese – #anno]
      ]
      v(0.5em)
      
      // Titolo IN EVIDENZA
      align(right)[
        #box(
          fill: geko-magenta,
          inset: (x: 12pt, y: 6pt),
          radius: 2pt,
          text(size: 20pt, weight: "bold", fill: white)[IN EVIDENZA]
        )
      ]
      
      v(1.2em)
      
      // Lista evidenze
      #for ev in evidenze {
        block(width: 100%, below: 1em)[
          #text(size: 11pt, weight: "bold", fill: geko-magenta)[#ev.titolo]
          #if "sottotitolo" in ev and ev.sottotitolo != none {
            text(size: 10pt, fill: geko-magenta)[:] 
          }
          #v(0.3em)
          #set text(size: 9pt)
          #set par(justify: true, leading: 0.5em)
          #ev.descrizione
        ]
      }
    ]
  )
  
  pagebreak()
}

// ============================================
// PAGINA LOGO (pagina 2)
// ============================================

#let pagina-logo(logo-grande: none, sottotitolo: none) = {
  set page(
    header: none,
    footer: context {
      let page-num = counter(page).get().first()
      align(center)[
        #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. 66 | Agosto - 2025]
      ]
      align(right)[
        #box(
          fill: geko-gold,
          inset: (x: 8pt, y: 4pt),
          radius: 2pt,
          text(fill: white, weight: "bold", size: 10pt)[#page-num]
        )
      ]
    },
    columns: 1,
  )
  
  v(3fr)
  
  align(center)[
    #if logo-grande != none {
      image(logo-grande, width: 70%)
    }
    
    #v(1em)
    
    #if sottotitolo != none {
      text(size: 12pt, style: "italic", fill: geko-magenta)[#sottotitolo]
    }
  ]
  
  v(4fr)
  
  pagebreak()
}

// ============================================
// SOMMARIO
// ============================================

#let sommario() = {
  text(size: 20pt, weight: "bold", fill: geko-gold)[SOMMARIO]
  v(1em)
  
  outline(
    title: none,
    indent: 1.5em,
    depth: 3,
  )
  
  pagebreak()
}

// ============================================
// SETUP DOCUMENTO
// ============================================

#let geko-magazine(
  numero: "XX",
  mese: "Mese", 
  anno: "2025",
  contenuto
) = {
  set document(
    title: "Geko Radio Magazine - Nr. " + numero,
    author: "Mountain QRP Club",
  )
  
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 1.8cm, right: 1.8cm),
    columns: 2,
    header: context {
      let page-num = counter(page).get().first()
      if page-num > 2 {
        page-header(numero, mese, anno)
        v(-0.5em)
        line(length: 100%, stroke: 0.3pt + geko-gold)
      }
    },
    footer: page-footer(),
  )
  
  // Font setup
  set text(
    font: "Linux Libertine",
    size: 10pt,
    lang: "it",
    fill: geko-dark,
  )
  
  // Paragrafi
  set par(
    justify: true,
    leading: 0.65em,
    first-line-indent: 0em,
  )
  
  // Heading styles
  set heading(numbering: none)
  
  show heading.where(level: 1): it => {
    titolo-articolo(it.body)
  }
  
  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 13pt, weight: "bold", fill: geko-gold, it.body)
    v(0.4em)
  }
  
  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 11pt, weight: "bold", fill: geko-magenta, it.body)
    v(0.3em)
  }
  
  // Link style
  show link: it => text(fill: geko-magenta, it)
  
  contenuto
}

// ============================================
// ESPORTAZIONE FUNZIONI
// ============================================

// Per uso nel documento principale, esporta tutto
