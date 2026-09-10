# data/ — Dataset Open Data

Qui dentro finiscono i file scaricati dai portali Open Data. **Nessun codice**, solo dati.

Il backend legge questa cartella allo startup: se trova file li normalizza e li carica in SQLite; se non trova nulla l'app parte lo stesso e mostra uno stato "in attesa dei dataset". Non serve toccare il codice per aggiungere dati.

## Come si aggiunge un dataset

1. Scarica il file dal portale (`.csv` o `.json`).
2. Mettilo in `data/facilities/` (o `data/waiting-times/`). Il nome del file è libero: il loader legge tutto quello che trova.
3. Riavvia il backend, oppure ricarica senza riavviare:

   ```bash
   cd backend && uv run python -m app.cli seed --reset
   ```

4. Committa il file. `data/` è **append-only**: si aggiungono file, non si rinominano né si cancellano quelli degli altri.

I CSV vengono letti con rilevamento automatico del separatore (`,` o `;` — i portali italiani usano spesso il punto e virgola) e con fallback di encoding `utf-8` → `utf-8-sig` → `latin-1`. I decimali con la virgola (`41,8697`) sono gestiti.

---

## `data/facilities/` — presidi sanitari

**Fonte principale:** Portale Open Data Regione Lazio — cercare *Pronto Soccorso*, *Posti letto*, *Strutture sanitarie* per il censimento di ospedali, ASL e carichi operativi.

Il loader riconosce da solo i nomi di colonna più comuni dei portali regionali. Non serve rinominare le intestazioni.

| Campo normalizzato | Obbligatorio | Alias riconosciuti |
|---|---|---|
| `name` | **sì** | `denominazione`, `denominazione_struttura`, `nome`, `descrizione_struttura`, `struttura`, `presidio` |
| `type` | no (default `altro`) | `tipologia`, `tipo`, `tipo_struttura`, `categoria`, `natura` |
| `asl` | no | `asl`, `azienda`, `azienda_sanitaria`, `codice_asl`, `ente` |
| `municipality` | no | `comune`, `citta`, `località`, `descrizione_comune` |
| `province` | no | `provincia`, `sigla_provincia`, `prov` |
| `address` | no | `indirizzo`, `via`, `sede`, `indirizzo_sede` |
| `postal_code` | no | `cap`, `codice_postale` |
| `latitude` | no | `latitudine`, `lat`, `coord_y`, `y` |
| `longitude` | no | `longitudine`, `lon`, `lng`, `coord_x`, `x` |
| `beds` | no | `posti_letto`, `posti_letto_totali`, `n_posti_letto`, `pl` |
| `phone` | no | `telefono`, `tel`, `recapito`, `contatto` |

Il confronto ignora maiuscole, accenti, spazi e underscore: `POSTI LETTO`, `posti_letto` e `Posti Letto` sono la stessa colonna.

Se un dataset ha un nome di colonna che il loader non riconosce, si aggiunge l'alias in `backend/app/features/facilities/loader.py` (dizionario `FIELD_ALIASES`) — una riga, niente riscritture.

### Tipologie riconosciute

Il valore grezzo viene normalizzato in una di queste categorie, usate poi dai filtri dell'interfaccia:

`pronto-soccorso` · `ospedale` · `casa-comunita` · `farmacia` · `ambulatorio` · `altro`

La normalizzazione è per parole chiave (es. qualsiasi valore che contenga "pronto soccorso", "dea" o "ps" → `pronto-soccorso`; "casa della comunità", "casa di comunità" o "cdc" → `casa-comunita`). Vedi `TYPE_KEYWORDS` nello stesso file.

### File di esempio

`facilities/example.facility.json` contiene 3 record che documentano lo schema normalizzato. **Serve solo da riferimento**: quando arrivano i dati veri si può cancellare, oppure lasciarlo (i duplicati vengono deduplicati per nome + comune).

---

## `data/waiting-times/` — tempi di attesa

**Fonte integrativa:** Portale Nazionale Open Data — cercare *Tempi di attesa Lazio* o *Flussi sanitari regionali* per le serie storiche sulle prestazioni ambulatoriali.

Slot predisposto ma non ancora consumato dal backend: sarà la base per una delle feature che il team deve ancora scegliere. Chi prende quella feature definisce lo schema in `STATE.md` e scrive il proprio loader in `backend/app/features/<feature>/`.
