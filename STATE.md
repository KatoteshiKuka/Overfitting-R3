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
// richiesta testuale
{ "messages": [{ "role": "user", "content": "Ho mal di gola da due giorni" }] }

// richiesta con foto clinica opzionale e temporanea
{
  "messages": [{
    "role": "user",
    "content": "Mi sono tagliato la mano da circa dieci minuti",
    "image": {
      "name": "ferita.jpg",
      "data_url": "data:image/jpeg;base64,..."
    }
  }]
}

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

`image` è ammesso solo sui messaggi dell'utente, nei formati JPEG, PNG o WebP, fino a 2 MB
decodificati. Viene inoltrato in memoria al provider multimodale e non viene scritto nel DB,
nei log applicativi, nel commitment, nella pre-accettazione o nella scheda paziente. La foto
resta visibile esclusivamente nella chat corrente del browser; il testo è comunque obbligatorio
per garantire il fallback prudenziale quando il provider non supporta immagini.

### `POST /api/v1/triage/plan` — 🔒 LOCKED (feature 1, esteso feature 2)

```json
// richiesta
{ "address": "Via Nazionale 100, Roma", "code": "verde", "limit": 5 }
```

Risposta: `origin` (indirizzo geocodificato), `options` ordinate per `total_minutes`
(`distance_km`, `travel_minutes`, `waiting_minutes`, `total_minutes`, `congestion_level`,
`route_source`, `recommended`) e `advice` scritto dall'LLM **sui numeri già calcolati**.

Ogni opzione porta anche `inbound_people` e `inbound_wait_minutes`: le persone che
HealthPulse ha già indirizzato lì e i minuti che aggiungono all'attesa. La risposta
include `crowding_note` quando la struttura che avremmo consigliato ignorando i nostri
stessi invii è diversa da quella consigliata, e `crowding_formula`
(`induced_crowding.v1`).

Il totale è `viaggio + attesa osservata + attesa indotta`: una struttura non viene mai
nascosta, viene mostrata con il tempo che avrà davvero quando ci si arriva.

Errori: `422 address_not_found`, `404 no_geolocated_facility`.

### `POST /api/v1/triage/nearby` — 🔒 LOCKED (feature 1)

Anteprima pubblica usata nella home, prima dell'autenticazione. Cerca i servizi territoriali
più vicini senza invocare l'LLM e senza salvare la posizione.

```json
// richiesta
{ "address": "geo:41.902800,12.496400", "limit": 8 }

// risposta
{
  "origin": { "label": "Posizione attuale", "latitude": 41.9028, "longitude": 12.4964 },
  "facilities": [{
    "facility_id": 91,
    "name": "Farmacia Centrale",
    "type": "farmacia",
    "address": "...",
    "municipality": "Roma",
    "latitude": 41.9,
    "longitude": 12.5,
    "distance_km": 0.6,
    "geo_precision": "esatta"
  }]
}
```

Sono incluse farmacie, case della comunità e ambulatori. Errori: `422 address_not_found`,
`404 no_geolocated_facility`.

### `GET /api/v1/triage/status` — 🔒 LOCKED (feature 1)

Disponibilità dei provider LLM. `fallback_ready` è sempre `true`: le regole non dipendono da nulla.

### `GET /api/v1/congestion` · `GET /api/v1/congestion/{facility_id}` — 🔒 LOCKED

Carico reale dei pronto soccorso, dal dataset regionale degli accessi:

```json
{
  "facility_id": 12,
  "queue": { "rosso": 0, "giallo": 4, "verde": 21, "bianco": 2, "non_assegnato": 0, "totale": 27 },
  "in_treatment": 49,
  "in_observation": 18,
  "ratio": 0.675,
  "level": "medio",
  "source": "open-data",
  "observed_at": "2021-07-31T16:34:00Z",
  "updated_at": "..."
}
```

Le code sono tenute **divise per colore**, non aggregate: l'attesa di chi arriva dipende
da quante persone più gravi ha davanti, e si calcola in
`backend/app/features/congestion/waiting.py`. Per questo `POST /triage/plan` restituisce
`waiting_minutes` diversi a seconda del codice della persona.

⚠️ `observed_at` è del 31/07/2021: è l'ultimo dato pubblico. La tabella `facility_loads`
è scrivibile ed è il punto di aggancio della feature 2, che porterà il tempo reale.

### `GET /api/v1/feature-b` — ⚪ SLOT LIBERO

Risponde `501` con `code: "not_implemented"`. Chi prende lo slot **sostituisce questa sezione**
con il contratto reale prima di implementare.

---

## Feature 2 — identità, commitment e console ospedaliera

Contratti scritti **prima** dell'implementazione, come impone il protocollo.

Regola trasversale: ogni valore esposto porta la propria **provenienza**, con questi valori
ammessi — `OBSERVED`, `HISTORICAL`, `OFFICIAL_FORECAST`, `DERIVED`, `SIMULATED`, `SYNTHETIC`,
`UNAVAILABLE`, `UNVERIFIED`. Non si mescolano: lo snapshot PS 2021 resta `HISTORICAL` e non
diventa mai `OBSERVED`.

### `POST /api/v1/auth/test-spid/login` — 🔒 LOCKED (feature 2)

```json
// richiesta
{ "username": "mario.rossi" }

// risposta 200
{
  "authenticated": true,
  "provider": "spid_test_mock",
  "synthetic": true,
  "profile": {
    "spidCode": "TESTSP00001",
    "name": "Mario",
    "familyName": "Rossi",
    "fiscalNumber": "RSSMRA80A01H501U",
    "dateOfBirth": "1980-01-01",
    "placeOfBirth": "Roma",
    "countyOfBirth": "RM",
    "gender": "M",
    "email": "mario.rossi@example.test",
    "mobilePhone": "+39 333 0000001"
  },
  "expires_at": "2026-09-10T22:00:00Z"
}
```

`401` con `code: "unknown_identity"` se lo username non esiste. La password non viene mai
richiesta né restituita. La risposta imposta il cookie `healthpulse_test_session`
(`HttpOnly`, `SameSite=Lax`, 8 ore).

### `GET /api/v1/auth/session` — 🔒 LOCKED (feature 2)

`200` con lo stesso oggetto della login quando la sessione è valida; `401` con
`code: "no_session"` altrimenti. È l'unica fonte dell'identità corrente: il client non
sceglie mai il `fiscal_code`.

### `POST /api/v1/auth/logout` — 🔒 LOCKED (feature 2)

`204`, cookie cancellato. Idempotente.

### `POST /api/v1/auth/hospital/login` — 🔒 LOCKED (feature 2)

Dominio **separato** da quello cittadino: il personale non usa SPID.

```json
// richiesta
{ "username": "ps.coordinator", "facility_id": 12 }

// risposta 200
{
  "authenticated": true,
  "provider": "hospital_mock",
  "synthetic": true,
  "operator": {
    "username": "ps.coordinator",
    "display_name": "Coordinamento PS",
    "role": "PS_COORDINATOR",
    "facility_id": 12,
    "facility_name": "Pol. Univ. Umberto I — Pronto Soccorso"
  },
  "expires_at": "..."
}
```

Ruoli: `HOSPITAL_ADMIN`, `PS_COORDINATOR`, `DEPARTMENT_LEAD`, `OPERATOR_READONLY`.
Cookie distinto: `healthpulse_hospital_session`.

### `GET /api/v1/citizens/me/profile` — 🔒 LOCKED (feature 2)

Profilo sanitario sintetico dell'utente autenticato, unito per `fiscal_code`. I campi
mancanti sono `null`, **non** stringhe vuote: l'interfaccia mostra `UNAVAILABLE`.

```json
{
  "fiscal_code": "RSSMRA80A01H501U",
  "given_name": "Mario",
  "family_name": "Rossi",
  "birth_date": "1980-01-01",
  "is_minor": false,
  "guardian": null,
  "gp": { "given_name": "Anna", "family_name": "Bianchi", "phone": "..." },
  "emergency_contact": null,
  "email": "mario.rossi@example.test",
  "exemptions": [{ "code": "048", "description": "..." }],
  "chronic_conditions": ["ipertensione"],
  "recent_episodes": [{ "date": "2025-11-02", "facility": "...", "outcome": "dimesso" }],
  "demo_care_intent": "minor_wound_care",
  "provenance": "SYNTHETIC",
  "synthetic": true
}
```

### `POST /api/v1/arrivals/commitments` — 🔒 LOCKED (feature 2)

Il cittadino dichiara che si sta dirigendo a una struttura. **Mai creato automaticamente**:
serve un'azione esplicita.

```json
// richiesta — il codice fiscale NON si accetta dal client, viene dalla sessione
{
  "facility_id": 12,
  "eta_minutes": 18,
  "care_intent": "musculoskeletal_minor",
  "care_cluster": "minor_trauma",
  "consents": { "share_arrival": true, "share_preadmission": true, "share_reason": true }
}

// risposta 201
{
  "commitment_id": "cmt_9f3a...",
  "facility_id": 12,
  "status": "CONFIRMED",
  "care_intent": "musculoskeletal_minor",
  "care_cluster": "minor_trauma",
  "created_at": "...",
  "expected_arrival_at": "...",
  "weight": 0.75,
  "weight_formula": "commitment_weight.v1",
  "provenance": "DERIVED",
  "synthetic": true
}
```

Stati: `CONFIRMED` · `EN_ROUTE` · `ARRIVED` · `CANCELLED` · `EXPIRED`.

`GET /api/v1/arrivals/commitments/mine` elenca i propri.
`POST /api/v1/arrivals/commitments/{id}/cancel` revoca — sempre possibile, **nessuna
penalità, nessun flag no-show sul cittadino**.

### `POST /api/v1/navigation/preadmission` — 🔒 LOCKED (feature 2)

Crea la pre-accettazione **dopo** un commitment. Composizione a tre provider: identità dalla
sessione, contesto clinico dai dati sintetici, contatti e consensi da input dell'utente.
La conferma della destinazione crea subito questa pre-accettazione: l'ospedale scelto vede
il resoconto prima dell'arrivo, senza dover attendere il check-in.

`triage_hint` è **sempre `null`**: HealthPulse non pre-assegna il triage ospedaliero.

```json
{
  "code": "PA-7QK4-2M",
  "commitment_id": "cmt_9f3a...",
  "status": "issued",
  "expires_at": "...",
  "triage_hint": null,
  "care_cluster": "minor_trauma",
  "identity": { "given_name": "Mario", "family_name": "Rossi", "fiscal_code": "..." },
  "clinical_context": { "exemptions": [], "chronic_conditions": [], "gp": null },
  "triage_summary": {
    "priority_code": "arancione",
    "reason": "Ferita con osso esposto, rischio di infezione e peggioramento",
    "advice": "Non muovere la gamba e copri la ferita con una garza pulita.",
    "provider": "groq",
    "provisional": true
  },
  "provenance": { "identity": "SYNTHETIC", "clinical": "SYNTHETIC", "input": "USER" }
}
```

`GET /api/v1/admission/resolve/{code}` — l'ospedale risolve il codice (token monouso).
`POST /api/v1/admission/{code}/accept` — segna `accepted`; un secondo tentativo dà
`409` con `code: "token_already_used"`, scaduto `410` con `code: "token_expired"`.
Il check-in conferma esclusivamente che la persona è arrivata e porta il commitment a
`ARRIVED`: non assegna il triage, non certifica la veridicità e non genera penalità.

### `GET /api/v1/hospital/incoming-patients` — 🔒 LOCKED (feature 2)

Elenca i resoconti dei pazienti sintetici che hanno confermato di dirigersi verso la
struttura dell'operatore autenticato. Identità, profilo sanitario e valutazione preliminare
sono disponibili **prima** del check-in; commitment annullati o scaduti sono esclusi.

### `PUT /api/v1/congestion/{facility_id}` — 🔒 LOCKED (feature 2)

L'operatore dichiara il carico reale del proprio PS. Riusa la tabella `facility_loads`
esistente: **nessuna tabella parallela**.

```json
// richiesta
{
  "waiting_red": 1, "waiting_yellow": 4, "waiting_green": 12,
  "waiting_white": 2, "waiting_unassigned": 0,
  "in_treatment": 9, "in_observation": 3,
  "observed_at": "2026-09-10T14:05:00Z"
}
```

Al salvataggio `source` diventa `dichiarato` e `observed_at` quello indicato. Il routing
cittadino legge la stessa riga, quindi l'effetto è immediato su tutta l'app.

### `GET /api/v1/hospital/console/overview` — 🔒 LOCKED (feature 2)

Vista aggregata della struttura dell'operatore autenticato. **Nessun dato nominativo.**

```json
{
  "facility": { "id": 12, "name": "...", "municipality": "Roma" },
  "pressure": { "level": "alto", "ratio": 0.92, "provenance": "HISTORICAL", "observed_at": "2021-07-31T16:34:00Z" },
  "inbound": {
    "next_30_min": { "commitments": 3, "weighted": 2.25 },
    "next_60_min": { "commitments": 5, "weighted": 3.75 },
    "next_4_hours": { "commitments": 8, "weighted": 6.0 },
    "provenance": "DERIVED",
    "weight_formula": "commitment_weight.v1"
  },
  "care_mix": [{ "cluster": "minor_trauma", "count": 4 }],
  "readiness": [{ "area": "Radiologia", "level": "HIGH", "reason": "..." }],
  "staffing": {
    "on_shift": 7, "on_call": 3, "resting": 5,
    "deficit": [{ "qualification": "INFERMIERE", "additional_shifts_suggested": 2, "reason": "..." }],
    "excluded": [{ "id": "MED-03", "exclusion_reason": "Riposo minimo non rispettato" }],
    "provenance": "SIMULATED",
    "policy": "SIMULATED HR POLICY"
  }
}
```

`readiness` usa categorie (`LOW`/`MODERATE`/`HIGH`/`VERY_HIGH`), mai percentuali: non
esiste un modello validato dietro. Formula `surge_deficit.v1`, versionata in configurazione.

### Righe che l'Orchestratore deve accodare ai file globali

`backend/app/main.py`, in fondo:

```python
from app.features.auth.router import router as auth_router  # noqa: E402
from app.features.citizens.router import router as citizens_router  # noqa: E402
from app.features.arrivals.router import router as arrivals_router  # noqa: E402
from app.features.hospital.router import router as hospital_router  # noqa: E402

app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(citizens_router, prefix=settings.api_prefix)
app.include_router(arrivals_router, prefix=settings.api_prefix)
app.include_router(hospital_router, prefix=settings.api_prefix)
```

`frontend/src/App.tsx` — modifica minima, l'unico punto condiviso che cambia:

```tsx
<AuthGate>
  <AppShell>{/* invariato */}</AppShell>
</AuthGate>
```

---

## 2. Dependency Requests

Nessuno installa dipendenze da solo. Si aggiunge una riga qui, l'Orchestratore approva e installa su `main`.

| Agente | Pacchetto | Ragione | Stato |
|---|---|---|---|
| `@diego/claude` | `leaflet` + `react-leaflet` | Mappa OpenStreetMap con i presidi colorati per congestione (feature 1). | **Merged** |
| `@diego/claude` | `httpx` | Chiamate a LM Studio, Groq, Nominatim e OSRM. Già presente come dipendenza di `fastapi[standard]`, nessuna installazione aggiuntiva. | **Merged** |
| `@diego/claude` | `qrcode` + `@types/qrcode` | QR del codice di pre-accettazione. Un encoder scritto a mano era stato tentato e scartato: la versione 1 richiede il blocco singolo, dalla 3 in poi serve l'interlacciamento, e un QR *quasi* corretto fallisce allo sportello senza dirlo. 20 KB, MIT. | **Merged** |

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
| `HEALTHPULSE_DATA_DIR` | `../data` | Cartella dei dataset Open Data |
| `HEALTHPULSE_DATABASE_URL` | `sqlite:///./healthpulse.db` | Connessione SQLite |
| `HEALTHPULSE_AUTO_SEED` | `true` | Carica i dati allo startup se il DB è vuoto |
| `HEALTHPULSE_LLM_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio, endpoint OpenAI-compatibile |
| `HEALTHPULSE_LLM_MODEL` | `google/gemma-4-e4b` | Modello locale caricato in LM Studio |
| `HEALTHPULSE_GROQ_API_KEY` | *(vuota)* | Chiave Groq, usata come secondo provider |
| `HEALTHPULSE_GROQ_MODEL` | `openai/gpt-oss-120b` | Modello Groq |

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
