import csv
import re
import os

def generate_rail_neo4j(input_path):
    # Data points extracted from 철도지하철팀_text.txt
    data_points = [
        {
            "proj": "동대구-영천 4공구",
            "proc": "공기연장 간접비 청구",
            "risk": "선행공구 토공구간 교량화 민원 등에 따른 공기 지연",
            "failure": "‘18.11 대법원 판결(차수별 기간 内 청구만 인정)로 발주처 협의 부정적",
            "lesson": "운행선 공사 시 신설공사와 달리 추가 RISK 검토 절차 필요",
            "strategy": "기존 운행선 인접공사 견적 시 할증 반영 및 세부 시공계획 검토"
        },
        {
            "proj": "동대구-영천 4공구",
            "proc": "하도급사 부도타절",
            "risk": "하도급사 부도징후 사전파악 실패",
            "failure": "토공 및 구조물 하도급사 부도 타절로 인한 미체불금액 발생",
            "lesson": "하도급사 부도징후 및 미체불관리 철저",
            "strategy": "일일투자분석 시행으로 적자여부 확인 및 초기대응 실시"
        },
        {
            "proj": "중앙선 도담-영천 3공구",
            "proc": "터널보조공법 변경",
            "risk": "지반조사 부족 및 과다설계 논란",
            "failure": "발주처의 과다설계 문제점 제기 및 전면 재설계 요구",
            "lesson": "충분한 지반조사 후 터널보조공법 선정 필요",
            "strategy": "지질 및 터널 전문가 배치를 통한 상세 공사관리"
        },
        {
            "proj": "중앙선 도담-영천 3공구",
            "proc": "부벽식 옹벽 공법 변경",
            "risk": "부벽식 옹벽 시공 시 인접 운행선 변위 위험 및 작업효율 저하",
            "failure": "연약지반 내 구조물 설치 지연 및 민원 발생 위험",
            "lesson": "현장여건에 따른 공정지연요소 분석 및 적자공종 배제한 공법선정",
            "strategy": "U-type 구조물로 공법 변경하여 안전성 확보 및 공기 단축"
        },
        {
            "proj": "중앙선 도담-영천 6공구",
            "proc": "하도급사 선정",
            "risk": "입찰 검토 시 투찰오류로 인한 준공 시 적자 예상",
            "failure": "하도업체 선정 시 적자 발생 의견 제출에도 최저가 업체 계약 진행",
            "lesson": "입찰경험 및 유사현장 경험있는 입찰조직 구성",
            "strategy": "P6 활용한 공정계획 Baseline 준수여부 일일확인"
        },
        {
            "proj": "신림선 경전철 2공구",
            "proc": "기존 교량 하부통과",
            "risk": "봉천교 설계 및 준공도서 부재",
            "failure": "설계도서 없어 시공 및 안전 리스크 증대 (말뚝기초 절단 위험)",
            "lesson": "설계단계부터 기존 구조물 및 지장물 철저 현황조사 수행",
            "strategy": "정밀 안전진단 및 자문의견 수렴 후 통과공법 변경"
        },
        {
            "proj": "서해선 홍성-송산 5공구",
            "proc": "공기연장 간접비 청구",
            "risk": "보상지연에 따른 공기연장 (50개월 -> 68개월)",
            "failure": "대법원 판결에 따라 차수별 기간 내 청구만 인정되어 난항 예상",
            "lesson": "보상 대상물 및 인허가 등 공기지연요소 사전파악 후 설계반영 필요",
            "strategy": "서해선 사업 시공사 공동대응 및 선제적 클레임"
        },
        {
            "proj": "서해선 홍성-송산 5공구",
            "proc": "터널 굴착",
            "risk": "화리현터널 저토피구간 지표침하 발생",
            "failure": "상반굴착 중 지표침하 54mm 발생으로 인한 강지보 보강 및 굴착 중지",
            "lesson": "설계 시 충분한 지반조사를 통한 지반여건 파악 필요",
            "strategy": "안정성 확보 용역 수행 및 보강 방안 수립"
        },
        {
            "proj": "삼성-동탄 광역급행 2공구",
            "proc": "상부거더공법 선정",
            "risk": "입찰 시 반영된 특허공법의 비효율성",
            "failure": "특허공법 사용 시 원가율 및 시공성 불량 우려",
            "lesson": "특허 이외 원가개선 일반공법 적용성 적극 검토 필요",
            "strategy": "V-BEAM 대신 IT & IPC Girder 공법으로 설계변경 추진"
        },
        {
            "proj": "울산-포항 2공구",
            "proc": "터널 전구간 보완설계",
            "risk": "당초 설계와 상이한 터널 지질조건 (대규모 단층파쇄대)",
            "failure": "굴착 진행 불가 및 사갱 접속부 대규모 붕락 발생",
            "lesson": "충분한 지반조사 수량 및 조사항목 반영 필요",
            "strategy": "외부전문가 검증을 통한 설계변경 타당성 확보 및 총사업비 증액"
        }
    ]

    # Node and Relationship storage
    projects = {}
    processes = {}
    risks = {}
    lessons = {}
    strategies = {}
    rels = []

    for i, d in enumerate(data_points):
        p_name = d['proj']
        if p_name not in projects:
            pid = f"Proj_{len(projects)+1}"
            projects[p_name] = [pid, p_name, "Project"]
        pid = projects[p_name][0]

        proc_name = d['proc']
        # WorkProcess might be unique to project or shared. Here we treat as unique per entry for detail
        wid = f"Proc_{i+1}"
        processes[wid] = [wid, proc_name, "WorkProcess"]

        rid = f"Risk_{i+1}"
        risks[rid] = [rid, d['risk'], d['failure'], "Risk"]

        lid = f"Lesson_{i+1}"
        lessons[lid] = [lid, d['lesson'], "LessonLearned"]

        sid = f"Strat_{i+1}"
        strategies[sid] = [sid, d['strategy'], "HedgeStrategy"]

        # Define Relationships
        rels.append([pid, wid, "HAS_PROCESS"])
        rels.append([wid, rid, "ENCOUNTERS"])
        rels.append([rid, lid, "LEARNED_AS"])
        rels.append([rid, sid, "MITIGATED_BY"])
        rels.append([wid, lid, "MUST_CHECK"])

    # Helper to write CSV
    def write_csv(filename, header, rows):
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    # Output directory
    output_dir = os.path.join(os.path.dirname(input_path), 'neo4j_import')
    os.makedirs(output_dir, exist_ok=True)
    
    write_csv(os.path.join(output_dir, 'nodes_project.csv'), ['id:ID', 'name', ':LABEL'], projects.values())
    write_csv(os.path.join(output_dir, 'nodes_process.csv'), ['id:ID', 'name', ':LABEL'], processes.values())
    write_csv(os.path.join(output_dir, 'nodes_risk.csv'), ['id:ID', 'description', 'failure_case', ':LABEL'], risks.values())
    write_csv(os.path.join(output_dir, 'nodes_lesson.csv'), ['id:ID', 'content', ':LABEL'], lessons.values())
    write_csv(os.path.join(output_dir, 'nodes_strategy.csv'), ['id:ID', 'action', ':LABEL'], strategies.values())
    write_csv(os.path.join(output_dir, 'rels.csv'), [':START_ID', ':END_ID', ':TYPE'], rels)

    print(f"Successfully generated {len(data_points)} rail/subway cases into Neo4j CSV files.")

if __name__ == "__main__":
    generate_rail_neo4j(r'c:\Users\sskjh\OneDrive\문서\antigravity\온톨로지\철도지하철팀_text.txt')
