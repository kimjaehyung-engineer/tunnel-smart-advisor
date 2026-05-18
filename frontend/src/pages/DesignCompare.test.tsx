import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DesignCompare from './DesignCompare';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

const nodeResponses = {
  process: { type: 'process', nodes: [{ 'id:ID': 'Process_001', ':LABEL': 'Process', name: '굴착' }] },
  ground: { type: 'ground', nodes: [{ 'id:ID': 'Ground_001', ':LABEL': 'Ground', condition_name: '파쇄대' }] },
  location: { type: 'location', nodes: [{ 'id:ID': 'Location_001', ':LABEL': 'Location', loc_name: '도심지' }] },
  method: { type: 'method', nodes: [{ 'id:ID': 'Method_001', ':LABEL': 'Method', method_name: 'NATM' }] },
  equipment: { type: 'equipment', nodes: [{ 'id:ID': 'Equipment_001', ':LABEL': 'Equipment', equip_name: '굴착기' }] },
  impact: { type: 'impact', nodes: [{ 'id:ID': 'Impact_001', ':LABEL': 'Impact', impact_type: '침하' }] },
};

describe('DesignCompare', () => {
  it('submits before and after conditions and renders comparison deltas', async () => {
    server.use(
      ...Object.entries(nodeResponses).map(([type, body]) => (
        http.get(`${API_BASE}/nodes/${type}`, () => HttpResponse.json(body))
      )),
      http.post(`${API_BASE}/compare/design-change`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({
          before: { query: '기존 조건' },
          after: { ground: '파쇄대', query: '변경 조건' },
        });
        return HttpResponse.json({
          model_version: 'p1_rule_components_v1',
          before: { total_risks: 0, max_score: 0, critical_count: 0 },
          after: { total_risks: 2, max_score: 8, critical_count: 1 },
          new_risks: [{ id: 'Risk_001', description: '지하수 유입 위험', score: 8, level: '최상위 위험', color: '#ef4444', matched: ['파쇄대'] }],
          removed_risks: [],
          increased_risks: [],
          decreased_risks: [],
          additional_strategies: ['차수 그라우팅'],
          related_standards: ['KCS 27 50 05'],
        });
      }),
      http.post(`${API_BASE}/compare/design-change/reports`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({
          before: { query: '기존 조건' },
          after: { ground: '파쇄대', query: '변경 조건' },
        });
        return HttpResponse.json({
          id: 1,
          report_type: 'comparison',
          title: '설계변경 비교 리포트 - 2026-05-18',
          created_at: '2026-05-18T00:00:00+00:00',
          download_url: '/reports/compare/1.html',
          pdf_url: '/reports/compare/1.pdf',
          package_url: '/reports/compare/1.zip',
          model_version: 'p1_rule_components_v1',
          data_version: { source_file: 'source.xlsx', source_file_hash: 'hash', source_file_mtime: '', ontology_build_at: '' },
        }, { status: 201 });
      }),
    );

    renderWithClient(<DesignCompare />);

    expect(await screen.findAllByText('파쇄대')).toHaveLength(2);
    await userEvent.type(screen.getByPlaceholderText('변경 전 자연어 맥락'), '기존 조건');
    await userEvent.selectOptions(screen.getAllByLabelText('2. 지반')[1], '파쇄대');
    await userEvent.type(screen.getByPlaceholderText('변경 후 자연어 맥락'), '변경 조건');
    await userEvent.click(screen.getByRole('button', { name: '비교 실행' }));

    expect(await screen.findByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.getByText('차수 그라우팅')).toBeInTheDocument();
    expect(screen.getByText('KCS 27 50 05')).toBeInTheDocument();
    expect(screen.getByText('p1_rule_components_v1')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: '비교 리포트 저장' }));
    expect(await screen.findByRole('link', { name: 'HTML 열기' })).toHaveAttribute('href', `${API_BASE}/reports/compare/1.html`);
  });
});
