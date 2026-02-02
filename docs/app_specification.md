# Tech Spec: Beancount DK Generator Engine (Auto-Ledger)

## 1. Formål & Systemmål
Udvikling af en Python-applikation til generering af et dansk Beancount-regnskab. Systemet transformerer rå datakilder (CSV, bankdata og bilag) til BeanCount transaktioner, der overholder danske virksomhedsregler og momslovgivning.

## 2. Konfiguration & Kontoplaner (YAML)
Systemet anvender YAML-filer som "Single Source of Truth" for firmaets opsætning og kontostruktur.

### 2.1 Lagdelt Kontostruktur
1. **Standard Kontoplan (Base Layer):** - Prædefineret hierarki: `Assets`, `Liabilities`, `Equity`, `Income`, `Expenses`.
   - Standard-undergrupper: `Expenses:Loen`, `Expenses:MedMoms`, `Expenses:UdenMoms`.
2. **Virksomhedsspecifik Mapping (`accounts.yaml`):**
   - Mapper ekstern `Kontoid` (fra f.eks. bank-CSV eller lønsystem) til en specifik Beancount-sti.
   - Hver mapping definerer en `default_parent` for automatisk kategorisering.

### 2.2 Firma-stamdata (`config.yaml`) & Pris-matrix (`prices.csv`)
- **Stamdata (YAML):** Navn, CVR, regnskabsår (inkl. historiske ændringer) og momsperiode.
- **Pris-matrix (CSV):** Kundespecifikke priser styret af gyldighedsperioder.
  - Format: `<konto>;<fradato>;<pristype>;<enhed>;<pris>`
  - Eksempel: `MinGodeKunde;2024-01-01;Udvikling;Timer;1000`

## 3. Input-formater & Datakilder
Systemet skal kunne processere og validere følgende kilder:
- **Salgsinformation (CSV):** Kunde, dato, pris ex. moms, pris inkl. moms, kreditperiode.
- **Lønudbetalinger (CSV):** Ansat, dato, bruttoløn, A-skat, ATP.
- **Bankkontoudskrift (CSV):** Dato, beløb (med korrekt fortegn), kommentar og aktuel saldo.
- **Bilags-indbakke:** Billeder (JPG/PNG) og PDF-filer.
    - *Billedbehandling:* Automatisk rotation, optimering og formindskelse.
    - *Ekstraktion:* Tekst hentes via OCR eller Vision LLM (Gemini 3).

## 4. Automations-pipeline (The Matching Engine)
Workflowet kører iterativt indtil alle posteringer er dannede og dokumenterede.

### 4.1 Identifikation & Matching
1. **Bank til Konto:** LLM analyserer bank-kommentarer mod navne og ID'er i `accounts.yaml`.
2. **Bank til Bilag:** Fuzzy-match mellem banktransaktion og ekstraheret bilagstekst baseret på `[Dato, Beløb, Nøgleord]`.
3. **Draft Generation:** Hvis match findes, oprettes en postering i "Draft" tilstand. Hvis ikke, notificeres brugeren om manglende stamdata/mapping.

### 4.2 Skabeloner (Posting Templates)
- **Salg:** `Assets:Debitorer` (Debet) mod `Income:Salg` (Kredit) og `Liabilities:Moms:SalgMoms` (Kredit).
- **Løn:** `Expenses:Loen` (Debet) mod `Liabilities:SkyldigLoen`, `Skat:ASkat` og `Skat:ATP` (Kredit).
- **Køb:** `Expenses:[ValgtKonto]` (Debet) + `Assets:Moms:KoebMoms` (Debet) mod `Assets:Bank` (Kredit).

## 5. User Workflow: Review & Approval
Systemet kræver menneskelig validering før endelig bogføring:
1. **Inspektion:** Brugeren checker draft-posteringer i editoren (dato, type, konto, priser jf. matrix).
2. **Approval:** Ved godkendelse køres genereringen igen i "Approved" tilstand, og transaktionen skrives til hoved-ledgeren via `BeancountConnector`.

## 6. Periodisering & Rapportering
- **Moms-lukning:** Script-baseret nulstilling af drifts-moms mod `Liabilities:Moms:SkyldigMoms`.
- **Årsafslutning:** Overførsel af årets resultat og nulstilling af resultatopgørelse.

## 7. Tekniske Retningslinjer (Cursor/AI)
- **Arkitektur:** Brug `driver/connector.py` til fil-I/O og BQL-queries.
- **BQL Syntax:** Datoer skal altid omsluttes af enkelte citationstegn (`'2026-02-02'`).
- **Fortegn:** Følg Beancount-standard (Indtægter/Gæld = negative, Aktiver/Udgifter = positive).
- **Persistens:** YAML til stamdata og kontomapping, CSV til priser, .beancount til transaktioner.
