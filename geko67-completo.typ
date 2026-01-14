// GEKO Radio Magazine Nr. 67 - Esempio Completo
// Con copertina, sommario automatico e immagini
#import "template.typ": *

// ============================================
// COPERTINA (pagina 1)
// ============================================

#copertina(
  numero: "67",
  mese: "Settembre",
  anno: "2025",
  immagine-principale: "assets/copertina-contest.jpg",
  evidenze: (
    (
      titolo: "Report Attività Estive",
      descrizione: "Una panoramica delle attivazioni QRP dei soci durante l'estate 2025. Cime raggiunte, QSO effettuati e tante avventure.",
    ),
    (
      titolo: "Costruiamo un RTX per i 40m",
      descrizione: "Un progetto semplice per chi vuole iniziare con l'autocostruzione: un trasmettitore CW con pochi componenti.",
    ),
    (
      titolo: "Il Remote Keyer di DL4YHF",
      descrizione: "Come operare in CW da remoto mantenendo il feeling del tasto locale. Software gratuito e ben documentato.",
    ),
    (
      titolo: "Nuovi Soci",
      descrizione: "Benvenuti ai nuovi iscritti! Siamo ormai quasi a quota 900.",
    ),
  ),
  editoriale-testo: [
    Bentornati dopo la pausa estiva! L'estate è volata, ma non siamo rimasti con le mani in mano. Tra attivazioni in quota, sperimentazioni e qualche meritato riposo, la comunità MQC ha continuato a farsi sentire sulle bande.
    
    In questo numero troverete diversi contributi interessanti: dal report sulle attività estive dei soci, a qualche spunto tecnico per chi vuole cimentarsi nell'autocostruzione autunnale.
  ],
  editoriale-autore: "Simone IU3QEZ",
)

// ============================================
// PAGINA LOGO (pagina 2)
// ============================================

#pagina-logo(
  logo-grande: "assets/logo-mqc-grande.png",
  sottotitolo: "Il GEKO RADIO MAGAZINE – Rivista aperiodica del Mountain QRP Club.",
)

// ============================================
// DOCUMENTO PRINCIPALE (da pagina 3)
// ============================================

#show: geko-magazine.with(
  numero: "67",
  mese: "Settembre",
  anno: "2025",
)

// ============================================
// SOMMARIO
// ============================================

#sommario()

// ============================================
// ARTICOLO 1: ATTIVITA' ESTIVE
// ============================================

= Attività Estive dei Soci <attivita-estive>

#sottotitolo[Un'estate ricca di attivazioni QRP]

L'estate 2025 ha visto numerose attivazioni da parte dei soci MQC. Ecco un breve riepilogo delle più significative, con le esperienze raccontate direttamente dai protagonisti.

== Monte Rosa - IK2ABC

Marco IK2ABC ha raggiunto la Capanna Margherita a 4554m s.l.m., stabilendo diversi collegamenti in 20m CW con soli 5W e un dipolo portatile autocostruito.

#box-evidenza(titolo: "Highlights attivazione")[
  *QSO più lontano:* VK3XYZ (14.500 km) \
  *Potenza:* 5W \
  *Antenna:* Dipolo 20m autocostruito \
  *Modo:* CW
]

La condizione di propagazione era eccezionale quel giorno, con aperture verso il Pacifico che hanno permesso collegamenti normalmente impossibili con potenze così ridotte.

== Dolomiti - IV3XYZ

Giovanni IV3XYZ ha attivato diverse cime delle Dolomiti durante il mese di agosto, accumulando oltre 200 QSO in QRP. La sua configurazione leggera, basata su un QCX+ e un'antenna EFHW, si è dimostrata vincente per le attivazioni in quota.

"Il segreto è viaggiare leggeri" racconta Giovanni. "Con meno di 2kg di attrezzatura radio riesco a salire veloce e operare comodamente anche in condizioni difficili."

== Appennino Tosco-Emiliano - IZ5ABC

Luca IZ5ABC ha preferito le quote più accessibili dell'Appennino, attivando una decina di cime tra giugno e agosto. Il suo setup preferito: un FT-817 a 2.5W e una vertical autocostruita per i 40m.

#separatore()

// ============================================
// ARTICOLO 2: TECNICO
// ============================================

= Costruiamo un RTX QRP per i 40m <rtx-40m>

#sottotitolo[Un progetto semplice per iniziare con l'autocostruzione]
#autore("IK0BDO", nome: "Roberto")

Molti soci mi chiedono da dove iniziare con l'autocostruzione. La risposta è sempre la stessa: partite da qualcosa di semplice ma funzionale. Un trasmettitore CW per i 40 metri è il progetto ideale.

== Schema a blocchi

Il cuore del trasmettitore è un oscillatore Pierce con un cristallo a 7.030 MHz, seguito da un buffer e un PA finale con un IRF510. Lo schema è volutamente minimale per ridurre le possibilità di errore.

== Lista componenti

#box-evidenza(titolo: "Componenti necessari")[
  - 1× Cristallo 7.030 MHz (o frequenza QRP preferita)
  - 1× IRF510 (finale di potenza)
  - 2× 2N2222 (oscillatore e buffer)
  - Condensatori ceramici: 100pF, 220pF, 10nF
  - Resistenze: 10Ω, 100Ω, 1kΩ, 10kΩ
  - 1× Trasformatore toroidale T50-43
  - 1× Trimmer 60pF per VXO
]

== Costruzione

Il montaggio può avvenire su una basetta millefori o, per i più esigenti, su un PCB dedicato. L'importante è mantenere i collegamenti corti, specialmente nella sezione RF.

Il trasformatore di uscita richiede un po' di attenzione: avvolgere 10 spire di filo smaltato 0.5mm sul primario e 3 spire sul secondario, entrambi sullo stesso toroide T50-43.

== Taratura

La taratura è semplice: regolare il trimmer del VXO per centrare la frequenza desiderata, poi ottimizzare l'impedenza del finale per massimizzare la potenza di uscita.

Con un'alimentazione a 12V si ottengono circa 3-4W, sufficienti per collegamenti DX in CW. Ho testato il TX durante il weekend e sono riuscito a collegare diverse stazioni europee, inclusa una S5 che mi ha dato 559.

#figura("assets/breakout-board.jpg", didascalia: "Setup di test con breakout board", width: 90%)

#separatore()

// ============================================
// ARTICOLO 3: ATTIVAZIONE CORNO GRANDE
// ============================================

= Attivazione con Bivacco al Corno Grande <corno-grande>

#sottotitolo[Un'avventura radio in alta quota]
#autore("IZ8TXC", nome: "Eugenio")

Riportiamo questa attivazione di Eugenio IZ8TXC, sicuramente meritevole di condivisione per l'impegno e la passione dimostrati.

== Il percorso

Da Campo Imperatore si percorre il sentiero che porta alla Sella di Monte Aquila, da lì si segue per il Sassone e poi per la Direttissima. 

#box-evidenza[
  *17:00* - Partenza da Campo Imperatore \
  *17:32* - Sella di Monte Aquila \
  *18:10* - Sassone \
  *19:10* - Vetta Occidentale (2912m)
]

Siamo ridiscesi l'indomani alle 7:15 dopo aver visto una meravigliosa alba! Il percorso di discesa è passato per la via normale, sella del Brecciaio, fino a Campo Imperatore dove siamo arrivati alle 10:20.

== L'attivazione

Sono riuscito a fare soltanto i collegamenti con il portatile, in quanto si stava facendo buio ed era complicato stendere l'antenna filare visto che lo spazio era poco.

La gente è iniziata a venire già delle 3:30 di notte per vedere l'alba. Alla fine eravamo in nove su quella piccola cengia!

*Radio utilizzate:* ICOM ID-51 e AnyTone 878

#figura("assets/corno-grande-1.jpg", didascalia: "In vetta al Corno Grande", width: 85%)

#figura("assets/corno-grande-2.jpg", didascalia: "Operazione notturna", width: 85%)

#separatore()

// ============================================
// NUOVI SOCI
// ============================================

= Nuovi Soci <nuovi-soci>

#sottotitolo[Benvenuti nella famiglia MQC!]

Diamo il benvenuto ai nuovi iscritti dell'ultimo periodo:

#tabella-geko(
  ("Nominativo", "Nr.", "QTH"),
  (
    ("IU1ABC", "#885", "Torino"),
    ("IK2XYZ", "#886", "Milano"),
    ("IV3QRS", "#887", "Udine"),
    ("IZ5TUV", "#888", "Firenze"),
    ("IW8WXY", "#889", "Napoli"),
    ("IN3ABC", "#890", "Trento"),
    ("IZ0DEF", "#891", "Roma"),
    ("IU4GHI", "#892", "Bologna"),
  )
)

E siamo a 892 soci! Grazie a tutti per la fiducia nel nostro club.

#separatore()

// ============================================
// TEAM MQC
// ============================================

= Il Team MQC <team>

#box-evidenza[
  *Presidente:* Simone IU3QEZ \
  *Vice Presidente:* Raffaele IU2OQK \
  *Segretario:* Carlo IW3HCN \
  *Consiglieri:* Roberto IK0BDO, Gianni IW0HLE, Jhonny IU3MBY
]

#v(0.5em)

*Manager diplomi:*
- Maurizio IV3GVY - QRP Portatile
- Riccardo IU3GKJ - Rifugi e Bivacchi  
- Stefano IK4UXA - Radio e Storia

#v(1em)

#align(center)[
  #box(
    fill: geko-light,
    inset: 12pt,
    radius: 4pt,
  )[
    #text(size: 11pt)[Per iscriversi al club: *www.mqc.it/iscrizione*]
    #v(0.3em)
    #text(size: 10pt, style: "italic")[Sono graditi i contributi dei lettori, particolarmente articoli tecnici e di autocostruzione.]
  ]
]

#v(1.5em)

#align(center)[
  #text(size: 16pt, weight: "bold", fill: geko-gold)[
    72 de Mountain QRP Club
  ]
  
  #v(0.5em)
  
  #link-geko("https://www.mqc.it", testo: "www.mqc.it")
]
