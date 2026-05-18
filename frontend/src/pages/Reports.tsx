import { useState } from 'react';
import { useReportShareAction, useReports } from '../api/queries';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import MetricCard from '../components/ui/MetricCard';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8080';

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}

export default function Reports() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error } = useReports(search);
  const shareAction = useReportShareAction();

  return (
    <div className="reports-page">
      <PageHeader
        title="리포트"
        description="저장된 분석 이력을 HTML 리포트로 열람하고 다운로드합니다."
        actions={<button className="btn btn-secondary" disabled>+ PDF 생성 준비 중</button>}
      />

      <div className="filter-bar">
        <input
          type="text"
          className="input search-input"
          placeholder="리포트 제목, 위험명, 조건 검색"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{ flex: 1 }}
        />
      </div>

      <div className="metric-grid">
        <MetricCard label="총 리포트" value={`${data?.summary.total ?? 0}건`} subValue="저장된 분석 기반" accentColor="#2563EB" />
        <MetricCard label="HTML 리포트" value={`${data?.summary.html ?? 0}건`} subValue="즉시 열람 가능" accentColor="#059669" />
        <MetricCard label="공유 중" value={`${data?.summary.shared ?? 0}건`} subValue="SQLite 상태 저장" accentColor="#EA580C" />
        <MetricCard label="다운로드" value="HTML" subValue="브라우저 저장 지원" accentColor="#7C3AED" />
      </div>

      <Card title="리포트 목록">
        {isLoading && <div className="empty-state">백엔드에서 리포트 목록을 불러오는 중입니다...</div>}
        {error && <div className="empty-state">리포트 목록을 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}
        {data && data.items.length === 0 && <div className="empty-state">생성 가능한 리포트가 없습니다. 워크스페이스에서 분석을 실행하면 HTML 리포트가 자동 제공됩니다.</div>}
        {data && data.items.length > 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>생성 시각</th>
                  <th>제목</th>
                  <th>상위 위험</th>
                  <th>위험 수</th>
                  <th>형식</th>
                  <th>모델</th>
                  <th>공유</th>
                  <th>다운로드</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="knowledge-row">
                    <td className="text-muted">{formatDate(item.created_at)}</td>
                    <td><span className="knowledge-title">{item.title}</span></td>
                    <td>{item.top_risk}</td>
                    <td>{item.total_risks}건</td>
                    <td>{item.format}</td>
                    <td className="text-muted">{item.model_version ?? '-'}</td>
                    <td>
                      {item.report_type === 'comparison' ? <span className="text-muted">비교 리포트</span> : (
                        <button
                          className="btn btn-secondary"
                          type="button"
                          disabled={shareAction.isPending}
                          onClick={() => shareAction.mutate({ historyId: item.history_id, shared: !item.shared })}
                        >
                          {item.shared ? '공유 해제' : '공유'}
                        </button>
                      )}
                      {item.report_type !== 'comparison' && item.shared && item.share_url && (
                        <a className="btn btn-secondary" href={`${API_BASE}${item.share_url}`} target="_blank" rel="noreferrer" style={{ marginLeft: '6px' }}>
                          공유 링크
                        </a>
                      )}
                    </td>
                    <td>
                      <a className="btn btn-secondary" href={`${API_BASE}${item.download_url}`} target="_blank" rel="noreferrer">
                        HTML
                      </a>{' '}
                      <a className="btn btn-secondary" href={`${API_BASE}${item.pdf_url}`} target="_blank" rel="noreferrer">
                        PDF
                      </a>
                      {item.package_url && (
                        <>
                          {' '}
                          <a className="btn btn-secondary" href={`${API_BASE}${item.package_url}`} target="_blank" rel="noreferrer">
                            패키지
                          </a>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
