# AGENTS.md

Regole del progetto per chiunque scriva codice qui: umani e agenti AI. Se una richiesta contraddice questo file, segnalalo invece di improvvisare.

Progetto: `<NOME_PROGETTO>` — web app sviluppata in hackathon da 3 persone, su PC diversi, con agenti diversi, sullo stesso repo.

---

## Stack

**Frontend** — React + TypeScript, build con Vite, package manager `pnpm`
**Backend** — FastAPI (Python 3.12+), validazione con Pydantic v2, dipendenze con `uv`
**Styling** — Tailwind CSS
**Data fetching** — TanStack Query
**DB** — SQLite + SQLAlchemy

Le versioni si pinnano il primo giorno e non si aggiornano più. Nessuna dipendenza nuova senza chiedere prima al team.

---

## Struttura

```
frontend/
  src/
    api/           # client HTTP e tipi condivisi
    features/      # <-- qui dentro si lavora
      <feature>/
    components/    # componenti riusabili
    lib/           # utility pure
    routes.tsx     # registro rotte
backend/
  app/
    main.py        # bootstrap + include_router
    core/          # config e dipendenze comuni
    features/      # <-- qui dentro si lavora
      <feature>/
        router.py
        schemas.py
        models.py
        service.py
```

Ogni feature vive in una sua cartella, sia lato frontend che backend. Chi lavora su una feature tocca solo quelle due cartelle.

---

## Le 5 regole che rendono il merge facile

**1. Ownership per feature, non per layer.**
Non si divide "tu il frontend, io il backend". Si divide per dominio: ognuno prende una feature e la fa end-to-end. Così due persone non aprono mai lo stesso file.

| Dev | Feature |
|---|---|
| A | `<feature-1>` |
| B | `<feature-2>` |
| C | `<feature-3>` |

**2. Un file = una cosa.**
Un componente per file, un router per feature, un modello per file. Niente file "contenitore" tipo `utils.ts` o `models.py` unici: sono calamite per conflitti.

**3. I file condivisi sono append-only.**
`main.py`, `routes.tsx`, `package.json`, `pyproject.toml`, `.env.example`: si aggiunge una riga in fondo, non si riordina e non si riformatta niente. Se un agente propone di "sistemare" o riorganizzare uno di questi file, rifiuta.

**4. Branch corti e rebase.**
Branch `feat/<nome>`, merge su `main` entro poche ore. `git pull --rebase origin main` prima di ogni push. Mai lasciare un branch aperto tutta la notte.

**5. Formattazione automatica, uguale per tutti.**
Prettier + ESLint sul frontend, Ruff sul backend, configurazione committata nel repo. Serve perché agenti diversi formattano in modo diverso, e un diff pieno di riformattazioni casuali è impossibile da mergiare. Nessuno cambia la config in locale.

---

## Convenzioni di codice

**TypeScript**
- `strict: true`, niente `any`
- Componenti in `PascalCase.tsx`, hook in `useNome.ts`, resto in `camelCase.ts`
- Solo componenti funzione, props tipizzate con `type`
- Import con alias `@/`

**Python**
- Type hints ovunque, `snake_case` per funzioni, `PascalCase` per classi
- `async def` per gli endpoint
- Il router fa solo HTTP, la logica sta in `service.py`
- Ogni endpoint ha un `response_model`

**API**
- Base path `/api/v1`, risorse al plurale in kebab-case
- JSON con chiavi in `snake_case`
- Date in ISO 8601 UTC
- Errori: `{ "detail": "...", "code": "..." }`
- Lo schema si concorda **prima** di implementare, così il frontend può partire su dati mock senza aspettare il backend

**Commit**
```
feat(auth): aggiunge login
fix(dashboard): corregge totale
chore(deps): aggiunge tanstack query
```

---

## Comandi

```bash
# setup
cd frontend && pnpm install
cd backend  && uv sync

# sviluppo
pnpm dev                          # :5173
uv run fastapi dev app/main.py    # :8000

# prima di ogni push
pnpm lint && pnpm typecheck && pnpm build
uv run ruff check --fix . && uv run ruff format .
```

Vite fa da proxy su `/api` verso il backend: nel codice si usano sempre URL relative, niente CORS in dev.

`.env` non si committa mai. Ogni variabile nuova va aggiunta a `.env.example` nello stesso commit.

---

## Per gli agenti AI

- Lavora solo dentro la cartella della feature in corso. Se serve toccare un file fuori, dillo prima di farlo.
- Non creare nuove cartelle top-level, nuovi pattern architetturali o nuovi layer di astrazione.
- Non riformattare, riordinare o "ripulire" file che non stai modificando: genera diff minimi.
- Scrivi codice completo e funzionante, niente `TODO` o funzioni vuote.
- Se cambi il contratto API, aggiorna nello stesso passaggio lo schema Pydantic, il router e la chiamata dal frontend.
- Codice in inglese, commenti in italiano. Commenta solo il perché, mai il cosa.
- Se un requisito è ambiguo, fai una domanda sola e proponi il default che useresti.

---

## Protocollo di sincronizzazione multi-agente

Regole tassative, valide per umani e agenti. Si applicano **sopra** tutto il resto di questo file.

**1. Nessun branch senza task.**
Nessun branch viene creato se il task non è prima assegnato in `TASKS.md`. Sposta la card da `TODO` a `IN_PROGRESS` con il tuo ID Agente, committa e pusha, *poi* apri il branch.

**2. Il contratto API viene prima del codice.**
Qualsiasi modifica all'API o al contratto dati deve essere preventivamente scritta e committata in `STATE.md`. Il frontend lavora sui mock di quel contratto senza aspettare il backend.

**3. File globali vietati.**
Le modifiche ai file globali (`backend/app/main.py`, `frontend/src/routes.tsx`, `package.json`, `pyproject.toml`, i lockfile, i token di tema) sono severamente vietate agli agenti feature. Ogni richiesta di modifica globale va annotata in `STATE.md` o comunicata al Reviewer Agent, che la applica lui.

**4. Sync continuo autonomo.**
L'agente è pienamente responsabile della sincronizzazione del repo. DEVE eseguire `git pull --rebase origin main` autonomamente: prima di iniziare un nuovo task, prima di scrivere in `STATE.md` o `TASKS.md`, e ogni 15 minuti durante l'implementazione di task lunghi, risolvendo i conflitti man mano che emergono.

**5. Test-driven git protocol.**
Prima di qualsiasi `git push` l'agente DEVE eseguire `git pull --rebase origin main` e verificare in locale che il codice compili e passi i controlli:

```bash
cd frontend && pnpm lint && pnpm typecheck && pnpm build
cd backend  && uv run ruff check . && uv run ruff format --check .
./check_compliance.sh
```

È vietato pushare codice che rompe la build locale.

**Dipendenze.** Se il tuo codice richiede un pacchetto non presente nella baseline, scrivi il codice normalmente ma aggiungi **subito** una riga in `STATE.md` → *Dependency Requests* e avvisa il Reviewer Agent. Non modificare `package.json` né `pyproject.toml` da solo.

Il ruolo dell'Orchestratore è descritto in `REVIEWER_PROMPT.md`.
