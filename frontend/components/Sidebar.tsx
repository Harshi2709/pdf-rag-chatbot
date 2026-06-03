'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { FileText, Database, Settings, Upload, Trash2 } from 'lucide-react';
import { StatusResponse } from '@/lib/api';
import DocumentList from './DocumentList';

interface SidebarProps {
  status: StatusResponse | null;
  onUploadClick: () => void;
  onDeleteDocument: (filename: string) => Promise<void>;
  onClearAll: () => Promise<void>;
}

export default function Sidebar({ status, onUploadClick, onDeleteDocument, onClearAll }: SidebarProps) {
  const handleClearAll = async () => {
    if (confirm('Clear all documents? This will delete all uploaded PDFs and their embeddings.')) {
      await onClearAll();
    }
  };

  return (
    <Card className="p-6 h-full flex flex-col">
      <div className="space-y-6 flex-1 overflow-hidden flex flex-col">
        {/* Upload Button - Always Visible */}
        <div>
          <Button 
            onClick={onUploadClick} 
            className="w-full"
            size="lg"
          >
            <Upload className="mr-2 h-4 w-4" />
            Upload PDF
          </Button>
        </div>

        <Separator />

        {/* Uploaded Documents */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Documents
            </h2>
            {status && status.documents && status.documents.length > 0 && (
              <Badge variant="secondary">
                {status.documents.length}
              </Badge>
            )}
          </div>

          <div className="flex-1 overflow-hidden">
            {status && status.documents ? (
              <DocumentList
                documents={status.documents}
                onDelete={onDeleteDocument}
              />
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <p className="text-sm">Loading...</p>
              </div>
            )}
          </div>

          {status && status.documents && status.documents.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              className="w-full mt-3 text-destructive hover:text-destructive"
              onClick={handleClearAll}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All Documents
            </Button>
          )}
        </div>

        <Separator />

        {/* Vector Database Info */}
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Database className="h-5 w-5" />
            Vector Database
          </h2>

          {status ? (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total Chunks:</span>
                <span className="font-medium">{status.vector_db_count}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Status:</span>
                <Badge variant={status.ollama_available ? 'default' : 'destructive'}>
                  {status.ollama_available ? 'Connected' : 'Disconnected'}
                </Badge>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Loading...</p>
          )}
        </div>

        <Separator />

        {/* Configuration */}
        <div>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Configuration
          </h2>

          {status && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Model:</span>
                <span className="font-medium">{status.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Chunk Size:</span>
                <span className="font-medium">{status.chunk_size}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Top-K:</span>
                <span className="font-medium">{status.top_k}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
