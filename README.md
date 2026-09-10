# HealthPulse — Emergency Triage Assistant

Web app che aiuta il cittadino a capire **dove andare** quando ha un problema di salute non grave: invece del pronto soccorso, la struttura territoriale più adatta al caso — casa della comunità, farmacia attrezzata, ambulatorio.

Traccia 3 — Sanità / Healthcare. Dati dal Portale Open Data della Regione Lazio e dal Portale Nazionale Open Data.

Stato: **percorso completo in entrambe le direzioni.** Il cittadino descrive il problema,
riceve un codice e la struttura più adatta con i tempi reali, conferma dove sta andando e
ottiene un codice per l'accettazione. La struttura vede arrivare quella persona, sa che
tipo di accesso aspettarsi e riceve una proposta su quante risorse servono.

L'app si apre con la scelta del ruolo, senza chiedere niente: l'identità viene richiesta
solo al momento di confermare una destinazione (cittadino) o di aprire la console
(personale). Vedi [`docs/SPID_TEST.md`](docs/SPID_TEST.md).

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
4. **Nessun effetto gregge.** Una struttura conveniente lo è per tutti quelli che chiedono
   nello stesso momento: consigliarla a venti persone creerebbe lì la coda che si voleva
   evitare. Prima di ordinare le opzioni si conta quante persone HealthPulse ha già
   indirizzato in ciascuna e non sono ancora arrivate, e quell'attesa si somma alle altre.
   Chi si vede consigliare una struttura più lontana legge il motivo
   (`backend/app/features/arrivals/crowding.py`, formula `induced_crowding.v1`).

### Configurazione LLM

Il modello locale si configura in `backend/.env` (vedi `.env.example`). Per Groq serve
`HEALTHPULSE_GROQ_API_KEY`. **La chiave non va committata**: il repo è pubblico.

### I dati sono reali

L'app è alimentata dagli Open Data della Regione Lazio, già scaricati e committati in
`data/` (vedi [`data/README.md`](data/README.md)):

- **1800+ presidi**: i 49 pronto soccorso del Lazio, gli ospedali pubblici, le farmacie
  attive e gli ambulatori accreditati, tutti georeferenziati.
- **Code reali per codice colore** in ogni pronto soccorso, dal dataset regionale degli
  accessi. Su questi conteggi si calcola l'attesa di chi arriva adesso: non un numero
  unico per struttura, ma il tempo che dipende da quante persone più gravi hai davanti.

⚠️ La fotografia delle code è del **31/07/2021**: è l'ultimo dato pubblico esposto dalla
Regione, che per il tempo reale offre solo una pagina web senza feed. I numeri sono reali
ma non aggiornati, e l'interfaccia dichiara sempre la data a cui si riferiscono. Il tempo
reale arriverà con la feature dedicata al personale, che scrive sulla stessa tabella.

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

### Provarla dal telefono

Vite è già in ascolto su tutte le interfacce, quindi `pnpm dev` (o `npm run dev`) stampa
anche un indirizzo di rete:

```
➜  Network: http://192.168.x.x:5173/
```

Aprilo dal telefono sulla stessa rete Wi-Fi. Le chiamate all'API passano dal proxy di
Vite, quindi funzionano senza configurare niente.

Per installarla come app (icona sulla home, schermo intero) serve la build vera, perché
il service worker è attivo solo in produzione:

```bash
cd frontend && pnpm build && pnpm preview --host   # :4173
```

Su Android: menu del browser → «Installa app». Su iOS: Condividi → «Aggiungi a Home».

### Dimostrare che la logica funziona

```bash
uv run --with httpx python scripts/demo_closed_loop.py
```

Percorre l'intero flusso con le API pubbliche e stampa cosa succede a ogni passaggio:
login, profilo, **saturazione di una struttura con 20 invii e spostamento della
raccomandazione**, conferma, codice di pre-accettazione, console della struttura,
accettazione allo sportello, revoca senza conseguenze.

Vite fa da proxy su `/api` verso il backend: nel codice si usano sempre URL relative,
niente CORS in dev. L'app parte anche **senza dati**: in quel caso mostra come caricarli
invece di rompersi.

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
    home/  triage/  operatore/  auth/  facilities/
  lib/          utility pure (triage, tipi struttura, tema, formattazione)
  routes.tsx    registro rotte — append-only

backend/app/
  core/         config, database, errori, stato dataset
  features/     <-- qui dentro si lavora
    auth/  citizens/  arrivals/  hospital/  triage/  congestion/  facilities/
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
| `POST /auth/test-spid/login` | Accesso con identità di test, imposta il cookie di sessione |
| `GET /citizens/me/profile` | Profilo sanitario dell'utente autenticato |
| `POST /arrivals/commitments` | Conferma della destinazione, revocabile |
| `POST /navigation/preadmission` | Codice di pre-accettazione, monouso |
| `GET /hospital/console/overview` | Vista aggregata della struttura, per il personale |
| `PUT /congestion/{id}` | L'operatore dichiara il carico reale del proprio PS |
