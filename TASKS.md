# TASKS.md — Task Queue

Coda di lavoro condivisa. È l'unica fonte di verità su **chi sta facendo cosa**.

## Regole (obbligatorie)

1. **Nessun branch senza task assegnata.** Prima di eseguire `git checkout -b feat/<nome>`, sposta la tua card da `TODO` a `IN_PROGRESS` e scrivici il tuo **ID Agente** (es. `@diego/claude`, `@marco/cursor`, `@sara/gemini`).
2. Prima di modificare questo file esegui sempre `git pull --rebase origin main`.
3. Una card = una feature = una cartella frontend + una cartella backend. Se la tua card richiede di toccare un file globale, annotalo in `STATE.md` invece di farlo.
4. Il commit che sposta la card va pushato **subito**, prima di iniziare a scrivere codice: è così che gli altri sanno che quell'area è occupata.
5. Da `IN_PROGRESS` si passa a `REVIEW` quando la PR è aperta e verde, a `DONE` solo dopo il merge su `main`.

Formato card:

```
- [ ] <id-task> — <descrizione breve> · owner: <ID Agente> · branch: `feat/<nome>` · area: `frontend/src/features/<x>` + `backend/app/features/<x>`
```

---

## TODO

- [ ] `spid-testenv2` — **P1.** Ambiente Docker `italia/spid-testenv2` e HealthPulse come Service Provider SAML. Oggi `SpidTestEnvProvider` è dichiarato ma solleva `NotImplementedError`, e il formato del file utenti è `UNVERIFIED`. Vedi `docs/SPID_TEST.md`. Richiede una eccezione per la cartella top-level `spid/` e probabilmente una dipendenza SAML: **entrambe da concordare prima**. · owner: _libero_
- [ ] `collective-routing` — **P1.** Far pesare gli Arrival Commitment sul ranking del cittadino: se HealthPulse ha già indirizzato troppe persone verso una struttura, le successive vanno penalizzate. Formula deterministica e versionata, niente apprendimento. · owner: _libero_
- [ ] `capability-graph` — **P1.** Grafo documentato delle prestazioni per tipologia di struttura, per rispondere `NO DOCUMENTED CAPABILITY MATCH` invece di consigliare a caso (caso HERO D). · owner: _libero_
- [ ] `feature-b` — slot residuo, ancora da definire. · owner: _libero_ · branch: `feat/<nome>` · area: `frontend/src/features/feature-b` + `backend/app/features/feature_b`

## IN_PROGRESS

_(vuoto)_

## REVIEW

_(vuoto)_

## DONE

- [x] `infra` — Protocollo multi-agente: `TASKS.md`, `STATE.md`, `REVIEWER_PROMPT.md`, CI di compliance. · owner: `@diego/claude` · branch: `feat/scocca`
- [x] `scocca` — Scaffold avviabile frontend + backend, app shell, tema triage, registry presidi, cartella `data/`. · owner: `@diego/claude` · branch: `feat/scocca`
- [x] `feature-1-triage` — Scelta del ruolo all'apertura; assistente di triage con LLM (LM Studio → Groq → regole), classificazione nei cinque codici, mappa OpenStreetMap con congestione e tempi reali di viaggio e attesa. · owner: `@diego/claude` · branch: `feat/triage-paziente`
- [x] `feature-2` — Identità SPID di test con sessione persistente, 15 pazienti sintetici, Arrival Commitment, pre-accettazione con token monouso, console ospedaliera con inbound aggregato, care mix, readiness e copertura turni. Closed loop verificato. · owner: `@diego/claude` · branch: `feat/dati-reali`
- [x] `dati-reali` — Ingestione degli open data della Regione Lazio: 1848 presidi georeferenziati e code reali per codice colore dei 49 pronto soccorso. Interfaccia a tutta finestra, mappa minimale con percorso tracciato. · owner: `@diego/claude` · branch: `feat/dati-reali`
