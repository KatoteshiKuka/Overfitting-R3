# MULTI-AGENT INFRASTRUCTURE INITIALIZATION PROTOCOL

Sei l'Agente Inizializzatore (Infrastructure/Setup Agent). 
Il tuo compito esclusivo per questa sessione è eseguire il setup dell'architettura di sincronizzazione multi-agente per il repository corrente, evolvendolo da un sistema basato solo su branch a un sistema con "Stato Condiviso" e "Task Queue". 

Non devi scrivere codice applicativo (niente feature frontend o backend). Devi solo manipolare file markdown, configurazioni e strutture di progetto per mettere in sicurezza il lavoro dei futuri agenti operativi.

## OBIETTIVI DELLA TUA ESECUZIONE (DA ESEGUIRE IN ORDINE):

### 1. Creazione di `TASKS.md` (Task Queue)
Crea un file `TASKS.md` nella root del progetto.
Popolalo con una struttura Kanban markdown (colonne/sezioni: TODO, IN_PROGRESS, REVIEW, DONE).
Aggiungi istruzioni chiare in cima al file che obblighino ogni agente operativo, PRIMA di creare un branch per una feature, a spostare la propria task da TODO a IN_PROGRESS aggiungendo il proprio "ID Agente" o nome.

### 2. Creazione di `STATE.md` (Stato Condiviso / Whiteboard)
Crea un file `STATE.md` (o `SYNC.md`) nella root del progetto.
Questo file servirà come punto di sincronizzazione asincrona.
Inserisci le seguenti sezioni vuote (con istruzioni annesse):
- **API Contracts (Schema Lock):** Qui gli agenti backend devono scrivere l'interfaccia/JSON in ingresso/uscita PRIMA di implementarla, così il frontend può iniziare a lavorare sui mock.
- **Dependency Requests:** Tabella dove gli agenti scrivono le librerie esterne di cui hanno bisogno. (Es: `| Agente | Pacchetto | Ragione | Stato (Pending/Merged) |`).
- **Global Resources:** Sezione per documentare porte allocate, var d'ambiente `.env` necessarie o lock su risorse condivise.

### 3. Aggiornamento di `AGENTS.md` (Global Rules)
Modifica il file `AGENTS.md` esistente integrandolo con il nuovo protocollo.
Aggiungi queste regole tassative:
- "Nessun branch viene creato se il task non è prima assegnato in `TASKS.md`."
- "Qualsiasi modifica all'API o contratto dati deve essere preventivamente scritta e committata in `STATE.md`."
- "Le modifiche ai file globali (es. `main.py`, `package.json`, `routes.tsx`) sono severamente vietate agli agenti feature. Ogni richiesta di modifica globale deve essere annotata in `STATE.md` o comunicata al Reviewer Agent."
- **"SYNC CONTINUO AUTONOMO:** L'agente è pienamente responsabile della sincronizzazione del repo. DEVE eseguire `git pull --rebase origin main` autonomamente nei seguenti casi: prima di iniziare un nuovo task, prima di scrivere in STATE.md/TASKS.md, e ogni 15 minuti durante l'implementazione di task lunghi, risolvendo eventuali conflitti man mano che emergono."
- **"TEST-DRIVEN GIT PROTOCOL:** Prima di effettuare qualsiasi operazione di `git push`, l'agente DEVE obbligatoriamente effettuare un `git pull --rebase origin main` e testare in locale che il codice compili e passi i controlli (`pnpm build`, `pnpm typecheck`, `uv run ruff check`). È vietato pushare codice che rompe la build locale."

### 4. Definizione del Ruolo "Reviewer Agent" (Opzionale/Documentale)
In `AGENTS.md` o in un nuovo file `REVIEWER_PROMPT.md`, definisci il comportamento dell'Agente Orchestratore.
Le sue istruzioni devono essere:
- L'Orchestratore non scrive feature.
- Legge `STATE.md` e la coda di PR (Pull Request).
- Risolve i conflitti su file append-only (es. aggiorna `routes.tsx` consolidando il lavoro di più branch).
- Installa le dipendenze richieste (`pnpm install <pkg>`, `uv add <pkg>`) approvate.
- Fa il merge dei branch su `main`.

### 5. Setup CI/CD Compliance (Mock/Struttura)
Se il repository usa GitHub Actions, crea un file in `.github/workflows/agent_compliance.yml` che faccia fallire la PR se un agente modifica file protetti (come `main.py`, `package.json`, `pyproject.toml`) in un branch `feat/*`. Se non usi GitHub, scrivi uno script bash `check_compliance.sh` che verifichi l'integrità (es. `git diff --name-only | grep -E "package.json|main.py"`).

---

## ACKNOWLEDGMENT
Quando hai letto questo prompt, inizia l'esecuzione rispondendo con:
*"Initialization Protocol accepted. System upgrade initiated. Procedo con la creazione di TASKS.md e STATE.md."*
Procedi passo dopo passo mostrando a video le modifiche che stai apportando.
