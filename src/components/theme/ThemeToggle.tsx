
import { Moon, Sun, Laptop } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/components/theme/ThemeProvider";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Sun className={cn(
            "h-5 w-5 transition-all",
            theme === "dark" ? "scale-0 rotate-90 opacity-0" : "scale-100 rotate-0 opacity-100"
          )} />
          <Moon className={cn(
            "absolute h-5 w-5 transition-all",
            theme === "light" ? "scale-0 -rotate-90 opacity-0" : (theme === "dark" ? "scale-100 rotate-0 opacity-100" : "scale-0 rotate-90 opacity-0")
          )} />
          <Laptop className={cn(
            "absolute h-5 w-5 transition-all", 
            theme === "system" ? "scale-100 rotate-0 opacity-100" : "scale-0 rotate-90 opacity-0"
          )} />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem 
          onClick={() => setTheme("light")}
          className={cn("cursor-pointer", theme === "light" && "bg-accent")}
        >
          <Sun className="mr-2 h-4 w-4" />
          Light
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setTheme("dark")}
          className={cn("cursor-pointer", theme === "dark" && "bg-accent")}
        >
          <Moon className="mr-2 h-4 w-4" />
          Dark
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => setTheme("system")}
          className={cn("cursor-pointer", theme === "system" && "bg-accent")}
        >
          <Laptop className="mr-2 h-4 w-4" />
          System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
