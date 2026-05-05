import pandas as pd
import os

file_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트\터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'
output_dir = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지'

try:
    # Read the sheet, skipping the first row (multi-level header or placeholder)
    df = pd.read_excel(file_path, sheet_name='터널표준체크리스트', skiprows=1)
    
    # Based on preview:
    # Col 2: 터널 세공종 -> Process
    # Col 4: LL제목 -> Risk
    # Col 7: Unnamed: 7 -> Strategy
    
    # Get columns by index to be safe (0-indexed)
    # Column names in df after skipping 1 row might be different, let's re-read to get correct headers or use index.
    df_raw = pd.read_excel(file_path, sheet_name='터널표준체크리스트')
    # Row 0 is the placeholder header, Row 1 is data.
    # So skip 1 row means Row 0 is gone, Row 1 becomes header.
    # Wait, in the preview, Row 0 (index 0) has "(리스크 요인)".
    # If I read without skipping, df.iloc[0] is that row.
    
    processes = df_raw.iloc[1:, 2].dropna().unique().tolist()
    risks = df_raw.iloc[1:, 4].dropna().unique().tolist()
    strategies = df_raw.iloc[1:, 7].dropna().unique().tolist()
    
    # Process Nodes
    proc_nodes = []
    for i, name in enumerate(processes):
        proc_nodes.append([f"Proc_{i+1:03d}", name, "Process"])
    
    # Risk Nodes
    risk_nodes = []
    for i, desc in enumerate(risks):
        risk_nodes.append([f"Risk_{i+1:03d}", desc, "Risk"])
        
    # Strategy Nodes
    strat_nodes = []
    for i, action in enumerate(strategies):
        strat_nodes.append([f"Strat_{i+1:03d}", action, "Strategy"])
        
    # Helper to write CSV
    def write_csv(filename, header, rows):
        path = os.path.join(output_dir, filename)
        pd.DataFrame(rows, columns=header).to_csv(path, index=False, encoding='utf-8-sig')
        print(f"Generated {filename} with {len(rows)} entries.")

    write_csv('nodes_process.csv', ['id:ID', 'name', ':LABEL'], proc_nodes)
    write_csv('nodes_risk.csv', ['id:ID', 'description', ':LABEL'], risk_nodes)
    write_csv('nodes_strategy.csv', ['id:ID', 'action', ':LABEL'], strat_nodes)

except Exception as e:
    print(f"Error: {e}")
