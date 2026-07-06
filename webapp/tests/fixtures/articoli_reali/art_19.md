Parlo spesso del QMX e delle prestazioni straordinarie che ottiene a fronte di un hardware addirittura banale: il ricevitore è un semplice mixer a conversione diretta ed il trasmettitore un generatore di onda quadra, un ponte a MOSFET alimentato da un transistor che ne regola l'inviluppo.

Il QMX è però un kit poco didattico: dall'hardware non si capisce cosa succeda dietro le quinte. Da dove vengono le straordinarie performance? Di certo non lo capiamo dall'hardware e dai pochi componenti analogici presenti.
È tutto, appunto, "dietro le quinte". Per un autocostruttore del 2026 è importante capire cosa succede dietro le quinte. Gli strumenti di oggi ci permettono di avventurarci nella creazione di codice *a patto di conoscerne il funzionamento*. Conoscerne il funzionamento unito a strumenti di Intelligenza Artificiale Generativa può portare le nostre competenze su un altro livello, fino alla creazione di una catena DSP e, volendo, di un intero RTX — oppure semplicemente di un filtro digitale.
Proviamo quindi a fare un percorso per vedere "il dietro le quinte", e partiamo dalla parte forse più innovativa del QMX: la catena di trasmissione.

![Schematico del finale QMX semplificato](QMX_schema_finale.png)

## Un po' di storia

Il problema è vecchio quanto la radio: amplificare in modo efficiente un segnale la cui ampiezza varia nel tempo. Un amplificatore lineare (Classe A/AB) riproduce fedelmente ampiezza e fase, ma dissipa in calore gran parte della potenza — per ogni watt prodotto abbiamo praticamente un watt perso in calore. La fedeltà nella riproduzione permette di trasmettere un segnale modulato in qualsiasi modo (SSB, AM, PSK, CW); un amplificatore commutato (Classe C/D/E/F) è efficientissimo ma "non lineare", cioè non conserva l'ampiezza. Può essere estremamente efficiente ma permette normalmente la trasmissione di segnali CW, FM o comunque "singoli toni" (RTTY).
La modulazione polare nasce proprio per superare questo limite: invece di pretendere linearità, si scompone il segnale in due grandezze — ampiezza (inviluppo) e fase — e le si tratta su percorsi separati, ciascuno con l'hardware più adatto.

Le prime risposte arrivano negli anni '30, in piena epoca delle valvole e della radiodiffusione AM. Nel 1935 Henri Chireix propone l'*outphasing*: due amplificatori ad ampiezza costante (quindi efficienti) le cui uscite, sommate con fase relativa variabile, ricostruiscono l'ampiezza desiderata.[^chireix] L'anno dopo, nel 1936, William Doherty introduce il suo amplificatore, in cui uno stadio "di picco" interviene solo sui picchi di modulazione mantenendo alta l'efficienza media.[^doherty] Sono già due modi per ottenere potenza e rendimento senza un vero amplificatore lineare.

L'antenato diretto della modulazione polare è però del 1952: Leonard Kahn pubblica su *Proc. IRE* la tecnica EER, *Envelope Elimination and Restoration*.[^kahn] L'idea è netta: da un segnale SSB di basso livello si eliminano le variazioni di ampiezza (limitandolo a una fase pura), si amplifica la fase con un efficiente stadio in Classe C, e all'ultimo stadio si ripristina l'inviluppo modulando l'alimentazione. È esattamente la struttura del QMX di oggi — percorso di fase e percorso d'ampiezza che si ricompongono nel finale. Nel 1979 Petrović e Gosling ne pubblicano la variante ad anello (*polar loop*), che aggiunge una retroazione per correggere le imperfezioni.[^polarloop]

Per decenni, però, l'EER resta relegato al mondo matematico: separare e riallineare con precisione i due percorsi è possibile sulla carta e in un'equazione, ma troppo complesso da realizzare con mixer e componenti analogici. La svolta arriva col digitale e con la spinta data dalla necessità di metterci in tasca un trasmettitore piccolo ed efficiente (il telefono cellulare). Tra fine anni '90 e anni 2000 le evoluzioni dell'hardware GSM/EDGE riportano la modulazione polare al centro della scena: qui ampiezza e fase non vengono più "estratte" da un segnale esistente, ma generate numericamente da un DSP, eliminando alla radice i problemi di sincronizzazione. È il salto concettuale che rende tutto ripetibile e a basso costo.

Nel mondo radioamatoriale questo filone riemerge una decina di anni fa: David NMØS usa l'approccio EER in economici amplificatori SSB.[^cripe] Nel 2017 Tony K1KP e Brian K1LI descrivono su *QEX* "The Polar Explorer", un trasmettitore polare sperimentale a generazione digitale di ampiezza e fase.[^polarexplorer] E tra il 2023 e il 2025 Hans Summers G0UPL porta tutto questo dentro un kit da poche decine di euro: il QMX genera fase e inviluppo nel firmware, pilota un Si5351 e un ponte di MOSFET, e ottiene SSB pulita ed efficiente da un hardware che, preso pezzo per pezzo, sembra "troppo semplice per funzionare".[^qmx]

(La CESSB, *Controlled Envelope SSB*, è un tassello vicino a questa logica ma con una storia sua: la tratteremo in un capitolo dedicato.)

## Ma *in concreto* come funziona la modulazione polare?

Qualunque segnale RF, per quanto complicato, si può scrivere come un unico vettore che ruota nel piano I/Q:

**z(t) = a(t) · e^(jφ(t))**

dove **a(t)** è la sua *lunghezza* (l'ampiezza, cioè l'inviluppo) e **φ(t)** il suo *angolo* (la fase). È tutto qui: l'informazione che vogliamo trasmettere non è altro che un vettore che, istante per istante, cambia lunghezza e direzione.

Un trasmettitore SDR tradizionale (I/Q) ricostruisce quel vettore sommando due componenti in quadratura, e per farlo serve un amplificatore lineare. La modulazione polare fa una scelta diversa: genera direttamente le due grandezze *polari* — lunghezza e angolo — e le manda ai due percorsi hardware che abbiamo visto nello schema. La **lunghezza** diventa la tensione di alimentazione Vdd(t) imposta dal transistor regolatore; l'**angolo** diventa l'istante di commutazione dell'onda quadra del Si5351. Il finale non deve più essere lineare: deve solo commutare al momento giusto con l'alimentazione giusta.

Per vederlo "in concreto" prendiamo un segnale a due toni (due sinusoidi di ampiezza 1 e 0,5). Ciascun tono è un fasore che ruota a velocità propria; il segnale trasmesso è la loro **somma** (in giallo il primo tono, in verde il secondo, in blu il vettore risultante z(t)). Seguiamo tre istanti successivi:

![Ricomposizione dai fasori — istante t1](fasori_polare_1.png)

![Ricomposizione dai fasori — istante t2](fasori_polare_2.png)

![Ricomposizione dai fasori — istante t3](fasori_polare_3.png)

Il vettore risultante **respira** (la lunghezza passa da ~1,44 a 0,50 e ritorno: è ciò che il modulatore d'inviluppo impone come Vdd) e nel frattempo **ruota** (l'angolo va da ~30° a 90° a ~150°: è ciò che fissa la temporizzazione dell'onda quadra). Nel pannello di destra si vede il risultato: una portante commutata la cui ampiezza segue l'inviluppo verde.

Il punto chiave è proprio questo: **non c'è alcun clipping**. Il segnale è pulito, non è distorto. L'inviluppo non tocca mai lo zero e quindi la fase si muove con continuità, senza le brusche inversioni di 180° che nascerebbero se il vettore attraversasse l'origine.
Certo, è un caso limite, semplificato: la realtà è diversa, il segnale rischia di essere distorto per le variazioni istantanee di fase a inviluppo nullo, che non si prestano ad essere amplificate (andremmo a generare armoniche). Ma qui entra in gioco il secondo pezzetto che vedremo più avanti.
È il caso "facile"; le complicazioni — inviluppo che va a zero, banda della fase, e la CESSB — arrivano dopo.

## L'SSB a inviluppo controllato (CESSB)

Nel capitolo precedente abbiamo un po' barato: un segnale pulito, a due toni scelti apposta perché l'inviluppo non toccasse mai lo zero. La realtà dell'SSB vocale è più ostile, e la colpa è della trasformata di Hilbert che è sempre dentro un segnale SSB.
Mi fermo perché dobbiamo parlare di questo sig. Hilbert e della sua trasformata. Cosa fa? Perché serve?
Per assurdo arriviamo alla generazione del segnale di fase dell'onda quadra attraverso una composizione di sinusoidi — insomma partiamo da qualcosa di pulito per arrivare ad un segnale "sporco". Matematicamente è molto semplice, e si basa sulla teoria di Fourier.
La semplicità matematica rende possibile le "magie" del DSP.
Per avere un segnale sfasato di 90 gradi ricorriamo alla trasformata di Hilbert: semplicemente prende un nostro segnale e lo sfasa di 90 gradi mantenendo l'ampiezza. Difficile, difficilissimo da fare per via analogica (i più ardimentosi lo hanno provato).
Ma qui si nasconde un folletto maligno che cerchiamo di capire con i prossimi grafici.

![L'onda quadra è somma di armoniche: i seni hanno gli zeri allineati](hilbert_1_quadra.png)

Se sfasiamo di 90 gradi abbiamo una sorpresa: dove avevamo "zeri allineati" (onda quadra e seni passano tutti assieme per lo zero) passiamo ad avere coseni fortemente diversi da zero che si sommano:

![Dopo la trasformata di Hilbert (−90°) i seni diventano coseni: ora si allineano i massimi](hilbert_2_coseni.png)

Questa è la fregatura del digitale: passiamo dalle limitazioni hardware a limitazioni matematiche. In questo caso è come dividere un numero qualsiasi per uno molto piccolo, vicino a zero, il risultato "impazzisce".
E questa "follia matematica" è sempre presente, anche se andiamo a clippare il segnale analogico o a ridurre l'ampiezza del segnale analogico di partenza. Lo vediamo in questo grafico, in modo qualitativo.
Si vede come l'inviluppo di un SSB convenzionale, con audio limitato a 1,0, passa quasi tutto il tempo *sopra* 1,0, con sovraelongazioni (overshoot) fino al ~59% quindi *splatter*.[^cessb]

![L'inviluppo dell'SSB sfonda ben oltre 1, pur con m(t) limitato](hilbert_3_inviluppo.png)

E quindi ci troviamo di fronte ad un dilemma, uno vecchio ed uno nuovo.
Il vecchio vale per qualunque trasmettitore SSB: quei picchi rari e alti fissano la PEP ma trasportano poca energia, così la potenza media (il "talk power") resta bassa — tanta PEP, pochi watt medi — e l'ALC non fa che arretrare la potenza per non splatterare, buttando via proprio il talk power.
Il motivo nuovo riguarda il nostro trasmettitore polare: il percorso d'ampiezza deve riprodurre *esattamente* quell'inviluppo, e un inviluppo con picchi incontrollati e a banda larga è precisamente ciò che il modulatore di Vdd fatica a inseguire.
Come già detto prima, nel digitale non basta clippare l'audio: la generazione SSB (Hilbert) rigenera gli overshoot a valle e l'inviluppo torna a sfondare; clippare di nuovo l'RF controlla l'ampiezza ma allarga lo spettro (splatter). È ciò che la letteratura riassume bene: controllare *insieme* ampiezza e banda è difficile.

La CESSB scioglie il nodo lavorando in DSP nel dominio complesso, sull'inviluppo, e non su I e Q separatamente. L'idea di base è vecchia — clippa, rifiltra, ripeti — ma converge troppo lentamente (dopo sette passaggi resta oltre il 4% di overshoot). Dave W9GR la fa convergere "in un colpo solo": invece di limitarsi a tagliare, isola i *ritagli* (le "clippings", cioè ingresso meno uscita del clipper), li amplifica e li sottrae, e infine passa un filtro passa-basso a fase lineare. La correzione additiva è una formula che non metto per non spaventare chi non è avvezzo alla matematica, ma il risultato finale è controllare simultaneamente ampiezza di picco e banda.

I numeri, a pari PEP, parlano da soli: l'overshoot scende dal ~59% dell'SSB convenzionale (o ~21% col solo *RF clipping*) all'~1,6% della CESSB; la potenza media sale di circa 2,56 dB rispetto a un buon ALC *fast look-ahead* (≈ +80%), e si arriva fino a ~3,8 dB di riduzione del picco (≈ +140% di potenza media) a pari inviluppo di picco.[^cessb] Tradotto: il wattmetro segna di più, senza distorsione udibile e senza allargare la banda.

| Metodo | Overshoot dell'inviluppo | **Talk power** (a pari PEP) |
|---|---|:---|
| SSB convenzionale | ~59% | **0 dB** — riferimento |
| Solo *RF clipping* | ~21% | inutilizzabile: alza la media ma *splattera* |
| **CESSB** | **~1,6%** | **+2,56 dB (≈ +80%)** vs ALC *fast look-ahead* \ fino a **+3,8 dB (≈ +140%)** rispetto all'SSB normale |

*A pari PEP* (Peak Envelope Power) significa **a parità di potenza di picco**: i tre metodi sono confrontati tenendo lo stesso picco d'inviluppo, cioè lo stesso limite imposto al finale. In questa condizione ciò che cambia è il **talk power**, la potenza media della voce trasmessa: è quella che rende il segnale "forte" in ricezione, ed è la colonna che conta.

È questo il tassello che rende finalmente *utilizzabile* il finale polare del QMX. La CESSB gli fornisce un inviluppo docile — picchi controllati, banda limitata — che il modulatore d'ampiezza può inseguire; e, a parità di picco (quindi di dissipazione e di componenti), estrae più watt medi in antenna.
Insomma, un compressore "gratis", estremamente efficiente, reso necessario dall'amplificatore in classe C. Ed è il motivo dell'ottima resa della voce, e della "forza" del segnale che abbiamo con meno di 5 watt in uscita!

L'altra cosa bella di tutto questo? Dave W9GR in pieno spirito radioamatoriale l'ha prima pubblicata in QEX, a disposizione del mondo radioamatoriale, e poi è andato in FlexRadio a collaborare per una realizzazione commerciale.

## Fonti

[^chireix]: H. Chireix, "High Power Outphasing Modulation", *Proceedings of the IRE*, vol. 23, n. 11, pp. 1370–1392, novembre 1935.
[^doherty]: W. H. Doherty, "A New High Efficiency Power Amplifier for Modulated Waves", *Proceedings of the IRE*, vol. 24, n. 9, pp. 1163–1182, settembre 1936.
[^kahn]: L. R. Kahn, "Single-Sideband Transmission by Envelope Elimination and Restoration", *Proceedings of the IRE*, vol. 40, n. 7, pp. 803–806, luglio 1952.
[^polarloop]: V. Petrović, W. Gosling, "Polar-loop transmitter", *Electronics Letters*, vol. 15, n. 10, pp. 286–288, 1979. DOI: [10.1049/el:19790204](https://digital-library.theiet.org/doi/10.1049/el%3A19790204).
[^cripe]: Riportato in T. Brock-Fisher (K1KP), B. Machesney (K1LI), "The Polar Explorer", *QEX*, marzo/aprile 2017 — amplificatore SSB 5–50 W per i 40 m di David Cripe (NMØS).
[^polarexplorer]: T. Brock-Fisher (K1KP), B. Machesney (K1LI), "[The Polar Explorer](https://www.arrl.org/files/file/QEX_Next_Issue/Mar-Apr2017/MBF.pdf)", *QEX*, marzo/aprile 2017.
[^qmx]: H. Summers (G0UPL), presentazioni FDIM: "[Bringing SSB to QMX](https://qrp-labs.com/images/qmx/fdim/G0UPL.pdf)", FDIM 2025 ([pagina](https://qrp-labs.com/qmx/fdim2025.html)); e "[Evolution in Radio Design: building the next](https://qrp-labs.com/images/qmx/docs/fdim2023.pdf)", FDIM 2023 — qrp-labs.com.
[^cessb]: D. L. Hershberger (W9GR), "Controlled Envelope Single Sideband", *QEX*, novembre/dicembre 2014. Overshoot 59% → 1,6%; +2,56 dB di potenza media rispetto ad ALC *fast look-ahead* (≈ +80%), fino a ~3,8 dB di riduzione del picco (≈ +140%) a pari PEP.