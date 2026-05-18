import pandas as pd
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
file_path = PROJECT_ROOT / 'data' / 'tunnel_checklist' / '터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
        print(f"\nSheet: {sheet}")
        print(f"Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"Error: {e}")
