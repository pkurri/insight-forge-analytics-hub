
import React, { useState, useEffect } from 'react';
import { Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { api } from '@/api/api';
import { Skeleton } from '@/components/ui/skeleton';
import { BusinessRule } from '@/api/types';

interface BusinessRulesSelectProps {
  datasetId?: string;
  onSelect: (selectedRules: string[]) => void;
  className?: string;
}

export const BusinessRulesSelect: React.FC<BusinessRulesSelectProps> = ({
  datasetId,
  onSelect,
  className,
}) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [businessRules, setBusinessRules] = useState<BusinessRule[]>([]);
  const [selectedRuleIds, setSelectedRuleIds] = useState<string[]>([]);

  useEffect(() => {
    const fetchBusinessRules = async () => {
      setLoading(true);
      try {
        const response = await api.businessRules.getBusinessRules();
        if (response.success && response.data) {
          setBusinessRules(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch business rules:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchBusinessRules();
  }, []);

  const handleSelect = (ruleId: string) => {
    const updatedSelection = selectedRuleIds.includes(ruleId)
      ? selectedRuleIds.filter(id => id !== ruleId)
      : [...selectedRuleIds, ruleId];
    
    setSelectedRuleIds(updatedSelection);
    onSelect(updatedSelection);
  };

  return (
    <div className={cn("space-y-2", className)}>
      <label className="text-sm font-medium leading-none text-gray-700">
        Apply Business Rules
      </label>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between"
            disabled={loading}
          >
            {selectedRuleIds.length > 0
              ? `${selectedRuleIds.length} rule${selectedRuleIds.length > 1 ? 's' : ''} selected`
              : "Select rules to apply..."}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-full p-0">
          {loading ? (
            <div className="p-4 space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
            </div>
          ) : (
            <Command>
              <CommandInput placeholder="Search business rules..." />
              <CommandList>
                <CommandEmpty>No business rules found.</CommandEmpty>
                <CommandGroup>
                  {businessRules.map((rule) => (
                    <CommandItem
                      key={rule.id}
                      value={rule.id}
                      onSelect={() => handleSelect(rule.id)}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          selectedRuleIds.includes(rule.id) 
                            ? "opacity-100" 
                            : "opacity-0"
                        )}
                      />
                      <div className="flex flex-col">
                        <span>{rule.name}</span>
                        <span className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {rule.description || rule.condition}
                        </span>
                      </div>
                      <span className={cn(
                        "ml-auto text-xs px-2 py-1 rounded-full",
                        rule.severity === 'high' ? "bg-red-100 text-red-800" :
                        rule.severity === 'medium' ? "bg-yellow-100 text-yellow-800" :
                        "bg-blue-100 text-blue-800"
                      )}>
                        {rule.severity}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          )}
        </PopoverContent>
      </Popover>
      {selectedRuleIds.length > 0 && (
        <div className="text-xs text-muted-foreground">
          {selectedRuleIds.length} business rule{selectedRuleIds.length > 1 ? 's' : ''} will be applied during data processing
        </div>
      )}
    </div>
  );
};

export default BusinessRulesSelect;
