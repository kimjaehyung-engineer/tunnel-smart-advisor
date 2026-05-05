import streamlit as st
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import re
from collections import defaultdict

# 웹 페이지 기본 설정
st.set_page_config(page_title="Tunnel Smart Advisor", layout="wide", page_icon="🏗️", initial_sidebar_state="expanded")

def inject_custom_css():
    st.markdown("""
        <style>
        /* 프리미엄 폰트 적용 (Pretendard) */
        @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
        
        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        }
        
        /* 거슬리는 기본 UI 요소 숨기기 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 메인 컨테이너 최적화 */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px;
        }
        
        /* 타이틀 스타일링 */
        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -1px;
            margin-bottom: 0.2rem;
        }
        .sub-title {
            font-size: 1.1rem;
            color: #64748b;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* 메트릭(통계) 카드 디자인 */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* 완벽 매칭 핵심 리스크 커스텀 박스 */
        .core-risk-box {
            background-color: #fff1f2;
            border-left: 5px solid #e11d48;
            padding: 1.2rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            margin-top: 1rem;
            box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05);
        }
        .core-risk-title {
            color: #be123c;
            font-weight: 700;
            font-size: 1.15rem;
            margin-bottom: 0.4rem;
        }
        .core-risk-desc {
            color: #881337;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        /* 부분 매칭 일반 박스 */
        .partial-risk-box {
            background-color: #f8fafc;
            border-left: 5px solid #cbd5e1;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            margin-top: 1rem;
        }
        .partial-risk-title {
            color: #334155;
            font-weight: 600;
            font-size: 1.05rem;
            margin-bottom: 0.4rem;
        }
        
        /* 닫혀있는 Selectbox의 텍스트 (배경이 네이비이므로 흰색) */
        div[data-baseweb="select"] * {
            color: #ffffff !important;
        }
        /* 펼쳐진 드롭다운 리스트의 텍스트 (배경이 흰색이므로 네이비) */
        div[data-baseweb="popover"] * {
            color: #0f172a !important;
        }
        ul[role="listbox"] * {
            color: #0f172a !important;
        }
        li[role="option"] span {
            color: #0f172a !important;
        }
        textarea {
            color: #0f172a !important;
            background-color: #ffffff !important;
        }
        
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

@st.cache_data
def load_data():
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

st.markdown('<div class="main-title">Tunnel Engineering Smart Advisor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-Powered Risk Intelligence & Knowledge Graph for Tunnel Construction</div>', unsafe_allow_html=True)

try:
    df_ground, df_method, df_equip, df_risk, df_proc, df_loc, df_strat, df_rels = load_data()
    
    proc_names = sorted(df_proc['name'].dropna().tolist(), key=natural_sort_key)
    ground_names = sorted(df_ground['condition_name'].dropna().tolist(), key=natural_sort_key)
    loc_names = sorted(df_loc['loc_name'].dropna().tolist(), key=natural_sort_key)
    
    with st.container():
        st.markdown("### 🔍 AI 현장 조건 및 텍스트 분석기")
        
        # 데스크톱에서는 3단 가로 배치, 모바일에서는 자동 세로 배치
        col_cond1, col_cond2, col_cond3 = st.columns(3)
        sel_proc = col_cond1.selectbox("1. Process (공종)", ["[상관없음/전체]"] + proc_names)
        sel_ground = col_cond2.selectbox("2. Ground (지반)", ["[상관없음/전체]"] + ground_names)
        sel_loc = col_cond3.selectbox("3. Location (위치)", ["[상관없음/전체]"] + loc_names)
        
        user_query = st.text_area(
            "💬 Semantic Search (자유 형식 자연어 검색)", 
            placeholder="현장 상황을 자유롭게 입력하세요. (예: 도심지 갱구부에서 굴착 중 파쇄대 조우 시 대책)",
            height=100
        )
        go_clicked = st.button("🚀 GO (분석 실행)", use_container_width=True)
        
    st.markdown("---")
    
    risk_scores = defaultdict(float)
    risk_matches = defaultdict(list)
    target_nodes = {}
    
    def apply_filter(node_id, node_label, color, rel_type):
        if node_id not in target_nodes:
            target_nodes[node_id] = (node_label, color)
            r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
            for r_id in r_ids:
                risk_scores[r_id] += 1.0
                if node_label not in risk_matches[r_id]:
                    risk_matches[r_id].append(node_label)
                    
    # 드롭다운 필터 적용
    if sel_proc != "[상관없음/전체]":
        p_id = df_proc[df_proc['name'] == sel_proc]['id:ID'].values[0]
        apply_filter(p_id, sel_proc, '#3b82f6', 'ENCOUNTERS')
            
    if sel_ground != "[상관없음/전체]":
        g_id = df_ground[df_ground['condition_name'] == sel_ground]['id:ID'].values[0]
        apply_filter(g_id, sel_ground, '#3b82f6', 'TRIGGER')
            
    if sel_loc != "[상관없음/전체]":
        l_id = df_loc[df_loc['loc_name'] == sel_loc]['id:ID'].values[0]
        apply_filter(l_id, sel_loc, '#3b82f6', 'OCCURS_AT')

    # 자연어 필터 적용
    if user_query:
        query_words = [w for w in re.split(r'\W+', user_query) if len(w) >= 2]
        
        for _, row in df_proc.dropna(subset=['name']).iterrows():
            name = row['name']
            clean = re.sub(r'^\d+\.\s*', '', name)
            for cw in clean.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_filter(row['id:ID'], name, '#8b5cf6', 'ENCOUNTERS')
                    break
                    
        for _, row in df_ground.dropna(subset=['condition_name']).iterrows():
            name = row['condition_name']
            if name in user_query or (len(name)>=2 and name[:2] in user_query):
                apply_filter(row['id:ID'], name, '#8b5cf6', 'TRIGGER')
                
        for _, row in df_loc.dropna(subset=['loc_name']).iterrows():
            name = row['loc_name']
            for cw in name.split():
                if len(cw) >= 2 and cw in user_query:
                    apply_filter(row['id:ID'], name, '#8b5cf6', 'OCCURS_AT')
                    break
                    
        for _, row in df_risk.dropna(subset=['description']).iterrows():
            r_id = row['id:ID']
            desc = row['description']
            for qw in query_words:
                if qw in desc:
                    risk_scores[r_id] += 0.5
                    if "자연어 내용 매칭" not in risk_matches[r_id]:
                        risk_matches[r_id].append("자연어 내용 매칭")

    if not risk_scores:
        st.info("👈 좌측 패널에서 현장 조건을 세팅하거나 질문을 입력하여 분석을 시작하세요.")
    else:
        sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_risks[0][1] if sorted_risks else 0
        
        perfect_matches = [(r_id, s) for r_id, s in sorted_risks if s == max_score]
        partial_matches = [(r_id, s) for r_id, s in sorted_risks if s < max_score]
        
        # 대시보드 메트릭 출력
        col1, col2, col3 = st.columns(3)
        col1.metric("총 식별된 위험 요소 (Risks Found)", f"{len(sorted_risks)} 건")
        col2.metric("최상위 핵심 위험 (Critical)", f"{len(perfect_matches)} 건")
        col3.metric("알고리즘 최고 매칭률", f"{max_score} Score")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. AI 답변 요약 (새로 추가)
        st.markdown("### 💡 AI 분석 요약")
        summary_tags = set()
        for matches in risk_matches.values():
            for m in matches:
                summary_tags.add(m)
        
        if summary_tags:
            tag_str = ", ".join([f"**[{t}]**" for t in summary_tags])
            st.info(f"입력하신 현장 조건 및 텍스트에서 {tag_str} 키워드가 식별되었습니다. 이를 바탕으로 총 **{len(sorted_risks)}건**의 잠재적 위험 요소가 분석되었으며, 특히 **{len(perfect_matches)}건**의 핵심 위험에 대한 우선적인 대비가 권장됩니다.")
        else:
            st.info(f"분석 결과 총 **{len(sorted_risks)}건**의 잠재적 위험 요소가 식별되었습니다.")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Risk Intelligence Report (가로로 꽉 차게)
        st.markdown("### 📄 Risk Intelligence Report")
        
        if perfect_matches:
            for r_id, score in perfect_matches[:10]:
                r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
                matched_tags = " | ".join(risk_matches[r_id])
                
                st.markdown(f'''
                    <div class="core-risk-box" style="width: 100%;">
                        <div class="core-risk-title">🚨 {r_desc}</div>
                        <div class="core-risk-desc">매칭 근거: {matched_tags}</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                with st.expander("🛠️ 현장 설계 및 시공 대책 보기"):
                    strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                    strats = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()
                    if strats:
                        for s in strats:
                            st.markdown(f"- {s}")
                    else:
                        st.write("등록된 세부 대책 데이터가 없습니다.")
        
        if partial_matches:
            st.markdown("<br>#### ⚠️ 참고 위험 요소 (Partial Match)", unsafe_allow_html=True)
            for r_id, score in partial_matches[:5]:
                r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
                matched_tags = " | ".join(risk_matches[r_id])
                
                st.markdown(f'''
                    <div class="partial-risk-box" style="width: 100%;">
                        <div class="partial-risk-title">🔸 {r_desc}</div>
                        <div style="color: #64748b; font-size: 0.85rem;">매칭 근거: {matched_tags}</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                with st.expander("세부 대책 보기"):
                    strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                    strats = df_strat[df_strat['id:ID'].isin(strat_ids)]['action'].tolist()
                    if strats:
                        for s in strats:
                            st.markdown(f"- {s}")
                    else:
                        st.write("등록된 세부 대책 데이터가 없습니다.")

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # 3. 지식 그래프 (그 아래에 가로로 꽉 차게)
        st.markdown("### 🕸️ Knowledge Graph Topology")
            
        net = Network(height='700px', width='100%', bgcolor='#f8fafc', font_color='#0f172a')
        # 물리 엔진 부드럽게 조정
        net.repulsion(node_distance=150, spring_length=200)
        
        for t_id, (t_label, t_color) in target_nodes.items():
            net.add_node(t_id, label="Condition", title=t_label, color=t_color, size=35)
        
        for r_id, score in sorted_risks[:10]:
            r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
            
            if score == max_score:
                net.add_node(r_id, label="Critical Risk", title=r_desc, color='#e11d48', size=45)
            else:
                net.add_node(r_id, label="Risk", title=r_desc, color='#cbd5e1', size=25)
            
            for t_id, (t_label, _) in target_nodes.items():
                if t_label in risk_matches[r_id]:
                    edge_width = 4 if score == max_score else 1
                    net.add_edge(t_id, r_id, title="RELATES_TO", width=edge_width, color='#94a3b8')
                
            if score == max_score:
                strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                for s_id in strat_ids[:2]: 
                    s_label = df_strat[df_strat['id:ID'] == s_id]['action'].values[0]
                    net.add_node(s_id, label="Strategy", title=s_label, color='#10b981', size=20)
                    net.add_edge(r_id, s_id, title="MITIGATED", color='#6ee7b7')

        net.save_graph('temp_graph.html')
        with open('temp_graph.html', 'r', encoding='utf-8') as f:
            components.html(f.read(), height=720)

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
