# Presidio Lazio — Emergency Triage Assistant

Web app che aiuta il cittadino a capire **dove andare** quando ha un problema di salute non grave: invece del pronto soccorso, la struttura territoriale più adatta al caso — casa della comunità, farmacia attrezzata, ambulatorio.

Traccia 3 — Sanità / Healthcare. Dati dal Portale Open Data della Regione Lazio e dal Portale Nazionale Open Data.

Stato: **feature 1 completa**. All'apertura si sceglie il ruolo; il percorso del paziente è
implementato end-to-end (chat di triage, classificazione nei cinque codici, mappa con tempi
reali). L'area del personale è predisposta ma vuota: la sviluppa il team.

## Come funziona il percorso del paziente

1. **Chat.** Un LLM raccoglie i sintomi facendo al massimo tre domande, poi assegna uno dei
   cinque codici. La catena dei provider è: **modello locale** (LM Studio) → **Groq** →
   **regole deterministiche**. L'app risponde sempre, anche senza rete e senza modello.
2. **Rete di sicurezza.** Un classificatore a parole chiave gira in parallelo all'LLM e può
   solo **alzare** la gravità, mai abbassarla: un dolore toracico classificato "bianco" dal
   modello diventa comunque rosso. In interfaccia si vede sempre da dove arriva la risposta.
3. **Mappa.** Inserito l'indirizzo, Nominatim lo geocodifica e OSRM calcola i tragitti reali.
   I minuti di viaggio e di attesa sono **calcolati**, non inventati dall'LLM, che si limita
   a scrivere il consiglio sui numeri già pronti.

### Configurazione LLM

Il modello locale si configura in `backend/.env` (vedi `.env.example`). Per Groq serve
`PRESIDIO_GROQ_API_KEY`. **La chiave non va committata**: il repo è pubblico.

⚠️ L'affollamento dei presidi è oggi un **valore generato**, non reale: gli Open Data non
espongono la saturazione in tempo reale. È deterministico (stessa struttura, stesso valore) e
sempre etichettato come stima in interfaccia.

---

## Avvio rapido

Serve Node 20+, Python 3.12+, [uv](https://docs.astral.sh/uv/) e pnpm.

```bash
# pnpm, se manca (senza sudo)
corepack enable --install-directory ~/.local/bin

# dipendenze
cd frontend && pnpm install
cd ../backend && uv sync
```

Poi, da due terminali:

```bash
cd backend  && uv run fastapi dev app/main.py   # http://localhost:8000
cd frontend && pnpm dev                         # http://localhost:5173
```

L'app si apre su **http://localhost:5173**. Vite fa da proxy su `/api` verso il backend: nel codice si usano sempre URL relative, niente CORS in dev.

L'app parte anche **senza dati**: in quel caso mostra come caricarli invece di rompersi.

---

## Caricare i dati

1. Scarica dal Portale Open Data Regione Lazio un dataset di strutture (*Pronto Soccorso*, *Posti letto*, *Strutture sanitarie*).
2. Copia il `.csv` o il `.json` in `data/facilities/`.
3. Ricarica:

   ```bash
   cd backend && uv run python -m app.cli seed --reset
   ```

Il loader riconosce da solo i nomi di colonna dei portali italiani (`DENOMINAZIONE`, `COMUNE`, `POSTI LETTO`…), il separatore `;`, i decimali con la virgola e gli encoding non-UTF8. Dettagli e schema completo in [`data/README.md`](data/README.md).

---

## Come lavora il team

Tre persone, PC diversi, agenti diversi, stesso repo. Le regole che rendono il merge indolore stanno in **[`AGENTS.md`](AGENTS.md)** e vanno lette prima di scrivere codice.

| File | A cosa serve |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Stack, convenzioni, protocollo di sincronizzazione. È legge. |
| [`TASKS.md`](TASKS.md) | Chi sta facendo cosa. **Nessun branch senza task assegnata.** |
| [`STATE.md`](STATE.md) | Contratti API, richieste di dipendenze, risorse globali. |
| [`REVIEWER_PROMPT.md`](REVIEWER_PROMPT.md) | Ruolo dell'Orchestratore che mergia e risolve i file condivisi. |
| [`docs/FEATURE_TEMPLATE.md`](docs/FEATURE_TEMPLATE.md) | Checklist per chi prende una feature. |

In sintesi: si divide **per feature, non per layer**. Ognuno prende un dominio e lo fa end-to-end, frontend + backend, toccando solo le sue due cartelle.

### Aggiungere una feature

```bash
./scripts/new-feature.sh tempi-attesa
```

Genera le cartelle e i file su entrambi i lati, poi stampa le due righe da far accodare all'Orchestratore in `routes.tsx` e `main.py` — quei file sono append-only e sotto lock.

### Prima di ogni push

```bash
cd frontend && pnpm lint && pnpm typecheck && pnpm build
cd backend  && uv run ruff check . && uv run ruff format --check .
./check_compliance.sh
```

`check_compliance.sh` verifica che il tuo branch non abbia toccato i file globali. La stessa cosa gira in CI su ogni PR.

---

## Struttura

```
frontend/src/
  api/          client HTTP tipizzato e tipi condivisi
  components/   componenti riusabili, uno per file
  features/     <-- qui dentro si lavora
    home/  facilities/  feature-a/  feature-b/
  lib/          utility pure (triage, tipi struttura, tema, formattazione)
  routes.tsx    registro rotte — append-only

backend/app/
  core/         config, database, errori, stato dataset
  features/     <-- qui dentro si lavora
    facilities/  status/  feature_a/  feature_b/
  main.py       bootstrap — append-only

data/           dataset Open Data (vedi data/README.md)
```

---

## API

Base path `/api/v1`. Contratti completi in [`STATE.md`](STATE.md), documentazione interattiva su http://localhost:8000/docs.

| Endpoint | Cosa fa |
|---|---|
| `GET /system-status` | Stato dell'app e dei dataset caricati |
| `GET /facilities` | Elenco presidi, con `q`, `type`, `asl`, `limit`, `offset` |
| `GET /facilities/summary` | Aggregati per tipologia, ASL e comuni |
| `GET /facilities/{id}` | Dettaglio di un presidio |
| `POST /triage/messages` | Un turno di chat: risposta, e valutazione quando `done` è `true` |
| `POST /triage/plan` | Indirizzo + codice → strutture ordinate per tempo totale, con consiglio |
| `GET /triage/status` | Disponibilità dei provider LLM |
| `GET /congestion` | Carico dei presidi (oggi stimato, vedi sopra) |
| `GET /feature-b` | Slot libero, risponde `501` |
