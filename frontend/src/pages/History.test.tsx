import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import History from './History';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('History', () => {
  it('renders analysis history from the backend and filters by search', async () => {
    server.use(
      http.get(`${API_BASE}/history/analyses`, ({ request }) => {
        const url = new URL(request.url);
        const query = url.searchParams.get('query') ?? '';
        const project = url.searchParams.get('project') ?? '';
        const items = [{
          id: 1,
          created_at: '2026-05-15T00:00:00+00:00',
          query: project || query || '지하수',
          filters: { process: null, ground: '파쇄대', location: null, method: null, equipment: null, impact: null },
          top_risk: '지하수 유입 위험',
          total_risks: 3,
          critical_count: 1,
          max_score: 8,
          model_version: 'p1_rule_components_v1',
        }];
        return HttpResponse.json({ items });
      }),
      http.post(`${API_BASE}/history/analyses/1/rerun`, () => HttpResponse.json({
        total_risks: 1,
        critical_count: 0,
        max_score: 4,
        risks: [],
        graph: { nodes: [], edges: [] },
        history_id: 2,
      })),
    );

    renderWithClient(<History />);

    expect(await screen.findByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.getByText('파쇄대')).toBeInTheDocument();
    expect(screen.getByText('p1_rule_components_v1')).toBeInTheDocument();

    await userEvent.clear(screen.getByPlaceholderText('검색어, 위험명, 조건 검색'));
    await userEvent.type(screen.getByPlaceholderText('검색어, 위험명, 조건 검색'), '장비');

    expect(await screen.findByText('장비')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText('프로젝트명 필터'), 'Alpha Project');
    await userEvent.selectOptions(screen.getByDisplayValue('전체 기간'), '7d');

    expect(await screen.findByText('Alpha Project')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '재실행' }));
    expect(await screen.findByRole('button', { name: '재실행' })).toBeInTheDocument();
  });
});
