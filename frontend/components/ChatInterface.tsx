'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api, ChatResponse, Message as APIMessage } from '@/lib/api';
import ChatMessage from './ChatMessage';
import { Send, Loader2, RefreshCw } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{ file: string; page: number }>;
  timestamp: string;
  debugInfo?: any;
}

interface ChatInterfaceProps {
  onRetrievalData?: (data: ChatResponse) => void;
}

// Generate unique session ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export default function ChatInterface({ onRetrievalData }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [showDebug, setShowDebug] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    console.log('Chat session started:', newSessionId);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // Build chat history for API (last 5 messages)
      const chatHistory: APIMessage[] = messages
        .slice(-10) // Last 10 messages (5 exchanges)
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

      // Make chat request with session and history
      const response = await api.chat({
        question: userMessage.content,
        session_id: sessionId,
        chat_history: chatHistory,
        debug: showDebug, // Include debug info if enabled
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        timestamp: new Date().toLocaleTimeString(),
        debugInfo: response.debug_info, // Store debug info
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Log debug information if available
      if (response.debug_info && showDebug) {
        console.log('🔍 Debug Info:', {
          intent: response.debug_info.intent,
          originalQuery: response.debug_info.original_query,
          rewrittenQuery: response.debug_info.rewritten_query,
          wasRewritten: response.debug_info.was_rewritten,
          retrievalPerformed: response.debug_info.retrieval_performed,
        });
      }

      if (onRetrievalData) {
        onRetrievalData(response);
      }
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error.message}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    setMessages([]);
    console.log('New chat session started:', newSessionId);
  };

  return (
    <Card className="flex flex-col h-full">
      {/* Header with controls */}
      <div className="p-3 border-b flex items-center justify-between bg-muted/30">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Session: {sessionId.slice(0, 20)}...</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDebug(!showDebug)}
            className="text-xs"
          >
            {showDebug ? '🔍 Debug ON' : '🔍 Debug OFF'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNewSession}
            title="Start new conversation"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-12">
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm mt-2">Upload PDFs and ask questions naturally</p>
              <p className="text-xs mt-2 text-muted-foreground/70">
                Try: "What's the main point?", "Summarize that", "Compare both documents"
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id}>
                <ChatMessage
                  role={message.role}
                  content={message.content}
                  citations={message.citations}
                  timestamp={message.timestamp}
                />
                {/* Show debug info if enabled */}
                {showDebug && message.role === 'assistant' && message.debugInfo && (
                  <div className="mt-2 p-3 bg-muted/50 rounded-lg text-xs font-mono">
                    <div className="font-bold mb-2">🔍 Debug Information:</div>
                    <div><strong>Intent:</strong> {message.debugInfo.intent}</div>
                    <div><strong>Original Query:</strong> {message.debugInfo.original_query}</div>
                    <div><strong>Rewritten Query:</strong> {message.debugInfo.rewritten_query}</div>
                    <div><strong>Was Rewritten:</strong> {message.debugInfo.was_rewritten ? 'Yes' : 'No'}</div>
                    <div><strong>Retrieval Performed:</strong> {message.debugInfo.retrieval_performed ? 'Yes' : 'No'}</div>
                  </div>
                )}
              </div>
            ))
          )}
          {loading && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Thinking...</span>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="p-4 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask naturally: 'What does it say?', 'Summarize that', 'Compare both'..."
            className="min-h-[60px] resize-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
            disabled={loading}
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </Card>
  );
}
