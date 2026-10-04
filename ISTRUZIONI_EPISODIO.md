# Istruzioni per scrivere un episodio di CV Intelligence Daily

Podcast quotidiano (lunedì–venerdì) su **Iveco Group, Tata Motors (business veicoli commerciali) e FPT Industrial**, letto da una voce sintetica italiana. Ascoltatore: un professionista che lavora su questi gruppi e vuole livello tecnico alto, niente banalità, esempi concreti con numeri.

## File da produrre

- Percorso: `scripts/AAAA-MM-GG.md`, con la data di uscita (la data di oggi, fuso Europe/Rome).
- Il push di questo file su `main` avvia da solo la generazione dell'audio e l'aggiornamento del feed. Non toccare `episodes.json`, `docs/` o `tools/`.

Formato esatto:

```
---
title: <titolo dell'episodio, max 90 caratteri, con i 2-3 temi principali>
date: AAAA-MM-GG
description: <2-3 frasi con i temi trattati, per le note dell'episodio>
---

<testo parlato>

===FONTI===

- [Titolo fonte](https://url)
- ...
```

Regole per il testo parlato:
- Si legge così com'è: niente URL, niente tabelle, niente elenchi puntati, niente sigle che non si pronunciano.
- Le indicazioni di regia vanno tra parentesi quadre, es. `[Cambio di tono]`: non vengono lette.
- Un titolo di sezione con `## ` per ogni blocco (viene letto come annuncio del blocco). Nel blocco tecnico puoi usare `### ` per i sottotitoli.
- Numeri scritti come si dicono: "più 42 per cento", "3,76 miliardi di euro", "2.850 newtonmetro". Niente simboli come %, €, ±.
- Frasi brevi, ritmo radiofonico, una sola voce che parla in prima persona plurale ("vediamo", "facciamo un conto").
- Mai citazioni testuali lunghe: parafrasa sempre le fonti con parole tue.
- Solo informazioni pubbliche. Mai contenuti interni, riservati o riferiti a persone private.

## Lunghezza

Totale tra 16.000 e 19.000 caratteri di testo parlato (circa 17–19 minuti). Ripartizione indicativa:

| Blocco | Caratteri |
| --- | --- |
| Executive Summary | 1.400 |
| Market Intelligence | 2.300 |
| Competitive Intelligence | 2.000 |
| Deep Dive IVECO Portfolio | 2.300 |
| Technical Deep Dive | 5.500 |
| FPT Industrial | 2.000 |
| Strategic Insights + chiusura | 2.300 |

## Struttura (sempre questa, in quest'ordine)

1. **Executive Summary** – saluto con giorno e data, poi le tre cose da portarsi via oggi, ognuna con un numero.
2. **Market Intelligence** – domanda, immatricolazioni, ordini, prezzi, regolazione: Europa, Sud America, India. Spiega cosa significa ogni dato per i tre gruppi.
3. **Competitive Intelligence** – Daimler Truck, Traton (Scania, MAN), Volvo, PACCAR/DAF, Ashok Leyland, Mahindra, Eicher/Volvo, BYD e costruttori cinesi, Cummins: mosse concrete e confronto diretto con Iveco/Tata/FPT.
4. **Deep Dive IVECO Portfolio** – un tema per volta (Truck, Daily, Bus, Capital, servizi, stabilimenti), con numeri e lettura critica.
5. **Technical Deep Dive** – lezione su UNO o DUE componenti. Prendi il primo argomento non spuntato in `lezioni_tecniche.md`, poi spuntalo aggiungendo la data. Spiega il principio fisico, le scelte di progetto, i compromessi, un calcolo d'ordine di grandezza fatto a voce, l'impatto sul TCO con ipotesi dichiarate, e chiudi con una domanda aperta.
6. **FPT Industrial** – prodotti, clienti, fiere, mercati off-road e power generation, nomine.
7. **Strategic Insights** – tre letture strategiche numerate, poi le date da segnare nei prossimi giorni, poi chiusura con anticipazione della lezione tecnica di domani (il prossimo argomento non spuntato; il venerdì "lunedì").

## Ricerca

- Cerca le notizie delle ultime 24 ore (il lunedì: dal venerdì precedente). Fonti preferite: comunicati ufficiali (ivecogroup.com, tatamotors.com, fptindustrial.com, Borsa Italiana, BSE/NSE), poi testate di settore e finanziarie.
- Verifica ogni numero aprendo la pagina da cui lo prendi. Se un dato non è verificabile, non usarlo.
- Leggi gli ultimi 3 script in `scripts/` e non ripetere le stesse notizie, salvo sviluppi nuovi; in quel caso dillo ("aggiornamento su...").
- Nei giorni con poche notizie, approfondisci invece di riempire: un dato di bilancio, un confronto con un concorrente, un caso di flotta.
- Elenca in `===FONTI===` solo le pagine effettivamente aperte e usate.
