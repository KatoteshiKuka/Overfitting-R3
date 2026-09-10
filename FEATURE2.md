# HEALTHPULSE — PROMPT DI IMPLEMENTAZIONE PER DIEGO

## CONTESTO

Repo:

`Overfitting-R3`

Branch su cui devi lavorare:

`feat/dati-reali`

Questo branch contiene già lavoro importante sui dati reali e NON deve essere ricostruito da zero.

L'obiettivo è integrare sul branch esistente le nuove funzionalità definite nel piano HealthPulse di Matteo, con particolare attenzione a:

1. autenticazione cittadino tramite identità SPID di TEST;
2. sessione persistente all'ingresso dell'app;
3. 15 pazienti sintetici coerenti end-to-end;
4. Citizen Navigator / compatibilità strutture;
5. pre-accettazione PS;
6. Arrival Commitment;
7. flusso cittadino → ospedale;
8. Hospital Operations Console;
9. inbound traffic HealthPulse;
10. supporto alla copertura turni;
11. provenance e distinzione rigorosa REAL / HISTORICAL / DERIVED / SIMULATED.

IMPORTANTE:

NON devi distruggere, sostituire o semplificare l'implementazione dati reali già presente.

Devi costruire SOPRA quella base.

---

# 0. REGOLA ASSOLUTA SUL BRANCH

Lavorare esclusivamente su:

`feat/dati-reali`

NON:

- fare checkout di main;
- fare reset;
- cancellare i tre commit dati-reali;
- ricreare il branch;
- sovrascrivere i dataset;
- sostituire la pipeline Open Data;
- fare force push;
- merge automatici su main.

Prima di scrivere codice:

```bash
git fetch --all --prune
git status --short --branch
git rev-parse --abbrev-ref HEAD
git rev-list --left-right --count origin/main...HEAD
git log --oneline --decorate -8
```

Devi essere su:

`feat/dati-reali`

Al momento dell'audit questo branch risultava:

- working tree pulito;
- 3 commit avanti a origin/main;
- 0 commit indietro.

NON assumere che sia ancora così: verifica.

Se `origin/main` nel frattempo è avanzato, segui AGENTS.md e il protocollo multi-agent senza perdere i commit del branch.

Prima di qualunque modifica leggi:

- `AGENTS.md`
- `STATE.md`
- `TASKS.md`
- `data/README.md`

Poi verifica se nel frattempo sono comparsi:

- `docs/HEALTHPULSE_INTEGRATION_PLAN.md`
- `docs/PREACCETTAZIONE_PS.md`
- `data/preadmission/example.preadmission.json`

Al momento dell'audit NON erano presenti.

Se ora esistono, sono fonte di verità e vanno letti.

Se non esistono, NON fingere che esistano e NON inventare contenuti attribuendoli a quei documenti.

---

# 1. COSA ESISTE GIÀ E NON DEVI ROMPERE

Il branch `feat/dati-reali` contiene già una pipeline reale.

## Dataset

Sono già presenti:

```text
data/raw/pronto_soccorso.csv
data/raw/farmacie.csv
data/raw/ospedali.csv
data/raw/private.csv

data/facilities/pronto-soccorso.json
data/facilities/farmacie.json
data/facilities/ospedali.json
data/facilities/ambulatori.json

data/congestion/pronto-soccorso.json
```

La provenienza è descritta in:

`data/README.md`

e nella matrice:

`data/FINALIDATASET.xlsx`

## Ingestione

Esiste già:

`scripts/fetch_open_data.py`

che:

- scarica i dataset;
- mantiene una copia raw;
- normalizza;
- geocodifica;
- usa Nominatim;
- controlla coordinate anomale;
- genera snapshot utilizzabili offline.

NON riscriverlo.

Estendilo soltanto quando indispensabile e con diff minimo.

## Facilities

Esistono già:

```text
backend/app/features/facilities/
```

con:

- loader;
- modelli;
- seed;
- service;
- router.

Il loader contiene già `FIELD_ALIASES`.

Riutilizzalo.

## Congestione

Esiste già:

```text
backend/app/features/congestion/
```

con `FacilityLoad`.

Importantissimo:

le code sono separate per:

- rosso;
- giallo;
- verde;
- bianco;
- non assegnato.

Sono inoltre disponibili:

- `in_treatment`;
- `in_observation`;
- `capacity_hint`;
- `ratio`;
- `source`;
- `observed_at`;
- `updated_at`.

Non perdere questa granularità.

Lo snapshot Open Data è reale ma storico:

31/07/2021.

NON deve mai diventare magicamente realtime.

## Waiting time

Esiste:

`backend/app/features/congestion/waiting.py`

L'attesa dipende dalla priorità e dalla composizione della coda.

NON sostituire questo comportamento con:

`waiting = queue / capacity`

o altre formule semplificate.

## Triage corrente

Esistono già:

```text
POST /api/v1/triage/messages
POST /api/v1/triage/plan
GET  /api/v1/triage/status
```

Il flusso usa:

LLM locale
→ Groq
→ fallback deterministico.

Il routing usa:

Nominatim
+
OSRM
+
attesa del PS
+
distanza/tempo.

NON cancellare questi endpoint.

NON rompere i relativi contratti.

Le nuove funzionalità devono essere additive.

---

# 2. PROBLEMA ARCHITETTURALE DA RISOLVERE: AUTH

Attualmente NON esiste autenticazione.

`frontend/src/lib/useRole.ts` memorizza soltanto:

`healthpulse-role`

in `localStorage`.

Questo NON è una sessione utente.

Dobbiamo introdurre una vera separazione:

```text
ROLE
!=
IDENTITY
!=
SESSION
```

---

# 3. NUOVO ENTRY FLOW

Il cittadino deve autenticarsi quando entra nell'app.

Flusso richiesto:

```text
APERTURA HEALTHPULSE
       ↓
controllo sessione
       ↓
sessione valida?
   ↙            ↘
 NO              YES
 ↓                ↓
SPID TEST       APP
 ↓
LOGIN
 ↓
SESSIONE
 ↓
APP
```

Se aggiorno il browser:

NON devo rifare login.

Se chiudo e riapro la tab:

la sessione deve rimanere valida finché non scade o finché non faccio logout.

---

# 4. AUTH GATE

Crea:

```text
frontend/src/features/auth/
```

con almeno:

```text
AuthGate.tsx
SpidTestLogin.tsx
AuthContext.tsx
useAuth.ts
types.ts
```

NON mettere la logica auth dentro `TriagePage`.

`AuthGate` deve:

1. chiamare all'avvio:

```text
GET /api/v1/auth/session
```

2. se la sessione è valida:
   - caricare il profilo;
   - renderizzare l'app.

3. se non è valida:
   - mostrare la schermata SPID TEST.

Non mostrare per mezzo secondo la HomePage prima del login.

Serve uno stato iniziale:

`AUTH_LOADING`

con uno Skeleton semplice.

---

# 5. PERSISTENZA SESSIONE

NON salvare codice fiscale, dati sanitari o intero profilo in `localStorage`.

Per il test usa una sessione backend.

Implementare:

```text
backend/app/features/auth/
```

con:

```text
models.py
schemas.py
service.py
router.py
providers.py
```

Creare una sessione random usando Python stdlib:

`secrets.token_urlsafe(...)`

Persistenza:

SQLite.

Cookie:

`HttpOnly`

`SameSite=Lax`

Nome suggerito:

`healthpulse_test_session`

Scadenza demo:

8 ore.

Il browser mantiene il login.

Il backend mantiene:

```text
session_id
fiscal_code
created_at
expires_at
last_seen_at
provider
synthetic
```

Il client NON sceglie autonomamente `fiscal_code` dopo la login.

Una volta autenticato, l'identità corrente viene sempre ricavata dalla sessione server.

Endpoint:

```text
POST /api/v1/auth/test-spid/login
GET  /api/v1/auth/session
POST /api/v1/auth/logout
```

Contratti da scrivere PRIMA in `STATE.md`.

Esempio:

```json
POST /api/v1/auth/test-spid/login

{
  "username": "..."
}
```

Risposta:

```json
{
  "authenticated": true,
  "provider": "spid_test_mock",
  "synthetic": true,
  "profile": {
    "spidCode": "...",
    "name": "...",
    "familyName": "...",
    "fiscalNumber": "...",
    "dateOfBirth": "...",
    "placeOfBirth": "...",
    "countyOfBirth": "...",
    "gender": "...",
    "email": "...",
    "mobilePhone": "..."
  },
  "expires_at": "..."
}
```

MAI mandare password nella response.

---

# 6. SPID TEST: NON FINGERE SAML

Vogliamo avere anche:

`spid-testenv2`

ma attenzione.

`spid-testenv2` è un Identity Provider.

HealthPulse deve essere un Service Provider SPID per completare davvero SAML.

Nel repo corrente NON esiste un middleware SPID/SAML.

Quindi:

## Vietato

NON implementare SAML2 a mano.

NON creare XML SAML artigianale.

NON dichiarare:

"SPID end-to-end funzionante"

se HealthPulse non è realmente configurato come Service Provider.

## Architettura

Implementare interfaccia:

```python
IdentityProvider
```

con almeno:

```text
MockIdentityProvider
SpidTestEnvProvider
```

`MockIdentityProvider`

è P0 ed è SEMPRE funzionante.

Usa gli stessi 15 profili sintetici.

`SpidTestEnvProvider`

è P1.

Può essere dichiarato operativo soltanto se viene effettivamente collegato a un Service Provider verificato.

---

# 7. AMBIENTE SPID DOCKER

L'obiettivo rimane avere:

```text
spid/
```

con ambiente `italia/spid-testenv2`.

ATTENZIONE:

AGENTS.md vieta nuovi pattern/cartelle top-level senza accordo.

Quindi prima registra in `STATE.md` la richiesta:

```text
Controlled exception: top-level spid/ required for isolated SPID test environment.
```

e segui il protocollo del repository.

Quando autorizzato:

```text
spid/
  docker-compose.yml
  README.md
  conf/
```

Con:

- `config.yaml`;
- certificato test;
- chiave test;
- metadata SP;
- utenti test.

Chiavi e certificati sono esclusivamente DEMO.

---

# 8. FORMATO UTENTI SPID

NON inventarlo.

Procedura obbligatoria:

1. avvia `spid-testenv2`;
2. crea un utente manualmente tramite `/add-user`;
3. identifica il file scritto dal container;
4. leggi lo schema effettivo;
5. documentalo;
6. solo dopo genera gli altri utenti.

Se non riesci:

scrivi:

`UNVERIFIED`

e NON creare un file users inventato.

---

# 9. 15 PAZIENTI SINTETICI

Implementare:

```text
scripts/gen_synthetic_patients.py
```

Python stdlib.

Seed default:

`577156`

CLI riproducibile.

Genera esattamente:

15 pazienti.

Gli stessi pazienti devono alimentare:

```text
SPID TEST
↓
MockIdentityProvider
↓
profilo sanitario
↓
pre-accettazione
↓
Arrival Commitment
```

Chiave di join:

`fiscal_code`

---

# 10. CODICE FISCALE

Ogni CF deve essere formalmente valido.

Implementare realmente:

- consonanti/vocali cognome;
- consonanti/vocali nome;
- anno;
- mese;
- giorno;
- +40 sesso femminile;
- codice catastale comune;
- carattere di controllo.

Non usare un generatore random di 16 caratteri.

Aggiungere validatore indipendente del checksum.

Tutti i profili:

```json
"synthetic": true
```

---

# 11. DATI PAZIENTI

Generare:

```text
data/preadmission/profiles.mock.csv
data/preadmission/exemptions.mock.csv
data/preadmission/clinical.mock.csv
data/preadmission/episodes.mock.csv
data/preadmission/profiles.mock.json
```

Il JSON DEVE derivare nella stessa esecuzione dagli stessi oggetti Python dei CSV.

Non mantenere due generatori differenti.

---

# 12. PROFILI INCOMPLETI

Assicurarsi di avere almeno:

### caso semplice

nessuna esenzione  
nessuna patologia cronica.

### missing GP

medico curante ASSENTE.

Non:

```text
gp_first_name=""
```

ma dato realmente assente/null nella rappresentazione che lo consente.

### missing contact

nessun contatto di emergenza  
nessuna email.

### minorenne

deve avere:

genitore/tutore.

La UI deve visualizzare:

`UNAVAILABLE`

quando il dato manca.

NON:

riga vuota.

NON:

placeholder inventato.

---

# 13. CARE INTENT

A ogni paziente associare un:

`demo_care_intent`

tra:

```text
minor_wound_care
prescription_renewal
vaccination
specimen_collection
specialist_referral
chronic_followup
pediatric_non_urgent
musculoskeletal_minor
medication_advice
```

Tutti devono comparire almeno una volta.

Aggiungere un caso in cui nessuna capability documentata soddisfi l'intent.

Risultato corretto:

`NO DOCUMENTED CAPABILITY MATCH`

NON raccomandare una struttura casualmente.

---

# 14. IMPORTANTE: NON RISCRIVERE SUBITO IL TRIAGE ESISTENTE

Il branch attuale possiede già un flusso funzionante:

```text
triage/messages
triage/plan
```

Non distruggerlo durante l'hackathon.

Il nuovo:

```text
CareIntent
CapabilityGraph
Navigator
```

deve essere ADDITIVO.

Se il kernel/taxonomy di Matteo è disponibile su main, riusalo.

Altrimenti implementa la minima integrazione necessaria senza duplicare cinque tassonomie diverse.

Non cambiare `TriageCode` solo per uniformare i nomi.

---

# 15. CITIZEN NAVIGATOR

Pipeline ideale:

```text
testo cittadino
       ↓
safety rules esistenti
       ↓
assessment corrente
       ↓
CareIntent
       ↓
required capabilities
       ↓
capability graph documentato
       ↓
facility candidate
       ↓
distanza / travel
       ↓
congestione
       ↓
network inbound
       ↓
recommendation
```

L'LLM:

- può interpretare;
- può spiegare.

L'LLM:

- NON inventa capability;
- NON inventa strutture;
- NON decide autonomamente sicurezza;
- NON inventa carico.

---

# 16. PRE-ACCETTAZIONE: QUANDO DEVE COMPARIRE

Una volta ottenuto il piano e selezionata la struttura:

oggi `TriagePage` mostra:

- mappa;
- RouteSummary;
- consiglio;
- alternative.

Aggiungere DOPO questa fase:

```text
Confermo che mi sto dirigendo qui
```

NON creare automaticamente la pre-accettazione.

Serve azione esplicita dell'utente.

---

# 17. ARRIVAL COMMITMENT

Quando il cittadino conferma:

creare un record operativo distinto dalla pre-accettazione.

Endpoint consigliato:

```text
POST /api/v1/arrivals/commitments
```

NON accettare dal client un codice fiscale arbitrario.

Derivarlo dalla sessione autenticata.

Input:

```json
{
  "facility_id": 12,
  "eta_minutes": 18,
  "care_intent": "musculoskeletal_minor",
  "consents": {
    "share_arrival": true,
    "share_preadmission": true,
    "share_reason": true
  }
}
```

Backend aggiunge:

```text
commitment_id
fiscal_code / internal patient reference
created_at
expected_arrival_at
status
synthetic
```

Stati:

```text
CONFIRMED
EN_ROUTE
ARRIVED
CANCELLED
EXPIRED
```

Il commitment DEVE essere revocabile.

NESSUNA sanzione.

NESSUNA penalità.

NESSUN flag punitivo per no-show.

---

# 18. RELIABILITY DEL COMMITMENT

Per il forecast ospedaliero non considerare necessariamente:

1 commitment = 1 arrivo certo.

Preparare il modello:

```text
commitment_weight
```

Esempio demo:

```text
CONFIRMED = 0.75
EN_ROUTE  = 0.90
ARRIVED   = 1.00
CANCELLED = 0
EXPIRED   = 0
```

Questi valori sono:

`SIMULATED / CONFIGURED`

NON statisticamente validati.

Devono stare in configurazione/versione formula.

---

# 19. PREADMISSION

Dopo il commitment:

utente può creare una pre-accettazione.

Provider:

```text
MockIdentityProvider
MockRecordProvider
PatientInputProvider
```

Identity deriva dalla sessione SPID TEST.

Clinical context deriva dai CSV sintetici.

Input manuale copre:

- contacts;
- consents;
- administrative additions.

`triage_hint`:

SEMPRE `null`.

HealthPulse NON pre-assegna il triage ospedaliero.

---

# 20. PRINCIPIO CLINICO

TUTTI i pazienti che vengono indirizzati a un ospedale entrano tramite:

# PRONTO SOCCORSO

HealthPulse può classificare:

```text
minor trauma
respiratory
chest-pain-like
abdominal
neurological
other
```

ma è:

`AI CARE CLUSTER`

NON:

diagnosi.

NON:

assegnazione reparto.

NON:

triage definitivo.

---

# 21. PREPAREDNESS AREA

Il care cluster può alimentare solamente la preparedness.

Esempio:

```text
MINOR_TRAUMA
→ PS
→ possibile aumento necessità supporto ortopedico/radiologico

CHEST_PAIN_CARDIO
→ PS
→ possibile necessità supporto cardiologico

ABDOMINAL
→ PS
→ possibile supporto chirurgico
```

La console può mostrare:

```text
EXPECTED CARE MIX
```

ma non:

```text
PAZIENTE X ASSEGNATO A CARDIOLOGIA
```

prima del triage reale.

---

# 22. TOKEN PRE-ACCETTAZIONE

Implementare token:

```text
issued
accepted
expired
```

Monouso.

Scadenza breve.

Endpoint:

```text
POST /api/v1/navigation/preadmission
GET  /api/v1/admission/resolve/{code}
POST /api/v1/admission/{code}/accept
```

Prima scrivere contratto completo in `STATE.md`.

---

# 23. QR

QR/pre-accept token per MVP.

Se creare un QR vero richiede dipendenza non approvata:

NON aggiungere package.

Preferire:

- codice testuale;
- SVG generato senza dipendenza;
- oppure componente client minimal.

La demo non deve bloccarsi sul QR.

---

# 24. HOSPITAL OPERATIONS CONSOLE

La pagina:

`/operatore`

esiste già:

```text
frontend/src/features/operatore/OperatorePage.tsx
```

ed è volutamente vuota.

Questa è la superficie giusta.

Non creare `/hospital-console-v2` o duplicati.

Costruire una console con:

```text
Overview
Arrivi previsti
Pressione PS
Care mix
Copertura
```

---

# 25. AUTH OPERATORE

NON usare l'identità SPID del cittadino come identità del personale ospedaliero.

Sono domini diversi.

Per MVP:

```text
HospitalMockAuthProvider
```

con account demo legati a:

`facility_id`

Ruoli:

```text
HOSPITAL_ADMIN
PS_COORDINATOR
DEPARTMENT_LEAD
OPERATOR_READONLY
```

La schermata iniziale SPID è il percorso cittadino predefinito.

Deve essere disponibile un ingresso secondario:

`Accesso struttura`

che usa l'auth operatore mock.

Sessioni distinte semanticamente.

---

# 26. ARRIVI PREVISTI NELLA CONSOLE

La console ospedaliera deve leggere:

`ArrivalCommitment`

aggregando:

### prossimi 30 minuti

### prossimi 60 minuti

### prossime 4 ore

Visualizzare:

```text
HealthPulse confirmed inbound
Expected external demand
Expected care mix
```

Non mostrare automaticamente dati sanitari nominativi.

Dashboard di default:

aggregata.

---

# 27. COLLECTIVE ROUTING

Gli Arrival Commitments devono alimentare il routing.

Esempio:

```text
Umberto I

current load
+
historical/external state
+
HealthPulse confirmed inbound
=
network state
```

Se HealthPulse ha già consigliato troppe persone verso una struttura:

il ranking dei successivi utenti deve poterla penalizzare.

NON utilizzare reinforcement learning.

Formula deterministica e versionata.

---

# 28. FACILITY LOADS: RIUTILIZZARE L'ESISTENTE

Esiste già:

`FacilityLoad`

NON creare:

`HospitalPressureV2`

con gli stessi dati duplicati.

La console operatori deve riutilizzare la stessa fonte che il routing cittadino già legge.

Se serve permettere all'operatore di aggiornare il carico:

aggiungere endpoint di scrittura nella feature `congestion`.

Contratto prima in `STATE.md`.

Esempio:

```text
PUT /api/v1/congestion/{facility_id}
```

con:

```text
waiting_red
waiting_yellow
waiting_green
waiting_white
waiting_unassigned
in_treatment
in_observation
observed_at
```

Al salvataggio:

```text
source = declared
```

o equivalente stabilito nel contratto.

L'intera app deve vedere immediatamente il nuovo valore.

---

# 29. DATA PROVENANCE

NON perdere il vantaggio del branch dati-reali.

Ogni dato visualizzato deve distinguere:

```text
OBSERVED
HISTORICAL
OFFICIAL_FORECAST
DERIVED
SIMULATED
UNAVAILABLE
UNVERIFIED
```

In particolare:

snapshot PS 2021:

`HISTORICAL`

NON LIVE.

Arrival Commitments:

`DERIVED / INTERNAL`

Turni mock:

`SIMULATED HR`

Profili SPID:

`SYNTHETIC / TEST`

---

# 30. COPERTURA TURNI

Implementare il modulo previsto da Matteo come layer della console.

Dataset:

```text
data/staffing/internal_shifts.mock.json
```

Per la versione da repository usare identificativi anonimi:

```text
MED-07
INF-12
INF-04
```

Campi:

```text
id
qualification
operational_area
status
last_shift_end
hours_since_last_shift
weekly_hours
on_call
synthetic
```

Stati:

```text
IN_TURNO
REPERIBILE
RIPOSO
```

---

# 31. STAFFING NON DECIDE

HealthPulse:

- misura;
- segnala;
- propone.

Responsabile umano:

- approva;
- rifiuta.

MAI:

chiamata automatica.

MAI:

assegnazione automatica.

Pulsante:

`Rivedi e approva`

NON:

`Attiva automaticamente`.

---

# 32. CARE MIX → READINESS

Usare gli Arrival Commitments per ottenere:

```text
Minor trauma       7
Respiratory        5
Abdominal          3
Chest-pain-like    2
Other              4
```

Da qui produrre:

```text
Triage          HIGH PRESSURE
Medicina PS     MODERATE
Radiologia      HIGH
Ortopedia       MODERATE
OBI             LOW
```

Questa è preparedness.

Non è allocation clinica.

---

# 33. SURGE

Implementare:

`surge_deficit.v1`

solo come formula DERIVED.

Input:

```text
pressure level
expected inbound
care mix
staff on shift
reference staffing parameters
```

Output:

```text
qualification
additional_shifts_suggested
reason
```

Non mostrare:

`85% predicted`

se non esiste un modello validato.

Preferire categorie:

```text
LOW
MODERATE
HIGH
VERY_HIGH
```

---

# 34. VINCOLI HR

Nel mock:

minimum rest = 11h

weekly threshold = configurato

ma visualizzare:

`SIMULATED HR POLICY`

Non presentare i parametri come verifica normativa completa.

Candidati incompatibili vanno SCARTATI.

Conservare sempre:

`exclusion_reason`.

Esempio:

```text
MED-03
EXCLUDED
Riposo minimo non rispettato
```

---

# 35. IDP SPID TEST E PROFILI DEVONO ESSERE GLI STESSI

Questo è un test fondamentale.

Dato:

```text
SPID fiscalNumber
```

deve corrispondere esattamente a:

```text
profiles.mock.csv fiscal_code
```

e al record aggregato:

```text
profiles.mock.json
```

Quando un utente effettua login:

```text
session
↓
fiscalNumber
↓
MockRecordProvider
↓
profilo sanitario corretto
```

NON selezionare il profilo per nome.

---

# 36. SPID LOGIN DEMO — UX

Schermata iniziale:

# Accedi a HealthPulse

Testo:

`Per questa demo vengono utilizzate esclusivamente identità sintetiche.`

Pulsante principale:

`Entra con SPID — ambiente di test`

Badge:

`DEMO`

Link secondario:

`Accesso struttura`

Dopo login:

TopBar deve poter mostrare in modo discreto:

```text
Mario Rossi
SPID TEST
```

e:

`Esci`

Non è necessario mostrare il codice fiscale completo nella top bar.

---

# 37. SESSION RESTORE

Test obbligatorio:

1. login;
2. entro in `/paziente`;
3. refresh browser;
4. rimango autenticato;
5. torno su `/`;
6. rimango autenticato;
7. logout;
8. session endpoint restituisce 401;
9. torno alla schermata login.

Il semplice fatto che `healthpulse-role` sia presente in localStorage NON conta come autenticazione.

---

# 38. HERO PATIENTS

Tra i 15 profili, congelare almeno quattro identità facilmente utilizzabili in demo.

### HERO A

adulto

profilo completo

`minor_wound_care`

### HERO B

adulto

GP mancante

`musculoskeletal_minor`

### HERO C

minorenne

tutore presente

`pediatric_non_urgent`

### HERO D

intent senza capability documentata

deve produrre:

`NO DOCUMENTED CAPABILITY MATCH`

Le credenziali demo devono essere documentate nel README dedicato.

---

# 39. PRE-ACCETTAZIONE E SESSIONE

L'utente NON deve scegliere:

`profile_id`

da una dropdown dopo aver fatto login.

È autenticato.

Quindi:

```text
session.fiscal_code
↓
profile
```

automaticamente.

Questo è essenziale per dimostrare la futura integrazione SPID/FSE.

---

# 40. PRIVACY DEMO

Tutti i dati:

`synthetic = true`

Nessuna persona reale.

Non effettuare chiamate verso sistemi esterni usando i codici fiscali sintetici.

Non usare i CF test per interrogare:

- FSE;
- IO;
- servizi Regione;
- anagrafi;
- API pubbliche di cittadini.

Sono esclusivamente fixture locali.

---

# 41. IO E FSE

NON integrarli realmente in questo task.

Preparare soltanto interfacce/adapter futuri.

Esempio:

```text
IdentityProvider
ClinicalRecordProvider
CitizenNotificationProvider
```

Implementazioni attuali:

```text
MockIdentityProvider
MockRecordProvider
MockNotificationProvider
```

In futuro:

```text
SPID/CIE
FSE 2.0
IO / infrastruttura istituzionale
```

Non attribuire a IO funzioni di GPS tracking.

---

# 42. NESSUNA PUNIZIONE NO-SHOW

Nel modello:

```text
NO_SHOW
```

serve eventualmente per calibrare l'affidabilità aggregata dei commitment.

NON:

- penalizzare il cittadino;
- blacklist;
- punteggio reputazionale;
- sanzione;
- segnalazione automatica.

---

# 43. FILE GLOBALI

Sono sotto lock:

```text
backend/app/main.py
frontend/src/routes.tsx
frontend/package.json
frontend/tailwind.config.ts
frontend/src/styles/theme.css
backend/pyproject.toml
lockfiles
```

NON modificarli direttamente.

Per ogni router/rotta richiesta:

scrivi in `STATE.md` esattamente la riga che l'Orchestratore deve aggiungere.

Per l'auth entry gate probabilmente servirà anche una modifica minima a:

`frontend/src/App.tsx`

Dato che è un punto condiviso, NON cambiarlo silenziosamente.

Registra prima la necessità e mantieni il diff minimo:

concettualmente:

```tsx
<AuthGate>
  <AppShell>...</AppShell>
</AuthGate>
```

o struttura equivalente.

---

# 44. COMPONENTI ESISTENTI REALMENTE PRESENTI

Riutilizzare quando opportuno:

```text
Badge
StatTile
NoDataNotice
EmptyState
Skeleton
FacilityCard
PageHeader
ErrorState
```

ATTENZIONE:

sul branch auditato `DataStatusPill.tsx` NON è presente.

NON scrivere codice assumendo che esista.

Verifica sempre il filesystem corrente.

---

# 45. NON RIPORTARE IN VITA COMPONENTI RIMOSSI

Sul branch dati-reali risultavano rimossi:

```text
DataStatusPill
NavRail
TabBar
```

Non recuperarli da commit vecchi solamente perché un prompt precedente li nomina.

Adatta la nuova UI alla struttura corrente.

---

# 46. API CLIENT

Esiste:

`frontend/src/api/client.ts`

Riutilizzarlo.

Non introdurre Axios.

Non duplicare client HTTP.

La demo Vite usa già:

`/api → backend :8000`

Il cookie HttpOnly same-origin deve funzionare attraverso questo flusso.

Se serve una modifica al client HTTP, farla minima e motivata.

---

# 47. NESSUNA NUOVA DIPENDENZA PER L'AUTH MOCK

Python dispone già di:

```text
secrets
datetime
csv
json
hashlib
hmac
```

Non serve installare un sistema auth esterno per la modalità mock.

Se per SPID SAML vero serve una dipendenza:

NON installarla autonomamente.

Dependency Request in `STATE.md`.

---

# 48. TEST BACKEND

Non dare per scontato `pytest`: attualmente non è nella baseline dichiarata.

Se non è disponibile, usare `unittest` della stdlib per:

- generatore CF;
- determinismo;
- join;
- incomplete profiles;
- session expiry;
- session restore;
- commitment;
- preadmission token;
- no-show behavior.

Non aggiungere pytest soltanto per questi test.

---

# 49. TEST GENERATORE

Obbligatori:

- 15 profili esatti;
- stesso seed → byte-identical;
- checksum CF indipendente;
- foreign key logiche valide;
- episodi non futuri;
- episodi successivi alla nascita;
- tutti CareIntent coperti;
- missing field realmente assenti;
- minorenne con tutore;
- `synthetic=true` ovunque.

---

# 50. TEST AUTH

Obbligatori:

```text
login valido
login sconosciuto
sessione valida
sessione scaduta
logout
cookie cancellato
profile join via fiscal_code
```

---

# 51. TEST CLOSED LOOP

Preparare almeno un test/demo end-to-end:

```text
LOGIN SPID TEST
↓
utente sintetico HERO A
↓
triage/navigator
↓
struttura consigliata
↓
utente conferma destinazione
↓
Arrival Commitment creato
↓
apri /operatore
↓
l'inbound della stessa struttura aumenta
↓
care mix cambia
↓
readiness viene ricalcolata
```

Questo è il percorso più importante dell'intera implementazione.

---

# 52. NON CAMBIARE IL SIGNIFICATO DEL TRIAGE

Nel progetto corrente il triage esiste già.

Per la nuova pre-accettazione:

`triage_hint = null`

se questo è il contratto della nuova feature.

Non riutilizzare automaticamente:

`assessment.code`

come triage ospedaliero definitivo.

Il codice prodotto dall'app e il triage effettuato realmente dal PS devono rimanere semanticamente separati nella nuova architettura.

---

# 53. REAL / MOCK / DERIVED

Ogni schermata deve permettere di capire:

### REAL / HISTORICAL

dataset PS Lazio 2021.

### REAL STRUCTURAL

facilities Open Data.

### SYNTHETIC

pazienti test.

### MOCK

operator users / staffing.

### DERIVED

ranking, commitment-weighted inbound, readiness.

### SIMULATED

surge scenarios.

Non mischiarli.

---

# 54. ORDINE DI IMPLEMENTAZIONE

Segui questo ordine.

## PHASE 1 — PRE-FLIGHT

Audit.

Contratti STATE.

Task ownership.

## PHASE 2 — SYNTHETIC IDENTITY DATA

Generatore 15 pazienti.

CSV + JSON.

Test determinismo e CF.

## PHASE 3 — AUTH

MockIdentityProvider.

Auth session SQLite.

AuthGate frontend.

Persistent login.

Logout.

## PHASE 4 — SPID TESTENV

Docker.

Un utente manuale.

Formato users verificato.

15 identità.

Non dichiarare SAML E2E senza vero SP.

## PHASE 5 — PREADMISSION DATA

MockRecordProvider.

Composizione profilo.

Missing-data handling.

## PHASE 6 — ARRIVAL COMMITMENT

Conferma struttura.

Persistenza.

ETA.

Status.

## PHASE 7 — CLOSED LOOP

Commitment → `/operatore`.

Inbound 30/60/240.

Care mix.

## PHASE 8 — STAFFING

Turni mock.

Eligibility.

Deficit.

Human approval.

## PHASE 9 — HARDENING

Build.

Lint.

Backend checks.

Demo test.

---

# 55. PRIORITÀ SE MANCA TEMPO

P0 assoluto:

```text
15 profili sintetici
SPID-style test login
sessione persistente
MockIdentityProvider
pre-accettazione
Arrival Commitment
Hospital inbound
closed-loop demo
```

P1:

```text
spid-testenv2 Docker
staffing completo
collective routing
```

P2:

```text
vero SAML SPID E2E
integrazioni FSE/IO
```

NON sacrificare il closed loop per combattere con SAML.

---

# 56. MOMENTO WOW DELLA DEMO

Deve funzionare questo:

### FINESTRA 1 — CITTADINO

Entra con:

`SPID TEST`

Profilo:

utente sintetico.

Descrive problema.

HealthPulse propone struttura.

Cittadino preme:

`Confermo che mi sto dirigendo qui`

HealthPulse mostra:

```text
Pre-accettazione pronta
ETA 18 min
```

### FINESTRA 2 — OSPEDALE

Apri `/operatore`.

Compare:

```text
HealthPulse inbound +1
```

Aggiornamento:

```text
NEXT 60 MIN
17 → 18
```

Care mix:

```text
Minor trauma
7 → 8
```

Se questo cambia la readiness:

mostrare la variazione.

Questo dimostra concretamente:

# HealthPulse è bidirezionale.

---

# 57. DEFINITION OF DONE

Il task NON è finito finché non funzionano tutti i P0:

- branch corretto;
- dati reali esistenti preservati;
- 15 profili sintetici;
- CF formalmente validi;
- dati incompleti testabili;
- login cittadino;
- session persistence;
- logout;
- SPID attributes 1:1 nel MockIdentityProvider;
- routing corrente non rotto;
- conferma della destinazione;
- Arrival Commitment;
- pre-accettazione;
- console ospedale;
- inbound aggregato;
- care mix aggregato;
- nessun routing diretto al reparto;
- tutti entrano dal PS;
- synthetic/derived/history chiaramente distinti;
- build frontend verde;
- controlli backend verdi;
- `check_compliance.sh` verde.

---

# 58. REPORT FINALE OBBLIGATORIO

Alla fine NON limitarti a dire "fatto".

Riporta esattamente:

```text
BRANCH
HEAD
COMMITS CREATI

FILE AGGIUNTI
FILE MODIFICATI

PROFILI GENERATI
PROFILI INCOMPLETI
CARE INTENT COPERTI

AUTH
session persistence: PASS/FAIL
logout: PASS/FAIL

SPID TESTENV
container: PASS/FAIL
users format verified: YES/NO
actual SAML E2E: PASS/FAIL/NOT IMPLEMENTED

PREADMISSION
composition: PASS/FAIL
token: PASS/FAIL

ARRIVAL COMMITMENT
create: PASS/FAIL
cancel: PASS/FAIL
hospital inbound update: PASS/FAIL

OPERATOR CONSOLE
30m inbound: PASS/FAIL
60m inbound: PASS/FAIL
care mix: PASS/FAIL
staff readiness: PASS/FAIL

EXISTING TRIAGE
messages: PASS/FAIL
plan: PASS/FAIL
map: PASS/FAIL

BUILD
frontend lint
frontend typecheck
frontend build
backend ruff
compliance

LIMITAZIONI REALI
```

Non nascondere FAIL.

---

# 59. PRINCIPIO FINALE

L'obiettivo non è creare "un login SPID finto".

L'obiettivo è dimostrare questa architettura:

```text
IDENTITÀ
      ↓
CONTESTO CITTADINO
      ↓
AI NAVIGATION
      ↓
STRUTTURA RACCOMANDATA
      ↓
ARRIVAL COMMITMENT
      ↓
PRE-ACCETTAZIONE
      ↓
HOSPITAL INBOUND
      ↓
RESOURCE READINESS
```

Il tutto preservando la pipeline Open Data reale che esiste già sul branch `feat/dati-reali`.

HealthPulse deve arrivare alla demo come:

# Predictive Healthcare Orchestration

e non semplicemente come symptom checker.