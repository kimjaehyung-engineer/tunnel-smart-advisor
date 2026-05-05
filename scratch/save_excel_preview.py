import pandas as pd
import os

file_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트\터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'
output_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\scratch\excel_preview.txt'

try:
    xl = pd.ExcelFile(file_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        for sheet in xl.sheet_names:
            f.write(f"--- Sheet: {sheet} ---\n")
            df = pd.read_excel(file_path, sheet_name=sheet).head(20)
            f.write(df.to_string())
            f.write("\n\n")
    print(f"Preview saved to {output_path}")
except Exception as e:
    print(f"Error: {e}")
