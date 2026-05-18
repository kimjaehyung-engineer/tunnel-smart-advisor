import { useNodeList } from '../api/queries';
import type { NodeType } from '../types';

type FilterKey = NodeType;

const filterMeta: Array<{ key: FilterKey; label: string; nameField: string }> = [
  { key: 'process', label: '1. 공종', nameField: 'name' },
  { key: 'ground', label: '2. 지반', nameField: 'condition_name' },
  { key: 'location', label: '3. 위치', nameField: 'loc_name' },
  { key: 'method', label: '4. 공법', nameField: 'method_name' },
  { key: 'equipment', label: '5. 장비', nameField: 'equip_name' },
  { key: 'impact', label: '6. 영향', nameField: 'impact_type' },
];

interface FilterPanelProps {
  values: Record<FilterKey, string | null>;
  onChange: (key: FilterKey, value: string | null) => void;
}

export default function FilterPanel({ values, onChange }: FilterPanelProps) {
  return (
    <section className="card filter-panel" style={{ marginBottom: '16px' }}>
      <div className="workspace-condition-row">
        {filterMeta.map((meta) => (
          <FilterSelect
            key={meta.key}
            meta={meta}
            value={values[meta.key]}
            onChange={(value) => onChange(meta.key, value)}
          />
        ))}
      </div>
    </section>
  );
}

function FilterSelect({
  meta,
  value,
  onChange,
}: {
  meta: { key: FilterKey; label: string; nameField: string };
  value: string | null;
  onChange: (value: string | null) => void;
}) {
  const { data, isLoading, error } = useNodeList(meta.key);

  return (
    <label className="filter-field">
      <span>{meta.label}</span>
      <select value={value ?? ''} onChange={(event) => onChange(event.target.value || null)} disabled={isLoading || !!error}>
        <option value="">{isLoading ? '불러오는 중...' : '[상관없음/전체]'}</option>
        {(data?.nodes ?? []).map((node) => {
          const name = String(node[meta.nameField] ?? '');
          return (
            <option key={node['id:ID']} value={name}>
              {name}
            </option>
          );
        })}
      </select>
      {error && <small className="field-error">목록을 불러오지 못했습니다.</small>}
    </label>
  );
}
