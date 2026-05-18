import { useState, type FormEvent } from 'react';
import { useDesignCompareAction, useDesignCompareReportAction } from '../api/queries';
import FilterPanel from '../components/FilterPanel';
import PageHeader from '../components/layout/PageHeader';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import MetricCard from '../components/ui/MetricCard';
import type { CompareRiskItem, Filters } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8080';

const EMPTY_FILTERS: Filters = {
  process: null,
  ground: null,
  location: null,
  method: null,
  equipment: null,
  impact: null,
};

function RiskDeltaList({ title, items, emptyText }: { title: string; items: CompareRiskItem[]; emptyText: string }) {
  return (
    <Card title={title}>
      {items.length === 0 ? <div className="empty-state">{emptyText}</div> : (
        <div className="recent-list">
          {items.slice(0, 6).map((risk) => (
            <div key={risk.id} className="recent-item">
              <div className="recent-item-content">
                <span className="recent-title">{risk.description}</span>
                <span className="recent-time">{risk.matched.length > 0 ? risk.matched.join(' / ') : '매칭 조건 없음'}</span>
              </div>
              <Badge variant={risk.level.includes('최상위') ? 'danger' : risk.level.includes('상위') ? 'warning' : 'info'}>{String(risk.score)}</Badge>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function DesignCompare() {
  const [beforeFilters, setBeforeFilters] = useState<Filters>(EMPTY_FILTERS);
  const [afterFilters, setAfterFilters] = useState<Filters>(EMPTY_FILTERS);
  const [beforeQuery, setBeforeQuery] = useState('');
  const [afterQuery, setAfterQuery] = useState('');
  const compareAction = useDesignCompareAction();
  const reportAction = useDesignCompareReportAction();
  const result = compareAction.data;
  const request = {
    before: { ...beforeFilters, query: beforeQuery },
    after: { ...afterFilters, query: afterQuery },
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    compareAction.mutate(request);
  };

  return (
    <form className="compare-page" onSubmit={submit}>
      <PageHeader
        title="설계변경 비교"
        description="변경 전·후 조건을 비교해 신규/감소 위험과 추가 대응전략을 확인합니다."
        actions={<button className="btn btn-danger" type="submit" disabled={compareAction.isPending}>{compareAction.isPending ? '비교 중...' : '비교 실행'}</button>}
      />

      <div className="compare-panels">
        <Card title="변경 전 조건">
          <FilterPanel values={beforeFilters} onChange={(key, value) => setBeforeFilters((current) => ({ ...current, [key]: value }))} />
          <input className="input" value={beforeQuery} onChange={(event) => setBeforeQuery(event.target.value)} placeholder="변경 전 자연어 맥락" />
        </Card>
        <Card title="변경 후 조건">
          <FilterPanel values={afterFilters} onChange={(key, value) => setAfterFilters((current) => ({ ...current, [key]: value }))} />
          <input className="input" value={afterQuery} onChange={(event) => setAfterQuery(event.target.value)} placeholder="변경 후 자연어 맥락" />
        </Card>
      </div>

      {compareAction.error && <div className="empty-state">{compareAction.error.message}</div>}
      {reportAction.error && <div className="empty-state">{reportAction.error.message}</div>}

      {result ? (
        <>
          <Card title="비교 리포트" subtitle="현재 변경 전·후 조건과 비교 결과를 저장해 리포트 메뉴에서 재사용합니다." action={
            <button className="btn btn-secondary" type="button" disabled={reportAction.isPending} onClick={() => reportAction.mutate(request)}>
              {reportAction.isPending ? '저장 중...' : '비교 리포트 저장'}
            </button>
          }>
            {reportAction.data ? (
              <div className="recent-item">
                <div className="recent-item-content">
                  <span className="recent-title">{reportAction.data.title}</span>
                  <span className="recent-time">모델 {reportAction.data.model_version}</span>
                </div>
                <a className="btn btn-secondary" href={`${API_BASE}${reportAction.data.download_url}`} target="_blank" rel="noreferrer">HTML 열기</a>
              </div>
            ) : (
              <div className="empty-state">저장하면 HTML/PDF/패키지 리포트 링크가 생성됩니다.</div>
            )}
          </Card>

          <div className="metric-grid">
            <MetricCard label="변경 전 위험" value={`${result.before.total_risks}건`} subValue={`최고 ${result.before.max_score}`} accentColor="#64748B" />
            <MetricCard label="변경 후 위험" value={`${result.after.total_risks}건`} subValue={`최고 ${result.after.max_score}`} accentColor="#2563EB" />
            <MetricCard label="신규 위험" value={`${result.new_risks.length}건`} subValue="변경 후 추가" accentColor="#EF4444" />
            <MetricCard label="모델 버전" value={result.model_version} subValue="비교 기준" accentColor="#7C3AED" />
          </div>

          <div className="compare-results-grid">
            <RiskDeltaList title="신규 발생 가능 리스크" items={result.new_risks} emptyText="신규 리스크가 없습니다." />
            <RiskDeltaList title="감소 또는 제거된 리스크" items={result.removed_risks} emptyText="감소/제거 리스크가 없습니다." />
            <RiskDeltaList title="위험등급 상승 리스크" items={result.increased_risks} emptyText="상승 리스크가 없습니다." />
            <RiskDeltaList title="위험등급 하락 리스크" items={result.decreased_risks} emptyText="하락 리스크가 없습니다." />
          </div>

          <div className="dashboard-bottom-row">
            <Card title="추가 대응전략">
              {result.additional_strategies.length > 0 ? <ul>{result.additional_strategies.map((item) => <li key={item}>{item}</li>)}</ul> : <div className="empty-state">추가 대응전략이 없습니다.</div>}
            </Card>
            <Card title="관련 기준 근거">
              {result.related_standards.length > 0 ? <ul>{result.related_standards.map((item) => <li key={item}>{item}</li>)}</ul> : <div className="empty-state">관련 기준 근거가 없습니다.</div>}
            </Card>
          </div>
        </>
      ) : (
        <div className="empty-state">비교 실행 후 설계변경 전·후 차이가 표시됩니다.</div>
      )}
    </form>
  );
}
