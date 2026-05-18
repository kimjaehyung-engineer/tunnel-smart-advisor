import { useState } from 'react';
import { useNotificationActions, useNotifications } from '../api/queries';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import type { NotificationFilter } from '../types';

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
}

export default function Notifications() {
  const [filter, setFilter] = useState<NotificationFilter>('all');
  const { data, isLoading, error } = useNotifications(filter);
  const actions = useNotificationActions();

  return (
    <div className="notifications-page">
      <PageHeader
        title="알림"
        description="데이터 갱신, 분석 완료, 시스템 점검 알림을 저장하고 읽음/중요 상태를 관리합니다."
      />

      <div className="tabs">
        <button className={`tab-btn ${filter === 'all' ? 'active' : ''}`} type="button" onClick={() => setFilter('all')}>전체 {data?.summary.total ?? 0}</button>
        <button className={`tab-btn ${filter === 'unread' ? 'active' : ''}`} type="button" onClick={() => setFilter('unread')}>읽지 않음 {data?.summary.unread ?? 0}</button>
        <button className={`tab-btn ${filter === 'important' ? 'active' : ''}`} type="button" onClick={() => setFilter('important')}>중요 {data?.summary.important ?? 0}</button>
        <div style={{ marginLeft: 'auto' }}>
          <button className="btn btn-secondary btn-sm" type="button" disabled={actions.markAllRead.isPending} onClick={() => actions.markAllRead.mutate()}>모두 읽음</button>
        </div>
      </div>

      <Card title="알림 목록">
        {isLoading && <div className="empty-state">백엔드에서 알림을 불러오는 중입니다...</div>}
        {error && <div className="empty-state">알림을 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}
        {data && data.items.length === 0 && <div className="empty-state">표시할 알림이 없습니다.</div>}
        {data && data.items.length > 0 && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>시각</th>
                  <th>분류</th>
                  <th>제목</th>
                  <th>내용</th>
                  <th>상태</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="knowledge-row">
                    <td className="text-muted">{formatDate(item.created_at)}</td>
                    <td>{item.category}</td>
                    <td><span className="knowledge-title">{item.is_important ? '★ ' : ''}{item.title}</span></td>
                    <td>{item.message}</td>
                    <td>{item.is_read ? '읽음' : '읽지 않음'}</td>
                    <td>
                      <button className="btn btn-secondary btn-sm" type="button" disabled={item.is_read || actions.markRead.isPending} onClick={() => actions.markRead.mutate(item.id)}>읽음</button>{' '}
                      <button className="btn btn-secondary btn-sm" type="button" disabled={actions.setImportant.isPending} onClick={() => actions.setImportant.mutate({ id: item.id, isImportant: !item.is_important })}>
                        {item.is_important ? '중요 해제' : '중요'}
                      </button>{' '}
                      <button className="btn btn-secondary btn-sm" type="button" disabled={actions.archive.isPending} onClick={() => actions.archive.mutate(item.id)}>보관</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
