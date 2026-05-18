import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Notifications from './Notifications';
import { renderWithClient } from '../test/render';
import { server } from '../test/server';

const API_BASE = 'http://127.0.0.1:8080';

describe('Notifications', () => {
  it('renders notifications and supports read and important actions', async () => {
    server.use(
      http.get(`${API_BASE}/notifications`, () => HttpResponse.json({
        items: [{
          id: 1,
          created_at: '2026-05-15T00:00:00+00:00',
          category: 'analysis',
          title: '분석 완료',
          message: '분석 #1이 완료되었습니다.',
          is_read: false,
          is_important: false,
          is_archived: false,
        }],
        summary: { total: 1, unread: 1, important: 0 },
      })),
      http.post(`${API_BASE}/notifications/1/read`, () => HttpResponse.json({ id: 1, is_read: true })),
      http.post(`${API_BASE}/notifications/1/important`, () => HttpResponse.json({ id: 1, is_important: true })),
      http.delete(`${API_BASE}/notifications/1`, () => HttpResponse.json({ id: 1, is_archived: true })),
      http.post(`${API_BASE}/notifications/read-all`, () => HttpResponse.json({ items: [], summary: { total: 1, unread: 0, important: 0 } })),
    );

    renderWithClient(<Notifications />);

    expect(await screen.findByText('분석 완료')).toBeInTheDocument();
    expect(screen.getByText('분석 #1이 완료되었습니다.')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: '읽음' }));
    await userEvent.click(screen.getByRole('button', { name: '중요' }));
    await userEvent.click(screen.getByRole('button', { name: '보관' }));
    await userEvent.click(screen.getByRole('button', { name: /모두 읽음/ }));

    expect(await screen.findByText('분석 완료')).toBeInTheDocument();
  });
});
