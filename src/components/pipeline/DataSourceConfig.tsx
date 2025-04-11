
import React, { useState } from 'react';
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
import { Plus, Trash2, Database, Globe, Key } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";

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

const DataSourceConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>("api");
  const [showApiDialog, setShowApiDialog] = useState<boolean>(false);
  const [showDbDialog, setShowDbDialog] = useState<boolean>(false);
  const [apiConnections, setApiConnections] = useState<any[]>([]);
  const [dbConnections, setDbConnections] = useState<any[]>([]);
  const { toast } = useToast();
  
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
  
  const onApiSubmit = (values: z.infer<typeof apiFormSchema>) => {
    // In a real app, this would save to the backend
    const newConnection = {
      id: `api-${Date.now()}`,
      ...values,
      createdAt: new Date().toISOString(),
    };
    
    setApiConnections([...apiConnections, newConnection]);
    setShowApiDialog(false);
    apiForm.reset();
    
    toast({
      title: "API Connection Added",
      description: `Successfully created connection to ${values.name}`,
    });
  };
  
  const onDbSubmit = (values: z.infer<typeof dbFormSchema>) => {
    // In a real app, this would save to the backend
    const newConnection = {
      id: `db-${Date.now()}`,
      ...values,
      createdAt: new Date().toISOString(),
    };
    
    setDbConnections([...dbConnections, newConnection]);
    setShowDbDialog(false);
    dbForm.reset();
    
    toast({
      title: "Database Connection Added",
      description: `Successfully created connection to ${values.name}`,
    });
  };
  
  const deleteApiConnection = (id: string) => {
    setApiConnections(apiConnections.filter(conn => conn.id !== id));
    toast({
      title: "Connection Removed",
      description: "API connection has been deleted",
    });
  };
  
  const deleteDbConnection = (id: string) => {
    setDbConnections(dbConnections.filter(conn => conn.id !== id));
    toast({
      title: "Connection Removed",
      description: "Database connection has been deleted",
    });
  };
  
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
                    <DialogTitle>Add New API Connection</DialogTitle>
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
            
            {apiConnections.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>URL</TableHead>
                    <TableHead>Auth Type</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiConnections.map((conn) => (
                    <TableRow key={conn.id}>
                      <TableCell className="font-medium">{conn.name}</TableCell>
                      <TableCell>{conn.url}</TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          {conn.authType === "none" && "None"}
                          {conn.authType === "basic" && "Basic Auth"}
                          {conn.authType === "bearer" && "Bearer Token"}
                          {conn.authType === "api_key" && "API Key"}
                          {conn.authType !== "none" && (
                            <Key className="ml-2 h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => deleteApiConnection(conn.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Globe className="mx-auto h-12 w-12 opacity-20 mb-2" />
                <p>No API connections configured</p>
                <p className="text-sm">Add a connection to get started</p>
              </div>
            )}
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
                    <DialogTitle>Add New Database Connection</DialogTitle>
                  </DialogHeader>
                  
                  <Form {...dbForm}>
                    <form onSubmit={dbForm.handleSubmit(onDbSubmit)} className="space-y-4 py-4">
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
            
            {dbConnections.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Host</TableHead>
                    <TableHead>Database</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dbConnections.map((conn) => (
                    <TableRow key={conn.id}>
                      <TableCell className="font-medium">{conn.name}</TableCell>
                      <TableCell>
                        <div className="capitalize">{conn.connectionType}</div>
                      </TableCell>
                      <TableCell>{conn.host}:{conn.port}</TableCell>
                      <TableCell>{conn.database}</TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm" onClick={() => deleteDbConnection(conn.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Database className="mx-auto h-12 w-12 opacity-20 mb-2" />
                <p>No database connections configured</p>
                <p className="text-sm">Add a connection to get started</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default DataSourceConfig;
