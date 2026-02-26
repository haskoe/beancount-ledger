from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .. import constants as const


@dataclass
class CsvColumnDetector:
    column_name: str
    detector_func: Callable[[pd.Series], pd.Series | None]

def detect_date_column(col: pd.Series) -> pd.Series | None:
    parsed_dates = pd.to_datetime(col, errors='coerce', dayfirst=True)
    if parsed_dates.notna().mean() > 0.99:
        return parsed_dates
    return None

def detect_danish_amount_column(col: pd.Series) -> pd.Series | None:
    cleaned_numbers = col.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    parsed_numbers = pd.to_numeric(cleaned_numbers, errors='coerce')
    if parsed_numbers.notna().mean() > 0.99:
        return parsed_numbers
    return None

def detect_text_column(col: pd.Series, min_length: int) -> pd.Series | None:
    stripped = col.str.strip()
    mean = stripped.str.len().mean()
    if mean > min_length:
        return stripped
    return None

def bank_csv_to_dataframe(input_file) -> pd.DataFrame | None:
    detectors = [
        CsvColumnDetector(column_name=const.DATE, detector_func=detect_date_column),
        CsvColumnDetector(column_name=const.TOTAL, detector_func=detect_danish_amount_column),
        CsvColumnDetector(column_name=const.AMOUNT, detector_func=detect_danish_amount_column),
        CsvColumnDetector(column_name=const.DESCRIPTION, detector_func=lambda col: detect_text_column(col, min_length=20)),
    ]
    result = csv_to_dataframe(input_file, detectors)
    print(input_file)
    if result is not None:
        # nu skal vi checke:
        # 1: er amount og total er korrekte eller skal de byttes om
        # 2: er rækker sorteret korrekt: asc efter dato
        col_date = result[const.DATE]
        if col_date.iloc[0] > col_date.iloc[-1]:
            result = result.iloc[::-1] # vendes om

        for i in range(2): # kører først med nuv sortering og anden gang med modsat hvis der kun er en dato forekomst
            col_date = result[const.DATE]

            col_names = (const.AMOUNT, const.TOTAL)
            for a,t in (col_names,reversed(col_names)):
                expected = result[t].shift(1) + result[a]
                is_close = np.isclose(result[t].iloc[1:], expected.iloc[1:])
                if is_close.all():
                    print(a)
                    if a != const.AMOUNT:
                        result = result[[const.DATE, const.TOTAL, const.AMOUNT, const.DESCRIPTION]]
                    return result

            # hvis vi er her kan det kun være fordi der er fejl i bank csv filen
            # eller der IKKE er forskellige datoer i csv filen
            if i<1 and col_date.iloc[0] == col_date.iloc[-1]:
                result = result.iloc[::-1] # vendes om
                print(result)
            else:
                break

    print('none')
    return None

def csv_to_dataframe(input_file, detectors: list[CsvColumnDetector]) -> pd.DataFrame | None:
    df = pd.read_csv(input_file, header=None, dtype=str, sep=";", engine='python')

    detected = {}
    for col_idx in df.columns:
        col = df[col_idx]
        if col.isna().any():
            continue

        for idx, detector in enumerate(detectors):
            if idx in detected:
                continue

            detected_col = detector.detector_func(col)
            if detected_col is not None:
                detected[idx] = detected_col
                break

    if len(detected) < len(detectors):
        return None  # Eller håndter det på en anden måde, f.eks. ved at kaste en fejl

    output_df = pd.DataFrame()
    for idx, detector in enumerate(detectors):
        output_df[detector.column_name] = detected[idx]
    return output_df
