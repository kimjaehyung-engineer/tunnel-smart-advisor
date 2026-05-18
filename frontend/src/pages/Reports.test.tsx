import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Reports from './Reports';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('Reports', () => {
  it('renders report list from the backend and filters by search', async () => {
    server.use(
      http.get(`${API_BASE}/reports`, ({ request }) => {
        const url = new URL(request.url);
        const query = url.searchParams.get('query') || '지하수';
        return HttpResponse.json({
          items: [{
            id: 1,
            history_id: 1,
            title: `터널 위험 분석 리포트 #1 - ${query}`,
            created_at: '2026-05-15T00:00:00+00:00',
            top_risk: '지하수 유입 위험',
            total_risks: 2,
            critical_count: 1,
            max_score: 8,
            format: 'HTML',
            download_url: '/reports/1.html',
            pdf_url: '/reports/1.pdf',
            package_url: '/reports/1.zip',
            shared: true,
            share_url: '/reports/shared/1.html',
            model_version: 'p1_rule_components_v1',
            report_type: 'analysis',
          }, {
            id: 'comparison-1',
            history_id: 1,
            title: '설계변경 비교 리포트 - 2026-05-18',
            created_at: '2026-05-18T00:00:00+00:00',
            top_risk: '설계변경 비교',
            total_risks: 2,
            critical_count: 1,
            max_score: 8,
            format: 'HTML',
            download_url: '/reports/compare/1.html',
            pdf_url: '/reports/compare/1.pdf',
            package_url: '/reports/compare/1.zip',
            shared: false,
            model_version: 'p1_rule_components_v1',
            report_type: 'comparison',
          }],
          summary: { total: 2, shared: 1, html: 2 },
        });
      }),
      http.post(`${API_BASE}/reports/1/share`, () => HttpResponse.json({ id: 1, history_id: 1, shared: true })),
    );

    renderWithClient(<Reports />);

    expect(await screen.findByText('터널 위험 분석 리포트 #1 - 지하수')).toBeInTheDocument();
    expect(screen.getByText('설계변경 비교 리포트 - 2026-05-18')).toBeInTheDocument();
    expect(screen.getByText('비교 리포트')).toBeInTheDocument();
    expect(screen.getByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.getAllByText('p1_rule_components_v1')).toHaveLength(2);
    expect(screen.getAllByRole('link', { name: 'HTML' })[0]).toHaveAttribute('href', `${API_BASE}/reports/1.html`);
    expect(screen.getAllByRole('link', { name: 'PDF' })[0]).toHaveAttribute('href', `${API_BASE}/reports/1.pdf`);
    expect(screen.getAllByRole('link', { name: '패키지' })[0]).toHaveAttribute('href', `${API_BASE}/reports/1.zip`);
    expect(screen.getAllByRole('link', { name: 'HTML' })[1]).toHaveAttribute('href', `${API_BASE}/reports/compare/1.html`);
    expect(screen.getByRole('link', { name: '공유 링크' })).toHaveAttribute('href', `${API_BASE}/reports/shared/1.html`);

    await userEvent.type(screen.getByPlaceholderText('리포트 제목, 위험명, 조건 검색'), '파쇄대');

    expect(await screen.findByText('터널 위험 분석 리포트 #1 - 파쇄대')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: '공유 해제' }));
    expect(await screen.findByRole('button', { name: '공유 해제' })).toBeInTheDocument();
  });
});
