type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info';

interface BadgeProps {
  children: string;
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, { bg: string; color: string }> = {
  default: { bg: '#F1F5F9', color: '#64748B' },
  success: { bg: '#ECFDF5', color: '#059669' },
  warning: { bg: '#FFF7ED', color: '#EA580C' },
  danger: { bg: '#FEF2F2', color: '#DC2626' },
  info: { bg: '#EFF6FF', color: '#2563EB' },
};

export default function Badge({ children, variant = 'default' }: BadgeProps) {
  const style = variantStyles[variant];
  return (
    <span
      className="badge"
      style={{ backgroundColor: style.bg, color: style.color }}
    >
      {children}
    </span>
  );
}