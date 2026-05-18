import type { AnalysisHistoryFilters, AnalysisHistoryResponse, DashboardSummary, DeleteConditionResponse, DesignCompareReportResponse, DesignCompareRequest, DesignCompareResponse, KnowledgeItemType, KnowledgeStatusRequest, KnowledgeSubmissionItem, KnowledgeSubmissionRequest, KnowledgeSubmissionsResponse, KnowledgeVerificationStatus, LibraryFilters, LibraryItemDetail, LibraryResponse, NodeItem, NotificationFilter, NotificationItem, NotificationsResponse, ReportItem, ReportsResponse, SavedCondition, SavedConditionsResponse, ScoreRequest, ScoreResponse, StandardEvidenceResponse, StandardsClausesResponse, StandardsLinkItem, StandardsLinkRequest, StandardsLinksResponse, StandardsRevalidationResponse, StandardsSearchResponse, StandardsVerifyResponse } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8080';

export async function fetchNodes(type: string): Promise<{ nodes: NodeItem[]; type: string }> {
  const response = await fetch(`${API_BASE}/nodes/${type}`);
  if (!response.ok) {
    throw new Error(`노드 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function scoreRisks(request: ScoreRequest): Promise<ScoreResponse> {
  const response = await fetch(`${API_BASE}/score/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`위험도 분석에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function compareDesignChange(request: DesignCompareRequest): Promise<DesignCompareResponse> {
  const response = await fetch(`${API_BASE}/compare/design-change`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`설계변경 비교에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function createDesignCompareReport(request: DesignCompareRequest): Promise<DesignCompareReportResponse> {
  const response = await fetch(`${API_BASE}/compare/design-change/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`설계변경 비교 리포트 생성에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function saveCondition(request: ScoreRequest): Promise<SavedCondition> {
  const response = await fetch(`${API_BASE}/conditions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`조건 저장에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchSavedConditions(): Promise<SavedConditionsResponse> {
  const response = await fetch(`${API_BASE}/conditions`);
  if (!response.ok) {
    throw new Error(`저장 조건 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function deleteSavedCondition(conditionId: number): Promise<DeleteConditionResponse> {
  const response = await fetch(`${API_BASE}/conditions/${conditionId}`, { method: 'DELETE' });
  if (!response.ok) {
    throw new Error(`저장 조건 삭제에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE}/dashboard/summary`);
  if (!response.ok) {
    throw new Error(`대시보드 요약을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchLibraryItems(filters: LibraryFilters = {}): Promise<LibraryResponse> {
  const params = new URLSearchParams();
  if (filters.query?.trim()) {
    params.set('query', filters.query.trim());
  }
  if (filters.category?.trim() && filters.category !== '전체') {
    params.set('category', filters.category.trim());
  }
  if (filters.tag?.trim() && filters.tag !== '전체') {
    params.set('tag', filters.tag.trim());
  }
  if (filters.relationType?.trim() && filters.relationType !== '전체') {
    params.set('relation_type', filters.relationType.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/library/items${suffix}`);
  if (!response.ok) {
    throw new Error(`지식 라이브러리를 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchLibraryItemDetail(riskId: string): Promise<LibraryItemDetail> {
  const response = await fetch(`${API_BASE}/library/items/${encodeURIComponent(riskId)}`);
  if (!response.ok) {
    throw new Error(`지식 상세를 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchKnowledgeSubmissions(filters: { itemType?: KnowledgeItemType; verificationStatus?: KnowledgeVerificationStatus } = {}): Promise<KnowledgeSubmissionsResponse> {
  const params = new URLSearchParams();
  if (filters.itemType) {
    params.set('item_type', filters.itemType);
  }
  if (filters.verificationStatus) {
    params.set('verification_status', filters.verificationStatus);
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/admin/knowledge/items${suffix}`);
  if (!response.ok) {
    throw new Error(`지식 등록 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function createKnowledgeSubmission(request: KnowledgeSubmissionRequest): Promise<KnowledgeSubmissionItem> {
  const response = await fetch(`${API_BASE}/admin/knowledge/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`지식 등록에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function updateKnowledgeSubmissionStatus(id: number, request: KnowledgeStatusRequest): Promise<KnowledgeSubmissionItem> {
  const response = await fetch(`${API_BASE}/admin/knowledge/items/${id}/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`지식 검증 상태 변경에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchStandardEvidence(query: string): Promise<StandardEvidenceResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('query', query.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/standards/evidence${suffix}`);
  if (!response.ok) {
    throw new Error(`기준 근거를 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function searchStandards(query: string): Promise<StandardsSearchResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('query', query.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/standards/search${suffix}`);
  if (!response.ok) {
    throw new Error(`기준 검색에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchStandardClauses(query: string, code = ''): Promise<StandardsClausesResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('query', query.trim());
  }
  if (code.trim()) {
    params.set('code', code.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/standards/clauses${suffix}`);
  if (!response.ok) {
    throw new Error(`기준 조항 검색에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function verifyStandardCode(code: string): Promise<StandardsVerifyResponse> {
  const params = new URLSearchParams({ code });
  const response = await fetch(`${API_BASE}/standards/verify?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`기준 코드 검증에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function revalidateStandards(): Promise<StandardsRevalidationResponse> {
  const response = await fetch(`${API_BASE}/standards/revalidate`, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`기준 재검증에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchStandardsLinks(filters: { targetType?: 'risk' | 'strategy'; targetId?: string; standardCode?: string } = {}): Promise<StandardsLinksResponse> {
  const params = new URLSearchParams();
  if (filters.targetType) {
    params.set('target_type', filters.targetType);
  }
  if (filters.targetId?.trim()) {
    params.set('target_id', filters.targetId.trim());
  }
  if (filters.standardCode?.trim()) {
    params.set('standard_code', filters.standardCode.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/standards/links${suffix}`);
  if (!response.ok) {
    throw new Error(`기준 연결 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function createStandardsLink(request: StandardsLinkRequest): Promise<StandardsLinkItem> {
  const response = await fetch(`${API_BASE}/standards/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`기준 연결 저장에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchAnalysisHistory(filters: string | AnalysisHistoryFilters = ''): Promise<AnalysisHistoryResponse> {
  const params = new URLSearchParams();
  const normalizedFilters: AnalysisHistoryFilters = typeof filters === 'string' ? { query: filters } : filters;
  if (normalizedFilters.query?.trim()) {
    params.set('query', normalizedFilters.query.trim());
  }
  if (normalizedFilters.project?.trim()) {
    params.set('project', normalizedFilters.project.trim());
  }
  if (normalizedFilters.dateFrom?.trim()) {
    params.set('date_from', normalizedFilters.dateFrom.trim());
  }
  if (normalizedFilters.dateTo?.trim()) {
    params.set('date_to', normalizedFilters.dateTo.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/history/analyses${suffix}`);
  if (!response.ok) {
    throw new Error(`분석 이력을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function rerunAnalysis(historyId: number): Promise<ScoreResponse> {
  const response = await fetch(`${API_BASE}/history/analyses/${historyId}/rerun`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`분석 재실행에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchReports(query = ''): Promise<ReportsResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('query', query.trim());
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/reports${suffix}`);
  if (!response.ok) {
    throw new Error(`리포트 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function setReportShared(historyId: number, shared: boolean): Promise<ReportItem> {
  const response = await fetch(`${API_BASE}/reports/${historyId}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ shared }),
  });
  if (!response.ok) {
    throw new Error(`리포트 공유 상태 변경에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function fetchNotifications(filter: NotificationFilter = 'all'): Promise<NotificationsResponse> {
  const params = new URLSearchParams();
  if (filter !== 'all') {
    params.set('filter', filter);
  }
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/notifications${suffix}`);
  if (!response.ok) {
    throw new Error(`알림 목록을 불러오지 못했습니다: ${response.status}`);
  }
  return response.json();
}

export async function markNotificationRead(notificationId: number): Promise<NotificationItem> {
  const response = await fetch(`${API_BASE}/notifications/${notificationId}/read`, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`알림 읽음 처리에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function setNotificationImportant(notificationId: number, isImportant: boolean): Promise<NotificationItem> {
  const response = await fetch(`${API_BASE}/notifications/${notificationId}/important`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ is_important: isImportant }),
  });
  if (!response.ok) {
    throw new Error(`알림 중요 상태 변경에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function archiveNotification(notificationId: number): Promise<NotificationItem> {
  const response = await fetch(`${API_BASE}/notifications/${notificationId}`, { method: 'DELETE' });
  if (!response.ok) {
    throw new Error(`알림 보관에 실패했습니다: ${response.status}`);
  }
  return response.json();
}

export async function markAllNotificationsRead(): Promise<NotificationsResponse> {
  const response = await fetch(`${API_BASE}/notifications/read-all`, { method: 'POST' });
  if (!response.ok) {
    throw new Error(`전체 알림 읽음 처리에 실패했습니다: ${response.status}`);
  }
  return response.json();
}
