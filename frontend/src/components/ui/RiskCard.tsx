import Badge from './Badge';

interface Risk {
  id: string;
  level: string;
  levelRaw?: string;
  description: string;
  score: number;
  color: string;
  cluster_band?: string;
  cluster_label?: string;
  matched: string;
  strategies: string[];
  standards?: string[];
  roles?: string[];
}

interface RiskCardProps {
  risk: Risk;
  rank?: number;
  onViewDetail?: (id: string) => void;
}

const levelVariantMap: Record<string, 'danger' | 'warning' | 'success' | 'info'> = {
  '최상위 위험': 'danger',
  '위험': 'warning',
  '보통': 'info',
  '낮음': 'success',
};

export default function RiskCard({ risk, rank, onViewDetail }: RiskCardProps) {
  const levelKey = risk.level.replace(/\s*\(\d+%\)/, '').trim();
  const variant = levelVariantMap[levelKey] ?? 'info';

  return (
    <article className="risk-card" style={{ borderLeftColor: risk.color }}>
      {rank && <span className="risk-rank">#{rank}</span>}
      <div className="risk-content">
        <div className="risk-header">
          <Badge variant={variant}>{risk.level}</Badge>
          {risk.cluster_band && <Badge variant="info">{risk.cluster_label ?? risk.cluster_band}</Badge>}
          <span className="risk-score-label">위험도</span>
          <strong className="risk-score" style={{ color: risk.color }}>{risk.score.toLocaleString()}</strong>
        </div>
        <h3 className="risk-title">{risk.description}</h3>
        <p className="risk-matched">매칭 근거: {risk.matched || '조건 매칭 없음'}</p>
        {risk.strategies.length > 0 && (
          <details className="risk-strategies">
            <summary>🛠️ 현장 설계 및 시공 대책 보기</summary>
            <ul>
              {risk.strategies.map((strategy, index) => (
                <li key={index}>{strategy}</li>
              ))}
            </ul>
          </details>
        )}
        {((risk.standards?.length ?? 0) > 0 || (risk.roles?.length ?? 0) > 0) && (
          <div className="risk-matched">
            {risk.standards?.length ? `기준: ${risk.standards.slice(0, 2).join(', ')}` : ''}
            {risk.standards?.length && risk.roles?.length ? ' · ' : ''}
            {risk.roles?.length ? `담당: ${risk.roles.slice(0, 2).join(', ')}` : ''}
          </div>
        )}
      </div>
      <div className="risk-actions">
        <button className="risk-detail-btn" onClick={() => onViewDetail?.(risk.id)}>
          상세 보기
        </button>
      </div>
    </article>
  );
}
