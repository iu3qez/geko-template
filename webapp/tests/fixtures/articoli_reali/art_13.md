# Le HF possono rilevare i terremoti?
> [!NOTE]
> Riporto questo articolo, in memoria e ricordo di Alex VE7DXW, SK dal 2024 a seguito di una lunga malattia.
>
> Aveva dedicato molto tempo ed energie a studiare l'interazione tra terremoti e propagazione, arrivando a creare una rete di monitoraggio (RF-Seismograph). La novità portata da Alex è stata di concentrare lo studio dalle VHF alle onde lunghe, medie e corte e *sulla raccolta di dati scientifici per prevedere i terremoti*. Il problema sostanziale dei monitoraggi in VHF era la necessità di essere "vicini" all'evento sismico.
>
> Attenzione: nonostante gli sforzi di Alex, non vi è alcun dato scientifico che correli propagazione e terremoti *prima* dell'evento sismico, mentre è certo che il terremoto sia rilevante ai fini della propagazione anche nelle bande radioamatoriali. Altri studi suggeriscono la correlazione tra "aperture" di propagazione e particolari eventi sismici; magari torneremo su questo in futuro.
>
> Per chi volesse approfondire l'argomento consiglio il link di *Scientific American*  (Ott. 2018): "Earthquakes in the Sky". https://www.ep.sci.hokudai.ac.jp/~heki/pdf/Scientific_American_Vance2018.pdf


**Pubblicato su:** *The Canadian Amateur* | Marzo-Aprile 2019

---

## Panoramica

Sempre più evidenze suggeriscono che sia possibile rilevare i terremoti misurando le variazioni della ionosfera. L'**RF-Seismograph** — uno strumento di monitoraggio della propagazione HF in tempo reale ideato da Alex Schwarz — ha registrato picchi di rumore e interruzioni di segnale (dropout) il 1° novembre che, data l'inattività solare, non potevano avere origine spaziale. L'indagine ha confermato la causa: i terremoti.

![Terremoti e Magnetosfera](/uploads/433c67a9_Screenshotfrom2026-02-2218-40-46.png)

Il team dell'RF-Seismograph collabora con *Earthquakes Canada* e l'USGS per correlare la propagazione HF con l'attività sismica. Analizzando 171 terremoti di magnitudo M6+ nell'arco di quattro anni, è stata riscontrata una variazione visibile nei livelli di rumore e propagazione.


## 1. Generazione di campi elettromagnetici dai terremoti

I terremoti influenzano la propagazione attraverso diversi meccanismi:

* **Effetto piezoelettrico:** Generato dallo scorrimento e dalla vibrazione delle rocce.
* **Micro-fratture:** Il cedimento meccanico delle rocce rilascia enormi quantità di elettroni liberi.
* **Correnti telluriche:** Gli elettroni risalgono verso la superficie o il fondale marino, circolando attorno all'epicentro.
* **Interazione ionosferica:** I campi elettromagnetici emergenti interagiscono con le particelle cariche della ionosfera, creando "buchi" o "cupole" di particelle cariche che deviano o assorbono le onde radio.



## 2. Anomalie nella Ionosfera

Le linee del campo magnetico terrestre si estendono fino alla ionosfera; le perturbazioni sismiche possono piegare o disturbare questi strati, interrompendo i percorsi radio esistenti. Questo fenomeno è fisicamente simile ai campi magnetici che emergono dalla superficie solare, sebbene meno energetico. Quando questo accade, i segnali ricevuti dal sismografo subiscono un brusco calo (*dropout*).


## 3. Cosa visualizza l'RF-Seismograph?

Basandosi su un caso studio di un evento M5.0 nella Columbia Britannica, sono state identificate diverse fasi:

1. **Accumulo di energia:** Aumento del rumore sugli 80m (traccia rossa) a partire da diverse ore prima dell'evento.
2. **Disruzione:** *Dropout* delle comunicazioni sulle bande dei 40m, 30m e 20m (le linee nel grafico diventano piatte).
3. **Rilascio (Quake):** Il momento esatto della scossa.
4. **Persistenza:** L'accumulo di energia e il blackout continuano spesso per un periodo equivalente a quello precedente alla scossa (circa 4-6 ore totali).
5. **Ripristino:** Dopo il rilascio dell'energia, la ionosfera si stabilizza gradualmente e la normale propagazione riprende.

![Andamento del SNR](/uploads/e6c83fc9_image_2026-02-22_201840004.png)


## Studio quadriennale: Propagazione vs Terremoti

### Perché questo studio è differente?

Precedenti ricerche si concentravano su misurazioni locali in VHF, rendendo difficile catturare l'evento. Questo studio utilizza le HF e dimostra che:

* È necessario trovarsi ad almeno **500 km** dall'epicentro per misurare correttamente i segnali riflessi dalla ionosfera perturbata.
* I terremoti possono generare segnali RF con potenze dell'ordine dei **Mega-Watt**.

### Risultati statistici

* **Eventi studiati:** 171 terremoti M6+ (agosto 2016 - oggi).
* **Frequenza:** Un evento maggiore ogni 5,6 giorni.
* **Correlazione:** Nel **72%** dei casi è stato osservato un aumento del rumore sugli 80m prima, dopo o durante il rilascio del sisma.
* **Rumore di fondo:** Circa il 17,3% del rumore di fondo è influenzato da questi grandi eventi; i terremoti più piccoli (< M3.0) sono responsabili di gran parte del "rumore di fondo" (rumble) percepibile sui 160m e 80m.


## Conclusioni

I dati suggeriscono che la maggior parte dei terremoti presenta un **livello di rumore precursore** rilevabile. Sebbene non sia ancora un sistema di allerta infallibile, l'RF-Seismograph rappresenta uno strumento supplementare per migliorare la previsione sismica, integrando i sismografi meccanici tradizionali.


### Riferimenti

* *Scientific American* (Ott. 2018): "Earthquakes in the Sky".
* Software RF-Seismograph (Linux/Raspberry Pi): [Groups.io MDSRadio](https://groups.io/g/MDSRadio/wiki/home).
* MDSR Software per PC: [users.skynet.be/myspace/mdsr/](http://users.skynet.be/myspace/mdsr/).