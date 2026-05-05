import pandas as pd
import os

file_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트\터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet, nrows=5)
        print(f"\nSheet: {sheet}")
        print(f"Columns: {df.columns.tolist()}")
except Exception as e:
    print(f"Error: {e}")
