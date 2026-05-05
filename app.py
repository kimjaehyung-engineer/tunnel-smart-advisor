import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import re
from collections import defaultdict

# 웹 페이지 기본 설정
st.set_page_config(page_title="터널 스마트 어드바이저 v6 (자연어 검색 지원)", layout="wide", page_icon="🚇")

@st.cache_data
def load_data():
    # 상대 경로로 변경 (GitHub 배포 시 경로 오류 방지)
    base_path = os.path.join(os.path.dirname(__file__), '터널표준체크리스트')
    df_ground = pd.read_csv(os.path.join(base_path, 'nodes_ground.csv'))
    df_method = pd.read_csv(os.path.join(base_path, 'nodes_method.csv'))
    df_equip = pd.read_csv(os.path.join(base_path, 'nodes_equipment.csv'))
    df_risk = pd.read_csv(os.path.join(base_path, 'nodes_risk.csv'))
    df_proc = pd.read_csv(os.path.join(base_path, 'nodes_process.csv'))
    df_loc = pd.read_csv(os.path.join(base_path, 'nodes_location.csv'))
    df_strat = pd.read_csv(os.path.join(base_path, 'nodes_strategy.csv'))
    df_rels = pd.read_csv(os.path.join(base_path, 'rels_total.csv'))
    return df_ground, df_method, df_equip, df_risk, df_proc, df_loc, df_strat, df_rels

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

st.title("🚇 터널 엔지니어링 스마트 어드바이저 (자연어 검색 & 지식 그래프)")
st.markdown("드롭다운으로 조건을 선택하거나, **채팅하듯 현장 상황을 글로 적어보세요.** AI가 텍스트를 분석하여 맞춤형 리스크와 대책, 지식 그래프를 띄워줍니다.")

try:
    df_ground, df_method, df_equip, df_risk, df_proc, df_loc, df_strat, df_rels = load_data()
    
    st.sidebar.header("🔍 복합 현장 조건 세팅")
    
    proc_names = sorted(df_proc['name'].dropna().tolist(), key=natural_sort_key)
    ground_names = sorted(df_ground['condition_name'].dropna().tolist(), key=natural_sort_key)
    loc_names = sorted(df_loc['loc_name'].dropna().tolist(), key=natural_sort_key)
    
    sel_proc = st.sidebar.selectbox("1. 공종 (Process)", ["[상관없음/전체]"] + proc_names)
    sel_ground = st.sidebar.selectbox("2. 지반 조건 (Ground)", ["[상관없음/전체]"] + ground_names)
    sel_loc = st.sidebar.selectbox("3. 현장 위치 (Location)", ["[상관없음/전체]"] + loc_names)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 AI 자연어 현장 검색")
    user_query = st.sidebar.text_area(
        "현장 여건이나 궁금한 점을 자유롭게 적어보세요.", 
        placeholder="예: 도심지 갱구부에서 굴착할 때 파쇄대를 만나면 어떻게 해?",
        height=100
    )
    
    # 랭킹 점수 계산 초기화
    risk_scores = defaultdict(float)
    risk_matches = defaultdict(list)
    target_nodes = {} # t_id : (t_label, t_color)
    
    def apply_filter(node_id, node_label, color, rel_type):
        if node_id not in target_nodes:
            target_nodes[node_id] = (node_label, color)
            r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
            for r_id in r_ids:
                risk_scores[r_id] += 1.0
                if node_label not in risk_matches[r_id]:
                    risk_matches[r_id].append(node_label)
                    
    # 1. 드롭다운 필터 적용
    if sel_proc != "[상관없음/전체]":
        p_id = df_proc[df_proc['name'] == sel_proc]['id:ID'].values[0]
        apply_filter(p_id, sel_proc, '#74b9ff', 'ENCOUNTERS')
            
    if sel_ground != "[상관없음/전체]":
        g_id = df_ground[df_ground['condition_name'] == sel_ground]['id:ID'].values[0]
        apply_filter(g_id, sel_ground, '#74b9ff', 'TRIGGER')
            
    if sel_loc != "[상관없음/전체]":
        l_id = df_loc[df_loc['loc_name'] == sel_loc]['id:ID'].values[0]
        apply_filter(l_id, sel_loc, '#74b9ff', 'OCCURS_AT')

    # 2. 자연어 검색 필터 (키워드 추출 및 시맨틱 매칭)
    if user_query:
        query_words = [w for w in re.split(r'\W+', user_query) if len(w) >= 2]
        
        # 공종 키워드 매칭
        for _, row in df_proc.dropna(subset=['name']).iterrows():
            name = row['name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_filter(row['id:ID'], name, '#a29bfe', 'ENCOUNTERS')
                    break
                    
        # 지반 키워드 매칭
        for _, row in df_ground.dropna(subset=['condition_name']).iterrows():
            name = row['condition_name']
            if name in user_query or (len(name)>=2 and name[:2] in user_query):
                apply_filter(row['id:ID'], name, '#a29bfe', 'TRIGGER')
                
        # 위치 키워드 매칭
        for _, row in df_loc.dropna(subset=['loc_name']).iterrows():
            name = row['loc_name']
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_filter(row['id:ID'], name, '#a29bfe', 'OCCURS_AT')
                    break
                    
        # 질문 내용 자체를 리스크 설명과 직접 비교 (가중치 0.5)
        for _, row in df_risk.dropna(subset=['description']).iterrows():
            r_id = row['id:ID']
            desc = row['description']
            for qw in query_words:
                if qw in desc:
                    risk_scores[r_id] += 0.5
                    if "자연어 내용 매칭" not in risk_matches[r_id]:
                        risk_matches[r_id].append("자연어 내용 매칭")

    if not risk_scores:
        st.info("👈 좌측 사이드바에서 조건을 선택하거나, 자연어로 자유롭게 질문해 보세요!")
    else:
        # 점수 순 내림차순 정렬
        sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_risks[0][1] if sorted_risks else 0
        
        # 완벽 매칭(핵심)과 부분 매칭 분리: 이제 최고 점수가 무조건 핵심 리스크!
        perfect_matches = [(r_id, s) for r_id, s in sorted_risks if s == max_score]
        partial_matches = [(r_id, s) for r_id, s in sorted_risks if s < max_score]
        
        st.subheader(f"🎯 AI 지능형 매칭 분석 결과")
        
        # 1. 완벽 매칭 핵심 리스크 UI (붉은색 강조)
        if perfect_matches:
            st.markdown("### 🔥 :red[가장 연관성이 높은 핵심 리스크 (최고 점수)]")
            for r_id, score in perfect_matches[:10]:
                r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
                matched_tags = " + ".join(risk_matches[r_id])
                
                st.error(f"🚨 **{r_desc}** (매칭 근거: {matched_tags})")
                
                with st.expander(f"↳ 🛠️ 핵심 리스크 해결 대책 보기"):
                    strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                    strats = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()
                    if strats:
                        for s in strats:
                            st.success(f"✅ {s}")
                    else:
                        st.warning("등록된 해결 대책이 없습니다.")
        
        # 2. 부분 매칭 리스크 UI
        if partial_matches:
            st.markdown("---")
            st.markdown("### ⚠️ 부분 연관 리스크 (참고용)")
            for r_id, score in partial_matches[:10]:
                r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
                matched_tags = " + ".join(risk_matches[r_id])
                
                with st.expander(f"🔸 {r_desc} (매칭 근거: {matched_tags})"):
                    strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                    strats = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()
                    if strats:
                        for s in strats:
                            st.info(f"✔️ {s}")
                    else:
                        st.warning("등록된 해결 대책이 없습니다.")

        # 지식 그래프 시각화 
        st.markdown("---")
        st.subheader("🕸️ 연관 지식 그래프")
        
        net = Network(height='500px', width='100%', bgcolor='#ffffff', font_color='black')
        
        # 조건 노드 렌더링
        for t_id, (t_label, t_color) in target_nodes.items():
            net.add_node(t_id, label="검색 조건", title=t_label, color=t_color, size=30)
        
        # 리스크 렌더링
        for r_id, score in sorted_risks[:15]:
            r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
            
            if score == max_score:
                net.add_node(r_id, label="핵심 Risk!", title=r_desc, color='#ff4757', size=45)
            else:
                net.add_node(r_id, label="Risk", title=r_desc, color='#ffeaa7', size=20)
            
            # 조건 -> 리스크 엣지 연결
            for t_id, (t_label, _) in target_nodes.items():
                if t_label in risk_matches[r_id]:
                    edge_width = 3 if score == max_score else 1
                    net.add_edge(t_id, r_id, title="MATCHED", width=edge_width)
                
            # 리스크 -> 대책 엣지 연결 (핵심 리스크 위주)
            if score == max_score:
                strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                for s_id in strat_ids[:3]: 
                    s_label = df_strat[df_strat['id:ID'] == s_id]['action'].values[0]
                    net.add_node(s_id, label="Strategy", title=s_label, color='#2ed573', size=15)
                    net.add_edge(r_id, s_id, title="MITIGATED")

        net.save_graph('temp_graph.html')
        with open('temp_graph.html', 'r', encoding='utf-8') as f:
            components.html(f.read(), height=520)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
