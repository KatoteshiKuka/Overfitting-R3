# Checklist: prendere in carico una feature

Da seguire in ordine. Ogni passo esiste per evitare un conflitto di merge già visto.

---

## 1. Prendi la task

```bash
git checkout main && git pull --rebase origin main
```

In `TASKS.md` sposta la card da `TODO` a `IN_PROGRESS`, scrivici il tuo ID agente e il nome del branch. Committa e **pusha subito**:

```bash
git commit -am "chore(tasks): prendo in carico <nome-feature>"
git push origin main
```

Questo è ciò che dice agli altri che l'area è occupata. Farlo *dopo* aver scritto il codice non serve a niente.

---

## 2. Scrivi il contratto

In `STATE.md`, sezione *API Contracts*, aggiungi il tuo endpoint con il JSON in ingresso e in uscita, **prima** di implementarlo. Rispetta le convenzioni: `/api/v1`, plurale kebab-case, chiavi `snake_case`, date ISO 8601 UTC, errori `{ detail, code }`.

Committa anche questo su `main`. Da qui in poi chi lavora sul frontend può partire sui mock senza aspettarti.

---

## 3. Genera lo scheletro

```bash
./scripts/new-feature.sh <nome-feature>
git checkout -b feat/<nome-feature>
```

Lo script crea `frontend/src/features/<nome>/` e `backend/app/features/<nome>/` e stampa le due righe da far accodare all'Orchestratore in `routes.tsx` e `main.py`.

Se invece stai riempiendo uno degli slot già esistenti (`feature-a` / `feature-b`), le rotte ci sono già: rinomina le cartelle e basta.

---

## 4. Implementa

Regole che valgono sempre:

- Tocca **solo** le tue due cartelle. Se ti serve qualcosa fuori, annotalo in `STATE.md` invece di prendertelo.
- Un file = una cosa. Niente `utils.ts` o `models.py` contenitore.
- Riusa quello che c'è invece di riscriverlo:
  - `@/lib/triage` — codici colore, soglie di pressione, livelli
  - `@/lib/facilityTypes` — tipologie di struttura, etichette, quali sono territoriali
  - `@/lib/format` — numeri, date, indirizzi
  - `@/api/client` — `apiGet` tipizzato con gestione errori
  - `@/components/*` — Card, Badge, StatTile, EmptyState, ErrorState, Skeleton, PageHeader…
  - backend: `app.core.database.get_db`, `app.core.errors.AppError`
- I colori semantici sono variabili CSS, mai valori hardcodati.
- Il router fa solo HTTP, la logica sta in `service.py`. Ogni endpoint ha un `response_model`.
- Codice in inglese, commenti in italiano, e solo sul *perché*.
- Serve una libreria nuova? Scrivi il codice, ma aggiungi **subito** una riga in `STATE.md` → *Dependency Requests* e avvisa l'Orchestratore. Non toccare `package.json` né `pyproject.toml`.

Ogni 15 minuti circa, e comunque prima di ogni pausa:

```bash
git pull --rebase origin main
```

---

## 5. Verifica prima del push

```bash
cd frontend && pnpm lint && pnpm typecheck && pnpm build
cd backend  && uv run ruff check . && uv run ruff format .
./check_compliance.sh
```

Tutti verdi, altrimenti non si pusha. Poi:

```bash
git pull --rebase origin main
git push origin feat/<nome-feature>
```

---

## 6. Apri la PR

Sposta la card in `TASKS.md` da `IN_PROGRESS` a `REVIEW`. Nella descrizione della PR metti il link alla sezione di `STATE.md` con il tuo contratto.

Se la PR tocca un file globale, aggiungi la label `integration` e spiega perché: senza, la CI la blocca — è il comportamento voluto.

Dopo il merge, la card va in `DONE`.
