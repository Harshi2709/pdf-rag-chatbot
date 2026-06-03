'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileText, Trash2, CheckCircle2, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface Document {
  filename: string;
  chunk_count: number;
  upload_timestamp: string;
  selected?: boolean;
}

interface DocumentListProps {
  documents: Document[];
  onDelete: (filename: string) => Promise<void>;
  onToggleSelect?: (filename: string) => void;
}

export default function DocumentList({ documents, onDelete, onToggleSelect }: DocumentListProps) {
  const [deletingDoc, setDeletingDoc] = useState<string | null>(null);

  const handleDelete = async (filename: string) => {
    if (confirm(`Delete "${filename}"? This cannot be undone.`)) {
      setDeletingDoc(filename);
      try {
        await onDelete(filename);
      } finally {
        setDeletingDoc(null);
      }
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  if (documents.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
        <p className="text-sm">No documents uploaded yet</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-2">
        {documents.map((doc) => (
          <Card
            key={doc.filename}
            className="p-3 hover:bg-muted/50 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {onToggleSelect && (
                    <button
                      onClick={() => onToggleSelect(doc.filename)}
                      className="flex-shrink-0"
                    >
                      {doc.selected ? (
                        <CheckCircle2 className="h-4 w-4 text-primary" />
                      ) : (
                        <div className="h-4 w-4 border-2 rounded-full border-muted-foreground/30" />
                      )}
                    </button>
                  )}
                  <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                  <span className="font-medium text-sm truncate" title={doc.filename}>
                    {doc.filename}
                  </span>
                </div>
                
                <div className="flex items-center gap-2 ml-6 text-xs text-muted-foreground">
                  <Badge variant="secondary" className="text-xs">
                    {doc.chunk_count} chunks
                  </Badge>
                  <span className="truncate">
                    {formatTimestamp(doc.upload_timestamp)}
                  </span>
                </div>
              </div>

              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 flex-shrink-0"
                onClick={() => handleDelete(doc.filename)}
                disabled={deletingDoc === doc.filename}
              >
                {deletingDoc === doc.filename ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4 text-destructive" />
                )}
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
