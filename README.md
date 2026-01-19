# Formål
Dansk regnskabsystem bygget på BeanCount og git.
Ideen er at lægge regnskabsdata i et private git repository, som på den måde udgør transaktionsporet.
Der arbejdes ikke direkte i BeanCount filer. Disse genereres i stedet fra flg.:
1. Bankkonto CSV fil (filer hvis firmaet har flere bankkonti).
1. Fil med salgsinformation.
1. Fil med løninformation.
1. Folder hvor bilag placeres ideelt set direkte fra en mobiltelefon app. 
1. Fil med konti, som refererer til firmaets kreditorer og debitorer. Hver række i filen indeholder: Kontonavn og kontoens kontogruppe eksempelvis "Accountant;Expenses:WithVat".
1. Fil som kan mappe mellem bankkonto transaktioner og firmaets konti.
1. Fil med priser, der refererer til priserne for timer og support. Der opereres pt. med time- og supportpriser i dato-intervaller, som kan overrides pr kundekonto.

I det daglige arbejder brugeren kun med bankkonto CSV filer, salgs- og løninformation og bilag som dannes med billede taget af mobiltelefon app.
Der kan være behov for at opdatere i konto og mapningsfil hvis der dukker en ukendt konto på i bankkonto CSV filen. 
Hvis firmaets salgspriser ændres skal dette tilføjes til pris filen.

# Flows

## Afstemning

### Identifikation af nye transaktioner
Brugeren opdaterer bankkonto CSV filen (og evt. salg og løn) og kører kommandoen "opdater".
Systemet gendanner nu samtlige BeanCount transaktioner ud fra:
- Bank transaktioner i CSV fil: target konto (eksempelvis "Accountant") findes ud fra beskrivelse, posteringstype findes ud fra target kontogruppe og beancount postering dannes ud fra et Jinja template fundet ud fra posteringstype.
- Salgs transaktioner i CSV fil: Time- oPriser target konto (eksempelvis "Accountant") findes ud fra beskrivelse, posteringstype findes ud fra target kontogruppe og beancount postering dannes ud fra et Jinja template fundet ud fra posteringstype.

finde target konto ud fra b
hvis der er ny 


bilag og 1-3 filer, men disse genererer 
Brugeren 

Herudover skal 


- 
men disse genereres via Python scripts.

Systemet er designet så bogføring kan ske så simpelt og hurtigt som muligt uden at skulle arbejde direkte i BeanCount filer. Det eneste brugeren skal gøre er at:
- Opdatere bankkonto CSV filer ved at hente dem fra banken og opdatere CSV filen i 
- Køre en 


modulært Python-baseret Beancount-økosystem skræddersyet til danske virksomhedsregler.
Systemet skal være opbygget så der *ikke* arbejdes direkte i BeanCount filer, men disse skal i stedet genereres via Python scripts. I stedet dannes der beancount posteringer ved at:
- Parse downloaded bankkonto CSV med generering af ny posteringer via mapninsgfiler.
- Tilføje entries til en salgsfil hvorved der dannes fakturaer og posteringer.
- Tilføje entries til en lønfil hvorved der dannes posteringer.
