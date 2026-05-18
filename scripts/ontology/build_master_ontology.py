import pandas as pd
import re
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.ontology_version import write_ontology_version

# 파일 경로 설정
base_path = PROJECT_ROOT / 'data' / 'tunnel_checklist'
excel_file = base_path / '터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx'
source_version = excel_file.name

def clean_text(text):
    if pd.isna(text): return ""
    text = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()

# 범주별 키워드 사전
dict_keywords = {
    'Ground': ['풍화암', '연암', '경암', '파쇄대', '단층', '고수압', '지하수', '복합지반', '연약지반', '토사', '붕적층', '석회암', '공동', '암반', '지질', '지층', '풍화토', '붕락', '용수', '함수', '침수'],
    'Method': ['NATM', 'TBM', '개착', '쉴드', '파이프루프', '보강공법', '차수공법', '그라우팅', '숏크리트', '락볼트', '발파', '기계굴착'],
    'Equipment': ['점보드릴', '백호', '굴착기', '크레인', '천공기', '페이로더', '덤프트럭', '자동계측', '환기시설', '배수펌프'],
    'Location': ['갱구부', '본선부', '교차부', '도심지', '하저', '하천', '근접구조물', '지장물', '주택가', '변전소', '철도교'],
    'Impact': ['공사비', '공기지연', '안전사고', '품질저하', '민원', '환경오염', '붕괴', '침하'],
    'Role': ['시공사', '감리단', '발주처', '설계사', '품질관리자', '안전관리자', '민원인', '유관기관'],
    'Standard': ['KDS', 'KCS', '설계기준', '가이드라인', '지침', '매뉴얼', '법령', '규칙', '시행령', '국가건설기준', '표준', '시방서', '기준', '법규']
}

def extract_all(text):
    results = {k: set() for k in dict_keywords.keys()}
    if not text or len(text) < 2: return results
    
    for category, kws in dict_keywords.items():
        for kw in kws:
            if category == 'Standard' and ('KDS' in kw or 'KCS' in kw):
                matches = re.findall(kw + r'\s?\d*', text, re.IGNORECASE)
                for m in matches: results[category].add(m.strip())
            else:
                if kw in text:
                    results[category].add(kw)
    return results

# 데이터 로드
df = pd.read_excel(excel_file)

# 마스터 저장소
nodes = {k: {} for k in dict_keywords.keys()} # {Category: {Name: ID}}
nodes['Process'] = {}
nodes['Risk'] = {}
nodes['Strategy'] = {}
nodes['Project'] = {}

csv_data = {k: [] for k in ['Process', 'Risk', 'Strategy', 'Project'] + list(dict_keywords.keys())}
rels = []

# ID 접두어 매핑
prefixes = {
    'Process': 'Proc_', 'Risk': 'Risk_', 'Strategy': 'Strat_', 'Project': 'Proj_',
    'Ground': 'G_', 'Method': 'M_', 'Equipment': 'EQ_',
    'Location': 'L_', 'Impact': 'I_', 'Role': 'ROLE_', 'Standard': 'STD_'
}

# 루프 실행
for idx, row in df.iterrows():
    if idx < 1: continue
    
    p_name = clean_text(row.iloc[1])
    r_title = clean_text(row.iloc[4])
    proj = clean_text(row.iloc[3])
    r_cause = clean_text(row.iloc[5])
    r_impact = clean_text(row.iloc[6])
    s_action = clean_text(row.iloc[7])
    
    if not r_title or not s_action: continue

    # 1. Core Nodes (Process, Risk, Strategy)
    def get_id(cat, name, extra_props=None):
        if name not in nodes[cat]:
            new_id = f"{prefixes[cat]}{len(nodes[cat])+1:03d}"
            nodes[cat][name] = new_id
            row_data = {'id:ID': new_id}
            if cat == 'Process': row_data['name'] = name
            elif cat == 'Project': row_data['name'] = name
            elif cat == 'Risk': 
                row_data.update({
                    'description': name,
                    'source_project': proj,
                    'source_version': source_version,
                    'likelihood': 1.0,
                    'impact_score': 3.0,
                    'frequency': 1.0,
                    'recency': 1.0,
                    'confidence': 0.0,
                    'expert_weight': 1.0,
                })
                if extra_props:
                    row_data.update(extra_props)
            elif cat == 'Strategy': 
                row_data.update({
                    'action': name,
                    'source_project': proj,
                    'target_risk': extra_props.get('target_risk', '') if extra_props else '',
                    'expected_effect': extra_props.get('expected_effect', '') if extra_props else '',
                    'required_equipment': extra_props.get('required_equipment', '') if extra_props else '',
                    'related_standard': extra_props.get('related_standard', '') if extra_props else '',
                    'responsible_role': extra_props.get('responsible_role', '') if extra_props else '',
                })
            else:
                label_map = {'Ground': 'condition_name', 'Method': 'method_name', 'Equipment': 'equip_name', 
                             'Location': 'loc_name', 'Impact': 'impact_type', 'Role': 'role_name', 'Standard': 'doc_name'}
                row_data[label_map[cat]] = name
            
            row_data[':LABEL'] = cat
            csv_data[cat].append(row_data)
        return nodes[cat][name]

    p_id = get_id('Process', p_name)
    proj_id = get_id('Project', proj)
    r_id = get_id('Risk', f"{r_title}_{proj}", {
        'source_ll': r_title,
        'cause': r_cause,
        'impact': r_impact,
        'impact_text': r_impact,
    })

    s_ext = extract_all(s_action)
    s_id = get_id('Strategy', f"{s_action}_{proj}", {
        'target_risk': r_id,
        'expected_effect': r_impact,
        'required_equipment': ', '.join(sorted(s_ext['Equipment'])),
        'related_standard': ', '.join(sorted(s_ext['Standard'])),
        'responsible_role': ', '.join(sorted(s_ext['Role'])),
    })

    # 2. Core Relationships
    rels.append({':START_ID': p_id, ':END_ID': r_id, ':TYPE': 'ENCOUNTERS'})
    rels.append({':START_ID': r_id, ':END_ID': s_id, ':TYPE': 'MITIGATED_BY'})
    rels.append({':START_ID': proj_id, ':END_ID': r_id, ':TYPE': 'HAS_RISK_CASE'})
    rels.append({':START_ID': proj_id, ':END_ID': s_id, ':TYPE': 'APPLIED_STRATEGY'})

    # 3. Contextual Extraction
    # Risk 관련 (Cause + Impact에서 추출)
    risk_text = r_cause + " " + r_impact
    r_ext = extract_all(risk_text)
    
    for g in r_ext['Ground']:
        rels.append({':START_ID': get_id('Ground', g), ':END_ID': r_id, ':TYPE': 'TRIGGER'})
    for m in r_ext['Method']:
        rels.append({':START_ID': get_id('Method', m), ':END_ID': r_id, ':TYPE': 'ASSOCIATED_WITH'})
    for l in r_ext['Location']:
        rels.append({':START_ID': get_id('Location', l), ':END_ID': r_id, ':TYPE': 'OCCURS_AT'})
    for i in r_ext['Impact']:
        rels.append({':START_ID': r_id, ':END_ID': get_id('Impact', i), ':TYPE': 'AFFECTS'})

    # Strategy 관련 (Action에서 추출)
    # Strategy 관련 (Action에서 추출)
    for eq in s_ext['Equipment']:
        eq_id = get_id('Equipment', eq)
        rels.append({':START_ID': s_id, ':END_ID': eq_id, ':TYPE': 'REQUIRES'})
        # 확장 3: Ground -> Equipment (지반별 장비 매칭)
        for g in r_ext['Ground']:
            rels.append({':START_ID': get_id('Ground', g), ':END_ID': eq_id, ':TYPE': 'REQUIRES'})
        # 추가: Process -> Equipment (공종별 기본 장비 매칭)
        rels.append({':START_ID': p_id, ':END_ID': eq_id, ':TYPE': 'USES'})

    for role in s_ext['Role']:
        rels.append({':START_ID': s_id, ':END_ID': get_id('Role', role), ':TYPE': 'ASSIGNED_TO'})
    
    for std in s_ext['Standard']:
        rels.append({':START_ID': s_id, ':END_ID': get_id('Standard', std), ':TYPE': 'BASED_ON'})

    # 확장 1: Ground -> Method (지반별 공법 매칭)
    for g in r_ext['Ground']:
        for m in s_ext['Method']:
            rels.append({':START_ID': get_id('Ground', g), ':END_ID': get_id('Method', m), ':TYPE': 'REQUIRES'})
            
    # 추가 2: Process -> Method (공종별 기본 공법 매칭)
    all_methods = set(r_ext['Method']).union(set(s_ext['Method']))
    for m in all_methods:
        rels.append({':START_ID': p_id, ':END_ID': get_id('Method', m), ':TYPE': 'USES'})
    
    # 확장 4: Location -> Ground (위치별 지질 특성)
    for l in r_ext['Location']:
        for g in r_ext['Ground']:
            rels.append({':START_ID': get_id('Location', l), ':END_ID': get_id('Ground', g), ':TYPE': 'CHARACTERIZED_BY'})

# Save Node Files
all_node_ids = set()
for cat, data in csv_data.items():
    filename = f"nodes_{cat.lower()}.csv"
    df_nodes = pd.DataFrame(data)
    df_nodes.to_csv(os.path.join(base_path, filename), index=False, encoding='utf-8-sig')
    all_node_ids.update(df_nodes['id:ID'].tolist())

# Split and Save Relationship Files by Type
rel_groups = {
    'proc_risk': [r for r in rels if r[':TYPE'] == 'ENCOUNTERS'],
    'risk_strat': [r for r in rels if r[':TYPE'] == 'MITIGATED_BY'],
    'project_risk': [r for r in rels if r[':TYPE'] == 'HAS_RISK_CASE'],
    'project_strategy': [r for r in rels if r[':TYPE'] == 'APPLIED_STRATEGY'],
    'ground_risk': [r for r in rels if r[':TYPE'] == 'TRIGGER'],
    'method_risk': [r for r in rels if r[':TYPE'] == 'ASSOCIATED_WITH'],
    'loc_risk': [r for r in rels if r[':TYPE'] == 'OCCURS_AT'],
    'risk_impact': [r for r in rels if r[':TYPE'] == 'AFFECTS'],
    'strat_equip': [r for r in rels if r[':TYPE'] == 'REQUIRES' and r[':START_ID'].startswith('Strat')],
    'strat_role': [r for r in rels if r[':TYPE'] == 'ASSIGNED_TO'],
    'strat_std': [r for r in rels if r[':TYPE'] == 'BASED_ON'],
    'ground_method': [r for r in rels if r[':TYPE'] == 'REQUIRES' and r[':START_ID'].startswith('G') and r[':END_ID'].startswith('M')],
    'ground_equip': [r for r in rels if r[':TYPE'] == 'REQUIRES' and r[':START_ID'].startswith('G') and r[':END_ID'].startswith('EQ')],
    'loc_ground': [r for r in rels if r[':TYPE'] == 'CHARACTERIZED_BY'],
    'proc_equip': [r for r in rels if r[':TYPE'] == 'USES' and r[':START_ID'].startswith('Proc') and r[':END_ID'].startswith('EQ')],
    'proc_method': [r for r in rels if r[':TYPE'] == 'USES' and r[':START_ID'].startswith('Proc') and r[':END_ID'].startswith('M')]
}

# Save Individual and Total Relationship Files
valid_rels_all = []
print("=== Advanced Ontology Construction Complete ===")

for name, data in rel_groups.items():
    if not data: continue
    df_temp = pd.DataFrame(data).drop_duplicates()
    valid_temp = df_temp[df_temp[':START_ID'].isin(all_node_ids) & df_temp[':END_ID'].isin(all_node_ids)]
    
    # Add to total list
    valid_rels_all.append(valid_temp)
    
    # Save individual file
    filename = f"rels_{name}.csv"
    valid_temp.to_csv(os.path.join(base_path, filename), index=False, encoding='utf-8-sig')
    print(f"Created {filename}: {len(valid_temp)} relationships")

# Final Total Integrated File
df_rels_total = pd.concat(valid_rels_all).drop_duplicates()
try:
    df_rels_total.to_csv(os.path.join(base_path, 'rels_total.csv'), index=False, encoding='utf-8-sig')
    print(f"\nFinal Total Integrated Relationships (rels_total.csv): {len(df_rels_total)}")
except PermissionError:
    print(f"\n[오류] 'rels_total.csv' 파일이 열려 있어서 저장할 수 없습니다. 파일을 닫고 다시 실행해주세요.")
    
for cat in csv_data.keys():
    print(f"Nodes {cat}: {len(csv_data[cat])}")

version = write_ontology_version(base_path / 'ontology_version.json', excel_file)
print(f"Ontology version metadata: {version['source_file']} / {version['source_file_hash'][:12]}")
