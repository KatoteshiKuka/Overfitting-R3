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

- [ ] `feature-2-operatori` — **Area del personale di struttura.** Monitoraggio dei reparti e aggiornamento del carico reale dei presidi. La pagina `/operatore` esiste già ed è volutamente vuota. · owner: _libero_ · branch: `feat/<nome>` · area: `frontend/src/features/operatore` + `backend/app/features/congestion`

> Punto di aggancio già pronto: la tabella `facility_loads` è scrivibile e oggi contiene valori
> generati in modo deterministico. Chi prende questa feature aggiunge gli endpoint di scrittura
> e l'interfaccia per dichiarare il carico reale; il resto dell'app si aggiorna da sé, perché
> legge già quella tabella.

- [ ] `feature-b` — slot residuo, ancora da definire. · owner: _libero_ · branch: `feat/<nome>` · area: `frontend/src/features/feature-b` + `backend/app/features/feature_b`

## IN_PROGRESS

_(vuoto)_

## REVIEW

_(vuoto)_

## DONE

- [x] `infra` — Protocollo multi-agente: `TASKS.md`, `STATE.md`, `REVIEWER_PROMPT.md`, CI di compliance. · owner: `@diego/claude` · branch: `feat/scocca`
- [x] `scocca` — Scaffold avviabile frontend + backend, app shell, tema triage, registry presidi, cartella `data/`. · owner: `@diego/claude` · branch: `feat/scocca`
- [x] `feature-1-triage` — Scelta del ruolo all'apertura; assistente di triage con LLM (LM Studio → Groq → regole), classificazione nei cinque codici, mappa OpenStreetMap con congestione e tempi reali di viaggio e attesa. · owner: `@diego/claude` · branch: `feat/triage-paziente`
- [x] `dati-reali` — Ingestione degli open data della Regione Lazio: 1848 presidi georeferenziati e code reali per codice colore dei 49 pronto soccorso. Interfaccia a tutta finestra, mappa minimale con percorso tracciato. · owner: `@diego/claude` · branch: `feat/dati-reali`
