import React from 'react';
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';

// Define a more specific type for trend data
interface TrendDataPoint {
  [key: string]: string | number | Date;
}

interface TrendIndicatorProps {
  data?: TrendDataPoint[];
  xKey?: string;
  yKey?: string;
  className?: string;
  loading?: boolean;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({
  data = [],
  xKey = 'date',
  yKey = 'value',
  className = '',
  loading = false
}) => {
  if (loading) {
    return (
      <div className={`flex items-center justify-center h-64 ${className}`}>
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-64 ${className}`}>
        <p className="text-muted-foreground">No trend data available</p>
      </div>
    );
  }

  // Calculate trend direction
  const calculateTrend = () => {
    if (!data || data.length < 2) return 'neutral';
    
    // Ensure we're working with numbers for calculations
    const firstValue = Number(data[0][yKey]);
    const lastValue = Number(data[data.length - 1][yKey]);
    
    // Check if values are valid numbers
    if (isNaN(firstValue) || isNaN(lastValue) || firstValue === 0) return 'neutral';
    
    const percentChange = ((lastValue - firstValue) / firstValue) * 100;
    
    if (percentChange > 5) return 'up';
    if (percentChange < -5) return 'down';
    return 'neutral';
  };

  const trend = calculateTrend();
  
  return (
    <div className={`w-full h-64 ${className}`}>
      <div className="flex items-center justify-end mb-2">
        <div className="flex items-center gap-1">
          <span className="text-sm font-medium">Trend:</span>
          {trend === 'up' ? (
            <div className="flex items-center text-green-500">
              <ArrowUpRight className="h-4 w-4" />
              <span className="text-sm">Increasing</span>
            </div>
          ) : trend === 'down' ? (
            <div className="flex items-center text-red-500">
              <ArrowDownRight className="h-4 w-4" />
              <span className="text-sm">Decreasing</span>
            </div>
          ) : (
            <div className="flex items-center text-muted-foreground">
              <ArrowRight className="h-4 w-4" />
              <span className="text-sm">Stable</span>
            </div>
          )}
        </div>
      </div>
      <ResponsiveContainer width="100%" height="90%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={yKey}
            stroke={
              trend === 'up' 
                ? 'var(--green-500)' 
                : trend === 'down' 
                  ? 'var(--red-500)' 
                  : 'var(--primary)'
            }
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TrendIndicator;
