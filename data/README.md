# data/ — Dataset Open Data

Qui dentro stanno i dati **reali** che alimentano l'app. Nessun valore inventato.

I file JSON di questa cartella sono **generati e committati**: chi clona il repo trova
l'app già piena di dati e non deve scaricare niente.

## Rigenerare i dati

```bash
uv run --with httpx python scripts/fetch_open_data.py
```

Lo script scarica le fonti, normalizza i record, geocodifica le strutture prive di
coordinate (Nominatim, una richiesta al secondo) e riscrive i file qui sotto. La cache
`.geocache.json` evita di rifare il lavoro già svolto.

`raw/` conserva i CSV scaricati così come arrivano dal portale. Sono committati per due
motivi: mostrano la provenienza esatta dei dati, e fanno da rete quando `dati.lazio.it`
risponde 503 — cosa già successa durante lo sviluppo. Se il portale è giù, lo script
riprova qualche volta e poi riparte dall'ultima copia buona invece di fallire.

Poi si ricarica il database:

```bash
cd backend && uv run python -m app.cli seed --reset
```

---

## Fonti usate

Selezionate dalla matrice in `FINALIDATASET.xlsx`, che censisce tutte le fonti valutate.

| ID | Dataset | Cosa ne ricaviamo |
|---|---|---|
| HP-D01 | [Pronto Soccorso — accessi in tempo reale](https://dati.lazio.it/dataset/pronto-soccorso-accessi-in-tempo-reale) | I 49 pronto soccorso del Lazio **e le code reali per codice colore** |
| HP-D08 | [Farmacie della Regione Lazio](https://dati.lazio.it/dataset/farmacie-della-regione-lazio) | Farmacie attive, già con latitudine e longitudine |
| HP-D05 | [Elenco degli ospedali del Lazio](https://dati.lazio.it/dataset/elenco-degli-ospedali-del-lazio) | Ospedali pubblici (geocodificati) |
| HP-D05b | [Strutture sanitarie private accreditate](https://dati.lazio.it/dataset/elenco-delle-strutture-sanitarie-private-accreditate) | Ambulatori accreditati, già geolocalizzati |

### `facilities/` — anagrafica dei presidi

Un file per tipologia. Schema normalizzato: `name`, `type`, `asl`, `municipality`,
`province`, `address`, `postal_code`, `latitude`, `longitude`, `beds`, `phone`.

Il loader (`backend/app/features/facilities/loader.py`) accetta anche CSV grezzi con le
intestazioni dei portali italiani: per aggiungere un dataset basta copiarlo qui e
ricaricare. I dettagli sugli alias di colonna riconosciuti sono nel modulo stesso.

### `congestion/` — code reali dei pronto soccorso

`pronto-soccorso.json` contiene, per ogni PS, quante persone sono in attesa **divise per
codice colore**, quante in trattamento e quante in osservazione.

Su questi conteggi il backend calcola l'attesa di chi arriva adesso: non un numero unico
per struttura, ma il tempo che dipende da **quante persone più gravi hai davanti**
(`backend/app/features/congestion/waiting.py`). Un codice bianco aspetta dietro a tutti,
un rosso entra subito.

---

## Limiti da conoscere

**La fotografia delle code è del 31/07/2021.** È l'ultimo dato pubblico: il portale
regionale mostra il tempo reale in una pagina web ma non espone né un feed né uno storico
scaricabile (la matrice lo annota su HP-D02). I numeri sono quindi **reali ma non
aggiornati**, e l'interfaccia dichiara sempre la data a cui si riferiscono.

Per avere il tempo reale servirebbe che le strutture dichiarassero il proprio carico: è
esattamente ciò che abiliterà la feature dedicata al personale, dato che la tabella
`facility_loads` è già scrivibile.

**Le coordinate dei dataset regionali non sono sempre affidabili.** Lo script scarta i
punti fuori dal Lazio e le farmacie dichiarate a Roma ma a oltre 30 km dal centro.

**Gli ospedali sono geocodificati, non forniti con coordinate.** Dove il nome abbreviato
del dataset non è riconoscibile (`Pol. Univ. Tor Vergata`), lo script espande le
abbreviazioni e, in ultima istanza, ripiega sul centro del comune.
