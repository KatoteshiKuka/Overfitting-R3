# STATE.md — Stato Condiviso (Whiteboard)

Punto di sincronizzazione **asincrona** tra agenti e sviluppatori su PC diversi.
Si legge prima di iniziare, si scrive prima di implementare. `git pull --rebase origin main` prima di ogni modifica a questo file.

---

## 1. API Contracts (Schema Lock)

Chi implementa un endpoint scrive **qui** il contratto (path, query, JSON in/out) **prima** di scrivere il codice, e committa. Così il frontend parte sui mock senza aspettare il backend.

Regole di contratto (da `AGENTS.md`): base path `/api/v1`, risorse al plurale in kebab-case, chiavi JSON in `snake_case`, date ISO 8601 UTC, errori `{ "detail": "...", "code": "..." }`.

### `GET /api/v1/system-status` — 🔒 LOCKED (scocca)

```json
{
  "status": "ok",
  "version": "0.1.0",
  "data_loaded": false,
  "facilities_count": 0,
  "asl_count": 0,
  "datasets": [
    { "name": "facilities", "files": 0, "records": 0, "last_loaded_at": null }
  ]
}
```

### `GET /api/v1/facilities` — 🔒 LOCKED (scocca)

Query: `q` (string, ricerca su nome/comune/indirizzo), `type` (`pronto-soccorso` | `casa-comunita` | `farmacia` | `ambulatorio` | `ospedale` | `altro`), `asl` (string), `limit` (int, default 50, max 200), `offset` (int, default 0).

```json
{
  "items": [
    {
      "id": 1,
      "name": "Ospedale San Camillo — Pronto Soccorso",
      "type": "pronto-soccorso",
      "asl": "ASL Roma 3",
      "municipality": "Roma",
      "address": "Circonvallazione Gianicolense 87",
      "latitude": 41.8697,
      "longitude": 12.4515,
      "beds": 24,
      "phone": "+39 06 58701",
      "source": "example.facility.json"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### `GET /api/v1/facilities/summary` — 🔒 LOCKED (scocca)

```json
{
  "total": 12,
  "by_type": [{ "type": "pronto-soccorso", "count": 4 }],
  "by_asl": [{ "asl": "ASL Roma 1", "count": 3 }],
  "municipalities": 5
}
```

### `GET /api/v1/facilities/{id}` — 🔒 LOCKED (scocca)

Ritorna un singolo oggetto con lo stesso schema degli `items` sopra. `404` con `{ "detail": "...", "code": "facility_not_found" }`.

### `POST /api/v1/triage/messages` — 🔒 LOCKED (feature 1)

Un turno di conversazione. Il client manda tutta la cronologia: il backend non tiene sessione.

```json
// richiesta
{ "messages": [{ "role": "user", "content": "Ho mal di gola da due giorni" }] }

// risposta
{
  "reply": "Da quanto tempo hai la febbre?",
  "done": false,
  "assessment": null,
  "provider": "locale"
}
```

Quando `done` è `true`, `assessment` è valorizzato:

```json
{
  "code": "verde",
  "reason": "Disturbo comune, gestibile sul territorio.",
  "care_setting": "guardia medica",
  "advice": "Riposa e bevi molto. Se peggiori, chiama il 118.",
  "escalated": false,
  "red_flags": []
}
```

`provider` vale `locale` (LM Studio), `groq` o `regole` (fallback deterministico).
`escalated` è `true` solo quando le regole di sicurezza hanno alzato il codice **fino ad
arancione o rosso**: le correzioni minori non vanno segnalate, altrimenti l'avviso perde valore.

### `POST /api/v1/triage/plan` — 🔒 LOCKED (feature 1)

```json
// richiesta
{ "address": "Via Nazionale 100, Roma", "code": "verde", "limit": 5 }
```

Risposta: `origin` (indirizzo geocodificato), `options` ordinate per `total_minutes`
(`distance_km`, `travel_minutes`, `waiting_minutes`, `total_minutes`, `congestion_level`,
`route_source`, `recommended`) e `advice` scritto dall'LLM **sui numeri già calcolati**.

Errori: `422 address_not_found`, `404 no_geolocated_facility`.

### `GET /api/v1/triage/status` — 🔒 LOCKED (feature 1)

Disponibilità dei provider LLM. `fallback_ready` è sempre `true`: le regole non dipendono da nulla.

### `GET /api/v1/congestion` · `GET /api/v1/congestion/{facility_id}` — 🔒 LOCKED

Carico dei presidi: `ratio` (0–1), `waiting_minutes`, `people_waiting`, `level`
(`basso`/`medio`/`alto`), `source`, `updated_at`.

⚠️ **I valori sono oggi generati in modo deterministico**, non reali: gli Open Data non
espongono la saturazione in tempo reale. La tabella `facility_loads` è però scrivibile,
ed è il punto di aggancio della feature 2.

### `GET /api/v1/feature-b` — ⚪ SLOT LIBERO

Risponde `501` con `code: "not_implemented"`. Chi prende lo slot **sostituisce questa sezione**
con il contratto reale prima di implementare.

---

## 2. Dependency Requests

Nessuno installa dipendenze da solo. Si aggiunge una riga qui, l'Orchestratore approva e installa su `main`.

| Agente | Pacchetto | Ragione | Stato |
|---|---|---|---|
| `@diego/claude` | `leaflet` + `react-leaflet` | Mappa OpenStreetMap con i presidi colorati per congestione (feature 1). | **Merged** |
| `@diego/claude` | `httpx` | Chiamate a LM Studio, Groq, Nominatim e OSRM. Già presente come dipendenza di `fastapi[standard]`, nessuna installazione aggiuntiva. | **Merged** |

Pacchetti già approvati e installati (baseline pinnata, non si tocca):

- **frontend**: `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`, `tailwindcss`, `vite`, `typescript`, `eslint`, `prettier`
- **backend**: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `ruff`

---

## 3. Global Resources

### Porte

| Porta | Servizio | Note |
|---|---|---|
| 5173 | Vite dev server (frontend) | proxy `/api` → 8000, quindi niente CORS in dev |
| 8000 | FastAPI (backend) | `uv run fastapi dev app/main.py` |

### Variabili d'ambiente

Definite in `.env.example` (append-only). `.env` non si committa mai.

| Variabile | Default | Descrizione |
|---|---|---|
| `PRESIDIO_DATA_DIR` | `../data` | Cartella dei dataset Open Data |
| `PRESIDIO_DATABASE_URL` | `sqlite:///./presidio.db` | Connessione SQLite |
| `PRESIDIO_AUTO_SEED` | `true` | Carica i dati allo startup se il DB è vuoto |
| `PRESIDIO_LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio, endpoint OpenAI-compatibile |
| `PRESIDIO_LLM_MODEL` | `google/gemma-4-e4b` | Modello locale caricato in LM Studio |
| `PRESIDIO_GROQ_API_KEY` | *(vuota)* | Chiave Groq, usata come secondo provider |
| `PRESIDIO_GROQ_MODEL` | `openai/gpt-oss-120b` | Modello Groq |

⚠️ La chiave Groq **non si committa**: sta in `backend/.env`, che è gitignorato. Il repo è
pubblico, una chiave nel sorgente verrebbe scrapata e revocata nel giro di minuti.

### File globali sotto lock

Gli agenti feature **non** modificano questi file. Serve una riga in più? Annotala qui sotto e chiedi all'Orchestratore.

- `backend/app/main.py` — append-only, solo `include_router` in fondo
- `frontend/src/routes.tsx` — append-only, solo una voce in fondo all'array
- `frontend/package.json`, `pnpm-lock.yaml`, `backend/pyproject.toml`, `uv.lock`
- `frontend/tailwind.config.ts`, `frontend/src/styles/theme.css` — i token di tema sono condivisi

#### Richieste di modifica ai file globali

_(vuoto — formato: `| Agente | File | Riga da aggiungere | Stato |`)_

### Cartella dati

`data/` è condivisa e **append-only**: si aggiungono file, non si rinominano né si cancellano quelli degli altri. Vedi `data/README.md`.
