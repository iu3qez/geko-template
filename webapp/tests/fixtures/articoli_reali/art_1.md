I modi digitali mi hanno sempre interessato ed in particolare l’RTTY dove ho per anni partecipato al Contest Italiano 40/80 metri nel quale io ho operato anche in QRP.
Devo dire che questa attività mi ha dato soddisfazioni cercando risultati nella Classifica QRP fino a quando qualcuno ha deciso che il QRP non era più considerato importante tale da meritarsi una Classifica apposita.
La sparizione della Categoria QRP ha conciso con il mio abbandono dell’RTTY, effettuato fino ad allora in maniera competitiva
Oggi, a distanza di anni, mi rendo conto che io non sarei più stato in grado di parteciparvi: l’età non mi permette la lucidità, la prontezza e la resistenza fisica per fare un contest impegnativo come quello; quindi per poter continuare un po’ di attività radio sono dovuto approdare anche io all’FT8, in modalità presenziata, come cacciatore.
Nella mia consueta parentesi estiva in Toscana la mia attività radio si limita a dare la caccia in HF e VHF ai soci attivatori che, fisicamente potendo, approfittano della bella stagione per recarsi in portatile.
L’attrezzatura che mi porto dietro da utilizzare, purtroppo, solo in modalità  “fissa” QRP  nella seconda casa, consiste  negli apparati portatili e dal PC altrettanto portatile.
A meno di utilizzare PC portatili d’epoca che io purtroppo non possiedo più, i portatili moderni non dispongono di porte seriali RS232, indispensabili per attivare il PTT, cosa prevista dai vari programmi digitali, a meno che non si usi la funzione VOX dell’apparato.
dove Io ho sempre combattuto con il VOX del mio FT817  https://www.mountainqrp.it/wp/geko-radio-magazine-nr-54-giugno-2022/   ed in particolare con la regolazione della sua sensibilità: o il PTT non si attivava se il livello era troppo basso oppure si innescava una sorta di ping-pong fra trasmissione e ricezione, fenomeno incontrollabile a meno di spegnere e riaccendere l’817. Non so se questo inconveniente sia normale o invece dipenda da un guasto del mio apparato. 
Dopo aver ripreso in considerazione una soluzione più complicata ma certamente più affidabile ho provato a far funzionare una soluzione già tentata che impiegava un adattatore  USB – DB9 che già possedevo e vedere se il dispositivo era riconosciuto sul mio Notepad SAMSUNG da 10 pollici in mio possesso.
Il fatto che il dispositivo non venisse rilevato l’ho attribuito a qualche difetto dell’adattatore.
A quel punto ho acquistato un altro adattatore differente dal mio e quindi sono iniziate le mie tribolazioni: dopo aver installato sul Notebook (Windows 7 “Starter”) il driver suggerito in rete
https://kb.plugable.com/serial-adapter/installing-the-plugable-usb-to-rs-232-db9-serial-adapter-on-windows-7 e continuato una serie interminabile di verifiche, ho provato il medesimo nuovo adattatore sul PC di stazione sul quale è installato Windows 7 Professional.
Esso non solo ha funzionato perfettamente, ma lo è stato altrettanto su un PC portatile moderno sul quale è installato Windows 11.
Ne ho dedotto che il mancato funzionamento sotto Windows 7 “Starter” dipendeva dal fatto che questo sistema operativo Windows 7 “Starter” è mancante di molte funzionalità rispetto al classico Windows 7.
A questo punto, piuttosto che installare sul modesto Notepad un livello di Windows più moderno, la soluzione potrebbe essere stata quella di portarmi dietro l’altro PC portatile con Windows 11.


Questa soluzione non mi soddisfaceva e quindi ho continuato a spremermi le meningi fino a rendermi conto che il solo applicare una delle due tag dell RS232 DB9 non poteva bastare per attivare il PTT in quanto quelle due tag variano come livello da -6V a riposo a +6V in trasmissione, mentre il PTT dell’817 richiede un “ground” per trasmettere. 

L’esperienza si fa sbattendoci la testa, oppure acquisendo le esperienze condivise da altri. 
A me occorreva solo poter attivare il PTT dell’apparato che mette in trasmissione l’817 con la linea portata verso ground.  Dopo aver verificato che era sufficiente una semplice resistenza da 1 kohm collegata a massa per commutare il PTT,  ho assunto che sarebbe stato sufficiente un transistor NPN  portato in conduzione con una delle due tag DTR o RTS (che tramite l’adattatore USB → DB9 vanno a +6V quando il programma comanda la trasmissione).
Per realizzare questo semplicissimo circuito è stato sufficiente acquistare (Amazon) un adattatore da femmina DB9 a morsettiera segnali e costruire su di esso il semplicissimo circuito.
Sembrava fosse finita questa interminabile avventura ?  E invece no, Il Notebook non ne voleva sapere di riconoscere l'adattatore USB. Dall’analisi dei dispositivi installati su Windows si vedeva che, a parte la COM1 assegnata, tutte le restanti 56 risultavano “in use” …..  In “use” da chi ?
Andare nei meandri di Windows per liberale non me la sentivo, tanto era complicata la procedura suggerita in rete e pertanto ho tentato una soluzione più azzardata: quella di rinominare la COM3 “in use” come Prolific, nome del chipset dell’adattatore.  Ho ignorato il “warning” prontamente segnalato da Windows e ho provato direttamente a vedere se l’apparato commutava in trasmissione assegnando COM3 al WSJT-X.
Uno dei nostri fondamenti è la condivisione delle proprie esperienze: raccomandazione da sempre volata al vento.
Ora si trattava di usarlo questo FT8 e posso assicurarvi che questo per me non è (o non è stato …) assolutamente facile.  Non ho trovato grande giovamento né dal suo manuale e né da qualche video tutorial trovato in rete.  Solo sbattendoci la testa (come immagino lo sia stato per tutti …) e a forza di prove e di QSO scopro le tante funzionalità. 

<call:6>PA5WJB <gridsquare:4>JO33 <mode:3>FT8 <rst_sent:3>-06 <rst_rcvd:3>-11 <qso_date:8>20250422 <time_on:6>144645 <qso_date_off:8>20250422 <time_off:6>144817 <band:3>20m <freq:9>14.074335 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:6>RX3ASQ <gridsquare:4>KO95 <mode:3>FT8 <rst_sent:3>-13 <rst_rcvd:3>-14 <qso_date:8>20250422 <time_on:6>151900 <qso_date_off:8>20250422 <time_off:6>152327 <band:3>20m <freq:9>14.075101 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:6>UA3QJJ <gridsquare:4>KO91 <mode:3>FT8 <rst_sent:3>-06 <rst_rcvd:3>-18 <qso_date:8>20250422 <time_on:6>152545 <qso_date_off:8>20250422 <time_off:6>152727 <band:3>20m <freq:9>14.075129 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:6>OK1ZCF <gridsquare:4>JO80 <mode:3>FT8 <rst_sent:3>-08 <rst_rcvd:3>-13 <qso_date:8>20250423 <time_on:6>084345 <qso_date_off:8>20250423 <time_off:6>084503 <band:3>20m <freq:9>14.074996 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:6>OZ4CHR <gridsquare:4>JO75 <mode:3>FT8 <rst_sent:3>-12 <rst_rcvd:3>-11 <qso_date:8>20250423 <time_on:6>091900 <qso_date_off:8>20250423 <time_off:6>092020 <band:3>20m <freq:9>14.074833 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:5>LZ2VQ <gridsquare:4>KN23 <mode:3>FT8 <rst_sent:3>-06 <rst_rcvd:3>-20 <qso_date:8>20250423 <time_on:6>092353 <qso_date_off:8>20250423 <time_off:6>092353 <band:3>20m <freq:9>14.074833 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>
<call:6>MI0NWA <gridsquare:4>IO64 <mode:3>FT8 <rst_sent:3>-09 <rst_rcvd:3>-24 <qso_date:8>20250423 <time_on:6>093915 <qso_date_off:8>20250423 <time_off:6>094032 <band:3>20m <freq:9>14.074662 <station_callsign:10>IK0BDO/QRP <my_gridsquare:6>JN53GC <eor>

Prove rigorosamente fatte con i 5 watt dell’817 e lo dimostrano i rapporti di ricezione ricevuti; il WWL JN53GC dichiarato si riferisce già a quello mio /P in Toscana perché a breve impacchetterò tutto contando di non doverci più rimettere le mani.

Contemporaneamente PSK Reporter ha mostrato ricezioni interessanti durante le mie prove.
Anche se questo mio articolo sembrerà puerile e banale, sapeste voi quanto avrei io desiderato trovarne di simili sul Forum o altrove; il loro aiuto mi avrebbe semplificato la vita;  non si finisce mai di imparare ma, alla mia età, il cervello ha quasi tutti i suoi neuroni occupati o disabilitati ….

ora, verificato che tutto sia funzionante non mi restava che attendere Giugno per provare FT8 con questa attrezzatura portatile dalla Toscana, sempre che me ne venga la voglia.
Sembrerà strano ma a me, più che fare un QSO anche in digitale ma in modo non competitivo, interessa molto di più la sperimentazione.
Conclusione: oggi, a fine Agosto, la voglia di provare a fare un po’ di FT8 non mi è ancora venuta né temo mi verrà prima del mio rientro. Questa modalità non mi appassiona gran che e certamente molto meno dello sperimentare qualcosa di nuovo nelle mie autocostruzioni.

Buone attivazioni.
Roberto IK0BDO


