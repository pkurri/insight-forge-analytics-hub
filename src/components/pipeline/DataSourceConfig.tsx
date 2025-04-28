import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Switch } from '@/components/ui/switch';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Plus, Trash2, Database, Globe, Key, Loader2 } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { api } from '@/api/api';
import { datasourceService } from '@/api/services/datasource/datasourceService';

// Schema for API connection form
const apiFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  url: z.string().url("Please enter a valid URL"),
  authType: z.enum(["none", "basic", "bearer", "api_key"]),
  username: z.string().optional(),
  password: z.string().optional(),
  apiKey: z.string().optional(),
  apiKeyName: z.string().optional(),
  bearerToken: z.string().optional(),
  headers: z.string().optional(),
});

// Schema for database connection form
const dbFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  connectionType: z.enum(["postgresql", "mysql", "sqlserver", "oracle", "mongodb"]),
  host: z.string().min(1, "Host is required"),
  port: z.string().refine((val) => !isNaN(parseInt(val)), "Port must be a number"),
  database: z.string().min(1, "Database name is required"),
  username: z.string().optional(),
  password: z.string().optional(),
  ssl: z.boolean().default(false),
  options: z.string().optional(),
});

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

interface Dataset {
  id: string;
  name: string;
  createdAt: string;
}

interface ApiConnection {
  id: string;
  name: string;
  url: string;
  authType: string;
  username?: string;
  password?: string;
  apiKey?: string;
  apiKeyName?: string;
  bearerToken?: string;
  headers?: string;
  createdAt: string;
}

interface DbConnection {
  id: string;
  name: string;
  connectionType: string;
  host: string;
  port: string;
  database: string;
  username?: string;
  password?: string;
  ssl: boolean;
  options?: string;
  createdAt: string;
}

interface ApiClient {
  callApi: <T = any>(endpoint: string, method?: "GET" | "POST" | "PUT" | "DELETE", data?: any) => Promise<ApiResponse<T>>;
  datasets: {
    getDatasets: () => Promise<ApiResponse<Dataset[]>>;
    getDataset: (id: string) => Promise<ApiResponse<Dataset>>;
    uploadDataset: (file: File, name: string) => Promise<ApiResponse<Dataset>>;
    deleteDataset: (id: string) => Promise<ApiResponse<void>>;
  };
  pipeline: {
    getApiConnections: () => Promise<ApiResponse<ApiConnection[]>>;
    getDbConnections: () => Promise<ApiResponse<DbConnection[]>>;
    createApiConnection: (data: Omit<ApiConnection, 'id' | 'createdAt'>) => Promise<ApiResponse<ApiConnection>>;
    createDbConnection: (data: Omit<DbConnection, 'id' | 'createdAt'>) => Promise<ApiResponse<DbConnection>>;
    deleteApiConnection: (id: string) => Promise<ApiResponse<void>>;
    deleteDbConnection: (id: string) => Promise<ApiResponse<void>>;
    testApiConnection: (id: string) => Promise<ApiResponse<{status: string}>>;
    testDbConnection: (id: string) => Promise<ApiResponse<{status: string}>>;
  };
}

const DataSourceConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("api");
  const [showApiDialog, setShowApiDialog] = useState<boolean>(false);
  const [showDbDialog, setShowDbDialog] = useState<boolean>(false);
  const [apiConnections, setApiConnections] = useState<ApiConnection[]>([]);
  const [dbConnections, setDbConnections] = useState<DbConnection[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [editingApiConnection, setEditingApiConnection] = useState<ApiConnection | null>(null);
  const [editingDbConnection, setEditingDbConnection] = useState<DbConnection | null>(null);
  const [testingConnectionId, setTestingConnectionId] = useState<string | null>(null);
  const { toast } = useToast();
  
  // Fetch existing connections when component mounts
  useEffect(() => {
    const fetchConnections = async () => {
      setIsLoading(true);
      try {
        const [apiResponse, dbResponse] = await Promise.all([
          datasourceService.getApiConnections(),
          datasourceService.getDbConnections()
        ]);

        if (apiResponse.success) {
          setApiConnections(apiResponse.data || []);
        } else {
          toast({
            title: 'Error',
            description: apiResponse.error || 'Failed to fetch API connections',
            variant: 'destructive'
          });
        }

        if (dbResponse.success) {
          setDbConnections(dbResponse.data || []);
        } else {
          toast({
            title: 'Error',
            description: dbResponse.error || 'Failed to fetch DB connections',
            variant: 'destructive'
          });
        }
      } catch (error) {
        console.error('Error fetching connections:', error);
        toast({
          title: 'Error',
          description: 'An unexpected error occurred while fetching connections',
          variant: 'destructive'
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchConnections();
  }, []);
  
  // API form
  const apiForm = useForm<z.infer<typeof apiFormSchema>>({
    resolver: zodResolver(apiFormSchema),
    defaultValues: {
      name: "",
      url: "",
      authType: "none",
      username: "",
      password: "",
      apiKey: "",
      apiKeyName: "",
      bearerToken: "",
      headers: "",
    },
  });
  
  // DB form
  const dbForm = useForm<z.infer<typeof dbFormSchema>>({
    resolver: zodResolver(dbFormSchema),
    defaultValues: {
      name: "",
      connectionType: "postgresql",
      host: "",
      port: "",
      database: "",
      username: "",
      password: "",
      ssl: false,
      options: "",
    },
  });
  
  const onApiSubmit = async (values: z.infer<typeof apiFormSchema>) => {
    try {
      setIsLoading(true);
      // Ensure all required fields are present for type safety
      const apiPayload: Omit<ApiConnection, 'id' | 'createdAt'> = {
        name: values.name,
        url: values.url,
        authType: values.authType,
        username: values.username ?? '',
        password: values.password ?? '',
        apiKey: values.apiKey ?? '',
        apiKeyName: values.apiKeyName ?? '',
        bearerToken: values.bearerToken ?? '',
        headers: values.headers ?? ''
      };
      const response = editingApiConnection
        ? await api.datasource.updateApiConnection(editingApiConnection.id, apiPayload)
        : await api.datasource.createApiConnection(apiPayload);
      
      if (response.success && response.data) {
        setApiConnections(editingApiConnection
          ? apiConnections.map(conn => conn.id === editingApiConnection.id ? response.data! : conn)
          : [...apiConnections, response.data]);
        
        setShowApiDialog(false);
        setEditingApiConnection(null);
        apiForm.reset();
        
        toast({
          title: editingApiConnection ? "API Connection Updated" : "API Connection Added",
          description: `Successfully ${editingApiConnection ? 'updated' : 'created'} connection to ${values.name}`,
        });
      } else {
        toast({
          title: "Error",
          description: response.error || 'Failed to save API connection',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error saving API connection:', error);
      toast({
        title: "Error",
        description: 'Failed to save API connection',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const onDbSubmit = async (values: z.infer<typeof dbFormSchema>) => {
    try {
      setIsLoading(true);
      // Save to backend
      // Ensure all required fields are present for type safety
      const dbPayload: Omit<DbConnection, 'id' | 'createdAt'> = {
        name: values.name,
        connectionType: values.connectionType,
        host: values.host,
        port: values.port,
        database: values.database,
        username: values.username ?? '',
        password: values.password ?? '',
        ssl: values.ssl,
        options: values.options ?? ''
      };
      const response = await api.datasource.createDbConnection(dbPayload);
      
      if (response.success && response.data) {
        // Add the new connection to state
        setDbConnections([...dbConnections, response.data]);
        setShowDbDialog(false);
        dbForm.reset();
        
        toast({
          title: "Database Connection Added",
          description: `Successfully created connection to ${values.name}`,
        });
      } else {
        toast({
          title: "Error",
          description: response.error || 'Failed to create database connection',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error creating database connection:', error);
      toast({
        title: "Error",
        description: 'Failed to create database connection',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const deleteApiConnection = async (id: string) => {
    try {
      setIsLoading(true);
      const response = await api.datasource.deleteApiConnection(id);
      
      if (response.success) {
        setApiConnections(apiConnections.filter(conn => conn.id !== id));
        toast({
          title: 'Success',
          description: 'API connection deleted successfully',
        });
      } else {
        toast({
          title: 'Error',
          description: response.error || 'Failed to delete API connection',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error deleting API connection:', error);
      toast({
        title: 'Error',
        description: 'An unexpected error occurred',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const deleteDbConnection = async (id: string) => {
    try {
      setIsLoading(true);
      // Delete from backend
      const response = await api.datasource.deleteDbConnection(id);
      
      if (response.success) {
        // Remove from state
        setDbConnections(dbConnections.filter(conn => conn.id !== id));
        toast({
          title: "Connection Removed",
          description: "Database connection has been deleted",
        });
      } else {
        toast({
          title: "Error",
          description: response.error || 'Failed to delete database connection',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error deleting database connection:', error);
      toast({
        title: "Error",
        description: 'Failed to delete database connection',
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const testConnection = async (type: 'api' | 'db', id: string) => {
    try {
      setTestingConnectionId(id);
      const response = type === 'api' 
        ? await api.datasource.testApiConnection(id)
        : await api.datasource.testDbConnection(id);
      
      if (response.success) {
        toast({
          title: 'Connection Test',
          description: `Connection test ${response.data?.status === 'success' ? 'passed' : 'failed'}`,
          variant: response.data?.status === 'success' ? 'default' : 'destructive'
        });
      } else {
        toast({
          title: 'Error',
          description: response.error || 'Failed to test connection',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      toast({
        title: 'Error',
        description: 'An unexpected error occurred',
        variant: 'destructive'
      });
    } finally {
      setTestingConnectionId(null);
    }
  };
  
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex flex-col justify-center items-center h-64 gap-2">
          <Loader2 className="animate-spin h-8 w-8 text-muted-foreground" />
          <span className="text-muted-foreground">Loading connections...</span>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Source Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-2 mb-4">
            <TabsTrigger value="api">External APIs</TabsTrigger>
            <TabsTrigger value="database">Databases</TabsTrigger>
          </TabsList>

          <TabsContent value="api" className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">API Connections</h3>
              <Dialog open={showApiDialog} onOpenChange={setShowApiDialog}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add API Connection
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
                    <DialogTitle>{editingApiConnection ? "Edit API Connection" : "Add API Connection"}</DialogTitle>
                    <button aria-label="Close dialog" className="absolute right-4 top-4" onClick={() => { setShowApiDialog(false); setEditingApiConnection(null); }}>
                      ×
                    </button>
                  </DialogHeader>
                  
                  <Form {...apiForm}>
                    <form onSubmit={apiForm.handleSubmit(onApiSubmit)} className="space-y-4 py-4">
                      <FormField
                        control={apiForm.control}
                        name="name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Connection Name</FormLabel>
                            <FormControl>
                              <Input placeholder="Sales API" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={apiForm.control}
                        name="url"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>API URL</FormLabel>
                            <FormControl>
                              <Input placeholder="https://api.example.com/v1" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={apiForm.control}
                        name="authType"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Authentication Type</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select authentication type" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                <SelectItem value="basic">Basic Auth</SelectItem>
                                <SelectItem value="bearer">Bearer Token</SelectItem>
                                <SelectItem value="api_key">API Key</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      {apiForm.watch("authType") === "basic" && (
                        <>
                          <FormField
                            control={apiForm.control}
                            name="username"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Username</FormLabel>
                                <FormControl>
                                  <Input {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          
                          <FormField
                            control={apiForm.control}
                            name="password"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>Password</FormLabel>
                                <FormControl>
                                  <Input type="password" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </>
                      )}
                      
                      {apiForm.watch("authType") === "bearer" && (
                        <FormField
                          control={apiForm.control}
                          name="bearerToken"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Bearer Token</FormLabel>
                              <FormControl>
                                <Input {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      )}
                      
                      {apiForm.watch("authType") === "api_key" && (
                        <>
                          <FormField
                            control={apiForm.control}
                            name="apiKeyName"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>API Key Name</FormLabel>
                                <FormControl>
                                  <Input placeholder="X-API-Key" {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                          
                          <FormField
                            control={apiForm.control}
                            name="apiKey"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>API Key Value</FormLabel>
                                <FormControl>
                                  <Input {...field} />
                                </FormControl>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        </>
                      )}
                      
                      <FormField
                        control={apiForm.control}
                        name="headers"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Additional Headers (JSON)</FormLabel>
                            <FormControl>
                              <Input placeholder='{"Content-Type": "application/json"}' {...field} />
                            </FormControl>
                            <FormDescription>
                              Enter JSON object with additional headers
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <DialogFooter>
                        <Button type="submit">Save Connection</Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            </div>
            
            <Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>URL</TableHead>
      <TableHead>Auth Type</TableHead>
      <TableHead>Created At</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {apiConnections.length === 0 ? (
      <TableRow>
        <TableCell colSpan={6} className="text-center text-muted-foreground">
          <div className="flex flex-col items-center gap-2">
            <Globe className="h-6 w-6 opacity-50" />
            <span>No API connections found.</span>
          </div>
        </TableCell>
      </TableRow>
    ) : (
      apiConnections.map((conn) => (
        <TableRow key={conn.id}>
          <TableCell>{conn.name}</TableCell>
          <TableCell>{conn.url}</TableCell>
          <TableCell>{conn.authType}</TableCell>
          <TableCell>{conn.createdAt}</TableCell>
          <TableCell>
            {testingConnectionId === conn.id ? (
              <span className="text-xs text-muted-foreground flex items-center gap-1"><Loader2 className="animate-spin h-4 w-4 inline" /> Testing...</span>
            ) : (
              <span className="text-xs bg-green-100 text-green-700 rounded px-2 py-0.5">Ready</span>
            )}
          </TableCell>
          <TableCell className="flex gap-2">
            <Button aria-label="Edit" onClick={() => { setEditingApiConnection(conn); setShowApiDialog(true); }}>
  Edit
</Button>
<Button aria-label="Delete" onClick={() => deleteApiConnection(conn.id)}>
  <Trash2 className="h-4 w-4" />
</Button>
<Button aria-label="Test Connection" onClick={() => testConnection('api', conn.id)} disabled={testingConnectionId === conn.id}>
  Test
</Button>
          </TableCell>
        </TableRow>
      ))
    )}
  </TableBody>
</Table>
          </TabsContent>
          
          <TabsContent value="database" className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Database Connections</h3>
              <Dialog open={showDbDialog} onOpenChange={setShowDbDialog}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-2 h-4 w-4" />
                    Add Database Connection
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
  <DialogTitle>{editingDbConnection ? "Edit Database Connection" : "Add Database Connection"}</DialogTitle>
  <button aria-label="Close dialog" className="absolute right-4 top-4" onClick={() => { setShowDbDialog(false); setEditingDbConnection(null); }}>
    ×
  </button>
</DialogHeader>
                  
                  <Form {...dbForm}>
                    <form onSubmit={dbForm.handleSubmit(onDbSubmit)} className="space-y-4 py-4">
  {editingDbConnection && (
    <input type="hidden" value={editingDbConnection.id} />
  )}
                      <FormField
                        control={dbForm.control}
                        name="name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Connection Name</FormLabel>
                            <FormControl>
                              <Input placeholder="Product Database" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={dbForm.control}
                        name="connectionType"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Database Type</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select database type" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="postgresql">PostgreSQL</SelectItem>
                                <SelectItem value="mysql">MySQL</SelectItem>
                                <SelectItem value="sqlserver">SQL Server</SelectItem>
                                <SelectItem value="oracle">Oracle</SelectItem>
                                <SelectItem value="mongodb">MongoDB</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={dbForm.control}
                          name="host"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Host</FormLabel>
                              <FormControl>
                                <Input placeholder="localhost" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={dbForm.control}
                          name="port"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Port</FormLabel>
                              <FormControl>
                                <Input placeholder="5432" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                      
                      <FormField
                        control={dbForm.control}
                        name="database"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Database Name</FormLabel>
                            <FormControl>
                              <Input placeholder="my_database" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={dbForm.control}
                          name="username"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Username</FormLabel>
                              <FormControl>
                                <Input {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        
                        <FormField
                          control={dbForm.control}
                          name="password"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Password</FormLabel>
                              <FormControl>
                                <Input type="password" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                      
                      <FormField
                        control={dbForm.control}
                        name="ssl"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                            <div className="space-y-0.5">
                              <FormLabel>SSL Connection</FormLabel>
                              <FormDescription>
                                Use SSL/TLS for the database connection
                              </FormDescription>
                            </div>
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                      
                      <FormField
                        control={dbForm.control}
                        name="options"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Additional Options</FormLabel>
                            <FormControl>
                              <Input placeholder="?sslmode=require&timeout=10" {...field} />
                            </FormControl>
                            <FormDescription>
                              Additional connection string parameters
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      
                      <DialogFooter>
                        <Button type="submit">Save Connection</Button>
                      </DialogFooter>
                    </form>
                  </Form>
                </DialogContent>
              </Dialog>
            </div>
            
            <Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Type</TableHead>
      <TableHead>Host</TableHead>
      <TableHead>Database</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {dbConnections.length === 0 ? (
      <TableRow>
        <TableCell colSpan={6} className="text-center text-muted-foreground">
          <div className="flex flex-col items-center gap-2">
            <Database className="h-6 w-6 opacity-50" />
            <span>No database connections found.</span>
          </div>
        </TableCell>
      </TableRow>
    ) : (
      dbConnections.map((conn) => (
        <TableRow key={conn.id}>
          <TableCell>{conn.name}</TableCell>
          <TableCell>
            <div className="capitalize">{conn.connectionType}</div>
          </TableCell>
          <TableCell>{conn.host}:{conn.port}</TableCell>
          <TableCell>{conn.database}</TableCell>
          <TableCell>
            {testingConnectionId === conn.id ? (
              <span className="text-xs text-muted-foreground flex items-center gap-1"><Loader2 className="animate-spin h-4 w-4 inline" /> Testing...</span>
            ) : (
              <span className="text-xs bg-green-100 text-green-700 rounded px-2 py-0.5">Ready</span>
            )}
          </TableCell>
          <TableCell className="flex gap-2">
            <Button aria-label="Edit" onClick={() => { setEditingDbConnection(conn); setShowDbDialog(true); }}>
  Edit
</Button>
<Button aria-label="Delete" onClick={() => deleteDbConnection(conn.id)}>
  <Trash2 className="h-4 w-4" />
</Button>
<Button aria-label="Test Connection" onClick={() => testConnection('db', conn.id)} disabled={testingConnectionId === conn.id}>
  Test
</Button>
          </TableCell>
        </TableRow>
      ))
    )}
  </TableBody>
</Table>
          </div>
        </TabsContent>
        <TabsContent value="database" className="space-y-4">
          <div>
            {/* Database connections table and controls here */}
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Host</TableHead>
                  <TableHead>Database</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dbConnections.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground">
                      <div className="flex flex-col items-center gap-2">
                        <Database className="h-6 w-6 opacity-50" />
                        <span>No database connections found.</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  dbConnections.map((conn) => (
                    <TableRow key={conn.id}>
                      <TableCell>{conn.name}</TableCell>
                      <TableCell>
                        <div className="capitalize">{conn.connectionType}</div>
                      </TableCell>
                      <TableCell>{conn.host}:{conn.port}</TableCell>
                      <TableCell>{conn.database}</TableCell>
                      <TableCell>
                        {testingConnectionId === conn.id ? (
                          <span className="text-xs text-muted-foreground flex items-center gap-1"><Loader2 className="animate-spin h-4 w-4 inline" /> Testing...</span>
                        ) : (
                          <span className="text-xs bg-green-100 text-green-700 rounded px-2 py-0.5">Ready</span>
                        )}
                      </TableCell>
                      <TableCell className="flex gap-2">
                        <Button aria-label="Edit" onClick={() => { setEditingDbConnection(conn); setShowDbDialog(true); }}>
                          Edit
                        </Button>
                        <Button aria-label="Delete" onClick={() => deleteDbConnection(conn.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                        <Button aria-label="Test Connection" onClick={() => testConnection('db', conn.id)} disabled={testingConnectionId === conn.id}>
                          Test
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>
    </CardContent>
  </Card>
);
}

export default DataSourceConfig;


export default DataSourceConfig;
