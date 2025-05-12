import React, { type ReactNode } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col h-screen bg-background-light dark:bg-background-dark text-text-light dark:text-text-dark transition-colors">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 border-r bg-sidebar-light dark:bg-sidebar-dark border-border-light dark:border-border-dark">
          <Sidebar />
        </aside>

        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
