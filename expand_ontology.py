import pandas as pd
import re
import os

# 파일 경로 설정
base_path = r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\터널표준체크리스트'
excel_file = os.path.join(base_path, '터널(NATM)표춘체크리스(26년4월 13일) (2).xlsx')

def clean_text(text):
    if pd.isna(text): return ""
    text = str(text).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()

# 키워드 정의 (더 포괄적으로 확장)
ground_keywords = [
    '풍화암', '연암', '경암', '파쇄대', '단층', '고수압', '지하수', '복합지반', 
    '연약지반', '토사', '붕적층', '석회암', '공동', '실트', '점토', '모래', '자갈', '전석',
    '암반', '지질', '지층', '풍화토', '붕락', '용수', '함수', '침수'
]

standard_keywords = [
    r'KDS\s?\d*', r'KCS\s?\d*', '설계기준', '가이드라인', '지침', '매뉴얼', 
    '법령', '규칙', '시행령', '국가건설기준', '표준', '시방서', '기준', '법규'
]

def extract_keywords(text, keywords, is_regex=False):
    found = set()
    if not text or len(text) < 2: return []
    
    for kw in keywords:
        if is_regex:
            matches = re.findall(kw, text, re.IGNORECASE)
            for m in matches: 
                if len(m) >= 2: found.add(m.strip())
        else:
            if kw in text:
                found.add(kw)
    return list(found)

# 데이터 로드
df = pd.read_excel(excel_file)

nodes_process = []
nodes_risk = []
nodes_strategy = []
nodes_ground = {}
nodes_standard = {}
rels = []

process_map = {}
risk_map = {}
strat_map = {}

# 데이터 클리닝 및 노드 생성 준비
for idx, row in df.iterrows():
    if idx < 1: continue # 헤더 제외
    
    proc_name = clean_text(row.iloc[1]) # 터널 중분류
    risk_title = clean_text(row.iloc[4]) # 리스크 명칭
    project = clean_text(row.iloc[3]) # 도출현장
    risk_cause = clean_text(row.iloc[5]) # LL내용 (원인)
    risk_impact = clean_text(row.iloc[6]) # 문제점 및 영향
    strat_action = clean_text(row.iloc[7]) # 대응대책
    
    if not risk_title or not strat_action: continue

    # 1. Process Node
    if proc_name not in process_map:
        p_id = f"Proc_{len(process_map)+1:03d}"
        process_map[proc_name] = p_id
        nodes_process.append({'id:ID': p_id, 'name': proc_name, ':LABEL': 'Process'})
    p_id = process_map[proc_name]
    
    # 2. Risk Node
    risk_key = f"{risk_title}_{project}"
    if risk_key not in risk_map:
        r_id = f"Risk_{len(risk_map)+1:03d}"
        risk_map[risk_key] = r_id
        nodes_risk.append({
            'id:ID': r_id, 
            'description': risk_title, 
            'cause': risk_cause,
            'impact': risk_impact,
            'source_project': project,
            ':LABEL': 'Risk'
        })
    r_id = risk_map[risk_key]
    
    # 3. Strategy Node
    strat_key = f"{strat_action}_{project}"
    if strat_key not in strat_map:
        s_id = f"Strat_{len(strat_map)+1:03d}"
        strat_map[strat_key] = s_id
        nodes_strategy.append({
            'id:ID': s_id, 
            'action': strat_action,
            'source_project': project,
            ':LABEL': 'Strategy'
        })
    s_id = strat_map[strat_key]
    
    # Relationships: P -> R, R -> S
    rels.append({':START_ID': p_id, ':END_ID': r_id, ':TYPE': 'ENCOUNTERS'})
    rels.append({':START_ID': r_id, ':END_ID': s_id, ':TYPE': 'MITIGATED_BY'})
    
    # 4. Ground Extraction (from Cause/LL내용)
    found_grounds = extract_keywords(risk_cause, ground_keywords)
    found_grounds += extract_keywords(risk_impact, ground_keywords)
    
    for g in set(found_grounds):
        if g not in nodes_ground:
            g_id = f"G_{len(nodes_ground)+1:03d}"
            nodes_ground[g] = g_id
        rels.append({':START_ID': nodes_ground[g], ':END_ID': r_id, ':TYPE': 'TRIGGER'})
        
    # 5. Standard Extraction (from Strategy action)
    found_stds_regex = extract_keywords(strat_action, [k for k in standard_keywords if 'K' in k], is_regex=True)
    found_stds_lit = extract_keywords(strat_action, [k for k in standard_keywords if 'K' not in k])
    
    for std in set(found_stds_regex + found_stds_lit):
        if std not in nodes_standard:
            std_id = f"STD_{len(nodes_standard)+1:03d}"
            nodes_standard[std] = std_id
        rels.append({':START_ID': s_id, ':END_ID': nodes_standard[std], ':TYPE': 'BASED_ON'})

# Create DataFrames
df_ground = pd.DataFrame([{'id:ID': v, 'condition_name': k, ':LABEL': 'Ground'} for k, v in nodes_ground.items()])
df_standard = pd.DataFrame([{'id:ID': v, 'doc_name': k, ':LABEL': 'Standard'} for k, v in nodes_standard.items()])
df_rels = pd.DataFrame(rels).drop_duplicates()

# Save CSVs
df_ground.to_csv(os.path.join(base_path, 'nodes_ground.csv'), index=False, encoding='utf-8-sig')
df_standard.to_csv(os.path.join(base_path, 'nodes_standard.csv'), index=False, encoding='utf-8-sig')
df_rels.to_csv(os.path.join(base_path, 'rels_expanded.csv'), index=False, encoding='utf-8-sig')

# Final results for nodes_risk and nodes_strategy to maintain consistency
pd.DataFrame(nodes_process).to_csv(os.path.join(base_path, 'nodes_process.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(nodes_risk).to_csv(os.path.join(base_path, 'nodes_risk.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(nodes_strategy).to_csv(os.path.join(base_path, 'nodes_strategy.csv'), index=False, encoding='utf-8-sig')

print(f"Nodes Ground: {len(df_ground)}")
print(f"Nodes Standard: {len(df_standard)}")
print(f"Total Relationships (Expanded): {len(df_rels)}")
print("\nSample Ground nodes:", list(nodes_ground.keys())[:5])
print("Sample Standard nodes:", list(nodes_standard.keys())[:5])
