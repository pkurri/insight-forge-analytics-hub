import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { CheckCircle, XCircle, AlertCircle, AlertTriangle } from 'lucide-react';

interface DataQualityReportProps {
  qualityData: {
    columns?: Array<{
      name: string;
      dataType: string;
      completeness: number;
      uniqueness?: number;
      validFormat?: number;
      issues?: string[];
    }>;
    overallScore?: number;
  };
  loading?: boolean;
}

const DataQualityReport: React.FC<DataQualityReportProps> = ({ qualityData, loading = false }) => {
  const getStatusIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="h-5 w-5 text-green-500" />;
    if (score >= 70) return <AlertCircle className="h-5 w-5 text-amber-500" />;
    if (score >= 50) return <AlertTriangle className="h-5 w-5 text-orange-500" />;
    return <XCircle className="h-5 w-5 text-red-500" />;
  };
  
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-amber-500';
    if (score >= 50) return 'text-orange-500';
    return 'text-red-500';
  };
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Data Quality Report</CardTitle>
            <CardDescription>Quality metrics by column</CardDescription>
          </div>
          {!loading && qualityData.overallScore !== undefined && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Overall Quality:</span>
              <span className={`text-lg font-bold ${getScoreColor(qualityData.overallScore)}`}>
                {qualityData.overallScore.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : qualityData.columns && qualityData.columns.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Column</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Completeness</TableHead>
                <TableHead>Uniqueness</TableHead>
                <TableHead>Valid Format</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {qualityData.columns.map((column, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{column.name}</TableCell>
                  <TableCell>{column.dataType}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                        <div 
                          className={getScoreColor(column.completeness)}
                          style={{ 
                            width: `${column.completeness}%`, 
                            height: '100%', 
                            backgroundColor: 'currentColor' 
                          }}
                        />
                      </div>
                      <span className="text-xs">{column.completeness}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {column.uniqueness !== undefined ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                          <div 
                            className={getScoreColor(column.uniqueness)}
                            style={{ 
                              width: `${column.uniqueness}%`, 
                              height: '100%', 
                              backgroundColor: 'currentColor' 
                            }}
                          />
                        </div>
                        <span className="text-xs">{column.uniqueness}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {column.validFormat !== undefined ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-secondary rounded-full overflow-hidden">
                          <div 
                            className={getScoreColor(column.validFormat)}
                            style={{ 
                              width: `${column.validFormat}%`, 
                              height: '100%', 
                              backgroundColor: 'currentColor' 
                            }}
                          />
                        </div>
                        <span className="text-xs">{column.validFormat}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {getStatusIcon(column.completeness)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No quality data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DataQualityReport;
