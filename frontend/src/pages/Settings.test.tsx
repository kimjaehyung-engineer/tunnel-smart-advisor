import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Settings from './Settings';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('Settings', () => {
  it('registers knowledge submissions and supports status updates', async () => {
    server.use(
      http.get(`${API_BASE}/admin/knowledge/items`, () => HttpResponse.json({
        items: [{
          id: 1,
          created_at: '2026-05-18T00:00:00+00:00',
          updated_at: '2026-05-18T00:00:00+00:00',
          item_type: 'lesson',
          title: '도심지 지하수 유입 사례',
          content: '지하수 유입 검토 내용',
          tags: ['지하수', 'NATM'],
          source: '운영자 수기 등록',
          verification_status: 'pending_review',
          data_version: {
            source_file: '터널(NATM)표준체크리스트.xlsx',
            source_file_hash: 'hash',
            source_file_mtime: '2026-05-18T00:00:00+00:00',
            ontology_build_at: '2026-05-18T00:00:00+00:00',
          },
          reviewer: '',
          review_note: '',
        }],
      })),
      http.post(`${API_BASE}/admin/knowledge/items`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({
          item_type: 'lesson',
          title: '새 지식 등록',
          content: '추가 검토 내용',
          tags: ['지하수', '보강'],
        });
        return HttpResponse.json({ id: 2, verification_status: 'pending_review', title: '새 지식 등록' }, { status: 201 });
      }),
      http.post(`${API_BASE}/admin/knowledge/items/1/status`, async ({ request }) => {
        const body = await request.json();
        expect(body).toMatchObject({ verification_status: 'verified', reviewer: 'internal-admin' });
        return HttpResponse.json({ id: 1, verification_status: 'verified' });
      }),
      http.post(`${API_BASE}/standards/revalidate`, () => HttpResponse.json({
        total: 2,
        verified_count: 1,
        candidate_count: 1,
        unknown_count: 0,
        source: 'KCSC Standards MCP seed evidence',
        items: [{
          id: 'Standard_001',
          doc_name: '터널 배수 및 방수 공사',
          status: 'matched_candidates',
          verified_code: '',
          candidate_codes: ['KCS 27 50 05'],
          message: '후보 기준 코드가 확인되었습니다.',
        }],
      })),
      http.get(`${API_BASE}/standards/links`, () => HttpResponse.json({
        items: [{
          id: 1,
          created_at: '2026-05-18T00:00:00+00:00',
          updated_at: '2026-05-18T00:00:00+00:00',
          target_type: 'risk',
          target_id: 'Risk_001',
          standard_code: 'KCS 27 50 05',
          standard_name: '터널 배수 및 방수 공사',
          clause_path: '3. 시공 > 3.3 시공기준',
          clause_label: '(7)',
          clause_text: '지수판 설치 기준',
          source_url: 'https://kcsc.re.kr/OpenApi/CodeViewer/123',
          note: '기존 방수 근거',
        }],
      })),
      http.post(`${API_BASE}/standards/links`, async ({ request }) => {
        const body = await request.json() as Record<string, unknown>;
        expect(body).toMatchObject({
          target_type: 'risk',
          target_id: 'Risk_002',
          standard_code: 'KCS 27 50 05',
          clause_path: '3. 시공 > 3.3 시공기준',
        });
        return HttpResponse.json({ id: 2, ...body, standard_name: '터널 배수 및 방수 공사', source_url: 'https://kcsc.re.kr/OpenApi/CodeViewer/123' }, { status: 201 });
      }),
    );

    renderWithClient(<Settings />);

    expect(await screen.findByText('도심지 지하수 유입 사례')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('제목'), '새 지식 등록');
    await userEvent.type(screen.getByLabelText('내용'), '추가 검토 내용');
    await userEvent.type(screen.getByLabelText('태그'), '지하수, 보강');
    await userEvent.click(screen.getByRole('button', { name: '검토 대기 등록' }));

    await userEvent.click(screen.getByRole('button', { name: '검증' }));

    await userEvent.click(screen.getByRole('button', { name: '기준 코드 재검증' }));

    expect(await screen.findByText('기존 방수 근거')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText('대상 ID'), 'Risk_002');
    await userEvent.type(screen.getByLabelText('기준 코드'), 'KCS 27 50 05');
    await userEvent.type(screen.getByLabelText('조항 경로'), '3. 시공 > 3.3 시공기준');
    await userEvent.type(screen.getByLabelText('메모'), '방수 리스크 검토 근거');
    await userEvent.click(screen.getByRole('button', { name: '기준 연결 저장' }));

    expect(await screen.findByText('도심지 지하수 유입 사례')).toBeInTheDocument();
    expect(await screen.findByText('전체 2건')).toBeInTheDocument();
    expect(screen.getAllByText('터널 배수 및 방수 공사').length).toBeGreaterThan(0);
  });
});
