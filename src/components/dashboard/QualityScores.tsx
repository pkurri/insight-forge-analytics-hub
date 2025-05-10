import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Award, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface QualityScore {
  id: string;
  name: string;
  score: number;
  category: string;
  lastUpdated: string;
}

interface QualityScoresProps {
  scores: QualityScore[];
  loading?: boolean;
}

const QualityScores: React.FC<QualityScoresProps> = ({ scores, loading = false }) => {
  if (loading) {
    return (
      <Card className="col-span-1">
        <CardHeader>
          <CardTitle>Quality Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center py-8">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group scores by category
  const scoresByCategory = scores.reduce<Record<string, QualityScore[]>>((acc, score) => {
    if (!acc[score.category]) {
      acc[score.category] = [];
    }
    acc[score.category].push(score);
    return acc;
  }, {});

  // Calculate average score per category
  const categoryAverages = Object.entries(scoresByCategory).map(([category, scores]) => {
    const total = scores.reduce((sum, score) => sum + score.score, 0);
    const average = total / scores.length;
    return { category, average };
  });

  // Calculate overall average
  const overallAverage = scores.length > 0
    ? scores.reduce((sum, score) => sum + score.score, 0) / scores.length
    : 0;

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-amber-500';
    return 'text-red-500';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (score >= 70) return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    return <XCircle className="h-4 w-4 text-red-500" />;
  };

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Quality Metrics</span>
          <div className="flex items-center gap-2">
            <span className={`text-lg font-bold ${getScoreColor(overallAverage)}`}>
              {Math.round(overallAverage)}%
            </span>
            <Award className="h-5 w-5 text-primary" />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {scores.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Award className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No quality metrics available</p>
            <p className="text-sm text-muted-foreground mt-2">Run evaluations to see quality scores</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Category averages */}
            <div className="grid grid-cols-2 gap-4">
              {categoryAverages.map(({ category, average }) => (
                <div key={category} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{category}</span>
                    <span className={`text-sm font-bold ${getScoreColor(average)}`}>
                      {Math.round(average)}%
                    </span>
                  </div>
                  <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                    <div 
                      className={`h-2 ${
                        average >= 90 ? 'bg-green-500' : average >= 70 ? 'bg-amber-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${average}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Individual scores */}
            <div className="space-y-3">
              {Object.entries(scoresByCategory).map(([category, categoryScores]) => (
                <div key={category} className="space-y-2">
                  <h4 className="text-sm font-medium">{category}</h4>
                  <div className="space-y-1">
                    {categoryScores.map((score) => (
                      <div key={score.id} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          {getScoreIcon(score.score)}
                          <span>{score.name}</span>
                        </div>
                        <span className={`font-medium ${getScoreColor(score.score)}`}>
                          {score.score}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default QualityScores;
