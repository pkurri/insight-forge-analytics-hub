import React from 'react';
import { BarChart as LucideBarChart, LineChart as LucideLineChart, PieChart as LucidePieChart } from 'lucide-react';

/* 
 * This file contains chart components for the dashboard.
 * In a real application, these would be implemented using a charting library
 * like Chart.js, D3.js, or Recharts. For now, we'll use placeholder components.
 */

interface ChartProps {
  data: any[];
  className?: string;
  height?: number;
  width?: number;
}

export const BarChart: React.FC<ChartProps> = ({ data, className, height = 300, width = 500 }) => {
  // In a real application, this would render an actual bar chart
  // For now, let's display a placeholder
  
  return (
    <div className={`flex flex-col items-center justify-center ${className}`} style={{ height, width }}>
      <div className="flex-1 w-full flex items-center justify-center p-4">
        <div className="relative w-full h-full flex items-end justify-between gap-2 pb-10">
          {data && data.length > 0 ? (
            // Render simple bars based on the data
            data.map((item, index) => {
              // Normalize the value to a percentage for visualization
              const value = typeof item.value !== 'undefined' 
                ? item.value 
                : (typeof item.usage !== 'undefined' ? item.usage : (typeof item.time !== 'undefined' ? item.time : 50));
              
              const normalizedHeight = (value / 100) * 80;
              
              return (
                <div 
                  key={index} 
                  className="relative flex flex-col items-center"
                  style={{ width: `${100 / data.length}%` }}
                >
                  <div 
                    className="w-full bg-primary/80 rounded-t-sm hover:bg-primary transition-all" 
                    style={{ height: `${normalizedHeight}%` }}
                  />
                  <div className="absolute -bottom-8 text-xs text-muted-foreground text-center max-w-full truncate">
                    {item.name || item.stage || `Item ${index+1}`}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="flex items-center justify-center w-full h-full">
              <LucideBarChart className="w-12 h-12 text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">No data available</span>
            </div>
          )}
          {/* X-axis line */}
          <div className="absolute bottom-0 left-0 w-full h-px bg-border" />
        </div>
      </div>
    </div>
  );
};

export const LineChart: React.FC<ChartProps> = ({ data, className, height = 300, width = 500 }) => {
  // In a real application, this would render an actual line chart
  // For now, let's display a placeholder
  
  return (
    <div className={`flex flex-col items-center justify-center ${className}`} style={{ height, width }}>
      <div className="flex-1 w-full flex items-center justify-center p-4">
        {data && data.length > 0 ? (
          <div className="relative w-full h-full">
            <svg 
              viewBox={`0 0 ${width} ${height}`} 
              className="w-full h-full overflow-visible"
            >
              {/* Create a simple line based on data points */}
              <polyline
                points={data.map((point, index) => {
                  const x = (index / (data.length - 1)) * width;
                  const value = typeof point.value !== 'undefined' ? point.value : 50;
                  const maxValue = Math.max(...data.map(d => d.value || 0));
                  const y = height - ((value / maxValue) * height * 0.8);
                  return `${x},${y}`;
                }).join(' ')}
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-primary"
              />
              
              {/* Add dots for each data point */}
              {data.map((point, index) => {
                const x = (index / (data.length - 1)) * width;
                const value = typeof point.value !== 'undefined' ? point.value : 50;
                const maxValue = Math.max(...data.map(d => d.value || 0));
                const y = height - ((value / maxValue) * height * 0.8);
                
                return (
                  <circle
                    key={index}
                    cx={x}
                    cy={y}
                    r="4"
                    className="fill-primary"
                  />
                );
              })}
            </svg>
          </div>
        ) : (
          <div className="flex items-center justify-center w-full h-full">
            <LucideLineChart className="w-12 h-12 text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">No data available</span>
          </div>
        )}
      </div>
    </div>
  );
};

export const PieChart: React.FC<ChartProps> = ({ data, className, height = 300, width = 300 }) => {
  // In a real application, this would render an actual pie chart
  // For now, let's display a placeholder
  
  // Calculate total for percentages
  const total = data?.reduce((sum, item) => sum + (item.count || item.value || 0), 0) || 0;
  
  // Define some colors for the pie segments
  const colors = [
    'fill-blue-500',
    'fill-green-500',
    'fill-yellow-500',
    'fill-red-500',
    'fill-purple-500',
    'fill-indigo-500',
    'fill-pink-500',
  ];
  
  // Calculate segments
  let startAngle = 0;
  const segments = data?.map((item, index) => {
    const value = item.count || item.value || 0;
    const percentage = total > 0 ? (value / total) * 100 : 0;
    const angle = (percentage / 100) * 360;
    
    const x1 = 50 + 40 * Math.cos(((startAngle) * Math.PI) / 180);
    const y1 = 50 + 40 * Math.sin(((startAngle) * Math.PI) / 180);
    const x2 = 50 + 40 * Math.cos(((startAngle + angle) * Math.PI) / 180);
    const y2 = 50 + 40 * Math.sin(((startAngle + angle) * Math.PI) / 180);
    
    // Determine if this segment is more than half the circle
    const largeArcFlag = angle > 180 ? 1 : 0;
    
    // Create SVG arc path
    const pathData = `
      M 50 50
      L ${x1} ${y1}
      A 40 40 0 ${largeArcFlag} 1 ${x2} ${y2}
      Z
    `;
    
    const segment = {
      path: pathData,
      color: colors[index % colors.length],
      name: item.name || item.status || `Segment ${index+1}`,
      percentage,
      startAngle,
      endAngle: startAngle + angle
    };
    
    startAngle += angle;
    return segment;
  }) || [];
  
  return (
    <div className={`flex flex-col items-center justify-center ${className}`} style={{ height, width }}>
      <div className="flex-1 w-full flex items-center justify-center p-4">
        {data && data.length > 0 ? (
          <div className="relative">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              {segments.map((segment, index) => (
                <path
                  key={index}
                  d={segment.path}
                  className={`${segment.color} hover:opacity-90 transition-opacity`}
                  stroke="white"
                  strokeWidth="1"
                />
              ))}
            </svg>
            
            <div className="mt-4 grid grid-cols-2 gap-2">
              {segments.map((segment, index) => (
                <div key={index} className="flex items-center text-xs">
                  <div className={`w-3 h-3 ${segment.color} mr-1 rounded-sm`} />
                  <span className="truncate">{segment.name}</span>
                  <span className="ml-1 font-medium">{segment.percentage.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center w-full h-full">
            <LucidePieChart className="w-12 h-12 text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">No data available</span>
          </div>
        )}
      </div>
    </div>
  );
};
