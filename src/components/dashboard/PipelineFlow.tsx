
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface PipelineNode {
  id: string;
  name: string;
  status: 'operational' | 'warning' | 'error' | 'inactive';
}

interface PipelineConnection {
  source: string;
  target: string;
  status: 'active' | 'warning' | 'error' | 'inactive';
}

interface PipelineFlowProps {
  nodes: PipelineNode[];
  connections: PipelineConnection[];
}

const PipelineFlow: React.FC<PipelineFlowProps> = ({ nodes, connections }) => {
  const getNodeColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'bg-success/20 border-success/50 text-success';
      case 'warning':
        return 'bg-warning/20 border-warning/50 text-warning';
      case 'error':
        return 'bg-error/20 border-error/50 text-error';
      case 'inactive':
      default:
        return 'bg-gray-100 border-gray-200 text-gray-500';
    }
  };

  const getConnectorColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'stroke-success';
      case 'warning':
        return 'stroke-warning';
      case 'error':
        return 'stroke-error';
      case 'inactive':
      default:
        return 'stroke-gray-300';
    }
  };

  // These would be calculated dynamically in a real app
  const nodePositions: Record<string, { x: number; y: number }> = {
    ingestion: { x: 50, y: 80 },
    cleaning: { x: 200, y: 80 },
    validation: { x: 350, y: 80 },
    anomaly: { x: 500, y: 80 },
    storage: { x: 650, y: 80 }
  };

  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle>Data Pipeline Flow</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative h-52">
          <svg className="w-full h-full" viewBox="0 0 700 150">
            {/* Draw connections */}
            {connections.map((conn, idx) => {
              const source = nodePositions[conn.source];
              const target = nodePositions[conn.target];
              if (!source || !target) return null;
              
              const connectorClass = cn(
                getConnectorColor(conn.status),
                "stroke-[3] fill-none",
              );
              
              return (
                <g key={`conn-${idx}`}>
                  <path
                    d={`M${source.x + 75} ${source.y} L${target.x} ${target.y}`}
                    className={cn(connectorClass, "animate-flow")}
                    strokeDasharray="5,5"
                  />
                </g>
              );
            })}
            
            {/* Draw nodes */}
            {nodes.map((node) => {
              const position = nodePositions[node.id];
              if (!position) return null;
              
              const nodeClass = getNodeColor(node.status);
              
              return (
                <g key={node.id} transform={`translate(${position.x}, ${position.y})`}>
                  <foreignObject width="150" height="60">
                    <div className="h-full">
                      <div 
                        className={cn(
                          "h-full border rounded-md p-2 flex items-center justify-center text-center text-sm font-medium shadow-sm",
                          nodeClass,
                          node.status === 'operational' && "animate-pulse-soft"
                        )}
                      >
                        {node.name}
                      </div>
                    </div>
                  </foreignObject>
                </g>
              );
            })}
          </svg>
        </div>
      </CardContent>
    </Card>
  );
};

export default PipelineFlow;
