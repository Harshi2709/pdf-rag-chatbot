'use client';

import { useState, useEffect } from 'react';
import ChatInterface from '@/components/ChatInterface';
import Sidebar from '@/components/Sidebar';
import RetrievalDebugPanel from '@/components/RetrievalDebugPanel';
import UploadModal from '@/components/UploadModal';
import { api, StatusResponse, ChatResponse } from '@/lib/api';
import { FileText, WifiOff, Wifi } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function Home() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [retrievalData, setRetrievalData] = useState<ChatResponse | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [backendConnected, setBackendConnected] = useState<boolean | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    fetchStatus();
    // Check connection every 30 seconds
    const interval = setInterval(() => {
      if (retryCount < 3) {
        fetchStatus();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [retryCount]);

  const fetchStatus = async () => {
    try {
      const statusData = await api.getStatus();
      setStatus(statusData);
      setBackendConnected(true);
      setRetryCount(0);
    } catch (error) {
      console.error('Failed to fetch status:', error);
      setBackendConnected(false);
      setRetryCount(prev => prev + 1);
    }
  };

  const handleUploadSuccess = async () => {
    await fetchStatus();
  };

  const handleDeleteDocument = async (filename: string) => {
    try {
      await api.deleteDocument(filename);
      await fetchStatus();
    } catch (error: any) {
      console.error('Failed to delete document:', error);
      alert(error.message || 'Failed to delete document');
    }
  };

  const handleClearAll = async () => {
    try {
      await api.clearAllDocuments();
      await fetchStatus();
    } catch (error: any) {
      console.error('Failed to clear documents:', error);
      alert(error.message || 'Failed to clear documents');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">PDF RAG Workspace</h1>
                <p className="text-sm text-muted-foreground">
                  Multi-document AI assistant
                </p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {backendConnected === null ? (
                <Badge variant="secondary" className="gap-2">
                  <div className="h-2 w-2 rounded-full bg-yellow-500 animate-pulse" />
                  Connecting...
                </Badge>
              ) : backendConnected ? (
                <Badge variant="default" className="gap-2">
                  <Wifi className="h-3 w-3" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="destructive" className="gap-2">
                  <WifiOff className="h-3 w-3" />
                  Disconnected
                </Badge>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {backendConnected === false && (
          <div className="mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
            <div className="flex items-center gap-2">
              <WifiOff className="h-5 w-5 text-destructive" />
              <div>
                <p className="font-medium text-destructive">Backend Disconnected</p>
                <p className="text-sm text-muted-foreground">
                  Make sure the backend server is running on http://127.0.0.1:8001
                </p>
                <button
                  onClick={fetchStatus}
                  className="text-sm text-primary hover:underline mt-1"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          {/* Sidebar */}
          <div className="col-span-3">
            <Sidebar
              status={status}
              onUploadClick={() => setUploadModalOpen(true)}
              onDeleteDocument={handleDeleteDocument}
              onClearAll={handleClearAll}
            />
          </div>

          {/* Main Chat Area */}
          <div className="col-span-6">
            <ChatInterface onRetrievalData={setRetrievalData} />
          </div>

          {/* Retrieval Debug Panel */}
          <div className="col-span-3">
            <RetrievalDebugPanel data={retrievalData} />
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
}
