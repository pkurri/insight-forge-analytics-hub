
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
  Bot
} from 'lucide-react';
import { useMediaQuery } from 'usehooks-ts';

interface SidebarProps {
  isMobile: boolean;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isMobile, isOpen, setIsOpen }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const matches = useMediaQuery('(min-width: 768px)');

  return (
    <nav className={`${isMobile ? (isOpen ? "flex" : "hidden") : "flex"} flex-col h-screen border-r bg-background p-4 w-72`}>
      <div className="flex items-center justify-between px-2 pb-3">
        <div className="flex items-center gap-2">
          <span className="font-bold text-xl">DataForge</span>
        </div>
        {isMobile && (
          <button onClick={() => setIsOpen(false)} className="p-1 rounded-md hover:bg-accent hover:text-accent-foreground">
            {/* Close Icon */}
          </button>
        )}
      </div>
      
      <div className="space-y-1">
        <p className="text-sm font-medium text-muted-foreground mb-2">Operations</p>
        <NavLink to="/dashboard" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <LayoutDashboard className="h-4 w-4" />
          Dashboard
        </NavLink>
        <NavLink to="/pipeline" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <GitBranch className="h-4 w-4" />
          Data Pipeline
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <BarChart3 className="h-4 w-4" />
          Analytics
        </NavLink>
        
        {/* Add new AI Chat link */}
        <NavLink to="/ai-chat" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <Bot className="h-4 w-4" />
          AI Chat
        </NavLink>
      </div>

      <div className="space-y-1 mt-6">
        <p className="text-sm font-medium text-muted-foreground mb-2">System</p>
        <NavLink to="/monitoring" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <Activity className="h-4 w-4" />
          Monitoring
        </NavLink>
        <NavLink to="/alerts" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <Bell className="h-4 w-4" />
          Alerts
        </NavLink>
        <NavLink to="/logs" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <ScrollText className="h-4 w-4" />
          Logs
        </NavLink>
        <NavLink to="/health" className={({ isActive }) => `${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'} flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium`}>
          <HeartPulse className="h-4 w-4" />
          Health
        </NavLink>
      </div>

      <div className="mt-auto px-2 pt-4">
        {matches && (
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-accent-foreground w-full"
          >
            {/* Collapse Icon */}
            {isCollapsed ? "Expand" : "Collapse"}
          </button>
        )}
      </div>
    </nav>
  );
};

export default Sidebar;
