import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { createDesignCompareReport, createKnowledgeSubmission, fetchAnalysisHistory, fetchDashboardSummary, fetchKnowledgeSubmissions, fetchLibraryItems, fetchNodes, fetchNotifications, fetchReports, fetchStandardClauses, markAllNotificationsRead, markNotificationRead, rerunAnalysis, revalidateStandards, scoreRisks, searchStandards, setNotificationImportant, setReportShared, updateKnowledgeSubmissionStatus, verifyStandardCode } from './client';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('API client', () => {
  it('fetches node lists from the backend API', async () => {
    server.use(
      http.get(`${API_BASE}/nodes/ground`, () => HttpResponse.json({
        type: 'ground',
        nodes: [{ 'id:ID': 'Ground_001', ':LABEL': 'Ground', condition_name: '파쇄대' }],
      })),
    );

    await expect(fetchNodes('ground')).resolves.toEqual({
      type: 'ground',
      nodes: [{ 'id:ID': 'Ground_001', ':LABEL': 'Ground', condition_name: '파쇄대' }],
    });
  });

  it('throws a helpful error when node list loading fails', async () => {
    server.use(
      http.get(`${API_BASE}/nodes/ground`, () => new HttpResponse(null, { status: 500 })),
    );

    await expect(fetchNodes('ground')).rejects.toThrow('노드 목록을 불러오지 못했습니다: 500');
  });

  it('posts score requests and returns score responses', async () => {
    server.use(
      http.post(`${API_BASE}/score/`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ ground: '파쇄대', query: '지하수' });

        return HttpResponse.json({
          total_risks: 1,
          critical_count: 1,
          max_score: 10,
          risks: [{
            id: 'Risk_001',
            description: '지하수 유입 위험',
            score: 10,
            level: '최상위 위험',
            color: '#ef4444',
            cluster_band: 'B1',
            cluster_label: '군집 B1 (상위 점수군)',
            matched: '파쇄대',
            strategies: ['차수 그라우팅'],
          }],
          graph: { nodes: [], edges: [] },
        });
      }),
    );

    const result = await scoreRisks({
      process: null,
      ground: '파쇄대',
      location: null,
      method: null,
      equipment: null,
      impact: null,
      query: '지하수',
    });

    expect(result.total_risks).toBe(1);
    expect(result.risks[0].description).toBe('지하수 유입 위험');
  });

  it('creates design comparison reports', async () => {
    server.use(
      http.post(`${API_BASE}/compare/design-change/reports`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ after: { ground: '파쇄대', query: '변경 조건' } });
        return HttpResponse.json({
          id: 1,
          report_type: 'comparison',
          title: '설계변경 비교 리포트',
          created_at: '2026-05-18T00:00:00+00:00',
          download_url: '/reports/compare/1.html',
          pdf_url: '/reports/compare/1.pdf',
          package_url: '/reports/compare/1.zip',
          model_version: 'p1_rule_components_v1',
          data_version: { source_file: 'source.xlsx', source_file_hash: 'hash', source_file_mtime: '', ontology_build_at: '' },
        }, { status: 201 });
      }),
    );

    await expect(createDesignCompareReport({
      before: { process: null, ground: null, location: null, method: null, equipment: null, impact: null, query: '' },
      after: { process: null, ground: '파쇄대', location: null, method: null, equipment: null, impact: null, query: '변경 조건' },
    })).resolves.toMatchObject({ report_type: 'comparison', download_url: '/reports/compare/1.html' });
  });

  it('fetches dashboard and library content endpoints', async () => {
    server.use(
      http.get(`${API_BASE}/dashboard/summary`, () => HttpResponse.json({
        kpis: [],
        distribution: [],
        trend: [],
        recentAnalyses: [],
        notifications: [],
      })),
      http.get(`${API_BASE}/library/items`, () => HttpResponse.json({
        items: [],
        categories: [{ label: '전체', count: 0 }],
        popularTags: [],
        relationTypes: [{ label: '전체', count: 0 }],
      })),
    );

    await expect(fetchDashboardSummary()).resolves.toMatchObject({ kpis: [] });
    await expect(fetchLibraryItems()).resolves.toMatchObject({ categories: [{ label: '전체', count: 0 }] });
  });

  it('manages admin knowledge submissions', async () => {
    server.use(
      http.get(`${API_BASE}/admin/knowledge/items`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('item_type')).toBe('lesson');
        expect(url.searchParams.get('verification_status')).toBe('pending_review');
        return HttpResponse.json({ items: [{ id: 1, item_type: 'lesson', title: '지하수 사례', verification_status: 'pending_review' }] });
      }),
      http.post(`${API_BASE}/admin/knowledge/items`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ item_type: 'lesson', title: '지하수 사례' });
        return HttpResponse.json({ id: 1, item_type: 'lesson', title: '지하수 사례', verification_status: 'pending_review' }, { status: 201 });
      }),
      http.post(`${API_BASE}/admin/knowledge/items/1/status`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ verification_status: 'verified', reviewer: 'admin' });
        return HttpResponse.json({ id: 1, verification_status: 'verified', reviewer: 'admin' });
      }),
    );

    await expect(fetchKnowledgeSubmissions({ itemType: 'lesson', verificationStatus: 'pending_review' })).resolves.toMatchObject({ items: [{ id: 1 }] });
    await expect(createKnowledgeSubmission({ item_type: 'lesson', title: '지하수 사례', content: '검토 내용' })).resolves.toMatchObject({ verification_status: 'pending_review' });
    await expect(updateKnowledgeSubmissionStatus(1, { verification_status: 'verified', reviewer: 'admin' })).resolves.toMatchObject({ verification_status: 'verified' });
  });

  it('fetches analysis history with optional search query', async () => {
    server.use(
      http.get(`${API_BASE}/history/analyses`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('query')).toBe('지하수');
        return HttpResponse.json({
          items: [{
            id: 1,
            created_at: '2026-05-15T00:00:00+00:00',
            query: '지하수',
            filters: { process: null, ground: null, location: null, method: null, equipment: null, impact: null },
            top_risk: '지하수 유입 위험',
            total_risks: 1,
            critical_count: 0,
            max_score: 2,
          }],
        });
      }),
    );

    await expect(fetchAnalysisHistory('지하수')).resolves.toMatchObject({
      items: [{ id: 1, query: '지하수' }],
    });
  });

  it('fetches analysis history with project and date filters', async () => {
    server.use(
      http.get(`${API_BASE}/history/analyses`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('query')).toBe('지하수');
        expect(url.searchParams.get('project')).toBe('Alpha Project');
        expect(url.searchParams.get('date_from')).toBe('2026-05-01T00:00:00.000Z');
        return HttpResponse.json({ items: [] });
      }),
    );

    await expect(fetchAnalysisHistory({
      query: '지하수',
      project: 'Alpha Project',
      dateFrom: '2026-05-01T00:00:00.000Z',
    })).resolves.toMatchObject({ items: [] });
  });

  it('fetches report list with optional search query', async () => {
    server.use(
      http.get(`${API_BASE}/reports`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('query')).toBe('파쇄대');
        return HttpResponse.json({
          items: [{
            id: 1,
            history_id: 1,
            title: '터널 위험 분석 리포트 #1 - 파쇄대',
            created_at: '2026-05-15T00:00:00+00:00',
            top_risk: '지하수 유입 위험',
            total_risks: 2,
            critical_count: 1,
            max_score: 8,
            format: 'HTML',
            download_url: '/reports/1.html',
            pdf_url: '/reports/1.pdf',
            shared: false,
          }],
          summary: { total: 1, shared: 0, html: 1 },
        });
      }),
    );

    await expect(fetchReports('파쇄대')).resolves.toMatchObject({
      summary: { total: 1 },
      items: [{ download_url: '/reports/1.html' }],
    });
  });

  it('reruns a saved analysis history item', async () => {
    server.use(
      http.post(`${API_BASE}/history/analyses/1/rerun`, () => HttpResponse.json({
        total_risks: 1,
        critical_count: 0,
        max_score: 4,
        risks: [],
        graph: { nodes: [], edges: [] },
        history_id: 2,
      })),
    );

    await expect(rerunAnalysis(1)).resolves.toMatchObject({ history_id: 2 });
  });

  it('manages notifications through the backend API', async () => {
    server.use(
      http.get(`${API_BASE}/notifications`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('filter')).toBe('unread');
        return HttpResponse.json({
          items: [{
            id: 1,
            created_at: '2026-05-15T00:00:00+00:00',
            category: 'analysis',
            title: '분석 완료',
            message: '분석 #1이 완료되었습니다.',
            is_read: false,
            is_important: false,
          }],
          summary: { total: 1, unread: 1, important: 0 },
        });
      }),
      http.post(`${API_BASE}/notifications/1/read`, () => HttpResponse.json({ id: 1, is_read: true })),
      http.post(`${API_BASE}/notifications/1/important`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ is_important: true });
        return HttpResponse.json({ id: 1, is_important: true });
      }),
      http.post(`${API_BASE}/notifications/read-all`, () => HttpResponse.json({ items: [], summary: { total: 1, unread: 0, important: 0 } })),
    );

    await expect(fetchNotifications('unread')).resolves.toMatchObject({ summary: { unread: 1 } });
    await expect(markNotificationRead(1)).resolves.toMatchObject({ is_read: true });
    await expect(setNotificationImportant(1, true)).resolves.toMatchObject({ is_important: true });
    await expect(markAllNotificationsRead()).resolves.toMatchObject({ summary: { unread: 0 } });
  });

  it('updates report shared state', async () => {
    server.use(
      http.post(`${API_BASE}/reports/1/share`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ shared: true });
        return HttpResponse.json({ id: 1, history_id: 1, shared: true });
      }),
    );

    await expect(setReportShared(1, true)).resolves.toMatchObject({ shared: true });
  });

  it('uses standards search, clause search, and verify endpoints', async () => {
    server.use(
      http.get(`${API_BASE}/standards/search`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('query')).toBe('방수');
        return HttpResponse.json({ query: '방수', source: 'seed', items: [{ code: 'KCS 27 50 05', name: '터널 배수 및 방수 공사', version: '2023', source_url: 'https://example.com', clause_count: 2 }] });
      }),
      http.get(`${API_BASE}/standards/clauses`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('query')).toBe('방수');
        expect(url.searchParams.get('code')).toBe('KCS 27 50 05');
        return HttpResponse.json({ query: '방수', code: 'KCS 27 50 05', source: 'seed', items: [{ code: 'KCS 27 50 05', name: '터널 배수 및 방수 공사', version: '2023', source_url: 'https://example.com', section_path: ['3. 시공'], section_label: '(7)', text: '방수', confidence: 'seed' }] });
      }),
      http.get(`${API_BASE}/standards/verify`, ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('code')).toBe('KCS 27 50 05');
        return HttpResponse.json({ code: 'KCS 27 50 05', is_valid: true, standard: { code: 'KCS 27 50 05', name: '터널 배수 및 방수 공사', version: '2023', source_url: 'https://example.com' }, clause_count: 2 });
      }),
      http.post(`${API_BASE}/standards/revalidate`, () => HttpResponse.json({ total: 1, verified_count: 0, candidate_count: 1, unknown_count: 0, source: 'seed', items: [{ id: 'STD_001', doc_name: '기준', status: 'matched_candidates', verified_code: '', candidate_codes: ['KCS 27 50 05'], message: 'matched' }] })),
    );

    await expect(searchStandards('방수')).resolves.toMatchObject({ items: [{ code: 'KCS 27 50 05' }] });
    await expect(fetchStandardClauses('방수', 'KCS 27 50 05')).resolves.toMatchObject({ items: [{ section_label: '(7)' }] });
    await expect(verifyStandardCode('KCS 27 50 05')).resolves.toMatchObject({ is_valid: true });
    await expect(revalidateStandards()).resolves.toMatchObject({ candidate_count: 1 });
  });
});
