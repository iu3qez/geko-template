// GEKO Radio Magazine Template
// Mountain QRP Club - Replica fedele del layout originale
// Versione 2.0 - Migliorata

// ============================================
// COLORI ESATTI DALLA RIVISTA
// ============================================

#let geko-gold = rgb("#C4A35A")      // Oro per box pagina, bordi, titolo SOMMARIO
#let geko-magenta = rgb("#C7338C")   // Magenta per IN EVIDENZA, titoli articoli, link
#let geko-dark = rgb("#333333")      // Testo principale scuro
#let geko-light = rgb("#F8F8F8")     // Sfondo chiaro per tabelle alternate
#let geko-white = rgb("#FFFFFF")     // Bianco

// ============================================
// FUNZIONE: Box numero pagina (angolo alto destra)
// ============================================

#let page-number-box() = {
  context {
    let page-num = counter(page).get().first()
    box(
      fill: geko-gold,
      inset: (x: 8pt, y: 4pt),
      radius: 2pt,
      text(fill: white, weight: "bold", size: 10pt)[#page-num]
    )
  }
}

// ============================================
// FUNZIONE: Titolo articolo principale
// (maiuscolo, magenta, linea oro sotto)
// ============================================

#let titolo-articolo(testo) = {
  v(1em)
  block(width: 100%)[
    #text(size: 16pt, weight: "bold", fill: geko-magenta, tracking: 0.5pt)[#upper(testo)]
    #v(4pt)
    #line(length: 100%, stroke: 2pt + geko-gold)
  ]
  v(0.8em)
}

// ============================================
// FUNZIONE: Sottotitolo di sezione
// ============================================

#let sottotitolo-sezione(testo) = {
  v(0.6em)
  text(size: 12pt, weight: "bold", fill: geko-magenta)[#upper(testo)]
  v(0.4em)
}

// ============================================
// FUNZIONE: Autore articolo
// ============================================

#let autore(nominativo, nome: none) = {
  v(0.2em)
  if nome != none {
    text(size: 10pt, style: "italic")[#nome #nominativo]
  } else {
    text(size: 10pt, style: "italic")[#nominativo]
  }
  v(0.6em)
}

// ============================================
// FUNZIONE: Link stilizzato (magenta)
// ============================================

#let link-geko(url, testo: none) = {
  let display = if testo != none { testo } else { url }
  link(url, text(fill: geko-magenta)[#display])
}

// ============================================
// FUNZIONE: Box evidenza (sfondo grigio, bordo oro)
// ============================================

#let box-evidenza(titolo: none, contenuto) = {
  block(
    width: 100%,
    fill: geko-light,
    inset: 12pt,
    radius: 3pt,
    stroke: 0.5pt + geko-gold,
    [
      #if titolo != none {
        text(weight: "bold", fill: geko-magenta, size: 11pt)[#titolo]
        v(0.4em)
      }
      #contenuto
    ]
  )
}

// ============================================
// FUNZIONE: Tabella stile GEKO
// (header oro, righe alternate)
// ============================================

#let tabella-geko(intestazioni, righe) = {
  table(
    columns: intestazioni.len(),
    fill: (col, row) => {
      if row == 0 { geko-gold }
      else if calc.odd(row) { geko-light }
      else { white }
    },
    stroke: 0.5pt + geko-dark.lighten(60%),
    inset: 6pt,
    align: (col, row) => if row == 0 { center } else { left },
    ..intestazioni.map(h => text(fill: white, weight: "bold", size: 9pt)[#h]),
    ..righe.flatten().map(c => text(size: 9pt)[#c])
  )
}

// ============================================
// FUNZIONE: Separatore articoli
// ============================================

#let separatore() = {
  v(0.8em)
  line(length: 100%, stroke: 0.5pt + geko-gold.lighten(40%))
  v(0.8em)
}

// ============================================
// COPERTINA (Pagina 1)
// Layout: 2 colonne
// - Sinistra: immagine principale + editoriale
// - Destra: Nr./data + IN EVIDENZA + lista articoli
// ============================================

#let copertina(
  numero: "66",
  mese: "Agosto",
  anno: "2025",
  immagine-principale: none,
  evidenze: (),
  editoriale-testo: none,
  editoriale-autore: none,
) = {
  // Pagina senza header/footer
  set page(
    paper: "a4",
    margin: (top: 1.2cm, bottom: 1.5cm, left: 1.5cm, right: 1.5cm),
    header: none,
    footer: none,
  )
  
  // Grid a due colonne: sinistra più larga
  grid(
    columns: (1.5fr, 1fr),
    gutter: 1.2em,

    // === COLONNA SINISTRA ===
    [
      // Immagine principale con bordo dorato
      #if immagine-principale != none {
        box(
          stroke: 3pt + geko-gold.darken(15%),
          radius: 0pt,
          clip: true,
          image(immagine-principale, width: 100%)
        )
      }

      #v(1.2em)

      // Box EDITORIALE con bordo dorato completo (rettangolo chiuso)
      #block(
        width: 100%,
        stroke: 3pt + geko-gold,
        inset: 12pt,
        [
          #text(size: 14pt, weight: "bold", fill: geko-gold)[EDITORIALE]
          #v(0.5em)

          #set text(size: 9pt, fill: geko-dark)
          #set par(justify: true, leading: 0.55em)
          #editoriale-testo

          #v(0.6em)
          #text(size: 9pt, weight: "bold", fill: geko-dark)[#editoriale-autore]
        ]
      )
    ],

    // === COLONNA DESTRA ===
    [
      // Header: numero e data
      #align(right)[
        #text(size: 10pt, fill: geko-dark)[Nr. #numero | #mese – #anno]
      ]
      #v(1em)

      // Titolo "IN EVIDENZA" in box magenta (larghezza intera colonna)
      #block(
        width: 100%,
        fill: geko-magenta,
        inset: (x: 14pt, y: 8pt),
        radius: 0pt,
        align(right, text(size: 20pt, weight: "bold", fill: white, tracking: 1pt)[IN EVIDENZA])
      )

      #v(1.5em)

      // Lista evidenze
      #for ev in evidenze {
        block(width: 100%, below: 1em)[
          // Titolo evidenza in magenta bold
          #text(size: 10pt, weight: "bold", fill: geko-magenta)[#upper(ev.titolo):]
          #v(0.25em)
          // Descrizione
          #set text(size: 9pt, fill: geko-dark)
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
// Logo grande centrato + sottotitolo
// ============================================

#let pagina-logo(
  numero: "66",
  mese: "Agosto",
  anno: "2025",
  logo-rivista: none,
  sottotitolo-testo: "Il GEKO RADIO MAGAZINE – Rivista aperiodica del Mountain QRP Club.",
) = {
  set page(
    paper: "a4",
    margin: (top: 2cm, bottom: 2cm, left: 2cm, right: 2cm),
    header: align(right)[#page-number-box()],
    footer: align(center)[
      #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
    ],
  )

  v(1fr)

  align(center)[
    #if logo-rivista != none {
      image(logo-rivista, width: 65%)
    }

    #v(1.5em)

    #text(size: 12pt, style: "italic", weight: "bold", fill: geko-magenta)[#sottotitolo-testo]
  ]

  v(2fr)

  pagebreak()
}

// ============================================
// SOMMARIO (Pagina 3)
// Titolo dorato + outline personalizzato
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

  // Titolo SOMMARIO
  text(size: 22pt, weight: "bold", fill: geko-gold, tracking: 1pt)[SOMMARIO]
  v(3pt)
  line(length: 100%, stroke: 2pt + geko-gold)
  v(1.2em)

  // Stile outline - usa lo stile predefinito con personalizzazione minima
  show outline.entry.where(level: 1): it => {
    v(0.3em)
    strong(it)
  }

  outline(
    title: none,
    indent: auto,
    depth: 2,
  )

  pagebreak()
}

// ============================================
// SETUP DOCUMENTO PRINCIPALE
// Usare per impaginare gli articoli
// ============================================

#let geko-magazine(
  numero: "66",
  mese: "Agosto",
  anno: "2025",
  contenuto
) = {
  // Metadata documento
  set document(
    title: "Geko Radio Magazine - Nr. " + numero,
    author: "Mountain QRP Club",
  )

  // Impostazioni pagina standard per articoli
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2cm, left: 2cm, right: 2cm),
    header: {
      grid(
        columns: (1fr, auto),
        align(left + horizon)[
          #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
        ],
        align(right + horizon)[#page-number-box()]
      )
      v(-0.2em)
      line(length: 100%, stroke: 0.5pt + geko-gold)
    },
    footer: align(center)[
      #text(size: 9pt, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
    ],
  )

  // Font principale (Latin Modern Roman simile a Libertine)
  set text(
    font: ("Latin Modern Roman", "DejaVu Serif", "FreeSerif"),
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

  // Heading senza numerazione
  set heading(numbering: none)

  // H1 = Titolo articolo principale (inizia a pagina nuova)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    titolo-articolo(it.body)
  }

  // H2 = Sottosezione (maiuscolo magenta)
  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 12pt, weight: "bold", fill: geko-magenta)[#upper(it.body)]
    v(0.4em)
  }

  // H3 = Sotto-sottosezione
  show heading.where(level: 3): it => {
    v(0.5em)
    text(size: 11pt, weight: "bold", fill: geko-dark)[#it.body]
    v(0.3em)
  }

  // Link in magenta
  show link: it => text(fill: geko-magenta)[#it]

  // Liste puntate con bullet dorato
  set list(marker: text(fill: geko-gold, size: 8pt)[●])

  // Liste numerate
  set enum(numbering: "1.")

  contenuto
}

// ============================================
// PAGINA TEAM MQC
// Per la pagina finale con i membri del team
// ============================================

#let pagina-team(
  membri: (),
) = {
  titolo-articolo("MQC TEAM")
  
  // Grid per i membri (3 colonne)
  if membri.len() > 0 {
    let cols = 3
    grid(
      columns: (1fr,) * cols,
      gutter: 1em,
      ..membri.map(m => {
        align(center)[
          #if m.at("foto", default: none) != none {
            image(m.foto, width: 80%)
          }
          #v(0.3em)
          #text(weight: "bold", size: 10pt, fill: geko-magenta)[#m.nominativo #m.nome]
          #v(0.1em)
          #text(size: 9pt)[#m.ruolo]
        ]
      })
    )
  }
}

// ============================================
// PAGINA BENVENUTO NUOVI SOCI
// ============================================

#let benvenuto-soci(
  soci: (),
  totale: 0,
) = {
  titolo-articolo("Un benvenuto a…")
  
  text(size: 10pt)[Ecco i nostri nuovi soci:]
  v(0.5em)
  
  // Tabella soci (5 colonne)
  if soci.len() > 0 {
    let cols = 5
    let rows = calc.ceil(soci.len() / cols)
    
    table(
      columns: (1fr,) * cols,
      stroke: 0.5pt + geko-dark.lighten(70%),
      inset: 4pt,
      ..soci.map(s => text(size: 8pt)[#s])
    )
  }
  
  v(0.5em)
  text(size: 11pt, weight: "bold")[E siamo #totale!]
}

// ============================================
// FIGURE CON DIDASCALIA
// ============================================

#let figura(percorso, didascalia: none, larghezza: 100%) = {
  figure(
    image(percorso, width: larghezza),
    caption: if didascalia != none { 
      text(size: 9pt, style: "italic")[#didascalia] 
    },
    supplement: none,
    numbering: none,
  )
}

// ============================================
// ESPORTAZIONI
// Tutte le funzioni principali sono disponibili
// ============================================
