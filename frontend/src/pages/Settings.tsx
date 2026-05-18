import { useState, type FormEvent } from 'react';
import { useKnowledgeSubmissionActions, useKnowledgeSubmissions, useStandardsLinkActions, useStandardsLinks, useStandardsRevalidationAction } from '../api/queries';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import type { KnowledgeItemType, KnowledgeVerificationStatus, StandardsLinkRequest, StandardsRevalidationResponse } from '../types';

const ITEM_TYPES: Array<{ value: KnowledgeItemType; label: string }> = [
  { value: 'risk', label: '리스크' },
  { value: 'strategy', label: '대응전략' },
  { value: 'lesson', label: 'Lessons Learned' },
  { value: 'project', label: '프로젝트 사례' },
  { value: 'standard', label: '기준 문서' },
  { value: 'equipment', label: '장비 정보' },
  { value: 'method', label: '공법 정보' },
];

const STATUS_LABELS: Record<KnowledgeVerificationStatus, string> = {
  pending_review: '검토 대기',
  verified: '검증 완료',
  rejected: '반려',
};

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}

function splitTags(value: string): string[] {
  return value.split(',').map((tag) => tag.trim()).filter(Boolean);
}

export default function Settings() {
  const [itemType, setItemType] = useState<KnowledgeItemType>('lesson');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [source, setSource] = useState('');
  const [statusFilter, setStatusFilter] = useState<KnowledgeVerificationStatus | 'all'>('all');
  const { data, isLoading, error } = useKnowledgeSubmissions({
    verificationStatus: statusFilter === 'all' ? undefined : statusFilter,
  });
  const actions = useKnowledgeSubmissionActions();
  const standardsRevalidation = useStandardsRevalidationAction();
  const [standardsResult, setStandardsResult] = useState<StandardsRevalidationResponse | null>(null);
  const { data: standardsLinks, isLoading: isStandardsLinksLoading, error: standardsLinksError } = useStandardsLinks();
  const standardsLinkActions = useStandardsLinkActions();
  const [standardsLinkForm, setStandardsLinkForm] = useState<StandardsLinkRequest>({
    target_type: 'risk',
    target_id: '',
    standard_code: '',
    clause_path: '',
    clause_label: '',
    clause_text: '',
    note: '',
  });

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await actions.create.mutateAsync({
      item_type: itemType,
      title,
      content,
      tags: splitTags(tags),
      source,
    });
    setTitle('');
    setContent('');
    setTags('');
    setSource('');
  };

  const updateStatus = (id: number, verificationStatus: KnowledgeVerificationStatus) => {
    actions.updateStatus.mutate({
      id,
      verificationStatus,
      reviewer: 'internal-admin',
      reviewNote: verificationStatus === 'verified' ? '설정 화면에서 검증 완료 처리' : '설정 화면에서 반려 처리',
    });
  };

  const handleStandardsRevalidation = async () => {
    const result = await standardsRevalidation.mutateAsync();
    setStandardsResult(result);
  };

  const handleStandardsLinkSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await standardsLinkActions.create.mutateAsync(standardsLinkForm);
    setStandardsLinkForm({
      target_type: 'risk',
      target_id: '',
      standard_code: '',
      clause_path: '',
      clause_label: '',
      clause_text: '',
      note: '',
    });
  };

  return (
    <div className="settings-page">
      <PageHeader
        title="설정"
        description="운영자가 신규 지식을 등록하고 검증 상태를 관리하는 내부 PoC 관리 화면입니다. 인증은 사내망/서버 접근 정책을 따릅니다."
      />

      <div className="dashboard-grid" style={{ alignItems: 'start' }}>
        <Card title="지식 등록" subtitle="Excel/CSV 원천은 그대로 두고 검토 대기 큐에 등록합니다.">
          <form className="filter-bar" onSubmit={handleSubmit} style={{ alignItems: 'stretch' }}>
            <label>
              유형
              <select className="select" value={itemType} onChange={(event) => setItemType(event.target.value as KnowledgeItemType)}>
                {ITEM_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
              </select>
            </label>
            <label>
              제목
              <input className="input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="예: 도심지 지하수 유입 사례" required />
            </label>
            <label style={{ flexBasis: '100%' }}>
              내용
              <textarea className="input" value={content} onChange={(event) => setContent(event.target.value)} placeholder="검토할 신규 지식 내용을 입력하세요." required rows={5} />
            </label>
            <label>
              태그
              <input className="input" value={tags} onChange={(event) => setTags(event.target.value)} placeholder="지하수, NATM, 도심지" />
            </label>
            <label>
              출처
              <input className="input" value={source} onChange={(event) => setSource(event.target.value)} placeholder="운영자 수기 등록, 보고서명 등" />
            </label>
            <button className="btn btn-primary" type="submit" disabled={actions.create.isPending}>
              {actions.create.isPending ? '등록 중...' : '검토 대기 등록'}
            </button>
          </form>
        </Card>

        <Card title="운영 원칙" subtitle="등록 지식은 검증 후 별도 운영 절차로 원천 데이터에 반영합니다.">
          <ul>
            <li>등록 즉시 분석 모델에 반영하지 않아 원천 Excel의 신뢰성을 유지합니다.</li>
            <li>모든 제출 항목은 현재 ontology data version snapshot을 함께 저장합니다.</li>
            <li>검증 완료/반려 상태는 내부 검토 이력으로 남깁니다.</li>
          </ul>
        </Card>

        <Card title="기준 근거 재검증" subtitle="현재 Standard 노드를 KCSC seed evidence 기준으로 수동 재검증합니다.">
          <button className="btn btn-secondary" type="button" disabled={standardsRevalidation.isPending} onClick={handleStandardsRevalidation}>
            {standardsRevalidation.isPending ? '재검증 중...' : '기준 코드 재검증'}
          </button>
          {standardsRevalidation.error && <div className="empty-state">기준 재검증에 실패했습니다. 백엔드 서버를 확인하세요.</div>}
          {standardsResult && (
            <div style={{ marginTop: '12px' }}>
              <p className="text-muted">출처: {standardsResult.source}</p>
              <div className="tag-list-inline">
                <span className="tag-inline">전체 {standardsResult.total}건</span>
                <span className="tag-inline">검증 {standardsResult.verified_count}건</span>
                <span className="tag-inline">후보 {standardsResult.candidate_count}건</span>
                <span className="tag-inline">미확인 {standardsResult.unknown_count}건</span>
              </div>
              {standardsResult.items.length > 0 && (
                <ul>
                  {standardsResult.items.slice(0, 5).map((item) => (
                    <li key={item.id}>
                      <strong>{item.doc_name}</strong>: {item.message}
                      {item.candidate_codes.length > 0 ? ` (${item.candidate_codes.join(', ')})` : ''}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </Card>

        <Card title="기준 조항 연결" subtitle="리스크/전략과 KDS·KCS 조항 근거를 내부 검토용으로 저장합니다.">
          <form className="filter-bar" onSubmit={handleStandardsLinkSubmit} style={{ alignItems: 'stretch' }}>
            <label>
              대상 유형
              <select
                className="select"
                value={standardsLinkForm.target_type}
                onChange={(event) => setStandardsLinkForm((form) => ({ ...form, target_type: event.target.value as 'risk' | 'strategy' }))}
              >
                <option value="risk">리스크</option>
                <option value="strategy">대응전략</option>
              </select>
            </label>
            <label>
              대상 ID
              <input className="input" value={standardsLinkForm.target_id} onChange={(event) => setStandardsLinkForm((form) => ({ ...form, target_id: event.target.value }))} placeholder="Risk_001" required />
            </label>
            <label>
              기준 코드
              <input className="input" value={standardsLinkForm.standard_code} onChange={(event) => setStandardsLinkForm((form) => ({ ...form, standard_code: event.target.value }))} placeholder="KCS 27 50 05" required />
            </label>
            <label>
              조항 경로
              <input className="input" value={standardsLinkForm.clause_path} onChange={(event) => setStandardsLinkForm((form) => ({ ...form, clause_path: event.target.value }))} placeholder="3. 시공 > 3.3 시공기준" required />
            </label>
            <label>
              조항 라벨
              <input className="input" value={standardsLinkForm.clause_label} onChange={(event) => setStandardsLinkForm((form) => ({ ...form, clause_label: event.target.value }))} placeholder="(7)" />
            </label>
            <label style={{ flexBasis: '100%' }}>
              메모
              <textarea className="input" value={standardsLinkForm.note} onChange={(event) => setStandardsLinkForm((form) => ({ ...form, note: event.target.value }))} placeholder="방수 리스크 검토 근거" rows={3} />
            </label>
            <button className="btn btn-primary" type="submit" disabled={standardsLinkActions.create.isPending}>
              {standardsLinkActions.create.isPending ? '저장 중...' : '기준 연결 저장'}
            </button>
          </form>
          {standardsLinkActions.create.error && <div className="empty-state">기준 연결 저장에 실패했습니다. 기준 코드를 확인하세요.</div>}
          {isStandardsLinksLoading && <div className="empty-state">기준 연결 목록을 불러오는 중입니다...</div>}
          {standardsLinksError && <div className="empty-state">기준 연결 목록을 불러오지 못했습니다.</div>}
          {standardsLinks && standardsLinks.items.length > 0 && (
            <div className="table-container" style={{ marginTop: '12px' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>대상</th>
                    <th>기준</th>
                    <th>조항</th>
                    <th>메모</th>
                  </tr>
                </thead>
                <tbody>
                  {standardsLinks.items.slice(0, 5).map((item) => (
                    <tr key={item.id} className="knowledge-row">
                      <td>{item.target_type} · {item.target_id}</td>
                      <td>{item.standard_code}<br /><span className="text-muted">{item.standard_name}</span></td>
                      <td>{item.clause_path} {item.clause_label}</td>
                      <td>{item.note || '메모 없음'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>

      <div className="tabs">
        <button className={`tab-btn ${statusFilter === 'all' ? 'active' : ''}`} type="button" onClick={() => setStatusFilter('all')}>전체</button>
        <button className={`tab-btn ${statusFilter === 'pending_review' ? 'active' : ''}`} type="button" onClick={() => setStatusFilter('pending_review')}>검토 대기</button>
        <button className={`tab-btn ${statusFilter === 'verified' ? 'active' : ''}`} type="button" onClick={() => setStatusFilter('verified')}>검증 완료</button>
        <button className={`tab-btn ${statusFilter === 'rejected' ? 'active' : ''}`} type="button" onClick={() => setStatusFilter('rejected')}>반려</button>
      </div>

      <Card title="등록 지식 검토 큐">
        {isLoading && <div className="empty-state">등록 지식 목록을 불러오는 중입니다...</div>}
        {error && <div className="empty-state">등록 지식 목록을 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}
        {data && data.items.length === 0 && <div className="empty-state">표시할 등록 지식이 없습니다.</div>}
        {data && data.items.length > 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>등록 시각</th>
                  <th>유형</th>
                  <th>제목</th>
                  <th>태그</th>
                  <th>상태</th>
                  <th>데이터 버전</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="knowledge-row">
                    <td className="text-muted">{formatDate(item.created_at)}</td>
                    <td>{ITEM_TYPES.find((type) => type.value === item.item_type)?.label ?? item.item_type}</td>
                    <td><span className="knowledge-title">{item.title}</span><br /><span className="text-muted">{item.source || '출처 미입력'}</span></td>
                    <td>{item.tags.length ? item.tags.join(', ') : '태그 없음'}</td>
                    <td><span className="badge">{STATUS_LABELS[item.verification_status]}</span></td>
                    <td className="text-muted">{item.data_version.source_file}</td>
                    <td>
                      <button className="btn btn-secondary btn-sm" type="button" disabled={item.verification_status === 'verified' || actions.updateStatus.isPending} onClick={() => updateStatus(item.id, 'verified')}>검증</button>{' '}
                      <button className="btn btn-secondary btn-sm" type="button" disabled={item.verification_status === 'rejected' || actions.updateStatus.isPending} onClick={() => updateStatus(item.id, 'rejected')}>반려</button>
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
