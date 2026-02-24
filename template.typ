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
    #set par(justify: false)
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
  align(center,
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
      ..{
        let cells = ()
        for row in righe {
          for c in row {
            cells.push({ set text(size: 9pt); c })
          }
        }
        cells
      }
    )
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
// Layout: 2 colonne con bordi dorati fino a fondo pagina
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

    // === COLONNA SINISTRA - Box unico con bordo dorato ===
    block(
      width: 100%,
      height: 100%,
      stroke: 3pt + geko-gold,
      inset: 12pt,
      [
        // Immagine principale
        #if immagine-principale != none {
          image(immagine-principale, width: 100%)
        }

        #v(1.2em)

        // Titolo rivista + sottotitolo editoriale
        #text(size: 18pt, weight: "bold", fill: geko-magenta)[Il Geko Radio Magazine]
        #v(0.3em)
        #text(size: 14pt, weight: "bold", fill: geko-gold)[EDITORIALE]
        #v(0.5em)

        #set text(size: 11pt, fill: geko-dark)
        #set par(justify: true, leading: 0.55em)
        #editoriale-testo

        #v(0.6em)
        #text(size: 11pt, weight: "bold", fill: geko-dark)[#editoriale-autore]
      ]
    ),

    // === COLONNA DESTRA - Box unico con bordo dorato ===
    block(
      width: 100%,
      height: 100%,
      stroke: 3pt + geko-gold,
      inset: 12pt,
      [
        // Header: numero e data
        #align(right)[
          #text(size: 10pt, fill: geko-dark)[Nr. #numero | #mese – #anno]
        ]
        #v(1em)

        // Titolo "IN EVIDENZA" in box magenta (larghezza intera)
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
    depth: 1,
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
    size: 12pt,
    lang: "it",
    fill: geko-dark,
  )

  // Paragrafi giustificati
  set par(
    justify: true,
    leading: 0.65em,
    spacing: 1.1em,
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
// PAGINA BENVENUTO NUOVI SOCI (pag 19)
// ============================================

#let benvenuto-soci(
  soci: (),
  totale: 0,
  logo-club: none,
) = {
  titolo-articolo("Un benvenuto a…")
  
  text(size: 10pt)[Ecco i nostri nuovi soci:]
  v(0.8em)
  
  // Tabella soci (5 colonne)
  if soci.len() > 0 {
    table(
      columns: (1fr,) * 5,
      stroke: 0.5pt + geko-dark.lighten(70%),
      inset: 5pt,
      align: center,
      ..soci.map(s => text(size: 8pt)[#s])
    )
  }
  
  v(0.8em)
  text(size: 12pt, weight: "bold")[E siamo #totale!]
  
  // Logo club centrato
  if logo-club != none {
    v(1em)
    align(center, image(logo-club, width: 35%))
  }
}

// ============================================
// PAGINA TEAM MQC (pag 20)
// Layout: righe con membri, poi info iscrizione
// ============================================

#let pagina-team(
  membri: (),
  link-iscrizione: none,
) = {
  titolo-articolo("MQC TEAM")
  
  // Grid per i membri - layout flessibile
  if membri.len() > 0 {
    // Prima riga: 4 membri (presidente, consigliere, consigliere, vice)
    // Seconda riga: 2 membri centrati (segretario, consigliere)
    // Terza riga: 3 membri (manager vari)
    
    let render-membro(m) = {
      align(center)[
        #if m.at("foto", default: none) != none {
          image(m.foto, width: 90%)
        }
        #v(0.4em)
        #text(weight: "bold", size: 10pt, fill: geko-magenta)[#m.nominativo #m.nome]
        #v(0.15em)
        #text(size: 9pt)[#m.ruolo]
        #if m.at("ruolo2", default: none) != none {
          linebreak()
          text(size: 9pt)[#m.ruolo2]
        }
      ]
    }
    
    // Riga 1: primi 4 membri
    if membri.len() >= 4 {
      grid(
        columns: (1fr,) * 4,
        gutter: 0.8em,
        ..membri.slice(0, 4).map(render-membro)
      )
    }
    
    v(1.2em)
    
    // Riga 2: membri 5-6 centrati
    if membri.len() >= 6 {
      align(center)[
        #grid(
          columns: (1fr, 1fr),
          gutter: 2em,
          ..membri.slice(4, 6).map(render-membro)
        )
      ]
    }
    
    v(1.2em)
    
    // Riga 3: membri 7-9
    if membri.len() >= 9 {
      grid(
        columns: (1fr,) * 3,
        gutter: 0.8em,
        ..membri.slice(6, 9).map(render-membro)
      )
    }
    
    // Eventuali altri membri
    if membri.len() > 9 {
      v(1em)
      grid(
        columns: (1fr,) * 3,
        gutter: 0.8em,
        ..membri.slice(9).map(render-membro)
      )
    }
  }
  
  v(1.5em)
  
  // Link iscrizione
  align(center)[
    #text(size: 11pt)[Per iscriversi al nostro club:]
    #v(0.3em)
    #if link-iscrizione != none {
      link(link-iscrizione, text(size: 12pt, weight: "bold", fill: geko-magenta)[Modulo d'iscrizione])
    } else {
      text(size: 12pt, weight: "bold", fill: geko-magenta)[Modulo d'iscrizione]
    }
  ]
  
  v(1em)
  
  align(center)[
    #text(size: 11pt, weight: "bold")[Sono graditi i contributi dei lettori, particolarmente con articoli]
    #linebreak()
    #text(size: 11pt, weight: "bold")[tecnici e di autocostruzione.]
  ]
}

// ============================================
// PAGINA FINALE (pag 21)
// Lista distribuzione, diffusione, donazione
// ============================================

#let pagina-finale(
  link-lista-distribuzione: none,
  link-donazione: none,
  immagine-frequenze: none,
  immagine-donazione: none,
) = {
  v(2em)
  
  // Invito lista distribuzione
  align(center)[
    #text(size: 11pt)[Per chi desidera ricevere questo Bollettino può iscriversi alla]
    #linebreak()
    #text(size: 11pt)[nostra ]
    #if link-lista-distribuzione != none {
      link(link-lista-distribuzione, text(weight: "bold", fill: geko-magenta)[Lista di Distribuzione])
    } else {
      text(weight: "bold", fill: geko-magenta)[Lista di Distribuzione]
    }
    #text(size: 11pt)[.]
  ]
  
  v(2em)
  
  // Invito diffusione - testo grande blu scuro
  align(center)[
    #text(size: 18pt, weight: "bold", fill: rgb("#1a4a6e"))[Diffondete il Geko Radio Magazine]
    #linebreak()
    #text(size: 18pt, weight: "bold", fill: rgb("#1a4a6e"))[fra i Vostri amici.]
  ]
  
  v(2.5em)
  
  // Sezione donazione
  align(center)[
    #text(size: 16pt, weight: "bold", fill: rgb("#1a4a6e"))[Aiutaci a sostenere il Mountain QRP Club!]
  ]
  
  v(1em)
  
  align(center)[
    #text(size: 10pt)[Ci stiamo mettendo tanta dedizione per offrirti un servizio sempre ai massimi livelli. Un tuo]
    #linebreak()
    #text(size: 10pt)[piccolo contributo è importante, anche del valore di un semplice caffè.]
    #linebreak()
    #text(size: 10pt)[Grazie.]
  ]
  
  v(1.5em)
  
  // Immagini frequenze e donazione affiancate
  grid(
    columns: (1fr, 1fr),
    gutter: 2em,
    align(center)[
      #if immagine-frequenze != none {
        image(immagine-frequenze, width: 80%)
      }
    ],
    align(center)[
      #if immagine-donazione != none {
        if link-donazione != none {
          link(link-donazione, image(immagine-donazione, width: 60%))
        } else {
          image(immagine-donazione, width: 60%)
        }
      }
    ]
  )
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
