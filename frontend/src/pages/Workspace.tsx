import { useMemo, useState, type FormEvent } from 'react';
import { scoreRisks } from '../api/client';
import { useSavedConditionActions, useSavedConditions, useStandardEvidence } from '../api/queries';
import FilterPanel from '../components/FilterPanel';
import KnowledgeGraph from '../components/KnowledgeGraph';
import PageHeader from '../components/layout/PageHeader';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';
import type { Filters, GraphNode, RiskNode, ScoreResponse } from '../types';

const EMPTY_FILTERS: Filters = {
  process: null,
  ground: null,
  location: null,
  method: null,
  equipment: null,
  impact: null,
};

const QUERY_SUGGESTIONS = ['지하수 유입', '파쇄대', '강구부 변위', '인허가 지연', 'TBM 커터 마모'];

function badgeVariant(level: string): 'danger' | 'warning' | 'success' | 'info' {
  if (level.includes('최상위')) return 'danger';
  if (level.includes('상위')) return 'warning';
  if (level.includes('저위험')) return 'success';
  return 'info';
}

function severityLabel(score: number, maxScore: number) {
  if (maxScore <= 0) return '낮음';
  const ratio = score / maxScore;
  if (ratio >= 0.8) return '높음';
  if (ratio >= 0.5) return '중간';
  return '낮음';
}

function confidenceLabel(risk: RiskNode) {
  if (typeof risk.confidence === 'number') {
    if (risk.confidence >= 0.75) return '높음';
    if (risk.confidence >= 0.45) return '보통';
    return '낮음';
  }
  const sourceCount = risk.strategies.length + (risk.matched ? risk.matched.split('|').length : 0);
  if (sourceCount >= 5) return '높음';
  if (sourceCount >= 2) return '보통';
  return '낮음';
}

function detailList(values: string[] | undefined) {
  return values && values.length > 0 ? values.join(' / ') : '정보 없음';
}

export default function Workspace() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [savingCondition, setSavingCondition] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bookmarkedRiskIds, setBookmarkedRiskIds] = useState<Set<string>>(() => new Set());
  const [selectedRiskLevels, setSelectedRiskLevels] = useState<Set<string>>(() => new Set());
  const [selectedGraphNodeId, setSelectedGraphNodeId] = useState<string | null>(null);
  const savedConditionsQuery = useSavedConditions();
  const savedConditionActions = useSavedConditionActions();

  const selectedConditions = useMemo(() => {
    return Object.values(filters).filter((value): value is string => Boolean(value));
  }, [filters]);

  const riskFilters = useMemo(() => {
    const risks = result?.risks ?? [];
    const counts = new Map<string, number>();
    for (const risk of risks) {
      counts.set(risk.level, (counts.get(risk.level) ?? 0) + 1);
    }
    return [
      { label: '전체', count: risks.length, checked: selectedRiskLevels.size === 0 },
      ...Array.from(counts.entries()).map(([label, count]) => ({
        label,
        count,
        checked: selectedRiskLevels.has(label),
      })),
    ];
  }, [result?.risks, selectedRiskLevels]);

  const visibleRisks = useMemo(() => {
    const risks = result?.risks ?? [];
    if (selectedRiskLevels.size === 0) return risks;
    return risks.filter((risk) => selectedRiskLevels.has(risk.level));
  }, [result?.risks, selectedRiskLevels]);

  const categoryFilters = useMemo(() => {
    const counts = new Map<string, number>();
    for (const risk of result?.risks ?? []) {
      const tags = risk.matched.split('|').map((item) => item.trim()).filter(Boolean);
      for (const tag of tags) {
        counts.set(tag, (counts.get(tag) ?? 0) + 1);
      }
    }
    return Array.from(counts.entries()).slice(0, 8).map(([label, count]) => ({ label, count }));
  }, [result?.risks]);

  const topRisk = result?.risks[0] ?? null;
  const recommendedActions = topRisk?.strategies.slice(0, 3) ?? [];
  const selectedGraphNode: GraphNode | null = useMemo(() => {
    if (!result?.graph || !selectedGraphNodeId) return null;
    return result.graph.nodes.find((node) => node.id === selectedGraphNodeId) ?? null;
  }, [result?.graph, selectedGraphNodeId]);
  const selectedStandardQuery = useMemo(() => {
    return selectedGraphNode?.detail?.standards?.join(' ') ?? '';
  }, [selectedGraphNode?.detail?.standards]);
  const standardEvidenceQuery = useStandardEvidence(selectedStandardQuery);
  const selectedGraphEdges = useMemo(() => {
    if (!result?.graph || !selectedGraphNodeId) return [];
    return result.graph.edges.filter((edge) => edge.from === selectedGraphNodeId || edge.to === selectedGraphNodeId);
  }, [result?.graph, selectedGraphNodeId]);
  const gaugePercent = topRisk
    ? topRisk.level.includes('최상위') ? 100 : topRisk.level.includes('상위') ? 72 : topRisk.level.includes('저위험') ? 28 : 48
    : 0;
  const gaugeColor = topRisk?.color ?? '#94A3B8';
  const dataVersionLabel = result?.data_version
    ? `${result.data_version.source_file} · ${result.data_version.source_file_hash.slice(0, 12)}`
    : null;
  const modelVersionLabel = result?.model_version ? `모델: ${result.model_version}` : null;

  const analyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const nextResult = await scoreRisks({ ...filters, query });
      setResult(nextResult);
      setSelectedRiskLevels(new Set());
      setSelectedGraphNodeId(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '분석 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const saveCurrentCondition = async () => {
    setSavingCondition(true);
    setSaveMessage(null);
    setError(null);
    try {
      const saved = await savedConditionActions.save.mutateAsync({ ...filters, query });
      setSaveMessage(`조건이 저장되었습니다: ${saved.title}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '조건 저장 중 오류가 발생했습니다.');
    } finally {
      setSavingCondition(false);
    }
  };

  const loadSavedCondition = (savedFilters: Filters, savedQuery: string) => {
    setFilters(savedFilters);
    setQuery(savedQuery);
    setSaveMessage('저장된 조건을 불러왔습니다. 분석 실행을 눌러 결과를 확인하세요.');
  };

  const deleteCondition = async (conditionId: number) => {
    setError(null);
    try {
      await savedConditionActions.delete.mutateAsync(conditionId);
      setSaveMessage('저장된 조건을 삭제했습니다.');
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '저장 조건 삭제 중 오류가 발생했습니다.');
    }
  };

  const submitAnalysis = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void analyze();
  };

  return (
    <form className="workspace-page" onSubmit={submitAnalysis}>
      <PageHeader
        title="분석 워크스페이스"
        description="현장 조건을 설정하면 백엔드 위험도 엔진이 실제 CSV 온톨로지를 분석합니다."
        actions={
          <div className="header-actions">
            <button className="btn btn-secondary" type="button" disabled={savingCondition} onClick={() => { void saveCurrentCondition(); }}>
              {savingCondition ? '저장 중...' : '조건 저장'}
            </button>
            <button className="btn btn-danger" type="submit" disabled={loading}>
              {loading ? '분석 중...' : '분석 실행'}
            </button>
          </div>
        }
      />

      <FilterPanel
        values={filters}
        onChange={(key, value) => setFilters((current) => ({ ...current, [key]: value }))}
      />

      <Card className="semantic-search-card">
        <div className="semantic-search-header">
          <h3>의미 기반 검색</h3>
          <button className="btn btn-secondary" type="button" onClick={() => setQuery('')}>초기화</button>
        </div>
        <input
          type="text"
          className="input semantic-search-input"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="예: 도심지 강구부에서 굴착 중 파쇄대 조우 시 대책"
        />
        <div className="search-tags">
          {QUERY_SUGGESTIONS.map((tag) => (
            <button key={tag} type="button" className="search-tag" onClick={() => setQuery(tag)}>{tag}</button>
          ))}
        </div>
      </Card>

      {error && <div className="empty-state">{error}</div>}
      {saveMessage && <div className="save-state">{saveMessage}</div>}

      <div className="workspace-main">
        <div className="workspace-left-panel">
          <Card title="필터 & 분석 상태">
            <div className="filter-history-section">
              <div className="filter-section-header">
                <h4>현재 분석 조건</h4>
              </div>
              <div className="history-list">
                {selectedConditions.length > 0 || query ? (
                  <div className="history-item">
                    <span className="history-condition">{[...selectedConditions, query].filter(Boolean).join(' / ')}</span>
                    <span className="history-time">현재</span>
                  </div>
                ) : (
                  <div className="history-item">
                    <span className="history-condition">조건 또는 자연어를 입력하세요.</span>
                    <span className="history-time">대기</span>
                  </div>
                )}
              </div>
            </div>

            <div className="filter-group">
              <h4>저장된 조건</h4>
              {savedConditionsQuery.isLoading && <p className="text-muted">저장 조건을 불러오는 중입니다.</p>}
              {!savedConditionsQuery.isLoading && (savedConditionsQuery.data?.items.length ?? 0) === 0 && (
                <p className="text-muted">저장된 조건이 없습니다.</p>
              )}
              {(savedConditionsQuery.data?.items ?? []).slice(0, 5).map((condition) => (
                <div key={condition.id} className="saved-condition-item">
                  <button
                    className="saved-condition-load"
                    type="button"
                    onClick={() => loadSavedCondition(condition.filters, condition.query)}
                  >
                    {condition.title}
                  </button>
                  <button
                    className="saved-condition-delete"
                    type="button"
                    aria-label={`${condition.title} 삭제`}
                    onClick={() => { void deleteCondition(condition.id); }}
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>

            <div className="filter-group">
              <h4>위험 수준 필터</h4>
              {riskFilters.map((filter) => (
                <label key={filter.label} className="filter-checkbox">
                  <input
                    type="checkbox"
                    checked={filter.checked}
                    onChange={() => {
                      if (filter.label === '전체') {
                        setSelectedRiskLevels(new Set());
                        return;
                      }
                      setSelectedRiskLevels((current) => {
                        const next = new Set(current);
                        if (next.has(filter.label)) {
                          next.delete(filter.label);
                        } else {
                          next.add(filter.label);
                        }
                        return next;
                      });
                    }}
                  />
                  <span>{filter.label}</span>
                  <span className="filter-count">{filter.count}</span>
                </label>
              ))}
            </div>

            <div className="filter-group">
              <h4>매칭 조건</h4>
              {categoryFilters.length > 0 ? categoryFilters.map((cat) => (
                <div key={cat.label} className="category-item">
                  <span>{cat.label}</span>
                  <span className="filter-count">{cat.count}</span>
                </div>
              )) : <p className="text-muted">분석 후 매칭 조건이 표시됩니다.</p>}
            </div>

            <button className="btn btn-secondary" type="button" style={{ width: '100%' }} onClick={() => { setFilters(EMPTY_FILTERS); setQuery(''); setResult(null); setSelectedRiskLevels(new Set()); setSelectedGraphNodeId(null); }}>
              필터 초기화
            </button>
          </Card>
        </div>

        <div className="workspace-center">
          <Card
            title={`분석 결과 (${result?.total_risks ?? 0})`}
            action={<span className="sort-label">{[dataVersionLabel ? `데이터: ${dataVersionLabel}` : '정렬: 백엔드 위험도 순', modelVersionLabel].filter(Boolean).join(' · ')}</span>}
          >
            {loading && <div className="empty-state">백엔드 위험도 엔진이 분석 중입니다...</div>}
            {!loading && !result && <div className="empty-state">분석 실행 버튼을 누르면 실제 백엔드 분석 결과가 표시됩니다.</div>}
            {!loading && result && result.risks.length === 0 && <div className="empty-state">매칭된 위험 요소가 없습니다. 조건이나 자연어를 바꿔보세요.</div>}
            {!loading && result && result.risks.length > 0 && visibleRisks.length === 0 && <div className="empty-state">선택한 위험 수준에 해당하는 결과가 없습니다.</div>}
            {!loading && result && visibleRisks.length > 0 && (
              <div className="risk-results">
                {visibleRisks.map((risk, idx) => (
                  <div key={risk.id} className="risk-result-card" style={{ borderLeftColor: risk.color }}>
                    <div className="risk-result-header">
                      <span className="risk-rank-badge">#{idx + 1}</span>
                      <Badge variant={badgeVariant(risk.level)}>{risk.level}</Badge>
                      <button
                        className={`bookmark-btn ${bookmarkedRiskIds.has(risk.id) ? 'active' : ''}`}
                        type="button"
                        aria-label="북마크"
                        aria-pressed={bookmarkedRiskIds.has(risk.id)}
                        title={bookmarkedRiskIds.has(risk.id) ? '북마크 해제' : '북마크 추가'}
                        onClick={() => setBookmarkedRiskIds((current) => {
                          const next = new Set(current);
                          if (next.has(risk.id)) {
                            next.delete(risk.id);
                          } else {
                            next.add(risk.id);
                          }
                          return next;
                        })}
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M3 2h10v12l-5-4-5 4V2z" />
                        </svg>
                      </button>
                    </div>
                    <h4 className="risk-result-title">{risk.description}</h4>
                    <div className="risk-result-meta">
                      {risk.matched ? risk.matched.split('|').map((tag) => <span key={tag.trim()}>{tag.trim()}</span>) : <span>매칭 조건 없음</span>}
                    </div>
                    <p className="risk-result-desc">백엔드 위험도 엔진이 선택 조건 및 자연어 매칭을 기반으로 산출한 위험 항목입니다.</p>
                    <div className="risk-indicators">
                      <div className="indicator">
                        <span className="indicator-label">위험도 점수</span>
                        <span className="indicator-value" style={{ color: risk.color }}>{risk.score}</span>
                      </div>
                      <div className="indicator">
                        <span className="indicator-label">발생 가능성</span>
                        <span className="indicator-value">{typeof risk.likelihood === 'number' ? risk.likelihood : severityLabel(risk.score, result.max_score)}</span>
                      </div>
                      <div className="indicator">
                        <span className="indicator-label">영향도</span>
                        <span className="indicator-value">{typeof risk.impact_score === 'number' ? risk.impact_score : risk.level}</span>
                      </div>
                      <div className="indicator">
                        <span className="indicator-label">신뢰도</span>
                        <span className="indicator-value">{confidenceLabel(risk)}</span>
                      </div>
                    </div>
                    <div className="risk-tags">
                      {(risk.matched ? risk.matched.split('|').map((tag) => tag.trim()).filter(Boolean) : []).map((tag) => (
                        <span key={tag} className="risk-tag">#{tag}</span>
                      ))}
                    </div>
                    {risk.strategies.length > 0 && (
                      <details className="risk-strategies">
                        <summary>권장 대응 전략 {risk.strategies.length}건</summary>
                        <ul>{risk.strategies.map((strategy) => <li key={strategy}>{strategy}</li>)}</ul>
                      </details>
                    )}
                    {risk.score_explanation?.rationale && risk.score_explanation.rationale.length > 0 && (
                      <details className="risk-strategies">
                        <summary>점수 산정 근거</summary>
                        <ul>{risk.score_explanation.rationale.map((reason) => <li key={reason}>{reason}</li>)}</ul>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <div className="workspace-right">
          <Card title="지식 그래프" action={<button className="icon-btn" type="button">⛶</button>}>
            <KnowledgeGraph data={result?.graph ?? null} onNodeSelect={setSelectedGraphNodeId} />
          </Card>

          <Card title="선택 노드 상세">
            {selectedGraphNode ? (
              <div className="graph-node-detail">
                <div className="detail-row">
                  <span className="detail-label">유형</span>
                  <span className="detail-value">{selectedGraphNode.label}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">제목</span>
                  <span className="detail-value">{selectedGraphNode.title}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">노드 ID</span>
                  <span className="detail-value">{selectedGraphNode.id}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">노드 크기</span>
                  <span className="detail-value">{selectedGraphNode.size}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">연결 관계</span>
                  <span className="detail-value">
                    {selectedGraphEdges.length > 0
                      ? selectedGraphEdges.map((edge) => edge.title).join(' / ')
                      : '연결 관계 없음'}
                  </span>
                </div>
                {selectedGraphNode.detail?.project && (
                  <div className="detail-row">
                    <span className="detail-label">관련 프로젝트</span>
                    <span className="detail-value">{selectedGraphNode.detail.project}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.sourceLL && selectedGraphNode.detail.sourceLL !== 'nan' && (
                  <div className="detail-row">
                    <span className="detail-label">원문 LL 내용</span>
                    <span className="detail-value">{selectedGraphNode.detail.sourceLL}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.sourceVersion && selectedGraphNode.detail.sourceVersion !== 'nan' && (
                  <div className="detail-row">
                    <span className="detail-label">원천 버전</span>
                    <span className="detail-value">{selectedGraphNode.detail.sourceVersion}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.cause && selectedGraphNode.detail.cause !== 'nan' && (
                  <div className="detail-row">
                    <span className="detail-label">원인</span>
                    <span className="detail-value">{selectedGraphNode.detail.cause}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.impactText && selectedGraphNode.detail.impactText !== 'nan' && (
                  <div className="detail-row">
                    <span className="detail-label">원문 영향</span>
                    <span className="detail-value">{selectedGraphNode.detail.impactText}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.matched && (
                  <div className="detail-row">
                    <span className="detail-label">매칭 조건</span>
                    <span className="detail-value">{detailList(selectedGraphNode.detail.matched)}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.strategies && (
                  <div className="detail-row">
                    <span className="detail-label">대응전략</span>
                    <span className="detail-value">{detailList(selectedGraphNode.detail.strategies)}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.impacts && (
                  <div className="detail-row">
                    <span className="detail-label">영향</span>
                    <span className="detail-value">{detailList(selectedGraphNode.detail.impacts)}</span>
                  </div>
                )}
                {selectedGraphNode.detail?.standards && (
                  <div className="detail-row">
                    <span className="detail-label">표준 근거</span>
                    <span className="detail-value">{detailList(selectedGraphNode.detail.standards)}</span>
                  </div>
                )}
                {selectedStandardQuery && (
                  <div className="detail-row">
                    <span className="detail-label">KCSC 조항</span>
                    <span className="detail-value">
                      {standardEvidenceQuery.isLoading && '기준 근거를 불러오는 중입니다.'}
                      {standardEvidenceQuery.error && '기준 근거를 불러오지 못했습니다.'}
                      {standardEvidenceQuery.data && standardEvidenceQuery.data.items.length === 0 && '조회된 기준 조항이 없습니다.'}
                      {standardEvidenceQuery.data && standardEvidenceQuery.data.items.length > 0 && (
                        <span className="standard-evidence-list">
                          {standardEvidenceQuery.data.items.slice(0, 3).map((item) => (
                            <span key={`${item.code}-${item.section_label}-${item.text}`} className="standard-evidence-item">
                              <strong>{item.code} {item.section_path.join(' > ')} {item.section_label}</strong>
                              <span>{item.text}</span>
                              <a href={item.source_url} target="_blank" rel="noreferrer">KCSC 원문</a>
                            </span>
                          ))}
                        </span>
                      )}
                    </span>
                  </div>
                )}
                {selectedGraphNode.detail?.roles && (
                  <div className="detail-row">
                    <span className="detail-label">담당 주체</span>
                    <span className="detail-value">{detailList(selectedGraphNode.detail.roles)}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">그래프 노드를 클릭하면 상세 정보가 표시됩니다.</div>
            )}
          </Card>

          <Card title="관련 근거 노드" action={<a href="/library" className="card-link">라이브러리 보기</a>}>
            <div className="timeline">
              {(result?.graph.nodes ?? []).slice(0, 6).map((node) => (
                <div key={node.id} className="timeline-item">
                  <div className="timeline-date">{node.label}</div>
                  <div className="timeline-dot" />
                  <div className="timeline-content">
                    <div className="timeline-title">{node.title}</div>
                    <div className="timeline-similarity">노드 크기 {node.size}</div>
                  </div>
                </div>
              ))}
              {!result?.graph.nodes.length && <div className="empty-state">분석 후 그래프 근거 노드가 표시됩니다.</div>}
            </div>
          </Card>

          <Card title="추가 검토 권고">
            <div className="action-list">
              {(result?.recommendations ?? []).length > 0 ? (result?.recommendations ?? []).map((recommendation, idx) => (
                <div key={`${recommendation.type}-${recommendation.title}`} className="action-item">
                  <span className="action-number">{idx + 1}</span>
                  <div className="action-content">
                    <span className="action-title">{recommendation.title}</span>
                    <p className="text-muted">{recommendation.reason}</p>
                    <div className="action-badges">
                      <Badge variant="warning">추가 검토</Badge>
                      {recommendation.suggested_filter.query && <Badge variant="info">{recommendation.suggested_filter.query}</Badge>}
                    </div>
                  </div>
                </div>
              )) : <div className="empty-state">현재 조건에서 별도 누락 권고가 없습니다.</div>}
            </div>
          </Card>

          <Card title="종합 위험도">
            <div className="risk-gauge-container">
              <div className="risk-gauge">
                <div className="gauge-bg" />
                <div className="gauge-fill" style={{ height: `${gaugePercent}%`, background: `linear-gradient(180deg, ${gaugeColor} 0%, #F97316 100%)` }} />
                <div className="gauge-value">{result?.max_score ?? 0}</div>
              </div>
              <div className="gauge-info">
                <Badge variant={topRisk ? badgeVariant(topRisk.level) : 'default'}>{topRisk?.level ?? '대기'}</Badge>
                <p className="gauge-desc">{result ? `총 ${result.total_risks}건 중 최상위 ${result.critical_count}건` : '분석 결과 대기 중입니다.'}</p>
              </div>
            </div>
          </Card>

          <Card title="권장 대응 전략 (Top Actions)">
            <div className="action-list">
              {recommendedActions.length > 0 ? recommendedActions.map((action, idx) => (
                <div key={action} className="action-item">
                  <span className="action-number">{idx + 1}</span>
                  <div className="action-content">
                    <span className="action-title">{action}</span>
                    <div className="action-badges">
                      <Badge variant="warning">백엔드 전략</Badge>
                      <Badge variant={idx === 0 ? 'danger' : 'info'}>{idx === 0 ? '우선 검토' : '검토'}</Badge>
                    </div>
                  </div>
                </div>
              )) : <div className="empty-state">분석 후 연결된 대응 전략이 표시됩니다.</div>}
            </div>
          </Card>
        </div>
      </div>
    </form>
  );
}
