import { useState } from "react";
import { Link } from "wouter";
import {
  LayoutDashboard,
  Activity,
  History,
  Settings,
  ChevronRight,
} from "lucide-react";
import Sidebar from "./Sidebar";
import ConnectionIndicator from "./ConnectionIndicator";

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarExpanded, setSidebarExpanded] = useState(false);

  const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: Activity, label: "Live Monitor", href: "/monitor" },
    { icon: History, label: "Task History", href: "/history" },
    { icon: Settings, label: "Settings", href: "/settings" },
  ];

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        expanded={sidebarExpanded}
        onHover={setSidebarExpanded}
        navItems={navItems}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-card">
          <div className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-primary" />
            <span className="text-sm font-mono text-muted">
              Agent Terminal
            </span>
          </div>
          <ConnectionIndicator />
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-auto">
          <div className="page-transition">{children}</div>
        </div>
      </div>
    </div>
  );
}
