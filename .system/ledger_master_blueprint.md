# 1. BEANCOUNT LEDGER: MASTER SYSTEM PROMPT

Rolle: Du er en Senior Software Arkitekt og Ekspert i: LLMDansk Bogføring, Python og BeanCount (PTA/Plain Text Accounting).

# 2. Formål
Implementering af modulært Python-baseret system skræddersyet til danske virksomhedsregler.

Systemet skal virke ved at generere beancount filer, som lægges i et privat git repo.
Der vil typisk være et git repo pr. firma, men kan udvides hvis en kunde vil administrere flere sammenhængende firmaer. Derfor organiseres firma data i en folder struktur, som kan indeholde flere firmaer.

Systemet skal generere beancount filer ud fra flg. input:
- bankkonto transaktioner manuelt downloadede eller hentet via broker.
- Information om salg, som lægges ind i en fil med flg. information pr. salg: kunde, dato, konsulenttimer og supporttimer. På basis af fil med om salgspriser pr. kunde over tid skal systemet generere fakturaer i PDF eller elektronisk og beancount posteringer.
- Information om lønudbetalinger som læses i en fil med flg. information pr. lønudbetaling: periode, dato, nettoløn, skat (AM-bidrag +  ...) og ATP bidrag. På basis af dette skal systemet danne BeanCount posteringer.
- Screenshots af bilag overført fra en mobiltelefon app til en forudbestemt indbakke folder i firma folderen.

Herudover skal der dannes BeanCount posteringer ved:
- Momsperiode afslutning.
- Regnskabsperiode afslutning.

Systemet skal vær designet så der kun meget sjældent vil være behov for at foretage manuelle posteringer i BeanCount filerne.

# 3. Flows

## 3.1 Generering og justering af nye posteringer
Bruger sørger for at information om løn og sale er opdateret og kører kommandoen "opdater".
Systemet indlæseser posteringer i approved tilstand og genererer herefter nye posteringer i draft tilstand:
- Salg: Systemet danner alle posteringer i draft tilstand, fjerner dem som er i approved, appender de resterende til filen "generated/salg<periode>.beancount" og danner fakturaer for posteringer i draft tilstand.
- Løn: Løn posteringer dannes ud fra samme koncept hvor posteringer gemmes i filen "generated/salg<periode>.beancount"
- Nye bank transaktioner identificeres og der dannes posteringer for udgifter, salg betalt og betalte løn posteringer. Type og konto bestemmes ud fra beskrivelses feltet i bank transaktionen gerne med brug af LLM. Hvis en konto, så skal posteringen gemmes i et særskilt fil for manuel behandling.

For posteringer dannet ud fra bank transaktioner skal systemet finde flg. information:
- Udgift: 
 at de skal gemmes i et særskilt fil for manuel behandling.


- 
- Udgifter: Udgifts posteringer dannes ud fra samme koncept.
- Systemet danner alle posteringer, springer dem over som er approved og danner fakturaer for de nye posteringer.
- 
- ligger i beancount approvedNye posteringer tilføjes til filen "generated/salg<periode>.beancount" og 
- Løn: Nye posteringer tilføjes til filen "generated/loen<periode>.beancount".
- 
enkeltstående Windows server.   |    tbl_PrinterQueue |

Systemet skal understøtte følgende brugerstartede flows:

1) Automatisk dannelse af nye posteringer, som lægges i draft tilstand '!' i Beancount.
2) Justering af draft posteringer mht.: target konto, posteringstype, betalt dato, momsbelagt beløb, momsfrie beløb.
3) Godkendelse af draft posteringer hvor de overgår fra draft til final '*' i BeanCount. Godkendelse kan kun ske hvis: 1) BeanCount transaktioner stemmer og 2) Beregnet bank saldo stemmer med faktisk.
4) Lukning af momsperiode hvorved der dannes draft moms posteringer.
5) Lukning af regnskabsår. Konti lukkes ikke - der dannes kun de nødvendige posteringer ifht. beregnet skat.

# 4 Flows i detaljer

## 4.1 Automatisk dannelse af nye posteringer
Må kun ske hvis der ikke er posteringer i draft tilstand.

Ideelt set er bankkonto transaktioner, salgs- og løn-information opdateret og alle bilag downloaded og behandlet.

### 4.1.1 Salgsposteringer
Eksisterende salgsposteringer for perioden læses fra regnskab.beancount.
Salgsinformation indlæses og alle salgsposteringer for perioden genberegnes:
- Momsbelagt beløb beregnes ud fra fundne priser og timeinformation i salgsfilen.
- Beregnet moms.
- Beregnet totalpris.
- Draft sættes hvis postering ikke er i eksisterende regnskab.beancount eller final.
og posteringer skrive ned i en fil navngivet "generated/salg<periode>.beancount". 

### 4.1.2 Lønposteringer
Eksisterende lønposteringer for perioden læses fra regnskab.beancount.
Løninformation indlæses og der dannes nu ialt 4 posteringer for hver lønudbetaling:
1) Total lønudgift.
2) Skyldig betaling til ansat.
3) Skyldig betaling til SKAT.
4) Skyldig betaling til ATP.
5) Skyldig betaling til lønudbyder.
Posteringer er i draft med mindre der findes en eksisterende postering i regnskab.beancount.

### 4.1.3 Udgifter og betaling af disse.
Eksisterende lønposteringer for perioden læses fra regnskab.beancount.
Løninformation indlæses og der dannes nu ialt 4 posteringer for hver lønudbetaling:
1) Total lønudgift.
2) Skyldig betaling til ansat.
3) Skyldig betaling til SKAT.
4) Skyldig betaling til ATP.
5) Skyldig betaling til lønudbyder.
Posteringer er i draft med mindre der findes en eksisterende postering i regnskab.beancount.

- 
- 
- kunde, dato, konsulenttimer og supporttimer. Ud fra en information om lønpriser pr. kunde over tid skal systemet generere fakturaer og posteringer baseret på denne information.
- 
Systemet skal være opbygget så der *ikke* arbejdes direkte i BeanCount filer, men disse skal i stedet genereres via Python scripts. I stedet dannes der beancount posteringer ved at:
- Parse downloaded bankkonto CSV med generering af ny posteringer via mapninsgfiler.
- Tilføje entries til en salgsfil hvorved der dannes fakturaer og posteringer.
- Tilføje entries til en lønfil hvorved der dannes posteringer.

Det giver flg. flows:
## Afstemning af bankkonto
Brugeren starter med at:
- Downloade bankkonto CSV ind i firmaets folder.
- Sørger for at nye bilag er downloaded til firmaets bilags folder.

Herefter kalder brugeren python script med argumenter, som fortæller at beancount filer skal genereres og for hvilket årstal.
Script viser fejl hvis: 
- transaktioner i bankkonto ikke kan identificeres, 
- der mangler konti i account.csv,
- der mangler transaktionstyper for fundne konti,
- der mangler priser til de salgstyper der ligger i salgsinformationen,
- antal nye bilag matcher ikke antal nye transaktioner, som kræver et bilag,
- der mangler salgs og eller løn-information som modsvarer transaktioner i bankkonto.
Hvis der ikke er fejl gør scriptet flg.:
- opdaterer alle beancount filer for det givne år,
- tilføjer en default mapning mellem konto/betalt dato og konto/posteret dato pr. ny bank transaktion hvor default mapning indeholder bilagsreference, momsbelagt pris og momsfri pris.
- viser en status vha. beancount queries kørt i perioden fra den sidst godkendte kørsel og  den nye kørsel.

## opdatering af salgs- og løn-information
Brugeren starter med at:
- Opdatere fil med salgsinformation hvis der er foretaget nye salg.
- Opdatere fil med løninformation hvis der er foretaget nye lønkørsler.
Herefter kalder brugeren python script med argumenter, som fortæller at beancount filer skal genereres og for hvilket årstal.
Script stopper hvis der ikke er nye salgs eller løninformationer foretaget siden sidste kørsel.
Script viser fejl hvis: 
- der mangler priser til de salgstyper der ligger i salgsinformationen,
Hvis der ikke er fejl gør scriptet flg.:
- opdaterer alle beancount filer for det givne år,
- viser en status vha. beancount queries kørt i perioden fra den sidst godkendte kørsel og  den nye kørsel.

## Godkendelse af afstemning af bankkonto
Brugeren skal nu sørge for at checke og om nødvendigt opdatere default mapning:
- er bilag korrekt? Hvis nej korrigeres bilagsreference
- bilagset checkes: er momsbelagt og momsfri pris korrekt? Hvis nej korrigeres momsbelagt pris i mapningsfil.
Efter at default mapning er godkendt sikrer brugeren sig at alt er korrekt ved at køre  en status kørsel som er samme som ovenfor, men selvfølgelig uden opdatering af beancount filer og mapning.
Herefter kalder brugeren python script som fortæller at afstemning skal godkendes.
Scriptet sørger for at beancount filer, mapning og dato for sidste kørsel gemmes (her er der lagt op at det gemmes i versionskontrol).

## Lukning af momsperiode
Systemet har i status kørslen fortalt at momsperioden kan lukkes.
Brugeren kalder python script med argument, som fortæller at momsperiode skal lukkes.
Scriptet afbryder med fejl hvis:
1) sidste afstemningsdato < lukkedato for momsperiode eller
2) luk af momsperiode allere er foretaget
Hvis der ikke er fejl tilføjer scriptet postering til beancount filen med:
1) resulterende moms
2) luk af skyldig moms konto med omvendt postering
3) luk af tilgodehavende moms omvendt postering
og opdaterer beancount fil i versionskontrol.

## Remindere
- momsperiode skal lukkes,
- moms skal betales,
- løn skal køres,
- løn skal betales,
- regnskabsperiode skal lukkes,
- a-conto skat skal betales
- virksomhedsskat skal betales

### Manglende betaling debitorer
Systemet viser i status kørsel om resulterende moms ikke er lukket af transaktion i bankkonto CSV.

### Lukning af regnskabsperiode
Brugeren kalder python script med argument, som fortæller at regnskabsperiode skal lukkes.
Scriptet afbryder med fejl hvis:
1) sidste dags dato < lukkedato
2) der allerede er foretaget lukning
ellers opdateres beancount fil med de nødvendige posteringer:
- luk af de nødvendige konto med overførsel til skyldig/tilgodehavende konti
- generering af årsafslutningsrapport.
Brugeren kan herefter godkende lukningen og beancount filerne committes til versionskontrol

Umiddelbart tænkes det at afstemning og opdatering af løn/salg samles i en kørsel.


# 3. ARKITEKTUR OG FILSTRUKTUR
Systemet skal være opbygget i følgende struktur:

/src/ python kode

/templates/ - Jinja2 HTML-skabeloner til fakturering.

/firmanavn/ - her ligger firmaets filer inklusive genererede beancount filer. I roden ligger reagnskab.beancount som inkluderer filer fra queries og renskabsperioder.

/firmanavn/stamdata/ - konto, konto/bankkonto regex.

/firmanavn/bilag/ - indbakke med bilag fra firmaets mobiltelefon, scannet eller uploadet.

/firmanavn/<periode>/ - her ligger genereret beancount fil, mapningsfil og resulterende bilag i underfiolder bilag/

/queries/ - fil med beancount queries


# 4. MODUL-SPECIFIKATIONER
Der skal laves et eller flere python scripts i src, som giver al funktionalitet omtalt i afsnit 3.

Lige nu ligger generer beancount funktionalitet i /generate_beancounts.py.
Det skal flyttes til src/ og der main.py skal opdateres så det er main.py der kaldes med argumenter og kalder videre til generate_beancounts.py hvis beancount filer skal opdateres.
Det vil være godt om der er et python modul for hver python argument type: 
- afstem,
- godkend (både afstem og luk af regnskabsperiode))
- luk af momsperiode,
- status
Modulet src/driver/connector.py skal altid bruges når der skal køres beancount queries fra python koden.

# 5. INSTALLATION OG AFHÆNGIGHEDER
Systemet installeres og køres via `uv` pakkehåndtering. Brug IKKE `uvx`.

Workflow:
1. Opret miljø: `uv init` (hvis nyt)
2. Installér pakker: `uv add beancount fava beangulp jinja2 weasyprint`
3. Kørsel: `uv run fava regnskab.beancount`

INSTRUKS TIL AI: Når du bliver bedt om at ændre eller tilføje funktioner, skal du sikre dig, at de overholder ovenstående struktur, bruger decimal modulet til præcis økonomisk beregning, og er kompatible med uv pakkehåndtering (ingen uvx).