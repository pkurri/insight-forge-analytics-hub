
import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  GitBranch, 
  BarChart3, 
  Activity, 
  Bell, 
  ScrollText, 
  HeartPulse,
  MessageSquare,
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
  
  const showSidebar = isMobile ? !isCollapsed : true;
  
  const sidebarWidth = isCollapsed && !isMobile ? 'w-16' : 'w-72';
  
  // Increased icon size when sidebar is collapsed
  const iconSize = isCollapsed && !isMobile ? 24 : 16;

  return (
    <nav className={`
      ${showSidebar ? "flex" : "hidden"} 
      ${sidebarWidth} 
      flex-col h-screen border-r border-border bg-background p-4 transition-all duration-300
      min-h-[100dvh]
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
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <LayoutDashboard size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Dashboard</span>}
        </NavLink>
        <NavLink 
          to="/pipeline" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <GitBranch size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Data Pipeline</span>}
        </NavLink>
        <NavLink 
          to="/analytics" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <BarChart3 size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Analytics</span>}
        </NavLink>
        
        <NavLink 
          to="/ai-chat" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <MessageSquare size={iconSize} />
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
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <Activity size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Monitoring</span>}
        </NavLink>
        <NavLink 
          to="/alerts" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <Bell size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Alerts</span>}
        </NavLink>
        <NavLink 
          to="/logs" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <ScrollText size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Logs</span>}
        </NavLink>
        <NavLink 
          to="/health" 
          className={({ isActive }) => `
            ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} 
            flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium
            ${isCollapsed && !isMobile ? 'justify-center' : ''}
          `}
        >
          <HeartPulse size={iconSize} />
          {(!isCollapsed || isMobile) && <span>Health</span>}
        </NavLink>
      </div>
    </nav>
  );
};

export default Sidebar;
