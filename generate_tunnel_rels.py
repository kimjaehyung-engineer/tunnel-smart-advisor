import pandas as pd
import os
import re

file_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트\터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'
output_dir = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트'

def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

try:
    # Read the sheet
    df_raw = pd.read_excel(file_path, sheet_name='터널표준체크리스트')
    data = df_raw.iloc[1:].copy()
    
    # 1. Re-generate ID mappings (Must match the previous node generation logic)
    # Processes
    processes = data.iloc[:, 2].dropna().unique().tolist()
    proc_map = {clean_text(name): f"Proc_{i+1:03d}" for i, name in enumerate(processes)}
    
    # Risks
    risk_data = data.iloc[:, [4, 5, 6]].drop_duplicates()
    risk_map = {}
    for i, row in enumerate(risk_data.itertuples(index=False)):
        title = clean_text(row[0])
        if title:
            # We use title as key because it was the primary identifier for uniqueness in nodes_risk.csv
            risk_map[title] = f"Risk_{i+1:03d}"
            
    # Strategies
    strat_data = data.iloc[:, [7, 9, 11]].drop_duplicates()
    strat_map = {}
    for i, row in enumerate(strat_data.itertuples(index=False)):
        action = clean_text(row[0])
        if action:
            strat_map[action] = f"Strat_{i+1:03d}"
            
    # 2. Build Relationships
    relationships = []
    
    for row in data.itertuples(index=False):
        p_name = clean_text(row[2])
        r_title = clean_text(row[4])
        s_action = clean_text(row[7])
        
        p_id = proc_map.get(p_name)
        r_id = risk_map.get(r_title)
        s_id = strat_map.get(s_action)
        
        # Link Process -> Risk
        if p_id and r_id:
            relationships.append([p_id, r_id, "ENCOUNTERS"])
            
        # Link Risk -> Strategy
        if r_id and s_id:
            relationships.append([r_id, s_id, "MITIGATED_BY"])
            
    # Remove duplicate relationships
    rels_df = pd.DataFrame(relationships, columns=[':START_ID', ':END_ID', ':TYPE']).drop_duplicates()
    
    # Save to CSV
    output_path = os.path.join(output_dir, 'rels.csv')
    rels_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"Generated rels.csv with {len(rels_df)} unique relationships in {output_path}")

except Exception as e:
    print(f"Error: {e}")
