// GEKO Radio Magazine Template
// Mountain QRP Club - Replica fedele del layout originale
// Versione 2.0 - Migliorata

// ============================================
// COLORI ESATTI DALLA RIVISTA
// ============================================

#let geko-gold = rgb("#C4A35A")      // Oro per box pagina, filetti, cornici, header tabelle (non per testo)
#let geko-magenta = rgb("#C7338C")   // Magenta per IN EVIDENZA, titoli articoli, link
#let geko-dark = rgb("#333333")      // Testo principale scuro
#let geko-light = rgb("#F8F8F8")     // Sfondo chiaro per tabelle alternate
#let geko-white = rgb("#FFFFFF")     // Bianco

// Oro per TESTO su bianco: geko-gold fa 2.40:1, questo 4.54:1 (WCAG AA).
// geko-gold resta per filetti, cornici e fondi.
#let geko-gold-testo = rgb("#8F7233")

// Colori funzionali (alert e pagina finale), fuori dall'identità oro/magenta
#let geko-verde = rgb("#2E7D32")     // alert tip — 4.83:1 su geko-light
#let geko-arancio = rgb("#BA5502")   // alert warning — 4.51:1 (era #ED6C02, 2.93:1)
#let geko-rosso = rgb("#D32F2F")     // alert caution — 4.69:1
#let geko-blu = rgb("#1A4A6E")       // appelli della pagina finale

// ============================================
// SCALA TIPOGRAFICA (unica per tutto il documento)
// Corpo 11.5pt; ogni livello di titolo è più grande del corpo e
// distinguibile dal successivo. Usata da `stile-geko`, dalle funzioni
// titolo/sottotitolo/autore e dalla copertina (editoriale).
// ============================================

#let geko-font = ("Libertinus Serif", "Linux Libertine O", "DejaVu Serif")
#let geko-size = (
  corpo: 11.5pt,
  h1: 18pt,      // titolo articolo (maiuscolo magenta, riga oro)
  h2: 14pt,      // sezione (maiuscolo magenta)
  h3: 12.5pt,    // sottosezione (grassetto scuro)
  h4: 11.5pt,    // paragrafo (grassetto corsivo scuro)
  sottotitolo: 13pt,
  autore: 10.5pt,
  piccolo: 9pt,  // header/footer, didascalie, tabelle
  // Elementi fissi (copertina, pagine speciali): tutti i corpi passano da qui
  minimo: 8pt,           // griglia nuovi soci, bullet
  nota: 10pt,            // numero pagina, Nr./data, titoli evidenze, nomi team, rimandi
  invito: 11pt,          // inviti di chiusura (team, pagina finale)
  invito-forte: 12pt,    // motto pag. 2, "Modulo d'iscrizione", "E siamo N!"
  etichetta: 14pt,       // EDITORIALE
  appello-sub: 16pt,     // titolo donazione
  testata: 18pt,         // "Il Geko Radio Magazine", appelli pagina finale
  evidenza: 20pt,        // IN EVIDENZA
  sommario: 22pt,        // SOMMARIO
)

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
      text(fill: geko-dark, weight: "bold", size: geko-size.nota)[#page-num]
    )
  }
}

// ============================================
// FUNZIONE: Titolo articolo principale
// (maiuscolo, magenta, linea oro sotto)
// ============================================

#let titolo-articolo(testo) = {
  block(width: 100%, above: 1em, below: 1em, sticky: true)[
    #set par(justify: false)
    #text(size: geko-size.h1, weight: "bold", fill: geko-magenta, tracking: 0.5pt)[#upper(testo)]
    #v(4pt)
    #line(length: 100%, stroke: 2pt + geko-gold)
  ]
}

// ============================================
// FUNZIONE: Sottotitolo (occhiello) dell'articolo
// Corsivo magenta: si distingue dai titoli di sezione (maiuscoli)
// ============================================

#let sottotitolo-sezione(testo) = {
  block(width: 100%, above: 0.4em, below: 0.6em, sticky: true)[
    #set par(justify: false)
    #text(size: geko-size.sottotitolo, style: "italic", fill: geko-magenta)[#testo]
  ]
}

// ============================================
// FUNZIONE: Autore articolo
// ============================================

#let autore(nominativo, nome: none) = {
  block(width: 100%, above: 0.2em, below: 1.2em, sticky: true)[
    #set text(size: geko-size.autore, style: "italic")
    #if nome != none [#nome #nominativo] else [#nominativo]
  ]
}

// ============================================
// STILE TIPOGRAFICO GEKO
// Font, corpo, paragrafi, gerarchia titoli, link, liste, tabelle.
// Applicato da copertina/pagina-logo/sommario/geko-magazine, così
// editoriale e articoli condividono la stessa resa grafica.
// Usabile anche direttamente: `#show: stile-geko`.
// ============================================

#let stile-geko(contenuto) = {
  set text(
    font: geko-font,
    size: geko-size.corpo,
    lang: "it",
    fill: geko-dark,
  )

  // Paragrafi giustificati
  set par(
    justify: true,
    leading: 0.68em,
    spacing: 1em,
    first-line-indent: 0em,
  )

  // Heading senza numerazione
  set heading(numbering: none)

  // Tabelle da markdown (cmarker emette #table nativo) con look GEKO
  set table(
    fill: (x, y) => if y == 0 { geko-gold } else if calc.odd(y) { geko-light } else { geko-white },
    stroke: 0.5pt + geko-dark.lighten(60%),
    inset: 6pt,
  )
  show table.cell.where(y: 0): set text(fill: geko-dark, weight: "bold", size: geko-size.piccolo)
  show table: set text(size: geko-size.piccolo)

  // H1 = Titolo articolo principale (inizia a pagina nuova)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    titolo-articolo(it.body)
  }

  // H2 = Sezione (maiuscolo magenta)
  show heading.where(level: 2): it => {
    block(width: 100%, above: 1.4em, below: 0.6em, sticky: true)[
      #set par(justify: false)
      #text(size: geko-size.h2, weight: "bold", fill: geko-magenta, tracking: 0.3pt)[#upper(it.body)]
    ]
  }

  // H3 = Sottosezione (grassetto scuro)
  show heading.where(level: 3): it => {
    block(width: 100%, above: 1.2em, below: 0.5em, sticky: true)[
      #set par(justify: false)
      #text(size: geko-size.h3, weight: "bold", fill: geko-dark)[#it.body]
    ]
  }

  // H4+ = Paragrafo (grassetto corsivo scuro)
  show heading.where(level: 4): it => {
    block(width: 100%, above: 1em, below: 0.4em, sticky: true)[
      #set par(justify: false)
      #text(size: geko-size.h4, weight: "bold", style: "italic", fill: geko-dark)[#it.body]
    ]
  }

  // Link in magenta
  show link: it => text(fill: geko-magenta)[#it]

  // Liste puntate con bullet dorato
  set list(marker: text(fill: geko-gold, size: geko-size.minimo)[●])

  // Liste numerate
  set enum(numbering: "1.")

  contenuto
}

// ============================================
// PAGINA STANDARD (tutte le pagine interne)
// Header: testata + numero pagina, riga oro; footer: testata.
// Ritorna il dizionario di argomenti per `set page(..)`.
// ============================================

#let pagina-standard(numero, mese, anno) = (
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2cm, left: 2cm, right: 2cm),
  header: {
    grid(
      columns: (1fr, auto),
      align(left + horizon)[
        #text(size: geko-size.piccolo, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
      ],
      align(right + horizon)[#page-number-box()]
    )
    v(-0.2em)
    line(length: 100%, stroke: 0.5pt + geko-gold)
  },
  footer: align(center)[
    #text(size: geko-size.piccolo, fill: geko-dark)[Geko Radio Magazine – Nr. #numero | #mese - #anno]
  ],
)

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

// Colori bordo/titolo per tipo di alert (GitHub-style)
#let _alert-colori = (
  note:      (bordo: geko-gold,        titolo: geko-magenta),
  tip:       (bordo: geko-verde,       titolo: geko-verde),
  warning:   (bordo: geko-arancio,     titolo: geko-arancio),
  important: (bordo: geko-magenta,     titolo: geko-magenta),
  caution:   (bordo: geko-rosso,       titolo: geko-rosso),
)

#let box-evidenza(titolo: none, tipo: "note", contenuto) = {
  let c = _alert-colori.at(tipo, default: _alert-colori.note)
  block(
    width: 100%,
    fill: geko-light,
    inset: 12pt,
    radius: 3pt,
    stroke: 0.5pt + c.bordo,
    [
      #if titolo != none and titolo != "" {
        text(weight: "bold", fill: c.titolo)[#titolo]
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
        else { geko-white }
      },
      stroke: 0.5pt + geko-dark.lighten(60%),
      inset: 6pt,
      align: (col, row) => if row == 0 { center } else { left },
      ..intestazioni.map(h => text(fill: geko-dark, weight: "bold", size: geko-size.piccolo)[#h]),
      ..righe.flatten().map(c => text(size: geko-size.piccolo)[#c])
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

  // Stesso font/corpo/titoli degli articoli: l'editoriale (Markdown reso
  // via cmarker) deve avere la stessa resa grafica del resto della rivista.
  show: stile-geko

  // Spigoli arrotondati delle due cornici dorate
  let raggio-cornice = 10pt

  // Colonna destra (IN EVIDENZA) — invariata, estratta per riuso
  let colonna-destra = block(
    width: 100%,
    height: 100%,
    stroke: 3pt + geko-gold,
    radius: raggio-cornice,
    inset: 12pt,
    [
      // Header: numero e data
      #align(right)[
        #text(size: geko-size.nota, fill: geko-dark)[Nr. #numero | #mese – #anno]
      ]
      #v(1em)

      // Titolo "IN EVIDENZA" in box magenta (larghezza intera)
      #block(
        width: 100%,
        fill: geko-magenta,
        inset: (x: 14pt, y: 8pt),
        radius: 5pt,
        align(right, text(size: geko-size.evidenza, weight: "bold", fill: geko-white, tracking: 1pt)[IN EVIDENZA])
      )

      #v(1.5em)

      // Lista evidenze
      #for ev in evidenze {
        block(width: 100%, below: 1em)[
          #text(size: geko-size.nota, weight: "bold", fill: geko-magenta)[#upper(ev.titolo):]
          #v(0.25em)
          #set text(size: geko-size.piccolo, fill: geko-dark)
          #set par(justify: true, leading: 0.5em)
          #ev.descrizione
        ]
      }
    ]
  )

  // Frammenti della colonna sinistra (definiti una volta, misurati e resi)
  let intestazione = {
    if immagine-principale != none {
      image(immagine-principale, width: 100%)
    }
    v(1.2em)
    text(size: geko-size.testata, weight: "bold", fill: geko-magenta)[Il Geko Radio Magazine]
    v(0.3em)
    text(size: geko-size.etichetta, weight: "bold", fill: geko-gold-testo)[EDITORIALE]
    v(0.5em)
  }
  // Corpo: eredita font/corpo/paragrafi da stile-geko (identici agli articoli)
  let corpo-editoriale = editoriale-testo
  let firma = {
    v(0.6em)
    text(weight: "bold", fill: geko-dark)[#editoriale-autore]
  }

  // Decidiamo layout in base allo spazio: se l'editoriale entra nella colonna
  // lo mostriamo per intero; altrimenti teaser troncato + rimando + pagina dedicata.
  context {
    // Geometria pagina (A4 meno i margini impostati sopra): 21-1.5-1.5, 29.7-1.2-1.5
    let regione = (width: 18cm, height: 27cm)
    let gutter = 0.5cm
    let larghezza-col = (regione.width - gutter) * 1.5 / 2.5
    let larghezza-interna = larghezza-col - 24pt   // inset 12pt * 2
    let altezza-interna = regione.height - 24pt

    let h-intestazione = measure(box(width: larghezza-interna, intestazione)).height
    let h-firma = measure(box(width: larghezza-interna, firma)).height
    let h-editoriale = measure(box(width: larghezza-interna, corpo-editoriale)).height

    // La pagina di continuazione è sempre quella subito dopo la copertina.
    let pag-continua = counter(page).get().first() + 1
    let nota-continua = {
      v(0.4em)
      text(size: geko-size.nota, style: "italic", fill: geko-magenta, weight: "bold")[
        → L'editoriale continua a pag. #pag-continua
      ]
    }

    // Decisione (stima): l'editoriale entra nello spazio residuo della colonna?
    let spazio-inline = altezza-interna - h-intestazione - h-firma
    let overflow = editoriale-testo != none and h-editoriale > spazio-inline

    // Teaser troncato a riga intera: un clip ad altezza fissa taglierebbe
    // l'ultima riga a metà. Il testo viene invece impaginato in 2 colonne
    // alte quanto lo spazio residuo: il flusso di Typst va a capo colonna
    // solo tra righe intere, e il box esterno mostra solo la prima colonna.
    let teaser = layout(spazio => {
      let g = 1cm
      box(width: spazio.width, height: spazio.height, clip: true,
        block(width: 2 * spazio.width + g, height: spazio.height,
          columns(2, gutter: g, corpo-editoriale)))
    })

    // Il layout della colonna usa un grid (auto, 1fr, auto): la riga centrale
    // riempie esattamente lo spazio residuo, così il teaser e la nota/firma
    // restano sempre dentro il box, senza calcoli d'altezza a mano.
    let colonna-sinistra = block(
      width: 100%,
      height: 100%,
      stroke: 3pt + geko-gold,
      radius: raggio-cornice,
      inset: 12pt,
      grid(
        rows: (auto, 1fr, auto),
        row-gutter: 0pt,
        intestazione,
        if overflow {
          teaser
        } else {
          corpo-editoriale
        },
        if overflow { nota-continua } else { firma },
      )
    )

    grid(
      columns: (1.5fr, 1fr),
      gutter: gutter,
      colonna-sinistra,
      colonna-destra,
    )

    pagebreak()

    // Pagina editoriale dedicata (solo se l'editoriale non entrava in copertina)
    // Impaginata come un articolo: stessa pagina standard (testata, riga
    // oro, numero), stesso titolo (maiuscolo magenta) e stesso corpo.
    if overflow {
      set page(..pagina-standard(numero, mese, anno))
      titolo-articolo("Editoriale")
      editoriale-testo
      v(0.8em)
      align(right, text(weight: "bold", fill: geko-dark)[#editoriale-autore])
      pagebreak()
    }
  }
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
  set page(..pagina-standard(numero, mese, anno))
  show: stile-geko

  v(1fr)

  align(center)[
    #if logo-rivista != none {
      image(logo-rivista, width: 65%)
    }

    #v(1.5em)

    #text(size: geko-size.invito-forte, style: "italic", weight: "bold", fill: geko-magenta)[#sottotitolo-testo]
  ]

  v(2fr)

  pagebreak()
}

// ============================================
// SOMMARIO (Pagina 3)
// Titolo dorato + outline personalizzato
// ============================================

#let sommario(numero: "66", mese: "Agosto", anno: "2025") = {
  set page(..pagina-standard(numero, mese, anno))
  show: stile-geko

  // Titolo SOMMARIO
  text(size: geko-size.sommario, weight: "bold", fill: geko-gold-testo, tracking: 1pt)[SOMMARIO]
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

  // Impostazioni pagina standard per articoli (condivise con editoriale,
  // pagina logo e sommario) + stile tipografico unico
  set page(..pagina-standard(numero, mese, anno))
  show: stile-geko

  contenuto
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
  
  text(size: geko-size.nota)[Ecco i nostri nuovi soci:]
  v(0.8em)
  
  // Tabella soci (5 colonne)
  if soci.len() > 0 {
    table(
      columns: (1fr,) * 5,
      stroke: 0.5pt + geko-dark.lighten(70%),
      inset: 5pt,
      align: center,
      ..soci.map(s => text(size: geko-size.minimo)[#s])
    )
  }
  
  v(0.8em)
  text(size: geko-size.invito-forte, weight: "bold")[E siamo #totale!]
  
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
        #text(weight: "bold", size: geko-size.nota, fill: geko-magenta)[#m.nominativo #m.nome]
        #v(0.15em)
        #text(size: geko-size.piccolo)[#m.ruolo]
        #if m.at("ruolo2", default: none) != none {
          linebreak()
          text(size: geko-size.piccolo)[#m.ruolo2]
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
    #text(size: geko-size.invito)[Per iscriversi al nostro club:]
    #v(0.3em)
    #if link-iscrizione != none {
      link(link-iscrizione, text(size: geko-size.invito-forte, weight: "bold", fill: geko-magenta)[Modulo d'iscrizione])
    } else {
      text(size: geko-size.invito-forte, weight: "bold", fill: geko-magenta)[Modulo d'iscrizione]
    }
  ]
  
  v(1em)
  
  align(center)[
    #text(size: geko-size.invito, weight: "bold")[Sono graditi i contributi dei lettori, particolarmente con articoli]
    #linebreak()
    #text(size: geko-size.invito, weight: "bold")[tecnici e di autocostruzione.]
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
    #text(size: geko-size.invito)[Per chi desidera ricevere questo Bollettino può iscriversi alla]
    #linebreak()
    #text(size: geko-size.invito)[nostra ]
    #if link-lista-distribuzione != none {
      link(link-lista-distribuzione, text(weight: "bold", fill: geko-magenta)[Lista di Distribuzione])
    } else {
      text(weight: "bold", fill: geko-magenta)[Lista di Distribuzione]
    }
    #text(size: geko-size.invito)[.]
  ]
  
  v(2em)
  
  // Invito diffusione - testo grande blu scuro
  align(center)[
    #text(size: geko-size.testata, weight: "bold", fill: geko-blu)[Diffondete il Geko Radio Magazine]
    #linebreak()
    #text(size: geko-size.testata, weight: "bold", fill: geko-blu)[fra i Vostri amici.]
  ]
  
  v(2.5em)
  
  // Sezione donazione
  align(center)[
    #text(size: geko-size.appello-sub, weight: "bold", fill: geko-blu)[Aiutaci a sostenere il Mountain QRP Club!]
  ]
  
  v(1em)
  
  align(center)[
    #text(size: geko-size.nota)[Ci stiamo mettendo tanta dedizione per offrirti un servizio sempre ai massimi livelli. Un tuo]
    #linebreak()
    #text(size: geko-size.nota)[piccolo contributo è importante, anche del valore di un semplice caffè.]
    #linebreak()
    #text(size: geko-size.nota)[Grazie.]
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
      text(size: geko-size.piccolo, style: "italic")[#didascalia]
    },
    supplement: none,
    numbering: none,
  )
}

// ============================================
// SCOPE per cmarker.render: reindirizza gli elementi markdown
// alle funzioni di stile GEKO senza toccare la prosa.
// ============================================

#let geko-md-scope = (
  // Link markdown -> #link-geko. dest può essere una label (anchor interni): in
  // quel caso si usa il link nativo.
  link: (dest, body) => if type(dest) == str {
    link-geko(dest, testo: body)
  } else {
    link(dest, body)
  },
  // Fallback per immagini dentro la prosa (le immagini "da sole" le gestisce il
  // segmenter Python emettendo #figura/#grid direttamente).
  image: (src, alt: none, ..args) => figura(src, didascalia: alt),
)

// ============================================
// ESPORTAZIONI
// Tutte le funzioni principali sono disponibili
// ============================================
