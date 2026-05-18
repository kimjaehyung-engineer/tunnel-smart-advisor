import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import MetricCard from '../components/ui/MetricCard';
import { useDashboardSummary } from '../api/queries';
import type { DashboardDistributionItem } from '../types';

export default function Dashboard() {
  const { data, isLoading, error } = useDashboardSummary();

  return (
    <div className="dashboard-page">
      <PageHeader
        title="대시보드"
        description="백엔드 CSV 온톨로지 기준의 위험 지식 현황을 확인하세요."
      />

      {isLoading && <div className="empty-state">백엔드에서 대시보드 데이터를 불러오는 중입니다...</div>}
      {error && <div className="empty-state">대시보드 데이터를 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}

      {data && (
        <>
          <div className="dashboard-kpi-row">
            {data.kpis.map((kpi) => (
              <MetricCard
                key={kpi.label}
                label={kpi.label}
                value={kpi.value}
                subValue={kpi.subValue}
                accentColor={kpi.accentColor}
              />
            ))}
          </div>

          <div className="dashboard-charts-row">
            <Card title="위험 연결도 추이" subtitle="백엔드 관계 그래프 상위 6개 위험 기준">
              <TrendChart data={data.trend} />
            </Card>
            <Card title="위험 분포" subtitle="CSV 관계 수 기반 분포">
              <DonutChart segments={data.distribution} />
            </Card>
            <Card title="영향 유형 분포" subtitle="AFFECTS 관계 기반 영향 유형">
              <DonutChart segments={data.impactDistribution ?? []} />
            </Card>
          </div>

          <div className="dashboard-bottom-row">
            <Card title="주요 위험 지식" action={<a href="/workspace" className="card-link">분석하기</a>}>
              <div className="recent-list">
                {data.recentAnalyses.map((item, idx) => (
                  <div key={item.id} className="recent-item">
                    <div className="recent-item-content">
                      <span className="recent-title">{item.title}</span>
                      <span className="recent-time">{item.project || '프로젝트 정보 없음'}</span>
                    </div>
                    <span className={`recent-score ${idx === 0 ? 'critical' : idx === 1 ? 'high' : 'normal'}`}>
                      {item.score}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="데이터 상태" action={<a href="/library" className="card-link">라이브러리 보기</a>}>
              <div className="notification-list">
                {data.notifications.map((notif) => (
                  <div key={notif.title} className="notification-item">
                    <div className="notification-icon" style={{ backgroundColor: `${notif.color}15`, color: notif.color }}>
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
                        <circle cx="9" cy="9" r="7" />
                      </svg>
                    </div>
                    <div className="notification-content">
                      <div className="notification-title">{notif.title}</div>
                      <div className="notification-desc">{notif.desc}</div>
                    </div>
                    <span className="notification-time">{notif.time}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card title="운영 상태" subtitle="데이터 최신성, 시스템 오류, 리포트 공유 현황">
            <div className="notification-list">
              {(data.operationalStatus ?? []).map((item) => (
                <div key={item.label} className="notification-item">
                  <div className="notification-icon" style={{ backgroundColor: `${item.color}15`, color: item.color }}>
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
                      <circle cx="9" cy="9" r="7" />
                    </svg>
                  </div>
                  <div className="notification-content">
                    <div className="notification-title">{item.label}</div>
                    <div className="notification-desc">{item.description}</div>
                  </div>
                  <span className="notification-time">{item.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function TrendChart({ data }: { data: number[] }) {
  const values = data.length > 0 ? data : [0];
  const max = Math.max(...values, 1);
  const points = values.map((value, index) => {
    const x = values.length === 1 ? 50 : (index / (values.length - 1)) * 100;
    const y = 100 - (value / max) * 80;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="trend-chart">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="chart-svg">
        <defs>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,100 ${points} 100,100`} fill="url(#lineGrad)" />
        <polyline points={points} fill="none" stroke="#3B82F6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {values.map((value, index) => {
          const x = values.length === 1 ? 50 : (index / (values.length - 1)) * 100;
          const y = 100 - (value / max) * 80;
          return <circle key={`${value}-${index}`} cx={x} cy={y} r="2" fill="#3B82F6" />;
        })}
      </svg>
      <div className="chart-labels">
        {values.map((_, index) => <span key={index}>상위 {index + 1}</span>)}
      </div>
    </div>
  );
}

function DonutChart({ segments }: { segments: DashboardDistributionItem[] }) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  let cursor = 0;
  const gradientStops = total > 0
    ? segments.map((segment) => {
        const start = cursor;
        const end = cursor + (segment.value / total) * 360;
        cursor = end;
        return `${segment.color} ${start}deg ${end}deg`;
      }).join(', ')
    : '#E2E8F0 0deg 360deg';

  return (
    <div className="donut-chart">
      <div className="donut-center" style={{ background: `conic-gradient(${gradientStops})` }}>
        <span className="donut-total">{total}</span>
        <span className="donut-label">총 위험</span>
      </div>
      <div className="donut-legend">
        {segments.map((segment) => (
          <div key={segment.label} className="legend-item">
            <span className="legend-dot" style={{ backgroundColor: segment.color }} />
            <span className="legend-label">{segment.label}</span>
            <span className="legend-value">{segment.value}건</span>
          </div>
        ))}
      </div>
    </div>
  );
}
