import { useEffect, useMemo, useState } from 'react';
import PageHeader from '../components/layout/PageHeader';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import { useLibraryItemDetail, useLibraryItems } from '../api/queries';
import type { LibraryRelatedItem, NodeType } from '../types';

const CONDITION_LABELS: Record<NodeType, string> = {
  process: '공종',
  ground: '지반',
  location: '위치',
  method: '공법',
  equipment: '장비',
  impact: '영향',
};

function RelatedList({ items, emptyText = '연결 정보 없음' }: { items: LibraryRelatedItem[]; emptyText?: string }) {
  if (items.length === 0) {
    return <span className="text-muted">{emptyText}</span>;
  }

  return (
    <div className="tag-list-inline">
      {items.map((item) => <span key={item.id} className="tag-inline">{item.label}</span>)}
    </div>
  );
}

export default function Library() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('전체');
  const [tag, setTag] = useState('전체');
  const [relationType, setRelationType] = useState('전체');
  const { data, isLoading, error } = useLibraryItems({ query: search, category, tag, relationType });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRiskId, setSelectedRiskId] = useState<string | null>(null);
  const { data: detail, isLoading: isDetailLoading, error: detailError } = useLibraryItemDetail(selectedRiskId);
  const pageSize = 20;

  const filteredItems = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return (data?.items ?? []).filter((item) => {
      const matchesKeyword = !keyword || item.title.toLowerCase().includes(keyword) || item.project.toLowerCase().includes(keyword);
      const matchesCategory = category === '전체' || item.category === category;
      const matchesTag = tag === '전체' || item.tags.includes(tag);
      const matchesRelation = relationType === '전체' || (item.relationTypes ?? []).includes(relationType);
      return matchesKeyword && matchesCategory && matchesTag && matchesRelation;
    });
  }, [category, data?.items, relationType, search, tag]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const pageItems = filteredItems.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  useEffect(() => {
    setCurrentPage(1);
  }, [category, relationType, search, tag]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  return (
    <div className="library-page">
      <PageHeader
        title="지식 라이브러리"
        description="백엔드 CSV 온톨로지에서 불러온 위험 지식과 연결 태그를 탐색할 수 있습니다."
        actions={<button className="btn btn-secondary" disabled>+ 지식 등록</button>}
      />

      <div className="filter-bar">
        <input
          type="text"
          className="input search-input"
          placeholder="검색어를 입력하세요"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{ flex: 1 }}
        />
        <select className="select category-filter" value={category} onChange={(event) => setCategory(event.target.value)}>
          {(data?.categories ?? [{ label: '전체', count: 0 }]).map((cat) => (
            <option key={cat.label}>{cat.label}</option>
          ))}
        </select>
        <select className="select tag-filter" value={tag} onChange={(event) => setTag(event.target.value)}>
          <option>전체</option>
          {(data?.popularTags ?? []).map((item) => (
            <option key={item.label}>{item.label}</option>
          ))}
        </select>
        <select className="select" aria-label="관계 유형" value={relationType} onChange={(event) => setRelationType(event.target.value)}>
          {(data?.relationTypes ?? [{ label: '전체', count: 0 }]).map((item) => (
            <option key={item.label} value={item.label}>{item.label}</option>
          ))}
        </select>
      </div>

      {isLoading && <div className="empty-state">백엔드에서 지식 라이브러리를 불러오는 중입니다...</div>}
      {error && <div className="empty-state">지식 라이브러리 데이터를 불러오지 못했습니다. 백엔드 서버를 확인하세요.</div>}

      {data && selectedRiskId && (
        <Card style={{ marginBottom: '16px' }}>
          <button className="btn btn-secondary" onClick={() => setSelectedRiskId(null)}>← 목록으로</button>
          {isDetailLoading && <div className="empty-state">지식 상세를 불러오는 중입니다...</div>}
          {detailError && <div className="empty-state">지식 상세를 불러오지 못했습니다.</div>}
          {detail && (
            <div className="library-detail">
              <div className="library-detail-header">
                <div>
                  <p className="text-muted">{detail.project || '프로젝트 정보 없음'} · 관계 {detail.relationCount.toLocaleString()}건</p>
                  {detail.sourceVersion && <p className="text-muted">원천 버전: {detail.sourceVersion}</p>}
                  <h2>{detail.title}</h2>
                </div>
                <Badge variant="info">읽기 전용</Badge>
              </div>

              <div className="detail-grid">
                <div className="detail-section">
                  <h3>관련 조건</h3>
                  {Object.entries(detail.relatedConditions).filter(([key]) => key !== 'impact').map(([key, items]) => (
                    <div key={key} className="detail-row">
                      <span className="detail-label">{CONDITION_LABELS[key as NodeType]}</span>
                      <div className="detail-value"><RelatedList items={items} /></div>
                    </div>
                  ))}
                </div>
                <div className="detail-section">
                  <h3>영향·담당·기준</h3>
                  <div className="detail-row"><span className="detail-label">영향</span><div className="detail-value"><RelatedList items={detail.impacts} /></div></div>
                  <div className="detail-row"><span className="detail-label">담당 주체</span><div className="detail-value"><RelatedList items={detail.roles} /></div></div>
                  <div className="detail-row"><span className="detail-label">관련 기준</span><div className="detail-value"><RelatedList items={detail.standards} /></div></div>
                </div>
              </div>

              <div className="detail-section">
                <h3>대응전략</h3>
                <RelatedList items={detail.strategies} />
              </div>

              <div className="detail-section">
                <h3>Lesson Learned</h3>
                <RelatedList items={detail.lessons ?? []} emptyText="연결된 Lesson Learned 없음" />
              </div>

              <div className="detail-section">
                <h3>관련 그래프</h3>
                {detail.graph && detail.graph.edges.length > 0 ? (
                  <div className="tag-list-inline">
                    {detail.graph.edges.slice(0, 12).map((edge) => {
                      const fromNode = detail.graph?.nodes.find((node) => node.id === edge.from);
                      const toNode = detail.graph?.nodes.find((node) => node.id === edge.to);
                      return (
                        <span key={`${edge.from}-${edge.to}-${edge.title}`} className="tag-inline">
                          {fromNode?.title ?? edge.from} → {edge.title} → {toNode?.title ?? edge.to}
                        </span>
                      );
                    })}
                  </div>
                ) : <span className="text-muted">관련 그래프 정보 없음</span>}
              </div>

              <div className="detail-grid">
                <div className="detail-section"><h3>원인</h3><p>{detail.cause || '원인 정보 없음'}</p></div>
                <div className="detail-section"><h3>영향 원문</h3><p>{detail.impactText || '영향 원문 없음'}</p></div>
              </div>
              <div className="detail-section"><h3>원문 LL 내용</h3><p>{detail.sourceLL || '원문 LL 정보 없음'}</p></div>
            </div>
          )}
        </Card>
      )}

      {data && !selectedRiskId && (
        <div className="library-content">
          <div className="library-sidebar">
            <Card>
              <h3 className="sidebar-section-title">카테고리</h3>
              <div className="category-list">
                {data.categories.map((cat) => (
                  <button
                    key={cat.label}
                    className={`category-btn ${cat.label === category ? 'active' : ''}`}
                    onClick={() => setCategory(cat.label)}
                  >
                    <span>{cat.label}</span>
                    <span className="category-count">{cat.count}</span>
                  </button>
                ))}
              </div>
            </Card>

            <Card style={{ marginTop: '16px' }}>
              <h3 className="sidebar-section-title">태그</h3>
              <div className="tag-list">
                {data.popularTags.map((tagItem) => (
                  <button key={tagItem.label} className="tag-chip" onClick={() => setTag(tagItem.label)}>
                    {tagItem.label}
                    <span className="tag-count">{tagItem.count}</span>
                  </button>
                ))}
              </div>
              <button className="btn btn-secondary" style={{ width: '100%', marginTop: '12px' }} onClick={() => setTag('전체')}>태그 초기화</button>
            </Card>

            <Card style={{ marginTop: '16px' }}>
              <h3 className="sidebar-section-title">관계 유형</h3>
              <div className="category-list">
                {(data?.relationTypes ?? [{ label: '전체', count: 0 }]).map((item) => (
                  <button
                    key={item.label}
                    className={`category-btn ${item.label === relationType ? 'active' : ''}`}
                    onClick={() => setRelationType(item.label)}
                  >
                    <span>{item.label}</span>
                    <span className="category-count">{item.count}</span>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          <div className="library-main">
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th scope="col">제목</th>
                    <th scope="col">카테고리</th>
                    <th scope="col">관련 태그</th>
                    <th scope="col">관계 유형</th>
                    <th scope="col">근거 수</th>
                    <th scope="col">프로젝트</th>
                  </tr>
                </thead>
                <tbody>
                  {pageItems.map((item) => (
                    <tr key={item.id} className="knowledge-row">
                      <td><button className="knowledge-title knowledge-title-btn" onClick={() => setSelectedRiskId(item.id)}>{item.title}</button></td>
                      <td><Badge variant="info">{item.category}</Badge></td>
                      <td>
                        <div className="tag-list-inline">
                          {item.tags.length > 0 ? item.tags.map((itemTag) => (
                            <span key={itemTag} className="tag-inline">{itemTag}</span>
                          )) : <span className="text-muted">연결 태그 없음</span>}
                        </div>
                      </td>
                      <td>
                        <div className="tag-list-inline">
                          {(item.relationTypes ?? []).length > 0 ? (item.relationTypes ?? []).slice(0, 3).map((relation) => (
                            <span key={relation} className="tag-inline">{relation}</span>
                          )) : <span className="text-muted">관계 없음</span>}
                        </div>
                      </td>
                      <td className="text-right">{item.relationCount.toLocaleString()}</td>
                      <td className="text-muted">{item.project || '정보 없음'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredItems.length === 0 && <div className="empty-state">조건에 맞는 백엔드 지식 데이터가 없습니다.</div>}

            <div className="pagination">
              <button className="pagination-btn" disabled={currentPage === 1} onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}>이전</button>
              <span className="pagination-status">{currentPage} / {totalPages}</span>
              <button className="pagination-btn" disabled={currentPage === totalPages} onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}>다음</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
