
import React from 'react';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { Menu, User, Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar } from '@/components/ui/avatar';

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ toggleSidebar }) => {
  return (
    <header className="border-b bg-background h-14 flex items-center px-2 sm:px-4">
      <div className="flex items-center gap-2 sm:gap-4">
        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="h-9 w-9" aria-label="Toggle sidebar">
          <Menu className="h-5 w-5" />
        </Button>
        <h1 className="text-lg sm:text-xl font-semibold truncate">DataForge Platform</h1>
      </div>
      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <Button variant="ghost" size="icon" className="h-8 w-8 hidden sm:flex" aria-label="Notifications">
          <Bell className="h-4 w-4" />
        </Button>
        <Avatar className="h-8 w-8 hidden sm:flex" aria-label="User profile">
          <User className="h-4 w-4" />
        </Avatar>
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;
