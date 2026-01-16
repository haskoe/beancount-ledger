# Formål
Vedligeholdelse og generering af et modulært Python-baseret Beancount-økosystem skræddersyet til danske virksomhedsregler.
Systemet skal være opbygget så der *ikke* arbejdes direkte i BeanCount filer, men disse skal i stedet genereres via Python scripts. I stedet dannes der beancount posteringer ved at:
- Parse downloaded bankkonto CSV med generering af ny posteringer via mapninsgfiler.
- Tilføje entries til en salgsfil hvorved der dannes fakturaer og posteringer.
- Tilføje entries til en lønfil hvorved der dannes posteringer.
