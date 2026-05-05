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
    
    # --- 1. Extract and Clean Data ---
    # Col 2: Process, Col 3: Project, Col 4: Risk Title, Col 5: Cause, Col 6: Impact, Col 7: Strategy, Col 9: Check1, Col 11: Check2
    
    # Process Nodes
    processes = data.iloc[:, 2].dropna().unique().tolist()
    proc_map = {clean_text(name): f"Proc_{i+1:03d}" for i, name in enumerate(processes)}
    proc_nodes = [[f"Proc_{i+1:03d}", clean_text(name), "Process"] for i, name in enumerate(processes)]
    
    # Risk Nodes (Unique by Title + Project)
    # Using Col 4 (Title), 5 (Cause), 6 (Impact) AND Col 3 (Project)
    risk_raw = data.iloc[:, [4, 5, 6, 3]].drop_duplicates()
    risk_nodes = []
    risk_id_map = {} # Key: (title, project), Value: ID
    
    for i, row in enumerate(risk_raw.itertuples(index=False)):
        title = clean_text(row[0])
        cause = clean_text(row[1])
        impact = clean_text(row[2])
        project = clean_text(row[3])
        if title:
            rid = f"Risk_{i+1:03d}"
            risk_nodes.append([rid, title, cause, impact, project, "Risk"])
            risk_id_map[(title, project)] = rid
            
    # Strategy Nodes (Unique by Action + Project)
    # Using Col 7 (Action), 9 (Check1), 11 (Check2) AND Col 3 (Project)
    strat_raw = data.iloc[:, [7, 9, 11, 3]].drop_duplicates()
    strat_nodes = []
    strat_id_map = {} # Key: (action, project), Value: ID
    
    for i, row in enumerate(strat_raw.itertuples(index=False)):
        action = clean_text(row[0])
        check1 = clean_text(row[1])
        check2 = clean_text(row[2])
        project = clean_text(row[3])
        if action:
            sid = f"Strat_{i+1:03d}"
            strat_nodes.append([sid, action, check1, check2, project, "Strategy"])
            strat_id_map[(action, project)] = sid
            
    # --- 2. Build Relationships ---
    relationships = []
    for row in data.itertuples(index=False):
        p_name = clean_text(row[2])
        project = clean_text(row[3])
        r_title = clean_text(row[4])
        s_action = clean_text(row[7])
        
        pid = proc_map.get(p_name)
        rid = risk_id_map.get((r_title, project))
        sid = strat_id_map.get((s_action, project))
        
        if pid and rid:
            relationships.append([pid, rid, "ENCOUNTERS"])
        if rid and sid:
            relationships.append([rid, sid, "MITIGATED_BY"])
            
    rels_df = pd.DataFrame(relationships, columns=[':START_ID', ':END_ID', ':TYPE']).drop_duplicates()
    
    # --- 3. Save Files ---
    pd.DataFrame(proc_nodes, columns=['id:ID', 'name', ':LABEL']).to_csv(os.path.join(output_dir, 'nodes_process.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(risk_nodes, columns=['id:ID', 'description', 'cause', 'impact', 'source_project', ':LABEL']).to_csv(os.path.join(output_dir, 'nodes_risk.csv'), index=False, encoding='utf-8-sig')
    pd.DataFrame(strat_nodes, columns=['id:ID', 'action', 'check_design', 'check_site', 'source_project', ':LABEL']).to_csv(os.path.join(output_dir, 'nodes_strategy.csv'), index=False, encoding='utf-8-sig')
    rels_df.to_csv(os.path.join(output_dir, 'rels.csv'), index=False, encoding='utf-8-sig')
    
    print(f"Successfully generated files with source_project property in {output_dir}")

except Exception as e:
    print(f"Error: {e}")
