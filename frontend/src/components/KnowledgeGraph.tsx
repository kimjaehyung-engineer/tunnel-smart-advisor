import { useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import type { GraphData } from '../types';

interface Props {
  data: GraphData | null;
  onNodeSelect?: (nodeId: string) => void;
}

interface NetworkClickParams {
  nodes?: string[];
}

export default function KnowledgeGraph({ data, onNodeSelect }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current || !data || data.nodes.length === 0) {
      return;
    }

    const network = new Network(
      containerRef.current,
      {
        nodes: data.nodes,
        edges: data.edges,
      },
      {
        nodes: { shape: 'dot', font: { color: '#0f172a' } },
        edges: { smooth: true, arrows: { to: { enabled: true, scaleFactor: 0.6 } } },
        physics: { repulsion: { nodeDistance: 150 }, solver: 'repulsion' },
        interaction: { hover: true, tooltipDelay: 80 },
      },
    );

    const resizeObserver = typeof ResizeObserver === 'undefined'
      ? null
      : new ResizeObserver(() => {
          network.redraw();
          network.fit({ animation: false });
        });
    resizeObserver?.observe(containerRef.current);

    network.on('click', (params: NetworkClickParams) => {
      const selectedNodeId = params.nodes?.[0];
      if (selectedNodeId) {
        onNodeSelect?.(selectedNodeId);
      }
    });

    return () => {
      resizeObserver?.disconnect();
      network.destroy();
    };
  }, [data, onNodeSelect]);

  return (
    <section className="panel graph-panel">
      <div className="section-heading">
        <h2>지식 그래프 토폴로지</h2>
        <p>조건, 위험, 대응전략 간 연결 구조를 시각화합니다.</p>
      </div>
      {data && data.nodes.length > 0 ? (
        <div className="graph-canvas" ref={containerRef} />
      ) : (
        <div className="graph-empty">분석을 실행하면 그래프가 표시됩니다.</div>
      )}
    </section>
  );
}
