import pandas as pd
import os
from pyvis.network import Network
from collections import defaultdict
import traceback

base_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트'
df_ground = pd.read_csv(os.path.join(base_path, 'nodes_ground.csv'))
df_method = pd.read_csv(os.path.join(base_path, 'nodes_method.csv'))
df_equip = pd.read_csv(os.path.join(base_path, 'nodes_equipment.csv'))
df_risk = pd.read_csv(os.path.join(base_path, 'nodes_risk.csv'))
df_proc = pd.read_csv(os.path.join(base_path, 'nodes_process.csv'))
df_loc = pd.read_csv(os.path.join(base_path, 'nodes_location.csv'))
df_strat = pd.read_csv(os.path.join(base_path, 'nodes_strategy.csv'))
df_rels = pd.read_csv(os.path.join(base_path, 'rels_total.csv'))

# Simulate selecting "굴착", "파쇄대"
sel_proc = df_proc['name'].tolist()[0]
sel_ground = df_ground['condition_name'].tolist()[0]
sel_loc = df_loc['loc_name'].tolist()[0]

risk_scores = defaultdict(int)
risk_matches = defaultdict(list)
target_nodes = []
num_filters = 2

p_id = df_proc[df_proc['name'] == sel_proc]['id:ID'].values[0]
target_nodes.append((p_id, sel_proc, '#74b9ff'))
r_ids = df_rels[(df_rels[':START_ID'] == p_id) & (df_rels[':TYPE'] == 'ENCOUNTERS')][':END_ID'].tolist()
for r_id in r_ids:
    risk_scores[r_id] += 1
    risk_matches[r_id].append(sel_proc)
    
g_id = df_ground[df_ground['condition_name'] == sel_ground]['id:ID'].values[0]
target_nodes.append((g_id, sel_ground, '#74b9ff'))
r_ids = df_rels[(df_rels[':START_ID'] == g_id) & (df_rels[':TYPE'] == 'TRIGGER')][':END_ID'].tolist()
for r_id in r_ids:
    risk_scores[r_id] += 1
    risk_matches[r_id].append(sel_ground)

sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)

try:
    net = Network(height='500px', width='100%', bgcolor='#ffffff', font_color='black')
    for t_id, t_label, t_color in target_nodes:
        net.add_node(t_id, label="조건", title=t_label, color=t_color, size=30)
    
    for r_id, score in sorted_risks[:15]:
        r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
        if score == num_filters:
            net.add_node(r_id, label="핵심 Risk!", title=r_desc, color='#ff4757', size=45, font_color='black')
        else:
            net.add_node(r_id, label="Risk", title=r_desc, color='#ffeaa7', size=20)
        
        for t_id, t_label, _ in target_nodes:
            if t_label in risk_matches[r_id]:
                edge_width = 3 if score == num_filters else 1
                net.add_edge(t_id, r_id, title="MATCHED", width=edge_width)
            
        if score == num_filters:
            strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
            for s_id in strat_ids[:2]: 
                s_label = df_strat[df_strat['id:ID'] == s_id]['action'].values[0]
                net.add_node(s_id, label="Strategy", title=s_label, color='#2ed573', size=15)
                net.add_edge(r_id, s_id, title="MITIGATED")
    print("Graph built successfully!")
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
