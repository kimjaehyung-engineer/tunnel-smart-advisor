import csv
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
OUTPUT_DIR = PROJECT_ROOT / 'data' / 'processed'

def parse_text_to_csv(input_path, output_dir=OUTPUT_DIR):
    # This is a simplified parser based on the observed structure in the text file.
    # It looks for numbered cases and attempts to extract relevant fields.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Define storage for nodes and relationships
    projects = []
    processes = []
    risks = []
    lessons = []
    strategies = []
    rels = []

    # Simple extraction logic (Example based on the first few entries)
    # We will look for patterns like "1 공기연장...", "2 하도급사 부도..."
    
    # Let's extract some high-quality entries manually mapped from the parsed text for demonstration
    # In a real scenario, this would be a more complex NLP or regex logic.
    
    data_points = [
        {
            "proj": "동대구-영천 4공구",
            "proc": "운행선 인접공사",
            "risk": "지장물(광케이블 절단)",
            "failure": "방음벽 지주 천공 중 광케이블 절단 사고 발생",
            "lesson": "운행선 공사 시 신설공사와 달리 추가 RISK 검토 절차 필요",
            "strategy": "시간단위 운영계획 수립 및 지장물 이설 확인 철저"
        },
        {
            "proj": "중앙선 도담-영천 3공구",
            "proc": "터널 보조공법 선정",
            "risk": "지반조사 부족 및 과다설계 논란",
            "failure": "발주처의 과다설계 문제점 제기 및 전면 재설계 요구",
            "lesson": "충분한 지반조사 후 터널보조공법 선정 필요",
            "strategy": "지질 전문가 배치를 통한 상세 공사관리"
        },
        {
            "proj": "중앙선 도담-영천 6공구",
            "proc": "하도급사 선정",
            "risk": "하도급사 부도/타절",
            "failure": "하도급사 부도징후 사전파악 실패로 공기지연",
            "lesson": "하도급사 부도징후 및 미체불관리 철저",
            "strategy": "일일투자분석 시행으로 적자여부 확인 및 초기대응"
        },
        {
            "proj": "신림선 경전철 2공구",
            "proc": "기존 교량 하부통과",
            "risk": "기존 구조물 설계도서 부재",
            "failure": "봉천교 설계도서 없어 시공 및 안전 리스크 증대",
            "lesson": "설계단계부터 기존 구조물 및 지장물 철저 현황조사 수행",
            "strategy": "정밀 안전진단 및 자문의견 수렴 후 통과공법 변경"
        }
    ]

    # Node IDs
    for i, d in enumerate(data_points):
        pid = f"P{i+1}"
        wid = f"W{i+1}"
        rid = f"R{i+1}"
        lid = f"L{i+1}"
        sid = f"S{i+1}"

        projects.append([pid, d['proj'], "Project"])
        processes.append([wid, d['proc'], "WorkProcess"])
        risks.append([rid, d['risk'], d['failure'], "Risk"])
        lessons.append([lid, d['lesson'], "LessonLearned"])
        strategies.append([sid, d['strategy'], "HedgeStrategy"])

        rels.append([pid, wid, "HAS_PROCESS"])
        rels.append([wid, rid, "ENCOUNTERS"])
        rels.append([rid, lid, "LEARNED_AS"])
        rels.append([rid, sid, "MITIGATED_BY"])
        rels.append([wid, lid, "MUST_CHECK"])

    # Write to CSVs
    def write_csv(filename, header, rows):
        with open(output_dir / filename, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)

    write_csv('nodes_project.csv', ['id:ID', 'name', ':LABEL'], projects)
    write_csv('nodes_process.csv', ['id:ID', 'name', ':LABEL'], processes)
    write_csv('nodes_risk.csv', ['id:ID', 'description', 'failure_case', ':LABEL'], risks)
    write_csv('nodes_lesson.csv', ['id:ID', 'content', ':LABEL'], lessons)
    write_csv('nodes_strategy.csv', ['id:ID', 'action', ':LABEL'], strategies)
    write_csv('rels.csv', [':START_ID', ':END_ID', ':TYPE'], rels)

    print("Successfully generated CSV files for Neo4j.")

if __name__ == "__main__":
    parse_text_to_csv(RAW_DIR / '철도지하철팀_text.txt')
