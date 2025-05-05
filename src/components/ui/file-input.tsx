
import React, { ChangeEvent, forwardRef, useRef } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';

export interface FileInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'onChange'> {
  onChange?: (file: File | null) => void;
}

export const FileInput = forwardRef<HTMLInputElement, FileInputProps>(
  ({ className, onChange, disabled, ...props }, ref) => {
    const inputRef = useRef<HTMLInputElement>(null);
    const [fileName, setFileName] = React.useState<string | null>(null);

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] || null;
      setFileName(file?.name || null);
      if (onChange) {
        onChange(file);
      }
    };

    const handleButtonClick = () => {
      inputRef.current?.click();
    };

    return (
      <div className="w-full">
        <input
          type="file"
          className="hidden"
          ref={(node) => {
            // Handle both the internal ref and the forwarded ref
            if (typeof ref === 'function') {
              ref(node);
            } else if (ref) {
              ref.current = node;
            }
            inputRef.current = node;
          }}
          onChange={handleChange}
          disabled={disabled}
          {...props}
        />
        <div className="flex items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={handleButtonClick}
            disabled={disabled}
            className={cn(className)}
          >
            <Upload className="w-4 h-4 mr-2" />
            Choose File
          </Button>
          <div className="text-sm text-muted-foreground">
            {fileName ? fileName : 'No file selected'}
          </div>
        </div>
      </div>
    );
  }
);

FileInput.displayName = 'FileInput';
