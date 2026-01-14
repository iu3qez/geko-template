// Esempio GEKO Radio Magazine Nr. 67 - Versione semplificata
#import "template.typ": *

#show: geko-magazine.with(
  numero: "67",
  mese: "Settembre",
  anno: "2025",
)

// ============================================
// EDITORIALE
// ============================================

= Editoriale

#sottotitolo[Bentornati dopo la pausa estiva!]
#autore("IU3QEZ", nome: "Simone")

L'estate è volata, ma non siamo rimasti con le mani in mano. Tra attivazioni in quota, sperimentazioni e qualche meritato riposo, la comunità MQC ha continuato a farsi sentire sulle bande.

In questo numero troverete diversi contributi interessanti: dal report sulle attività estive dei soci, a qualche spunto tecnico per chi vuole cimentarsi nell'autocostruzione autunnale.

Un ringraziamento speciale a tutti coloro che hanno inviato articoli e foto. Il Geko vive grazie a voi!

72 de Simone IU3QEZ

#separatore()

// ============================================
// ARTICOLO 1
// ============================================

= Attività Estive dei Soci

#sottotitolo[Un'estate ricca di attivazioni]

L'estate 2025 ha visto numerose attivazioni da parte dei soci MQC. Ecco un breve riepilogo delle più significative.

== Monte Rosa - IK2ABC

Marco IK2ABC ha raggiunto la Capanna Margherita a 4554m s.l.m., stabilendo diversi collegamenti in 20m CW con soli 5W e un dipolo portatile.

#box-evidenza(titolo: "Highlights")[
  - QSO più lontano: VK3XYZ (14.500 km)
  - Potenza: 5W
  - Antenna: Dipolo 20m autocostruito
  - Modo: CW
]

== Dolomiti - IV3XYZ

Giovanni IV3XYZ ha attivato diverse cime delle Dolomiti durante il mese di agosto, accumulando oltre 200 QSO in QRP.

La sua configurazione leggera, basata su un QCX+ e un'antenna EFHW, si è dimostrata vincente per le attivazioni in quota.

#separatore()

// ============================================
// ARTICOLO TECNICO
// ============================================

= Costruiamo un RTX QRP per i 40m

#sottotitolo[Un progetto semplice per iniziare]
#autore("IK0BDO", nome: "Roberto")

Molti soci mi chiedono da dove iniziare con l'autocostruzione. La risposta è sempre la stessa: partite da qualcosa di semplice ma funzionale.

== Il circuito

Il cuore del trasmettitore è un oscillatore Pierce con un cristallo a 7.030 MHz, seguito da un buffer e un PA finale con un IRF510.

#box-evidenza(titolo: "Lista componenti")[
  - 1x Cristallo 7.030 MHz
  - 1x IRF510 (finale)
  - 2x 2N2222 (oscillatore e buffer)
  - Condensatori e resistenze vari
  - Trasformatore toroidale T50-43
]

== Taratura

La taratura è semplice: basta regolare il trimmer del VXO per centrare la frequenza desiderata e poi ottimizzare l'impedenza del finale per massimizzare la potenza di uscita.

Con un'alimentazione a 12V si ottengono circa 3-4W, sufficienti per collegamenti DX in CW.

== Risultati

Ho testato il TX durante il weekend e sono riuscito a collegare diverse stazioni europee, inclusa una S5 che mi ha dato 559. Non male per un apparato costruito con componenti di recupero!

#separatore()

// ============================================
// RUBRICHE
// ============================================

= Nuovi Soci

#sottotitolo[Benvenuti nella famiglia MQC!]

Diamo il benvenuto ai nuovi iscritti:

#tabella-geko(
  ("Nominativo", "Numero", "QTH"),
  (
    ("IU1ABC", "#890", "Torino"),
    ("IK2XYZ", "#891", "Milano"),
    ("IV3QRS", "#892", "Udine"),
    ("IZ5TUV", "#893", "Firenze"),
    ("IW8WXY", "#894", "Napoli"),
  )
)

E siamo a 894 soci! Grazie a tutti per la fiducia.

#separatore()

// ============================================
// CHIUSURA
// ============================================

= Il Team MQC

#box-evidenza[
  *Presidente:* Simone IU3QEZ \
  *Vice Presidente:* Raffaele IU2OQK \
  *Segretario:* Carlo IW3HCN \
  *Consiglieri:* Roberto IK0BDO, Gianni IW0HLE, Jhonny IU3MBY
]

#v(1em)

#align(center)[
  #text(size: 14pt, weight: "bold", fill: geko-gold)[
    72 de Mountain QRP Club
  ]
  
  #v(0.5em)
  
  #link-geko("https://www.mqc.it", testo: "www.mqc.it")
]
