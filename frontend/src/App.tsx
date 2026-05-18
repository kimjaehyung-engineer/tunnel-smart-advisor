import { useEffect, useState } from 'react';
import AppShell from './components/layout/AppShell';
import Dashboard from './pages/Dashboard';
import Workspace from './pages/Workspace';
import DesignCompare from './pages/DesignCompare';
import Library from './pages/Library';
import History from './pages/History';
import Reports from './pages/Reports';
import Notifications from './pages/Notifications';
import Settings from './pages/Settings';

type PagePath = '/dashboard' | '/workspace' | '/compare' | '/library' | '/history' | '/reports' | '/notifications' | '/settings' | '/help';

const VALID_PATHS: PagePath[] = ['/dashboard', '/workspace', '/compare', '/library', '/history', '/reports', '/notifications', '/settings', '/help'];

function normalizePath(pathname: string): PagePath {
  return VALID_PATHS.includes(pathname as PagePath) ? (pathname as PagePath) : '/dashboard';
}

export default function App() {
  const [activePath, setActivePath] = useState<PagePath>(() => normalizePath(window.location.pathname));

  useEffect(() => {
    const handlePopState = () => setActivePath(normalizePath(window.location.pathname));
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = (path: string) => {
    const nextPath = normalizePath(path);
    setActivePath(nextPath);
    if (window.location.pathname !== nextPath) {
      window.history.pushState(null, '', nextPath);
    }
  };

  const renderPage = () => {
    switch (activePath) {
      case '/dashboard':
        return <Dashboard />;
      case '/workspace':
        return <Workspace />;
      case '/compare':
        return <DesignCompare />;
      case '/library':
        return <Library />;
      case '/history':
        return <History />;
      case '/reports':
        return <Reports />;
      case '/notifications':
        return <Notifications />;
      case '/settings':
        return <Settings />;
      case '/help':
        return <PlaceholderPage title="도움말" description="사용 가이드와 지원 문서는 준비 중입니다." />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <AppShell activePath={activePath} onNavigate={handleNavigate}>
      {renderPage()}
    </AppShell>
  );
}

function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="placeholder-page">
      <div className="empty-state">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-description">{description}</p>
        </div>
      </div>
    </div>
  );
}
