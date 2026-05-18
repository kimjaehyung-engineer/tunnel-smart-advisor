import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { act, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Workspace from './Workspace';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const graphHandlers = vi.hoisted(() => ({
  click: undefined as ((params: { nodes: string[] }) => void) | undefined,
}));

vi.mock('vis-network/standalone', () => ({
  Network: class {
    on = vi.fn((event: string, handler: (params: { nodes: string[] }) => void) => {
      if (event === 'click') {
        graphHandlers.click = handler;
      }
    });

    redraw = vi.fn();

    fit = vi.fn();

    destroy = vi.fn();
  },
}));

const API_BASE = 'http://127.0.0.1:8080';

const nodeResponses = {
  process: { type: 'process', nodes: [{ 'id:ID': 'Process_001', ':LABEL': 'Process', name: '굴착' }] },
  ground: { type: 'ground', nodes: [{ 'id:ID': 'Ground_001', ':LABEL': 'Ground', condition_name: '파쇄대' }] },
  location: { type: 'location', nodes: [{ 'id:ID': 'Location_001', ':LABEL': 'Location', loc_name: '도심지' }] },
  method: { type: 'method', nodes: [{ 'id:ID': 'Method_001', ':LABEL': 'Method', method_name: 'NATM' }] },
  equipment: { type: 'equipment', nodes: [{ 'id:ID': 'Equipment_001', ':LABEL': 'Equipment', equip_name: '굴착기' }] },
  impact: { type: 'impact', nodes: [{ 'id:ID': 'Impact_001', ':LABEL': 'Impact', impact_type: '침하' }] },
};

const workspaceReferenceHandlers = () => [
  ...Object.entries(nodeResponses).map(([type, body]) => (
    http.get(`${API_BASE}/nodes/${type}`, () => HttpResponse.json(body))
  )),
  http.get(`${API_BASE}/conditions`, () => HttpResponse.json({ items: [] })),
  http.get(`${API_BASE}/standards/evidence`, () => HttpResponse.json({
    query: '기준',
    source: 'KCSC Standards MCP seed evidence',
    items: [{
      code: 'KCS 27 30 00',
      name: '터널 지보재 시공',
      version: '2023',
      source_url: 'https://kcsc.re.kr/OpenApi/CodeViewer/KCS/273000',
      section_path: ['3. 시공', '3.1 시공조건확인'],
      section_label: '(4)',
      text: '터널지보재는 적합한 방법으로 적절한 시기와 순서에 따라 시공하여야 한다.',
      confidence: 'KCSC MCP 원문 직접 근거',
    }],
  })),
];

describe('Workspace', () => {
  it('submits analysis and renders risk cards, graph evidence, and actions', async () => {
    server.use(
      ...workspaceReferenceHandlers(),
      http.post(`${API_BASE}/score/`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ query: '지하수 유입' });

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
            matched: '파쇄대 | 지하수',
            strategies: ['차수 그라우팅', '배수로 확보'],
          }],
          graph: {
            nodes: [{ id: 'Risk_001', label: 'Risk', title: '지하수 유입 위험', color: '#ef4444', size: 45 }],
            edges: [],
          },
          data_version: {
            source_file: '터널.xlsx',
            source_file_hash: 'abcdef1234567890',
            source_file_mtime: '2026-05-18T00:00:00+00:00',
            ontology_build_at: '2026-05-18T00:00:00+00:00',
          },
          model_version: 'p1_rule_components_v1',
          recommendations: [{
            type: 'missing_condition',
            title: '지하수·용수 유입 추가 검토 권고',
            reason: '파쇄대 조건에서는 지하수 유입을 함께 검토해야 합니다.',
            suggested_filter: { query: '지하수 유입' },
          }],
        });
      }),
    );

    renderWithClient(<Workspace />);

    expect(await screen.findByText('파쇄대')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText('예: 도심지 강구부에서 굴착 중 파쇄대 조우 시 대책'), '지하수 유입');
    await userEvent.click(screen.getByRole('button', { name: '분석 실행' }));

    expect(await screen.findAllByText('지하수 유입 위험')).toHaveLength(2);
    expect(screen.getByText('데이터: 터널.xlsx · abcdef123456 · 모델: p1_rule_components_v1')).toBeInTheDocument();
    expect(screen.getAllByText('차수 그라우팅')).toHaveLength(2);
    expect(screen.getByText('지하수·용수 유입 추가 검토 권고')).toBeInTheDocument();
    expect(screen.getByText('노드 크기 45')).toBeInTheDocument();
  });

  it('filters rendered risks by selected risk level', async () => {
    server.use(
      ...workspaceReferenceHandlers(),
      http.post(`${API_BASE}/score/`, () => HttpResponse.json({
        total_risks: 2,
        critical_count: 1,
        max_score: 10,
        risks: [
          {
            id: 'Risk_001',
            description: '지하수 유입 위험',
            score: 10,
            level: '최상위 위험',
            color: '#ef4444',
            matched: '파쇄대 | 지하수',
            strategies: ['차수 그라우팅'],
          },
          {
            id: 'Risk_002',
            description: '장비 반입 지연 위험',
            score: 3,
            level: '저위험',
            color: '#22c55e',
            matched: '굴착기',
            strategies: ['반입 동선 사전 검토'],
          },
        ],
        graph: {
          nodes: [],
          edges: [],
        },
      })),
    );

    renderWithClient(<Workspace />);

    await userEvent.click(screen.getByRole('button', { name: '분석 실행' }));

    expect(await screen.findByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.getByText('장비 반입 지연 위험')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('checkbox', { name: /최상위 위험/ }));

    expect(screen.getByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.queryByText('장비 반입 지연 위험')).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('checkbox', { name: /전체/ }));

    expect(screen.getByText('장비 반입 지연 위험')).toBeInTheDocument();
  });

  it('shows graph node details after selecting a graph node', async () => {
    server.use(
      ...workspaceReferenceHandlers(),
      http.post(`${API_BASE}/score/`, () => HttpResponse.json({
        total_risks: 1,
        critical_count: 1,
        max_score: 10,
        risks: [{
          id: 'Risk_001',
          description: '지하수 유입 위험',
          score: 10,
          level: '최상위 위험',
          color: '#ef4444',
          matched: '파쇄대 | 지하수',
          strategies: ['차수 그라우팅'],
        }],
        graph: {
          nodes: [
            { id: 'Ground_001', label: 'Condition', title: '파쇄대', color: '#64748b', size: 35 },
            {
              id: 'Risk_001',
              label: 'Critical Risk',
              title: '지하수 유입 위험',
              color: '#ef4444',
              size: 45,
              detail: {
                project: 'Alpha Project',
                sourceLL: 'LL 원문 위험 내용',
                cause: '지하수 유입 원인',
                impactText: '라이닝 품질 저하',
                matched: ['파쇄대', '지하수'],
                strategies: ['차수 그라우팅'],
                impacts: ['침하'],
                standards: ['KCS 27 20 00'],
                roles: ['시공사'],
              },
            },
          ],
          edges: [{ from: 'Ground_001', to: 'Risk_001', title: 'RELATES_TO', color: '#94a3b8' }],
        },
      })),
    );

    renderWithClient(<Workspace />);

    await userEvent.click(screen.getByRole('button', { name: '분석 실행' }));
    expect(await screen.findByText('그래프 노드를 클릭하면 상세 정보가 표시됩니다.')).toBeInTheDocument();

    act(() => {
      graphHandlers.click?.({ nodes: ['Risk_001'] });
    });

    expect(screen.getAllByText('Critical Risk').length).toBeGreaterThan(0);
    expect(screen.getAllByText('지하수 유입 위험').length).toBeGreaterThan(0);
    expect(screen.getByText('RELATES_TO')).toBeInTheDocument();
    expect(screen.getByText('Alpha Project')).toBeInTheDocument();
    expect(screen.getByText('LL 원문 위험 내용')).toBeInTheDocument();
    expect(screen.getByText('지하수 유입 원인')).toBeInTheDocument();
    expect(screen.getByText('라이닝 품질 저하')).toBeInTheDocument();
    expect(screen.getAllByText('차수 그라우팅').length).toBeGreaterThan(0);
    expect(screen.getByText('KCS 27 20 00')).toBeInTheDocument();
    expect(await screen.findByText(/터널지보재는 적합한 방법/)).toBeInTheDocument();
    expect(screen.getByText('시공사')).toBeInTheDocument();
  });

  it('saves the current condition set', async () => {
    server.use(
      ...workspaceReferenceHandlers(),
      http.post(`${API_BASE}/conditions`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ ground: '파쇄대', query: '지하수' });

        return HttpResponse.json({
          id: 1,
          created_at: '2026-05-18T00:00:00+00:00',
          title: '파쇄대 / 지하수',
          query: '지하수',
          filters: {
            process: null,
            ground: '파쇄대',
            location: null,
            method: null,
            equipment: null,
            impact: null,
          },
        }, { status: 201 });
      }),
    );

    renderWithClient(<Workspace />);

    expect(await screen.findByText('파쇄대')).toBeInTheDocument();
    await userEvent.selectOptions(await screen.findByLabelText('2. 지반'), '파쇄대');
    await userEvent.type(screen.getByPlaceholderText('예: 도심지 강구부에서 굴착 중 파쇄대 조우 시 대책'), '지하수');
    await userEvent.click(screen.getByRole('button', { name: '조건 저장' }));

    expect(await screen.findByText('조건이 저장되었습니다: 파쇄대 / 지하수')).toBeInTheDocument();
  });

  it('loads and deletes saved conditions', async () => {
    server.use(
      ...Object.entries(nodeResponses).map(([type, body]) => (
        http.get(`${API_BASE}/nodes/${type}`, () => HttpResponse.json(body))
      )),
      http.get(`${API_BASE}/conditions`, () => HttpResponse.json({
        items: [{
          id: 7,
          created_at: '2026-05-18T00:00:00+00:00',
          title: '파쇄대 / 지하수',
          query: '지하수',
          filters: {
            process: null,
            ground: '파쇄대',
            location: null,
            method: null,
            equipment: null,
            impact: null,
          },
        }],
      })),
      http.delete(`${API_BASE}/conditions/7`, () => HttpResponse.json({ id: 7, deleted: true })),
    );

    renderWithClient(<Workspace />);

    await userEvent.click(await screen.findByRole('button', { name: '파쇄대 / 지하수' }));

    expect(screen.getByPlaceholderText('예: 도심지 강구부에서 굴착 중 파쇄대 조우 시 대책')).toHaveValue('지하수');
    expect(screen.getByText('저장된 조건을 불러왔습니다. 분석 실행을 눌러 결과를 확인하세요.')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '파쇄대 / 지하수 삭제' }));

    expect(await screen.findByText('저장된 조건을 삭제했습니다.')).toBeInTheDocument();
  });
});
