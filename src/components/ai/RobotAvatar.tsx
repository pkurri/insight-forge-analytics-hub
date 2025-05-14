import React from 'react';
import { cn } from '@/lib/utils';

interface RobotAvatarProps {
  className?: string;
  isAnimated?: boolean;
}

/**
 * A modern animated robot avatar component for the AI assistant
 */
const RobotAvatar: React.FC<RobotAvatarProps> = ({ 
  className,
  isAnimated = true 
}) => {
  return (
    <div className={cn(
      "flex items-center justify-center overflow-hidden rounded-full bg-primary/10 ring-1 ring-primary/20",
      className
    )}>
      {isAnimated ? (
        // Animated SVG robot with modern design
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="p-1"
        >
          <g className="animate-pulse">
            <circle cx="16" cy="16" r="14" fill="currentColor" fillOpacity="0.1" />
          </g>
          
          {/* Robot head */}
          <rect 
            x="10" 
            y="8" 
            width="12" 
            height="14" 
            rx="2" 
            fill="currentColor" 
            className="text-primary"
          />
          
          {/* Robot eyes - animated */}
          <circle 
            cx="13" 
            cy="13" 
            r="1.5" 
            fill="white" 
            className="animate-[pulse_3s_ease-in-out_infinite]"
          />
          <circle 
            cx="19" 
            cy="13" 
            r="1.5" 
            fill="white" 
            className="animate-[pulse_3s_ease-in-out_infinite_0.5s]"
          />
          
          {/* Robot mouth - animated */}
          <rect 
            x="13" 
            y="17" 
            width="6" 
            height="1" 
            rx="0.5" 
            fill="white" 
            className="animate-[pulse_4s_ease-in-out_infinite]"
          />
          
          {/* Robot antennas */}
          <rect 
            x="15.5" 
            y="5" 
            width="1" 
            height="3" 
            fill="currentColor" 
            className="text-primary"
          />
          <circle 
            cx="16" 
            cy="5" 
            r="1" 
            fill="currentColor" 
            className="text-primary animate-[pulse_2s_ease-in-out_infinite]"
          />
          
          {/* Robot body parts */}
          <rect 
            x="12" 
            y="22" 
            width="8" 
            height="4" 
            rx="1" 
            fill="currentColor" 
            className="text-primary/80"
          />
          
          {/* Connection lines - animated */}
          <line 
            x1="10" 
            y1="24" 
            x2="7" 
            y2="24" 
            stroke="currentColor" 
            strokeWidth="0.75" 
            className="text-primary animate-[pulse_4s_ease-in-out_infinite]"
          />
          <line 
            x1="22" 
            y1="24" 
            x2="25" 
            y2="24" 
            stroke="currentColor" 
            strokeWidth="0.75" 
            className="text-primary animate-[pulse_4s_ease-in-out_infinite_0.5s]"
          />
        </svg>
      ) : (
        // Static fallback
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="p-1"
        >
          <rect 
            x="10" 
            y="8" 
            width="12" 
            height="14" 
            rx="2" 
            fill="currentColor" 
            className="text-primary"
          />
          <circle cx="13" cy="13" r="1.5" fill="white" />
          <circle cx="19" cy="13" r="1.5" fill="white" />
          <rect x="13" y="17" width="6" height="1" rx="0.5" fill="white" />
          <rect x="15.5" y="5" width="1" height="3" fill="currentColor" className="text-primary" />
          <circle cx="16" cy="5" r="1" fill="currentColor" className="text-primary" />
          <rect x="12" y="22" width="8" height="4" rx="1" fill="currentColor" className="text-primary/80" />
        </svg>
      )}
    </div>
  );
};

export default RobotAvatar;
