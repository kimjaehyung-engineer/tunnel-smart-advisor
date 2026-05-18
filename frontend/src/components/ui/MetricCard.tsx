interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  accentColor?: string;
}

export default function MetricCard({ label, value, subValue, accentColor }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-icon" style={accentColor ? { backgroundColor: accentColor + '15', color: accentColor } : undefined}>
        {accentColor && (
          <svg width="18" height="18" viewBox="0 0 18 18" fill="currentColor">
            <circle cx="9" cy="9" r="7"/>
          </svg>
        )}
      </div>
      <div className="metric-content">
        <span className="metric-label">{label}</span>
        <strong className="metric-value">{value}</strong>
        {subValue && <span className="metric-sub">{subValue}</span>}
      </div>
    </div>
  );
}