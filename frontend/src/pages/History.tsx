import { useMemo, useState } from 'react';
import { useAnalysisHistory, useRerunAnalysis } from '../api/queries';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

type DateRange = 'all' | 'today' | '7d' | '30d';

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}


function activeFilterText(filters: Record<string, string | null>) {
  const values = Object.values(filters).filter(Boolean);
  return values.length > 0 ? values.join(' / ') : '조건 없음';
}


function dateFromRange(range: DateRange) {
  if (range === 'all') return '';
  const date = new Date();
  if (range === 'today') {
    date.setHours(0, 0, 0, 0);
  } else if (range === '7d') {
    date.setDate(date.getDate() - 7);
  } else {
    date.setDate(date.getDate() - 30);
  }
  return date.toISOString();
}

export default function History() {
  const [search, setSearch] = useState('');
  const [project, setProject] = useState('');
  const [dateRange, setDateRange] = useState<DateRange>('all');
  const dateFrom = useMemo(() => dateFromRange(dateRange), [dateRange]);
  const { data, isLoading, error } = useAnalysisHistory({
    query: search,
    project,
    dateFrom,
  });
  const rerun = useRerunAnalysis();

  return (
    <div className="history-page">
      <PageHeader
        title="과거 분석"
        description="백엔드에 저장된 실제 분석 요청과 결과 snapshot을 조회합니다."
      />

      <div className="filter-bar">
        <input
          type="text"
          className="input project-filter"
          placeholder="프로젝트명 필터"
          value={project}
          onChange={(event) => setProject(event.target.value)}
        />
        <select
          className="select date-filter"
          value={dateRange}
          onChange={(event) => setDateRange(event.target.value as DateRange)}
        >
          <option value="all">전체 기간</option>
          <option value="today">오늘</option>
          <option value="7d">최근 7일</option>
          <option value="30d">최근 30일</option>
        </select>
        <input
          type="text"
          className="input search-input"
          placeholder="검색어, 위험명, 조건 검색"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{ flex: 1 }}
        />
      </div>

      <Card title="분석 이력">
        {isLoading && <div className="empty-state">백엔드에서 분석 이력을 불러오는 중입니다...</div>}
        {error && <div className="empty-state">분석 이력을 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}
        {data && data.items.length === 0 && <div className="empty-state">저장된 분석 이력이 없습니다. 워크스페이스에서 분석을 실행하면 자동 저장됩니다.</div>}
        {data && data.items.length > 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>분석 시각</th>
                  <th>검색어</th>
                  <th>조건</th>
                  <th>상위 위험</th>
                  <th>위험 수</th>
                  <th>최고 점수</th>
                  <th>모델</th>
                  <th>재실행</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="knowledge-row">
                    <td className="text-muted">{formatDate(item.created_at)}</td>
                    <td>{item.query || '자연어 없음'}</td>
                    <td className="text-muted">{activeFilterText(item.filters)}</td>
                    <td><span className="knowledge-title">{item.top_risk || '매칭 위험 없음'}</span></td>
                    <td><Badge variant={item.critical_count > 0 ? 'danger' : 'info'}>{`${item.total_risks}건`}</Badge></td>
                    <td className="text-right">{item.max_score}</td>
                    <td className="text-muted">{item.model_version ?? '-'}</td>
                    <td>
                      <button
                        className="btn btn-secondary"
                        type="button"
                        disabled={rerun.isPending}
                        onClick={() => rerun.mutate(item.id)}
                      >
                        재실행
                      </button>
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
