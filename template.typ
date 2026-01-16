// GEKO Radio Magazine Template
// Mountain QRP Club - Replica fedele del layout originale

// ============================================
// COLORI
// ============================================

#let geko-gold = rgb("#C4A35A")      // Oro per titoli, box pagina, bordi
#let geko-magenta = rgb("#C7338C")   // Magenta per sottotitoli, link, evidenze
#let geko-dark = rgb("#333333")      // Testo principale
#let geko-light = rgb("#F5F5F5")     // Sfondo tabelle alternate

// ============================================
// NUMERO PAGINA (box dorato in alto a destra)
// ============================================

#let page-number-box() = {
  context {
    let page-num = counter(page).get().first()
    box(
      fill: geko-gold,
      inset: (x: 10pt, y: 5pt),
      radius: 3pt,
      text(fill: white, weight: "bold", size: 11pt)[#page-num]
    )
  }
}

// ============================================
// TITOLO ARTICOLO (maiuscolo, magenta, linea oro sotto)
// ============================================

#let titolo-articolo(testo) = {
  v(0.8em)
  text(size: 18pt, weight: "bold", fill: geko-magenta, upper(testo))
  v(0.3em)
  line(length: 100%, stroke: 2pt + geko-gold)
  v(0.8em)
}

// ============================================
// SOTTOTITOLO SEZIONE (magenta, corsivo)
// ============================================

#let sottotitolo(testo) = {
  v(0.5em)
  text(size: 12pt, style: "italic", fill: geko-magenta, testo)
  v(0.5em)
}

// ============================================
// AUTORE
// ============================================

#let autore(nominativo, nome: none) = {
  v(0.3em)
  if nome != none {
    text(size: 10pt, weight: "bold")[#nome #nominativo]
  } else {
    text(size: 10pt, weight: "bold")[#nominativo]
  }
  v(0.8em)
}

// ============================================
// FIGURA CON DIDASCALIA
// ============================================

#let figura(path, didascalia: none, width: 100%) = {
  figure(
    image(path, width: width),
    caption: if didascalia != none { text(size: 9pt, didascalia) },
    supplement: none,
    numbering: none,
  )
}

// ============================================
// BOX EVIDENZA (sfondo grigio, bordo oro)
// ============================================

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

// ============================================
// TABELLA STILE GEKO (header oro, righe alternate)
// ============================================

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

// ============================================
// LINK STILIZZATO (magenta)
// ============================================

#let link-geko(url, testo: none) = {
  let display = if testo != none { testo } else { url }
  link(url, text(fill: geko-magenta, display))
}

// ============================================
// SEPARATORE ARTICOLI
// ============================================

#let separatore() = {
  v(1em)
  line(length: 100%, stroke: 0.5pt + geko-gold.lighten(50%))
  v(1em)
}

// ============================================
// COPERTINA (Pagina 1)
// Layout: 2 colonne - sinistra immagine+editoriale, destra IN EVIDENZA
// ============================================

#let copertina(
  numero: "XX",
  mese: "Mese",
  anno: "2025",
  immagine-principale: none,
  evidenze: (),
  editoriale-testo: none,
  editoriale-autore: none,
) = {
  set page(
    paper: "a4",
    margin: (top: 1.2cm, bottom: 1.2cm, left: 1.5cm, right: 1.5cm),
    header: none,
    footer: none,
  )

  grid(
    columns: (1.6fr, 1fr),
    gutter: 1.5em,

    // === COLONNA SINISTRA ===
    [
      // Immagine principale con bordo
      #if immagine-principale != none {
        box(
          stroke: 3pt + geko-gold.darken(10%),
          radius: 0pt,
          clip: true,
          image(immagine-principale, width: 100%)
        )
      }

      #v(1em)

      // Box EDITORIALE
      #block(
        width: 100%,
        stroke: (left: 4pt + geko-gold),
        inset: (left: 12pt, y: 8pt, right: 4pt),
        [
          #text(size: 16pt, weight: "bold", fill: geko-gold)[EDITORIALE]
          #v(0.6em)

          #set text(size: 9pt)
          #set par(justify: true, leading: 0.52em)
          #editoriale-testo

          #v(0.5em)
          #text(size: 9pt, weight: "bold")[#editoriale-autore]
        ]
      )
    ],

    // === COLONNA DESTRA ===
    [
      // Header numero/mese
      #align(right)[
        #text(size: 10pt, fill: geko-dark)[Nr. #numero | #mese – #anno]
      ]
      #v(0.8em)

      // Titolo IN EVIDENZA (box magenta)
      #align(right)[
        #box(
          fill: geko-magenta,
          inset: (x: 15pt, y: 8pt),
          text(size: 22pt, weight: "bold", fill: white)[IN EVIDENZA]
        )
      ]

      #v(1.5em)

      // Lista evidenze
      #for ev in evidenze {
        block(width: 100%, below: 1.2em)[
          // Titolo evidenza in magenta
          #text(size: 11pt, weight: "bold", fill: geko-magenta)[#ev.titolo:]
          #v(0.3em)
          // Descrizione
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
// PAGINA LOGO (Pagina 2)
// Grande immagine centrata + sottotitolo magenta
// ============================================

#let pagina-logo(
  numero: "66",
  mese: "Agosto",
  anno: "2025",
  logo-grande: none,
  sottotitolo: "Il GEKO RADIO MAGAZINE – Rivista aperiodica del Mountain QRP Club.",
) = {
  set page(
    paper: "a4",
    margin: (top: 1.5cm, bottom: 2cm, left: 2cm, right: 2cm),
    header: align(right)[#page-number-box()],
    footer: align(center)[
      #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
    ],
  )

  v(1fr)

  align(center)[
    #if logo-grande != none {
      box(
        stroke: 1pt + geko-dark.lighten(70%),
        image(logo-grande, width: 85%)
      )
    }

    #v(1.5em)

    #text(size: 13pt, style: "italic", weight: "bold", fill: geko-magenta)[#sottotitolo]
  ]

  v(2fr)

  pagebreak()
}

// ============================================
// SOMMARIO (Pagina 3)
// Titolo dorato maiuscolo + outline
// ============================================

#let sommario(numero: "66", mese: "Agosto", anno: "2025") = {
  set page(
    paper: "a4",
    margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm),
    header: align(right)[#page-number-box()],
    footer: align(center)[
      #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
    ],
  )

  text(size: 24pt, weight: "bold", fill: geko-gold)[SOMMARIO]
  v(0.3em)
  line(length: 100%, stroke: 2pt + geko-gold)
  v(1em)

  // Stile outline personalizzato
  show outline.entry.where(level: 1): it => {
    v(0.3em)
    text(weight: "bold", size: 11pt)[#it.body()]
    box(width: 1fr, repeat[.])
    text(weight: "bold")[#it.page()]
    v(0.2em)
  }

  show outline.entry.where(level: 2): it => {
    h(1.5em)
    text(size: 10pt)[#it.body()]
    box(width: 1fr, repeat[ .])
    it.page()
  }

  outline(
    title: none,
    indent: 0em,
    depth: 2,
  )

  pagebreak()
}

// ============================================
// SETUP DOCUMENTO PRINCIPALE
// Da usare per il contenuto articoli
// ============================================

#let geko-magazine(
  numero: "66",
  mese: "Agosto",
  anno: "2025",
  contenuto
) = {
  set document(
    title: "Geko Radio Magazine - Nr. " + numero,
    author: "Mountain QRP Club",
  )

  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2cm, right: 2cm),
    header: {
      grid(
        columns: (1fr, auto),
        align(left + horizon)[
          #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
        ],
        align(right)[#page-number-box()]
      )
      v(-0.3em)
      line(length: 100%, stroke: 0.5pt + geko-gold)
    },
    footer: align(center)[
      #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
    ],
  )

  // Font Linux Libertine come originale
  set text(
    font: "Linux Libertine",
    size: 10pt,
    lang: "it",
    fill: geko-dark,
  )

  // Paragrafi giustificati
  set par(
    justify: true,
    leading: 0.65em,
    first-line-indent: 0em,
  )

  // Stili heading
  set heading(numbering: none)

  // H1 = Titolo articolo (maiuscolo magenta + linea oro)
  show heading.where(level: 1): it => {
    titolo-articolo(it.body)
  }

  // H2 = Sezione (magenta corsivo)
  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 13pt, style: "italic", fill: geko-magenta, it.body)
    v(0.4em)
  }

  // H3 = Sottosezione
  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 11pt, weight: "bold", fill: geko-dark, it.body)
    v(0.3em)
  }

  // Link in magenta
  show link: it => text(fill: geko-magenta, it)

  // Liste puntate
  set list(marker: text(fill: geko-gold)[•])

  contenuto
}
