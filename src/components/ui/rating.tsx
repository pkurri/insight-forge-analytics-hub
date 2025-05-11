import React, { useState } from 'react';
import { Star, StarHalf } from 'lucide-react';
import { cn } from '@/utils/utils';

interface RatingProps {
  value: number;
  onValueChange?: (value: number) => void;
  max?: number;
  readOnly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  color?: string;
}

/**
 * Rating component for collecting user feedback
 * Supports half-star precision and customizable styling
 */
export function Rating({
  value,
  onValueChange,
  max = 5,
  readOnly = false,
  size = 'md',
  className,
  color = 'text-yellow-400'
}: RatingProps) {
  const [hoverValue, setHoverValue] = useState<number | null>(null);
  
  const displayValue = hoverValue !== null ? hoverValue : value;
  
  const sizes = {
    sm: { star: 'h-4 w-4', wrapper: 'gap-1' },
    md: { star: 'h-5 w-5', wrapper: 'gap-1.5' },
    lg: { star: 'h-6 w-6', wrapper: 'gap-2' }
  };
  
  const stars = Array.from({ length: max }, (_, i) => {
    const starValue = i + 1;
    const isHalfStar = displayValue > i && displayValue < i + 1;
    const isFullStar = displayValue >= starValue;
    
    return (
      <button
        key={i}
        type="button"
        className={cn(
          'relative flex items-center justify-center focus:outline-none',
          readOnly ? 'cursor-default' : 'cursor-pointer'
        )}
        onClick={() => {
          if (!readOnly && onValueChange) {
            onValueChange(starValue);
          }
        }}
        onMouseEnter={() => {
          if (!readOnly) {
            setHoverValue(starValue);
          }
        }}
        onMouseLeave={() => {
          if (!readOnly) {
            setHoverValue(null);
          }
        }}
        disabled={readOnly}
        aria-label={`Rate ${starValue} out of ${max}`}
      >
        {isFullStar ? (
          <Star className={cn(sizes[size].star, color, 'fill-current')} />
        ) : isHalfStar ? (
          <div className="relative">
            <Star className={cn(sizes[size].star, 'text-gray-300')} />
            <div className="absolute inset-0 overflow-hidden w-1/2">
              <Star className={cn(sizes[size].star, color, 'fill-current')} />
            </div>
          </div>
        ) : (
          <Star className={cn(sizes[size].star, 'text-gray-300')} />
        )}
      </button>
    );
  });
  
  return (
    <div className={cn('flex items-center', sizes[size].wrapper, className)}>
      {stars}
    </div>
  );
}
