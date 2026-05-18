import type { ReactNode } from 'react';
import Sidebar from './Sidebar';

interface AppShellProps {
  children: ReactNode;
  activePath: string;
  onNavigate: (path: string) => void;
}

export default function AppShell({ children, activePath, onNavigate }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar activePath={activePath} onNavigate={onNavigate} />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}