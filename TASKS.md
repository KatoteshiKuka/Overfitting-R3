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

- [ ] `feature-a` — **da definire dal team**. Slot già predisposto e navigabile. · owner: _libero_ · branch: `feat/<nome>` · area: `frontend/src/features/feature-a` + `backend/app/features/feature_a`
- [ ] `feature-b` — **da definire dal team**. Slot già predisposto e navigabile. · owner: _libero_ · branch: `feat/<nome>` · area: `frontend/src/features/feature-b` + `backend/app/features/feature_b`

> Candidati coerenti con la Traccia 3 (non vincolanti): assistente di triage sintomi → codice colore → struttura consigliata; motore di contesto picchi termici + eventi in città → indice di pressione sui pronto soccorso; serie storiche tempi di attesa ambulatoriali.

## IN_PROGRESS

_(vuoto)_

## REVIEW

_(vuoto)_

## DONE

- [x] `infra` — Protocollo multi-agente: `TASKS.md`, `STATE.md`, `REVIEWER_PROMPT.md`, CI di compliance. · owner: `@diego/claude` · branch: `feat/scocca`
- [x] `scocca` — Scaffold avviabile frontend + backend, app shell, tema triage, registry presidi, cartella `data/`. · owner: `@diego/claude` · branch: `feat/scocca`
