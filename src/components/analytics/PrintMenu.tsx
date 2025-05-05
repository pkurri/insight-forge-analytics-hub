
import React from "react";
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function PrintMenu() {
  const handlePrint = () => {
    window.print();
  };
  
  return (
    <div className="mb-4">
      <Button 
        onClick={handlePrint} 
        variant="outline"
        className="flex items-center gap-2 hover:bg-orange-50 border-orange-300 text-orange-600 hover:text-orange-700"
      >
        <Printer size={18} />
        Print / Save as PDF
      </Button>
    </div>
  );
}
