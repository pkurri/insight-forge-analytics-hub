
import React from "react";
import { Printer, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";

interface PrintMenuProps {
  onExportPDF?: () => void;
  onExportCSV?: () => void;
  className?: string;
}

export default function PrintMenu({ onExportPDF, onExportCSV, className }: PrintMenuProps) {
  const handlePrint = () => {
    window.print();
  };
  
  return (
    <div className={className}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button 
            variant="outline"
            className="flex items-center gap-2 hover:bg-orange-50 border-orange-300 text-orange-600 hover:text-orange-700"
            aria-label="Print or export options"
          >
            <Printer className="h-4 w-4" />
            <span className="hidden sm:inline">Export / Print</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={handlePrint}>
            <Printer className="h-4 w-4 mr-2" />
            Print / Save as PDF
          </DropdownMenuItem>
          {onExportPDF && (
            <DropdownMenuItem onClick={onExportPDF}>
              <Download className="h-4 w-4 mr-2" />
              Export as PDF
            </DropdownMenuItem>
          )}
          {onExportCSV && (
            <DropdownMenuItem onClick={onExportCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export as CSV
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
