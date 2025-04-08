
import React from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Home,
  Database,
  Activity,
  BarChart3,
  Settings,
  AlertTriangle,
  Terminal,
  Server,
  HeartPulse,
  MenuIcon,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, setIsCollapsed }) => {
  return (
    <div
      className={cn(
        "h-screen bg-white border-r border-gray-200 flex flex-col transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <Server className="h-6 w-6 text-purple" />
            <h1 className="text-xl font-bold">InsightForge</h1>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label="Toggle sidebar"
          className={cn("ml-auto", isCollapsed && "mx-auto")}
        >
          <MenuIcon className="h-5 w-5" />
        </Button>
      </div>
      <Separator />
      <nav className="flex-1 p-2">
        <ul className="space-y-1">
          <SidebarItem
            icon={<Home className="h-5 w-5" />}
            text="Dashboard"
            to="/"
            isCollapsed={isCollapsed}
            active
          />
          <SidebarItem
            icon={<Database className="h-5 w-5" />}
            text="Data Pipeline"
            to="/pipeline"
            isCollapsed={isCollapsed}
          />
          <SidebarItem
            icon={<Activity className="h-5 w-5" />}
            text="Monitoring"
            to="/monitoring"
            isCollapsed={isCollapsed}
          />
          <SidebarItem
            icon={<BarChart3 className="h-5 w-5" />}
            text="Analytics"
            to="/analytics"
            isCollapsed={isCollapsed}
          />
          <SidebarItem
            icon={<AlertTriangle className="h-5 w-5" />}
            text="Alerts"
            to="/alerts"
            isCollapsed={isCollapsed}
          />
          <SidebarItem
            icon={<Terminal className="h-5 w-5" />}
            text="Logs"
            to="/logs"
            isCollapsed={isCollapsed}
          />
        </ul>
      </nav>
      <Separator />
      <div className="p-2">
        <ul className="space-y-1">
          <SidebarItem
            icon={<HeartPulse className="h-5 w-5" />}
            text="Health"
            to="/health"
            isCollapsed={isCollapsed}
          />
          <SidebarItem
            icon={<Settings className="h-5 w-5" />}
            text="Settings"
            to="/settings"
            isCollapsed={isCollapsed}
          />
        </ul>
      </div>
    </div>
  );
};

interface SidebarItemProps {
  icon: React.ReactNode;
  text: string;
  to: string;
  isCollapsed: boolean;
  active?: boolean;
}

const SidebarItem: React.FC<SidebarItemProps> = ({
  icon,
  text,
  to,
  isCollapsed,
  active,
}) => {
  return (
    <li>
      <Link
        to={to}
        className={cn(
          "flex items-center px-2 py-2 rounded-md text-gray-700 hover:bg-gray-100 transition-colors",
          active && "bg-blue-50 text-blue-700"
        )}
      >
        <div className={cn("flex items-center", isCollapsed ? "justify-center w-full" : "")}>
          {icon}
          {!isCollapsed && <span className="ml-3">{text}</span>}
        </div>
      </Link>
    </li>
  );
};

export default Sidebar;
