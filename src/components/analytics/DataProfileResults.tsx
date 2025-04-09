
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/api/api';
import { useToast } from '@/hooks/use-toast';
import {
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const COLORS = ['#4ade80', '#facc15', '#f87171', '#60a5fa', '#a78bfa'];

export interface ProfileSummary {
  row_count: number;
  column_count: number;
  missing_cells: number;
  missing_cells_pct: number;
  duplicate_rows: number;
  duplicate_rows_pct: number;
  memory_usage: number;
}

const DataProfileResults: React.FC = () => {
  const [profileData, setProfileData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        // Use sample dataset ID for demo
        const response = await api.profileDataset('ds001');
        if (response.success && response.data) {
          setProfileData(response.data);
        } else {
          toast({
            title: "Error fetching profile data",
            description: response.error || "Unknown error occurred",
            variant: "destructive"
          });
        }
      } catch (error) {
        console.error("Error fetching profile data:", error);
        toast({
          title: "Error fetching profile data",
          description: "Failed to fetch profile results",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchProfileData();
  }, [toast]);

  const renderSummaryCards = () => {
    if (!profileData?.summary) {
      return <Skeleton className="h-40 w-full" />;
    }

    const summary: ProfileSummary = profileData.summary;
    
    const summaryCards = [
      { title: "Rows", value: summary.row_count.toLocaleString() },
      { title: "Columns", value: summary.column_count.toLocaleString() },
      { title: "Missing Values", value: `${summary.missing_cells.toLocaleString()} (${summary.missing_cells_pct.toFixed(2)}%)` },
      { title: "Duplicate Rows", value: `${summary.duplicate_rows.toLocaleString()} (${summary.duplicate_rows_pct.toFixed(2)}%)` },
      { title: "Memory Usage", value: `${(summary.memory_usage / (1024 * 1024)).toFixed(2)} MB` }
    ];

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {summaryCards.map((card, index) => (
          <Card key={index} className="shadow-sm">
            <CardHeader className="py-4">
              <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold">{card.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  const renderColumnDistribution = () => {
    if (!profileData?.detailed_profile?.variables) {
      return <Skeleton className="h-80 w-full" />;
    }

    // Extract column types data from the profile
    const variables = profileData.detailed_profile.variables;
    const columnTypes = Object.keys(variables).reduce((acc: any, key) => {
      const type = variables[key].type;
      if (!acc[type]) {
        acc[type] = 0;
      }
      acc[type]++;
      return acc;
    }, {});

    const columnTypesData = Object.keys(columnTypes).map(type => ({
      name: type,
      value: columnTypes[type]
    }));

    return (
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={columnTypesData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              fill="#8884d8"
              paddingAngle={5}
              dataKey="value"
              label={({name, percent}) => `${name} ${(percent * 100).toFixed(1)}%`}
            >
              {columnTypesData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderMissingValues = () => {
    if (!profileData?.detailed_profile?.variables) {
      return <Skeleton className="h-80 w-full" />;
    }

    // Extract missing values data
    const variables = profileData.detailed_profile.variables;
    const missingData = Object.keys(variables).map(key => ({
      name: key,
      missing: variables[key].n_missing,
      complete: variables[key].n - variables[key].n_missing
    })).sort((a, b) => b.missing - a.missing).slice(0, 10); // Top 10 columns with missing values

    return (
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={missingData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" />
            <Tooltip />
            <Legend />
            <Bar dataKey="missing" stackId="a" fill="#f87171" name="Missing" />
            <Bar dataKey="complete" stackId="a" fill="#4ade80" name="Complete" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Dataset Profile Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : (
            <>
              {renderSummaryCards()}
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Column Type Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-80 w-full" /> : renderColumnDistribution()}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Missing Values by Column (Top 10)</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? <Skeleton className="h-80 w-full" /> : renderMissingValues()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DataProfileResults;
