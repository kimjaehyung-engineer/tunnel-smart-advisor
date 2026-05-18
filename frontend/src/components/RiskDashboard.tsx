import type { ScoreResponse } from '../types';

export default function RiskDashboard({ data }: { data: ScoreResponse | null }) {
  if (!data) {
    return <div className="empty-state">조건을 선택하거나 자연어를 입력한 뒤 분석을 실행하세요.</div>;
  }

  if (data.total_risks === 0) {
    return <div className="empty-state">분석은 완료됐지만 매칭된 위험 요소가 없습니다. 조건을 바꾸거나 자연어를 더 구체적으로 입력해보세요.</div>;
  }

  return (
    <section className="dashboard">
      <div className="metric-grid">
        <Metric label="총 식별된 위험 요소" value={`${data.total_risks} 건`} />
        <Metric label="최상위 핵심 위험" value={`${data.critical_count} 건`} />
        <Metric label="최고 위험도 스코어" value={`${data.max_score.toLocaleString()} 점`} />
      </div>
      <div className="summary-box">
        총 <strong>{data.total_risks}</strong>건의 잠재 위험을 분석했습니다. 상위 위험은 그래프에서 우선 확인하세요.
      </div>
      <div className="risk-list">
        {data.risks.map((risk) => (
          <article className="risk-card" key={risk.id} style={{ borderLeftColor: risk.color }}>
            <div className="risk-card-main">
              <h3>[{risk.level}] {risk.description}</h3>
              <p>매칭 근거: {risk.matched || '조건 매칭 없음'}</p>
              {risk.strategies.length > 0 && (
                <details>
                  <summary>🛠️ 현장 설계 및 시공 대책 보기</summary>
                  <ul>{risk.strategies.map((strategy, index) => <li key={index}>{strategy}</li>)}</ul>
                </details>
              )}
            </div>
            <div className="score-badge" style={{ color: risk.color, borderColor: risk.color }}>
              <span>RISK SCORE</span>
              <strong>{risk.score.toLocaleString()}</strong>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
