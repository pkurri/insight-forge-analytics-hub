
import React, { useState } from 'react';
import { UploadCloud, AlertCircle, File, Table } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { useToast } from "@/hooks/use-toast";

const PipelineUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dataSource, setDataSource] = useState("local");
  const [fileType, setFileType] = useState("csv");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      setUploadProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        setIsUploading(false);
        toast({
          title: "Upload completed",
          description: "Your file has been uploaded successfully",
        });
      }
    }, 200);
  };

  const supportedFormats = {
    csv: "Comma Separated Values (.csv)",
    json: "JSON (.json)",
    excel: "Excel Spreadsheet (.xlsx, .xls)",
    pdf: "PDF Document (.pdf)"
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">Data Source</label>
          <Select value={dataSource} onValueChange={setDataSource}>
            <SelectTrigger>
              <SelectValue placeholder="Select source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="local">Local File Upload</SelectItem>
              <SelectItem value="api">External API</SelectItem>
              <SelectItem value="database">Database Connection</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">File Format</label>
          <Select value={fileType} onValueChange={setFileType}>
            <SelectTrigger>
              <SelectValue placeholder="Select file format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="csv">CSV</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
              <SelectItem value="excel">Excel</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {/* Format description */}
      <Alert>
        <Table className="h-4 w-4" />
        <AlertDescription>
          {fileType in supportedFormats ? 
            supportedFormats[fileType as keyof typeof supportedFormats] : 
            "Select a file format"}
        </AlertDescription>
      </Alert>
      
      {/* File dropzone */}
      <div 
        className={`border-2 border-dashed rounded-lg p-8 text-center ${
          selectedFile ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
      >
        <div className="flex flex-col items-center">
          {selectedFile ? (
            <>
              <File className="h-10 w-10 text-blue-500 mb-2" />
              <p className="font-medium">{selectedFile.name}</p>
              <p className="text-sm text-gray-500 mt-1">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <Button 
                variant="outline" 
                onClick={() => setSelectedFile(null)} 
                className="mt-3"
                size="sm"
              >
                Remove
              </Button>
            </>
          ) : (
            <>
              <UploadCloud className="h-10 w-10 text-gray-400 mb-2" />
              <p className="text-lg font-medium">Drag and drop your file here</p>
              <p className="text-sm text-gray-500 mt-1 mb-4">
                or click to browse files
              </p>
            </>
          )}
          <Input
            type="file"
            id="file-upload"
            className={selectedFile ? "hidden" : "opacity-0 absolute"}
            onChange={handleFileChange}
          />
        </div>
      </div>
      
      {isUploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Uploading...</span>
            <span>{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} />
        </div>
      )}
      
      <div className="flex justify-end">
        <Button 
          onClick={handleUpload} 
          disabled={!selectedFile || isUploading}
          className="px-6"
        >
          {isUploading ? "Processing..." : "Upload and Process"}
        </Button>
      </div>
    </div>
  );
};

export default PipelineUploadForm;
