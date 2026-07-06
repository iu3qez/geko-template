##INTRODUZIONE
Nel mondo QRP e delle attività “al limite”, spesso ci si interroga su quale sia la vera. barriera tra ciò che si può ascoltare e ciò che, semplicemente, si perde nel rumore. L’articolo di Ray Soifer, storico operatore EME e sperimentatore di segnali deboli, ci riporta agli ZRO Test: un esperimento collettivo – condotto via satellite – per capire davvero quanto può arrivare in basso l’orecchio umano in CW… e come si confrontano le prestazioni umane con quelle delle più moderne tecniche digitali, come FT8
##GLI ZRO TEST: ASCOLTARE L’IMPOSSIBILE
Negli anni ‘80 e ‘90, tramite i satelliti Oscar 10 e 13, AMSAT organizzò i ZRO Test in memoria di Kaz Deskur, K2ZRO: una stazione trasmetteva sequenze casuali di 5 cifre in CW, abbassando ogni volta la potenza di 3 dB, finché solo pochissimi riuscivano ancora a copiare qualcosa.
Questi test sono storici per due motivi:
- Condizioni standardizzate: tutti ricevevano lo stesso segnale, con SNR limitato non dalla stazione ricevente ma dal rumore del satellite stesso;
- Sfida all’orecchio umano: si valutava non la tecnologia, ma la sensibilità, la preparazione e l’allenamento dell’operatore.
##FIN DOVE PUÒ ARRIVARE L’ORECCHIO UMANO?
L’analisi dei risultati di centinaia di partecipanti ai test ZRO, integrata dall’esperienza EME di W2RS, mostra dati sorprendenti, qui tutti riportati come SNR su 100 Hz per confronto diretto:

Modalità	SNR (100 Hz)	Condizione	Descrizione
CW	–3,6 dB	Z8 (top quartile)	Sequenze di cifre, test ZRO
CW	–6,6 dB	Z9 (record)	Solo 4% dei partecipanti
CW (EME)	–6 / –7 dB	QSO schedulati	Ascolto prolungato e chiamate note
SSB	–7,4 / –10,7 dB (*)	QSO EME con W5UN	Con picchi di propagazione e concentrazione
FT8	–6 dB (**)	QSO digitale	Decodifica automatica, limite software
(*) valori originariamente calcolati su 2,1 kHz (vedi “Come si confrontano SNR a larghezze di banda diverse”)
(**) conversione da –20 dB in 2,5 kHz a 100 Hz (vedi “Come si confrontano SNR a larghezze di banda diverse”)
##SSB: ANCHE LA FONIA HA I SUOI “MIRACOLI”
Non solo CW: anche in SSB, come dimostra W2RS, l’orecchio umano può spingersi oltre i limiti immaginati.
QSO in SSB con SNR di –7,4 dB e persino –10,7 dB (in 2,1 kHz) sono stati possibili grazie a momenti di propagazione favorevole e a una concentrazione estrema.
Studi storici mostrano che solo una parte dello spettro SSB veicola le informazioni essenziali, e il cervello umano riesce a “filtrare” mentalmente ciò che serve, quasi come un DSP biologico.

##FT8: L’UOMO SFIDA LA MACCHINA?
Oggi il sistema digitale più popolare per i segnali deboli è FT8. Il software è in grado di decodificare segnali con SNR anche di –20 dB in 2,5 kHz di banda.
Ma cosa significa questo rispetto alle capacità umane?
Convertendo a 100 Hz di banda, FT8 e l’orecchio umano allenato (in CW e SSB) risultano sorprendentemente vicini: circa –6 dB il limite teorico per entrambi!

##TECNICA, ALLENAMENTO… E UN PO’ DI “MUSICA”
•	Il cervello umano può restringere mentalmente la banda audio tra 50 e 200 Hz, migliorando la ricezione;
•	Alcuni operatori, spesso musicisti, riescono a distinguere variazioni di pochi Hz;
•	Filtri DSP moderni (Linrad, filtri attivi, ecc.) possono dare un vantaggio ulteriore di 2–3 dB.
##COME SI CONFRONTANO SNR A LARGHEZZE DI BANDA DIVERSE?
Quando si confrontano valori SNR, è essenziale considerarli sulla stessa larghezza di banda.
La formula è:
Esempio:
•	FT8 dichiara –20 dB di SNR su 2,5 kHz;
•	Portato a 100 Hz di banda audio:
Conclusione:
Un segnale FT8 decodificabile a –20 dB SNR (in 2,5 kHz) corrisponde a circa –6 dB SNR (in 100 Hz).
PERCHÉ TUTTO QUESTO INTERESSA ANCORA I QRPISTI?
1. Gli “standard umani” restano un riferimento, anche nell’era digitale: FT8 non è “magia”, ma un raffinato filtro automatico.
2. L’allenamento fa la differenza: anche con mezzi modesti, il limite è spesso tra le nostre orecchie!
3. Chi ama la sfida può organizzare (magari tra soci MQC) dei test ZRO, sfruttando beacon, webSDR o trasmettitori QRP, per vedere dove può arrivare oggi l’orecchio… o il software!
##FONTI E APPROFONDIMENTI
•	Ray Soifer, W2RS, The Weak-Signal Capability of the Human Ear (2002, Central States VHF Society Conference)
•	https://www.amsat.org/
•	Linrad DSP software di SM5BSZ: http://ham.te.hik.se/homepage/sm5bsz/linuxdsp/linrad.htm
•	WSJT-X (FT8): https://physics.princeton.edu/pulsar/k1jt/wsjtx.html

