'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { User, Bot, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Citation {
  file: string;
  page: number;
}

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp?: string;
}

export default function ChatMessage({ role, content, citations, timestamp }: ChatMessageProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="h-5 w-5 text-primary" />
        </div>
      )}

      <div className={`flex flex-col gap-2 max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <Card className={`p-4 ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {isUser ? (
              <p className="m-0">{content}</p>
            ) : (
              <ReactMarkdown>{content}</ReactMarkdown>
            )}
          </div>
        </Card>

        {citations && citations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {citations.map((citation, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                <FileText className="h-3 w-3 mr-1" />
                {citation.file} - Page {citation.page}
              </Badge>
            ))}
          </div>
        )}

        {timestamp && (
          <span className="text-xs text-muted-foreground">{timestamp}</span>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <User className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}
