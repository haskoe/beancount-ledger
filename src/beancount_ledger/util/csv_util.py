import pandas as pd
import numpy as np
from dataclasses import dataclass
from collections.abc import Callable

@dataclass
class CsvColumnDetector:
    column_name: str
    detector_func: Callable[[pd.Series], pd.Series]

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
    print(mean)
    if mean > min_length:
        return stripped
    return None

def bank_csv_to_dataframe(input_file) -> pd.DataFrame | None:
    detectors = [
        CsvColumnDetector(column_name='date', detector_func=detect_date_column),
        CsvColumnDetector(column_name='amount', detector_func=detect_danish_amount_column),
        CsvColumnDetector(column_name='total', detector_func=detect_danish_amount_column),
        CsvColumnDetector(column_name='description', detector_func=lambda col: detect_text_column(col, min_length=20)),
    ]
    return csv_to_dataframe(input_file, detectors)

def csv_to_dataframe(input_file, detectors: list[CsvColumnDetector]) -> pd.DataFrame:
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
                print('d',col_idx,idx)
                detected[idx] = detected_col
                break

    if len(detected) < len(detectors):
        return None  # Eller håndter det på en anden måde, f.eks. ved at kaste en fejl

    output_df = pd.DataFrame()
    for idx, detector in enumerate(detectors):
        output_df[detector.column_name] = detected[idx]
    return output_df
