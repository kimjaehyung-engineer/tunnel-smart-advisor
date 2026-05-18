import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Library from './Library';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('Library', () => {
  it('renders library items and filters them by search keyword', async () => {
    server.use(
      http.get(`${API_BASE}/library/items`, () => HttpResponse.json({
        items: [
          {
            id: 'Risk_001',
            title: '지하수 유입 위험',
            category: '지반',
            tags: ['파쇄대', '지하수'],
            relationTypes: ['TRIGGER', 'MITIGATED_BY'],
            project: 'NATM 표준',
            relationCount: 7,
          },
          {
            id: 'Risk_002',
            title: '장비 고장 위험',
            category: '위험',
            tags: ['장비'],
            relationTypes: ['USES_EQUIPMENT'],
            project: '장비 점검',
            relationCount: 3,
          },
        ],
        categories: [
          { label: '전체', count: 2 },
          { label: '지반', count: 1 },
        ],
        popularTags: [
          { label: '파쇄대', count: 1 },
          { label: '장비', count: 1 },
        ],
        relationTypes: [
          { label: '전체', count: 2 },
          { label: 'TRIGGER', count: 1 },
          { label: 'USES_EQUIPMENT', count: 1 },
        ],
      })),
    );

    renderWithClient(<Library />);

    expect(await screen.findByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.getByText('장비 고장 위험')).toBeInTheDocument();

    await userEvent.type(screen.getByPlaceholderText('검색어를 입력하세요'), '지하수');

    expect(screen.getByText('지하수 유입 위험')).toBeInTheDocument();
    expect(screen.queryByText('장비 고장 위험')).not.toBeInTheDocument();

    await userEvent.clear(screen.getByPlaceholderText('검색어를 입력하세요'));
    await userEvent.selectOptions(screen.getByLabelText('관계 유형'), 'USES_EQUIPMENT');

    expect(await screen.findByText('장비 고장 위험')).toBeInTheDocument();
    expect(screen.queryByText('지하수 유입 위험')).not.toBeInTheDocument();
  });

  it('opens read-only detail for a library item', async () => {
    server.use(
      http.get(`${API_BASE}/library/items`, () => HttpResponse.json({
        items: [
          {
            id: 'Risk_001',
            title: '지하수 유입 위험',
            category: '지반',
            tags: ['파쇄대', '지하수'],
            relationTypes: ['TRIGGER'],
            project: 'NATM 표준',
            relationCount: 7,
          },
        ],
        categories: [{ label: '전체', count: 1 }],
        popularTags: [{ label: '파쇄대', count: 1 }],
        relationTypes: [{ label: '전체', count: 1 }, { label: 'TRIGGER', count: 1 }],
      })),
      http.get(`${API_BASE}/library/items/Risk_001`, () => HttpResponse.json({
        id: 'Risk_001',
        title: '지하수 유입 위험',
        project: 'NATM 표준',
        sourceLL: '터널 막장 유입수 원문',
        cause: '파쇄대 및 지하수위 상승',
        impactText: '침수 및 공정 지연',
        relationCount: 7,
        relatedConditions: {
          process: [{ id: 'Process_001', label: '굴착' }],
          ground: [{ id: 'Ground_001', label: '파쇄대' }],
          location: [],
          method: [{ id: 'Method_001', label: 'NATM' }],
          equipment: [],
          impact: [],
        },
        strategies: [{ id: 'Strategy_001', label: '선진 배수공 적용' }],
        lessons: [{ id: 'Lesson_1', label: '충분한 지반조사 후 터널보조공법 선정 필요' }],
        impacts: [{ id: 'Impact_001', label: '공정 지연' }],
        roles: [{ id: 'Role_001', label: '시공사' }],
        standards: [{ id: 'Standard_001', label: 'KCS 27 00 00' }],
        graph: {
          nodes: [
            { id: 'Risk_001', label: 'Risk', title: '지하수 유입 위험', color: '#EF4444', size: 28 },
            { id: 'Strategy_001', label: 'Strategy', title: '선진 배수공 적용', color: '#10B981', size: 18 },
            { id: 'Lesson_1', label: 'LessonLearned', title: '충분한 지반조사 후 터널보조공법 선정 필요', color: '#F59E0B', size: 18 },
          ],
          edges: [
            { from: 'Risk_001', to: 'Strategy_001', title: 'MITIGATED_BY', color: '#6EE7B7' },
            { from: 'Risk_001', to: 'Lesson_1', title: 'LEARNED_AS', color: '#FCD34D' },
          ],
        },
      })),
    );

    renderWithClient(<Library />);

    await userEvent.click(await screen.findByRole('button', { name: '지하수 유입 위험' }));

    expect(await screen.findByText('읽기 전용')).toBeInTheDocument();
    expect(screen.getByText('선진 배수공 적용')).toBeInTheDocument();
    expect(screen.getByText('충분한 지반조사 후 터널보조공법 선정 필요')).toBeInTheDocument();
    expect(screen.getByText(/MITIGATED_BY/)).toBeInTheDocument();
    expect(screen.getByText(/LEARNED_AS/)).toBeInTheDocument();
    expect(screen.getByText('KCS 27 00 00')).toBeInTheDocument();
    expect(screen.getByText('터널 막장 유입수 원문')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '← 목록으로' }));

    expect(screen.getByRole('button', { name: '지하수 유입 위험' })).toBeInTheDocument();
  });
});
