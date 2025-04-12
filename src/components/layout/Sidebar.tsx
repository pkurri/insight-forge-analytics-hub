
import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  GitBranch, 
  BarChart3, 
  Activity, 
  Bell, 
  ScrollText, 
  HeartPulse,
  Bot,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useMediaQuery } from 'usehooks-ts';

interface SidebarProps {
  isMobile: boolean;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isMobile, isCollapsed, setIsCollapsed }) => {
  const matches = useMediaQuery('(min-width: 768px)');
  
  // Determine if sidebar should be shown based on mobile state and collapse state
  const showSidebar = isMobile ? !isCollapsed : true;
  
  // Calculate sidebar width based on collapse state
  const sidebarWidth = isCollapsed && !isMobile ? 'w-16' : 'w-72';

  return (
    <nav className={`
      ${showSidebar ? "flex" : "hidden"} 
      ${sidebarWidth} 
      flex-col h-screen border-r bg-background p-4 transition-all duration-300
    `}>
      <div className="flex items-center justify-between px-2 pb-3">
        <div className={`flex items-center gap-2 ${isCollapsed && !isMobile ? 'justify-center w-full' : ''}`}>
          {!isCollapsed || isMobile ? (
            <span className="font-bold text-xl">DataForge</span>
          ) : (
            <span className="font-bold text-xl">DF</span>
          )}
        </div>
        
        {isMobile && (
          <button 
            onClick={() => setIsCollapsed(true)} 
            className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        )}
        
        {!isMobile && (
          <button 
            onClick={() => setIsCollapsed(!isCollapsed)} 
            className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground"
          >
            {isCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <ChevronLeft className="h-5 w-5" />
            )}
          </button>
        )}
      </div>
      
      <div className="space-y-1">
        <p className={`text-sm font-medium text-muted-foreground mb-2 ${isCollapsed && !isMobile ? 'sr-only' : ''}`}>
          Operations
        </p>
        <NavLink 
          to="/dashboard" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <LayoutDashboard className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Dashboard</span>}
        </NavLink>
        <NavLink 
          to="/pipeline" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <GitBranch className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Data Pipeline</span>}
        </NavLink>
        <NavLink 
          to="/analytics" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <BarChart3 className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Analytics</span>}
        </NavLink>
        
        <NavLink 
          to="/ai-chat" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <Bot className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>AI Chat</span>}
        </NavLink>
      </div>

      <div className="space-y-1 mt-6">
        <p className={`text-sm font-medium text-muted-foreground mb-2 ${isCollapsed && !isMobile ? 'sr-only' : ''}`}>
          System
        </p>
        <NavLink 
          to="/monitoring" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <Activity className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Monitoring</span>}
        </NavLink>
        <NavLink 
          to="/alerts" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <Bell className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Alerts</span>}
        </NavLink>
        <NavLink 
          to="/logs" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <ScrollText className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Logs</span>}
        </NavLink>
        <NavLink 
          to="/health" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
          `}
        >
          <HeartPulse className="h-4 w-4" />
          {(!isCollapsed || isMobile) && <span>Health</span>}
        </NavLink>
      </div>
    </nav>
  );
};

export default Sidebar;
