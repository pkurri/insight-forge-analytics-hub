
import React from 'react';
import { Bell, Search, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <div className="flex-1">
        <div className="relative max-w-md">
          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            placeholder="Search..."
            className="pl-8 bg-gray-50 border-gray-200 focus-visible:ring-blue-500"
          />
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
        </Button>
        <Button variant="ghost" size="icon" className="rounded-full">
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
};

export default Header;
