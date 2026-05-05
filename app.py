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
    
    risk_scores = defaultdict(lambda: 1.0)
    risk_matches = defaultdict(list)
    target_nodes = {}
    
    def apply_filter(node_id, node_label, color, rel_type):
        if node_id not in target_nodes:
            target_nodes[node_id] = (node_label, color)
            r_ids = df_rels[(df_rels[':START_ID'] == node_id) & (df_rels[':TYPE'] == rel_type)][':END_ID'].tolist()
            degree = len(r_ids)
            if degree == 0:
                degree = 1
            for r_id in r_ids:
                risk_scores[r_id] *= degree
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
                    risk_scores[r_id] *= 2.0
                    if "자연어 내용 매칭" not in risk_matches[r_id]:
                        risk_matches[r_id].append("자연어 내용 매칭")

    if not risk_scores:
        st.info("👈 좌측 패널에서 현장 조건을 세팅하거나 질문을 입력하여 분석을 시작하세요.")
    else:
        sorted_risks = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_risks[0][1] if sorted_risks else 0
        
        total_risks = len(sorted_risks)
        risk_levels = {}
        for idx, (r_id, s) in enumerate(sorted_risks):
            percentile = (idx + 1) / total_risks
            if percentile <= 0.05:
                risk_levels[r_id] = ("최상위 위험", "#ef4444")  # Red
            elif percentile <= 0.20:
                risk_levels[r_id] = ("상위 위험", "#f97316")  # Orange
            elif percentile <= 0.50:
                risk_levels[r_id] = ("중위험", "#eab308")     # Yellow
            else:
                risk_levels[r_id] = ("저위험", "#22c55e")     # Green
                
        critical_count = sum(1 for l, c in risk_levels.values() if l == "최상위 위험")
        
        # 대시보드 메트릭 출력
        col1, col2, col3 = st.columns(3)
        col1.metric("총 식별된 위험 요소 (Risks Found)", f"{total_risks} 건")
        col2.metric("최상위 핵심 위험 (Critical)", f"{critical_count} 건")
        col3.metric("최고 위험도 스코어 (Max Risk Score)", f"{max_score:,.1f} 점")
        
        st.caption("ℹ️ **최고 위험도 스코어란?** 선택한 조건들이 가지고 있는 과거 리스크 발생 건수(빈도)를 조합하여 산출한 정량적 위험도입니다. *(상위 5%: 최상위, 20%: 상위, 50%: 중위험)*")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. AI 답변 요약 (새로 추가)
        st.markdown("### 💡 AI 분석 요약")
        summary_tags = set()
        for matches in risk_matches.values():
            for m in matches:
                summary_tags.add(m)
        
        if summary_tags:
            tag_str = ", ".join([f"**[{t}]**" for t in summary_tags])
            st.info(f"입력하신 현장 조건 및 텍스트에서 {tag_str} 키워드가 식별되었습니다. 이를 바탕으로 총 **{total_risks}건**의 잠재적 위험 요소가 분석되었으며, 특히 **{critical_count}건**의 최상위 핵심 위험에 대한 우선적인 대비가 권장됩니다.")
        else:
            st.info(f"분석 결과 총 **{total_risks}건**의 잠재적 위험 요소가 식별되었습니다.")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Risk Intelligence Report (가로로 꽉 차게)
        st.markdown("### 📄 Risk Intelligence Report")
        
        for r_id, score in sorted_risks[:15]:
            r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
            matched_tags = " | ".join(risk_matches[r_id])
            
            level_text, level_color = risk_levels[r_id]
            if level_text == "최상위 위험":
                icon = "🚨"
            elif level_text == "상위 위험":
                icon = "🔸"
            elif level_text == "중위험":
                icon = "⚡"
            else:
                icon = "✅"
                
            st.markdown(f'''
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; padding: 16px; background-color: white; border-left: 6px solid {level_color}; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="flex: 1; padding-right: 20px;">
                        <div style="font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-bottom: 6px;">{icon} [{level_text}] {r_desc}</div>
                        <div style="color: #64748b; font-size: 0.85rem; margin: 0;">매칭 근거: {matched_tags}</div>
                    </div>
                    <div style="flex-shrink: 0; text-align: center; background: white; padding: 8px 16px; border-radius: 8px; border: 2px solid {level_color};">
                        <div style="font-size: 0.7rem; color: {level_color}; font-weight: 800; letter-spacing: 0.5px;">RISK SCORE</div>
                        <div style="font-size: 1.4rem; color: {level_color}; font-weight: 900; line-height: 1.2;">{score:,.1f}</div>
                    </div>
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

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # 3. 지식 그래프 (그 아래에 가로로 꽉 차게)
        st.markdown("### 🕸️ Knowledge Graph Topology")
        
        st.markdown('''
            <div style="background-color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; font-size: 0.85rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">
                <div style="font-weight: 700; margin-bottom: 8px; color: #1e293b;">📌 그래프 범례 (Legend)</div>
                <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 8px; color: #475569;">
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #3b82f6;"></div> 기본 조건</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #8b5cf6;"></div> 검색 조건</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #ef4444;"></div> 최상위 위험</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #f97316;"></div> 상위 위험</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #eab308;"></div> 중위험</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #22c55e;"></div> 저위험</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 12px; height: 12px; border-radius: 50%; background-color: #10b981;"></div> 대응 대책</div>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 16px; border-top: 1px solid #e2e8f0; padding-top: 8px; color: #475569;">
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 20px; height: 4px; background-color: #94a3b8; border-radius: 2px;"></div> 위험의 원인/연관 (RELATES_TO)</div>
                    <div style="display: flex; align-items: center; gap: 6px;"><div style="width: 20px; height: 4px; background-color: #6ee7b7; border-radius: 2px;"></div> 위험의 해결/저감 (MITIGATED)</div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
            
        net = Network(height='500px', width='100%', bgcolor='#f8fafc', font_color='#0f172a')
        # 물리 엔진 부드럽게 조정
        net.repulsion(node_distance=150, spring_length=200)
        
        for t_id, (t_label, t_color) in target_nodes.items():
            net.add_node(t_id, label="Condition", title=t_label, color=t_color, size=35)
        
        for r_id, score in sorted_risks[:10]:
            r_desc = df_risk[df_risk['id:ID'] == r_id]['description'].values[0]
            level_text, level_color = risk_levels[r_id]
            
            is_critical = (level_text == "최상위 위험")
            
            if is_critical:
                net.add_node(r_id, label="Critical Risk", title=r_desc, color=level_color, size=45)
            else:
                net.add_node(r_id, label="Risk", title=r_desc, color=level_color, size=25)
            
            for t_id, (t_label, _) in target_nodes.items():
                if t_label in risk_matches[r_id]:
                    edge_width = 4 if is_critical else 1
                    net.add_edge(t_id, r_id, title="RELATES_TO", width=edge_width, color='#94a3b8')
                
            if is_critical:
                strat_ids = df_rels[(df_rels[':START_ID'] == r_id) & (df_rels[':TYPE'] == 'MITIGATED_BY')][':END_ID'].tolist()
                for s_id in strat_ids[:2]: 
                    s_label = df_strat[df_strat['id:ID'] == s_id]['action'].values[0]
                    net.add_node(s_id, label="Strategy", title=s_label, color='#10b981', size=20)
                    net.add_edge(r_id, s_id, title="MITIGATED", color='#6ee7b7')

        net.save_graph('temp_graph.html')
        with open('temp_graph.html', 'r', encoding='utf-8') as f:
            components.html(f.read(), height=520)

except Exception as e:
    st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
