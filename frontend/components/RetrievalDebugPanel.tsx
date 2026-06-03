'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { ChatResponse } from '@/lib/api';
import { Search, FileText, Zap } from 'lucide-react';

interface RetrievalDebugPanelProps {
  data: ChatResponse | null;
}

export default function RetrievalDebugPanel({ data }: RetrievalDebugPanelProps) {
  if (!data) {
    return (
      <Card className="p-6 h-full">
        <div className="text-center text-muted-foreground py-12">
          <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No Retrieval Data</p>
          <p className="text-sm mt-2">Ask a question to see retrieved chunks</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 h-full flex flex-col">
      <div className="mb-4">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Search className="h-5 w-5" />
          Retrieval Debug Panel
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Retrieved {data.retrieved_chunks.length} chunks in {data.processing_time}
        </p>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4">
          {data.retrieved_chunks.map((chunk, idx) => (
            <Card key={idx} className="p-4 bg-muted/50">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">
                    {chunk.metadata.filename} - Page {chunk.metadata.page}
                  </span>
                </div>
                <Badge variant="secondary" className="text-xs">
                  <Zap className="h-3 w-3 mr-1" />
                  {(chunk.similarity_score * 100).toFixed(1)}%
                </Badge>
              </div>

              <Separator className="my-2" />

              <div className="text-sm text-muted-foreground">
                <p className="line-clamp-4">{chunk.text}</p>
              </div>

              <div className="mt-2 text-xs text-muted-foreground">
                Chunk ID: {chunk.metadata.chunk_id}
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>

      {data.metadata && (
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Model:</span>
            <Badge variant="outline">{data.metadata.model}</Badge>
          </div>
        </div>
      )}
    </Card>
  );
}
