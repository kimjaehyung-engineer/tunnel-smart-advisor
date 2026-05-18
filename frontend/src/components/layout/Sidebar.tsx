import type { ReactNode} from 'react';

interface NavItem {
  label: string;
  path: string;
  icon: ReactNode;
}

interface SidebarProps {
  activePath: string;
  onNavigate: (path: string) => void;
}

const mainNavItems: NavItem[] = [
  { label: '대시보드', path: '/dashboard', icon: <GridIcon /> },
  { label: '분석 워크스페이스', path: '/workspace', icon: <AnalysisIcon /> },
  { label: '설계변경 비교', path: '/compare', icon: <AnalysisIcon /> },
  { label: '지식 라이브러리', path: '/library', icon: <BookIcon /> },
  { label: '과거 분석', path: '/history', icon: <HistoryIcon /> },
  { label: '리포트', path: '/reports', icon: <ReportIcon /> },
  { label: '알림', path: '/notifications', icon: <BellIcon /> },
];

const bottomNavItems = [
  { label: '설정', path: '/settings', icon: <SettingsIcon /> },
  { label: '도움말', path: '/help', icon: <HelpIcon /> },
];

export default function Sidebar({ activePath, onNavigate }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <circle cx="14" cy="14" r="12" fill="#2563EB" opacity="0.2"/>
            <circle cx="14" cy="14" r="8" fill="#2563EB" opacity="0.4"/>
            <circle cx="14" cy="14" r="4" fill="#2563EB"/>
          </svg>
        </div>
        <span className="logo-text">Tunnel Smart Advisor</span>
      </div>

      <nav className="sidebar-nav">
        {mainNavItems.map((item) => (
          <button
            key={item.path}
            className={`nav-item ${activePath === item.path ? 'active' : ''}`}
            onClick={() => onNavigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        {bottomNavItems.map((item) => (
          <button
            key={item.path}
            className={`nav-item ${activePath === item.path ? 'active' : ''}`}
            onClick={() => onNavigate(item.path)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </div>
    </aside>
  );
}

// Icons
function GridIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="3" y="3" width="6" height="6" rx="1.5"/>
      <rect x="11" y="3" width="6" height="6" rx="1.5"/>
      <rect x="3" y="11" width="6" height="6" rx="1.5"/>
      <rect x="11" y="11" width="6" height="6" rx="1.5"/>
    </svg>
  );
}

function AnalysisIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M10 2v6l4 2"/>
      <circle cx="10" cy="10" r="8"/>
      <path d="M10 6v4l-3 2"/>
    </svg>
  );
}

function BookIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M3 4h10a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3V4z"/>
      <path d="M3 4V2a1 1 0 0 1 1-1h10"/>
      <path d="M7 8h6M7 11h4"/>
    </svg>
  );
}

function HistoryIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="7"/>
      <path d="M10 6v4l2.5 2.5"/>
      <path d="M7 3h4M7 17h4" strokeLinecap="round"/>
    </svg>
  );
}

function ReportIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <rect x="4" y="2" width="12" height="16" rx="2"/>
      <path d="M7 6h6M7 9h6M7 12h4"/>
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M8 16a2 2 0 0 0 4 0"/>
      <path d="M16 8a4 4 0 0 1-14 0"/>
      <path d="M4 8h.01M20 8h.01"/>
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="2"/>
      <path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4"/>
    </svg>
  );
}

function HelpIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="10" cy="10" r="8"/>
      <path d="M8 8a2 2 0 1 1 2.5 1.8C10 10.5 9 11 9 12"/>
      <circle cx="10" cy="15" r=".5" fill="currentColor"/>
    </svg>
  );
}
