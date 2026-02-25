import pandas as pd
import numpy as np

DATE = 'date'
AMOUNT = 'amount'
TOTAL = 'total'
DESVC = 'description'

def transform_bank_csv(input_file, output_file):
    # 1. Læs CSV-filen ind. Da vi ikke har headers, lader vi pandas give dem tal-navne (0, 1, 2...)
    # Vi læser alt som tekst (str) først, så vi selv har fuld kontrol over formateringen.
    df = pd.read_csv(input_file, header=None, dtype=str, sep=";", engine='python')
    
    date_cols = []
    numeric_cols = []
    text_cols = []
    
    # 2. Heuristik: Analyser hver kolonne for at finde dens type
    for col in df.columns:
        # Fjerner NaN/tomme felter i vores test
        sample = df[col].dropna()
        if sample.empty:
            continue
            
        # Forsøg at parse som datoer. dayfirst=True er godt for danske/europæiske datoer
        parsed_dates = pd.to_datetime(sample, errors='coerce', dayfirst=True)
        # Hvis mere end 80% af kolonnen kan læses som en dato, antager vi det er datokolonnen
        if parsed_dates.notna().mean() > 0.99:
            date_cols.append(col)
            # Fyld kolonner med de parsede datoer i YYYYMMDD format
            df[col] = parsed_dates.dt.strftime('%d-%m-%Y')
            continue
            
        # Forsøg at parse som beløb. (Håndterer dansk format fx. 1.234,56 til 1234.56)
        # Vi fjerner evt. tusindetals-punktummer og erstatter decimalkomma med punktum
        cleaned_numbers = sample.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        parsed_numbers = pd.to_numeric(cleaned_numbers, errors='coerce')
        
        # Hvis mere end 80% kan læses som tal, antager vi det er en beløbskolonne
        if parsed_numbers.notna().mean() > 0.99:
            numeric_cols.append(col)
            # Anvend de rensede tal i kolonnen
            df[col] = parsed_numbers
            continue
            
        # Hvis det hverken er dato eller tal, må det være beskrivelsesteksten
        if (df[col].notna()).all() and (df[col] != "").all() and (df[col].str.len().mean()>10):
            text_cols.append(col)
            print(len(text_cols))
            print(df[col].str.len())

    # 3. Mellemregning og kortlægning af kolonner (Mapping)
    # Vi forventer mindst 1 datokolonne, mindst 2 talkolonner og 1 tekstkolonne
    
    # Initialiser output dataframe
    output_df = pd.DataFrame()
    
    # Mapping af Dato
    if date_cols is not None:
        output_df[DATE] = df[date_cols[0]]  # Vi tager den første datokolonne, hvis der er flere
    else:
        output_df[DATE] = '19700101' # Fallback
        print("Advarsel: Kunne ikke finde en datokolonne.")

    if len(numeric_cols) >= 2:
        output_df[AMOUNT] = df[numeric_cols[0]]
        output_df[TOTAL] = df[numeric_cols[1]]
    else:
        print("Advarsel: Kunne ikke finde en numeriske kolonner")

    if len(text_cols) == 1:
        output_df[DESVC] = df[text_cols[0]]
    else:
        print("Advarsel: Kunne ikke finde en tekst kolonner")
        
    # kode til automatisk bestemmels af saldo. Det skippes under antagelse af at det første tal er beløb, og det andet er saldo.
        
    #     # Funktion til at teste ligningen: Total = Forrige Total + Aktuelt Beløb
    #     def count_saldo_matches(total_col, amount_col, direction):
    #         # direction = 1 kigger på rækken over (kronologisk)
    #         # direction = -1 kigger på rækken under (omvendt kronologisk)
    #         expected_total = df[total_col].shift(direction) + df[amount_col]
            
    #         # Afrunding forhindrer decimalfejl under sammenligningen
    #         matches = (df[total_col].round(2) == expected_total.round(2)).sum()
    #         return matches

    #     # 1. Test kronologisk rækkefølge (ældste øverst)
    #     calc_1_fwd = count_saldo_matches(col1, col2, 1)  # Antag col1 er Saldo
    #     calc_2_fwd = count_saldo_matches(col2, col1, 1)  # Antag col2 er Saldo
        
    #     # 2. Test omvendt kronologisk rækkefølge (nyeste øverst)
    #     calc_1_rev = count_saldo_matches(col1, col2, -1) # Antag col1 er Saldo
    #     calc_2_rev = count_saldo_matches(col2, col1, -1) # Antag col2 er Saldo
        
    #     # 3. Saml resultaterne for at finde scenariet med flest hits
    #     scores = {
    #         (col1, col2): max(calc_1_fwd, calc_1_rev), # Tuple (Saldo, Beløb)
    #         (col2, col1): max(calc_2_fwd, calc_2_rev)
    #     }
        
    #     # 4. Find det vinder-par der har flest hits
    #     best_scenario = max(scores, key=scores.get)
    #     saldo_col = best_scenario[0]
    #     belob_col = best_scenario[1]
        
    #     if scores[best_scenario] > 0:
    #         print(f"Match fundet: Kolonne {belob_col} er Beløb, og {saldo_col} er Saldo.")
    #     else:
    #         print("Advarsel: Kunne ikke finde en garanteret sammenhæng mellem Beløb og Saldo.")
            
    #     # Tilknyt til output dataframe
    #     output_df['Amount'] = df[belob_col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    #     output_df['Saldo'] = df[saldo_col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")    if len(numeric_cols) >= 2:
        # Her antager vi at det første tal er beløb, og det andet er saldo.
        # Dette kan du bytte om på, hvis logikken for din specifikke bank er anderledes.

    # 4. Eksporter til ny CSV
    # index=False fjerner rækkenumre, og vi kan fjerne headers hvis ønsket (header=False)
    output_df.to_csv(output_file, index=False, sep=';', encoding='utf-8')
    print(f"Filen er succesfuldt transformeret og gemt som: {output_file}")

# Kør funktionen (husk at ændre filnavnene)
if __name__ == "__main__":
    transform_bank_csv('firma/aps34720908/2026/bank.csv', 'output.csv')
