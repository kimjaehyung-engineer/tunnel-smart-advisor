import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export default function Card({ children, title, subtitle, action, className = '', style }: CardProps) {
  return (
    <div className={`card ${className}`} style={style}>
      {(title || subtitle || action) && (
        <div className="card-header">
          <div className="card-titles">
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {action && <div className="card-action">{action}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}