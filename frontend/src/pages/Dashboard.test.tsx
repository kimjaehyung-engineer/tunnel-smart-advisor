import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import Dashboard from './Dashboard';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('Dashboard', () => {
  it('renders dashboard summary returned by the backend', async () => {
    server.use(
      http.get(`${API_BASE}/dashboard/summary`, () => HttpResponse.json({
        kpis: [
          { label: '전체 위험 지식', value: '316건', subValue: '프로젝트 1개', accentColor: '#3B82F6' },
          { label: '대응전략', value: '316건', subValue: 'MITIGATED_BY', accentColor: '#10B981' },
        ],
        distribution: [
          { label: '상위 연결', value: 63, color: '#EF4444' },
          { label: '기타', value: 253, color: '#10B981' },
        ],
        impactDistribution: [
          { label: '침하', value: 12, color: '#EF4444' },
        ],
        operationalStatus: [
          { label: '데이터 최신성', value: '1일 전', status: 'ok', description: '원천 파일: checklist.xlsx', color: '#8B5CF6' },
          { label: '시스템 오류 상태', value: '정상', status: 'ok', description: '누적 요청 3건 기준', color: '#10B981' },
          { label: '리포트 공유 현황', value: '2건', status: 'ok', description: '공유 상태가 켜진 리포트 수', color: '#10B981' },
        ],
        trend: [12, 8, 4],
        recentAnalyses: [
          { id: 'Risk_001', title: '막장 붕락 위험', project: 'NATM 표준', score: 12 },
        ],
        notifications: [
          { title: '위험 지식 데이터가 로드되었습니다.', desc: '위험 316건', time: '실시간', color: '#3B82F6' },
        ],
      })),
    );

    renderWithClient(<Dashboard />);

    expect(await screen.findByText('전체 위험 지식')).toBeInTheDocument();
    expect(screen.getAllByText('316건')).toHaveLength(2);
    expect(screen.getByText('영향 유형 분포')).toBeInTheDocument();
    expect(screen.getByText('침하')).toBeInTheDocument();
    expect(screen.getByText('운영 상태')).toBeInTheDocument();
    expect(screen.getByText('데이터 최신성')).toBeInTheDocument();
    expect(screen.getByText('시스템 오류 상태')).toBeInTheDocument();
    expect(screen.getByText('리포트 공유 현황')).toBeInTheDocument();
    expect(screen.getByText('막장 붕락 위험')).toBeInTheDocument();
    expect(screen.getByText('위험 지식 데이터가 로드되었습니다.')).toBeInTheDocument();
  });
});
