import pandas as pd
import os
import re

file_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트\터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'
output_dir = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지'

def clean_text(text):
    if pd.isna(text):
        return ""
    # Remove excessive newlines and tabs to keep CSV clean
    text = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

try:
    # Read the sheet
    df_raw = pd.read_excel(file_path, sheet_name='터널표준체크리스트')
    
    # Data starts from Row 1 (Index 1)
    data = df_raw.iloc[1:].copy()
    
    # Extract Processes
    processes = data.iloc[:, 2].dropna().unique().tolist()
    proc_nodes = [[f"Proc_{i+1:03d}", clean_text(name), "Process"] for i, name in enumerate(processes)]
    
    # Extract Risks (with more details)
    # Col 4: Title (LL제목)
    # Col 5: Cause (LL내용)
    # Col 6: Impact (Unnamed: 6)
    risk_data = data.iloc[:, [4, 5, 6]].drop_duplicates()
    risk_nodes = []
    for i, row in enumerate(risk_data.itertuples(index=False)):
        title = clean_text(row[0])
        cause = clean_text(row[1])
        impact = clean_text(row[2])
        if title:
            risk_nodes.append([f"Risk_{i+1:03d}", title, cause, impact, "Risk"])
            
    # Extract Strategies (with more details)
    # Col 7: Action (Unnamed: 7)
    # Col 9: Checkpoint 1 (Risk 기술검토)
    # Col 11: Checkpoint 2 (Risk 실무)
    strat_data = data.iloc[:, [7, 9, 11]].drop_duplicates()
    strat_nodes = []
    for i, row in enumerate(strat_data.itertuples(index=False)):
        action = clean_text(row[0])
        check1 = clean_text(row[1])
        check2 = clean_text(row[2])
        if action:
            # Combine action and checkpoints if needed, or keep separate
            full_action = f"{action} [체크사항: {check1} / {check2}]"
            strat_nodes.append([f"Strat_{i+1:03d}", action, check1, check2, "Strategy"])
            
    # Helper to write CSV
    def write_csv(filename, header, rows):
        path = os.path.join(output_dir, filename)
        pd.DataFrame(rows, columns=header).to_csv(path, index=False, encoding='utf-8-sig')
        print(f"Generated {filename} with {len(rows)} entries and enriched properties.")

    write_csv('nodes_process.csv', ['id:ID', 'name', ':LABEL'], proc_nodes)
    write_csv('nodes_risk.csv', ['id:ID', 'description', 'cause', 'impact', ':LABEL'], risk_nodes)
    write_csv('nodes_strategy.csv', ['id:ID', 'action', 'check_design', 'check_site', ':LABEL'], strat_nodes)

except Exception as e:
    print(f"Error: {e}")
