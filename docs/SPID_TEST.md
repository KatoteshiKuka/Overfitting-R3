# Accesso con identità di test

## Cosa è implementato, e cosa no

**Implementato e funzionante (P0)** — `MockIdentityProvider`:

- 15 identità sintetiche con attributi SPID (`spidCode`, `name`, `familyName`,
  `fiscalNumber`, `dateOfBirth`, `placeOfBirth`, `countyOfBirth`, `gender`, `email`,
  `mobilePhone`), gli stessi nomi che usa lo standard;
- sessione lato server con cookie `HttpOnly`, durata 8 ore, logout;
- il profilo sanitario viene unito **sempre per codice fiscale**, mai per nome.

**NON implementato** — SAML vero con `spid-testenv2`:

`spid-testenv2` è un **Identity Provider**. Per completare uno scambio SAML reale
HealthPulse dovrebbe essere registrato come **Service Provider**, con metadata, certificati
e un middleware SAML. Nel repository non esiste nulla di tutto questo.

Scrivere qui uno scambio SAML artigianale darebbe l'impressione di un'integrazione
funzionante che non c'è. Quindi `SpidTestEnvProvider` esiste come interfaccia ma solleva
`NotImplementedError`, e lo stato dichiarato è:

```
SPID SAML end-to-end: NOT IMPLEMENTED
formato utenti spid-testenv2: UNVERIFIED
```

Il formato del file utenti di `spid-testenv2` **non è stato verificato**: la procedura
corretta (avviare il container, creare un utente da `/add-user`, leggere il file scritto
dal container e documentarne lo schema effettivo) non è stata eseguita. Inventare quel
formato sarebbe peggio che ammettere di non averlo.

## Perché l'architettura regge lo stesso

Il resto dell'applicazione non sa da dove arriva l'identità: conosce solo l'interfaccia
`IdentityProvider` in `backend/app/features/auth/providers.py`. Sostituire il mock con
SPID o CIE veri significa aggiungere una classe, non riscrivere sessione, profilo,
pre-accettazione o console.

Lo stesso vale per gli altri confini verso l'esterno, dichiarati ma non integrati:

| Interfaccia | Oggi | Domani |
|---|---|---|
| `IdentityProvider` | `MockIdentityProvider` | SPID / CIE |
| Record clinico (`features/citizens/records.py`) | profili sintetici | FSE 2.0 |
| Notifiche al cittadino | non implementate | infrastruttura istituzionale |

I codici fiscali sintetici sono **fixture locali**: formalmente validi, ma non
appartengono a nessuno e non vanno usati per interrogare FSE, anagrafi o servizi regionali.

---

## Identità per la demo

Nessuna password. Si sceglie l'identità dalla schermata di accesso.

| Utente | Chi è | Intento | Particolarità |
|---|---|---|---|
| `mario.rossi` | **HERO A** | `minor_wound_care` | profilo completo |
| `giulia.bianchi` | **HERO B** | `musculoskeletal_minor` | **senza medico curante** |
| `giuseppe.ferrari` | **HERO C** | `pediatric_non_urgent` | **minorenne, con tutore** |
| `chiara.esposito` | **HERO D** | `specimen_collection` | **nessuna struttura documenta questa prestazione** |

Le altre undici identità sono elencate nella schermata sotto «Altre identità di test».
Fra loro ci sono due profili **senza contatti** (né email né contatto di emergenza) e uno
**senza esenzioni né patologie**, per provare i casi limite dell'interfaccia.

Dove un dato manca, l'interfaccia mostra `UNAVAILABLE`: nel JSON il campo è `null`, mai
una stringa vuota o un valore inventato.

## Accesso struttura

Dominio **separato**: il personale non usa l'identità SPID del cittadino.

| Account | Ruolo | Può dichiarare il carico |
|---|---|---|
| `hospital.admin` | `HOSPITAL_ADMIN` | sì |
| `ps.coordinator` | `PS_COORDINATOR` | sì |
| `reparto.lead` | `DEPARTMENT_LEAD` | no |
| `sola.lettura` | `OPERATOR_READONLY` | no |

Si sceglie anche la struttura: la console mostra solo quella.

## Rigenerare le identità

```bash
python3 scripts/gen_synthetic_patients.py            # seme 577156
python3 scripts/gen_synthetic_patients.py --check    # solo verifica
```

A parità di seme l'output è byte-identico. I controlli interni impediscono di generare un
insieme incoerente: quindici profili esatti, codici fiscali validi e unici, tutti gli
intenti coperti, un minorenne con tutore, i quattro HERO presenti, nessun episodio nel
futuro o precedente alla nascita.
