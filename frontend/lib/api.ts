/**
 * API Client for Backend Communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  chat_history?: Message[];
  top_k?: number;
  debug?: boolean;
}

export interface ChatResponse {
  answer: string;
  session_id?: string;
  citations: Array<{
    file: string;
    page: number;
  }>;
  retrieved_chunks: Array<{
    text: string;
    metadata: {
      filename: string;
      page: number;
      chunk_id: string;
    };
    similarity_score: number;
  }>;
  processing_time: string;
  metadata?: {
    num_chunks_retrieved: number;
    model: string;
    intent?: string;
  };
  debug_info?: {
    intent: string;
    intent_description: string;
    original_query: string;
    rewritten_query: string;
    was_rewritten: boolean;
    needs_retrieval: boolean;
    retrieval_performed: boolean;
    conversation_history_length: number;
    temperature: number;
  };
}

export interface UploadResponse {
  status: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  vector_db_count: number;
  processing_time: string;
  upload_timestamp?: string;
}

export interface StatusResponse {
  vector_db_count: number;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  model: string;
  ollama_available: boolean;
  documents: Array<{
    filename: string;
    chunk_count: number;
    upload_timestamp: string;
  }>;
}

export const api = {
  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    return response.json();
  },

  async getStatus(): Promise<StatusResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Backend status request failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch backend status:', error);
      throw error;
    }
  },

  async checkBackendHealth(): Promise<{ status: string; connected: boolean }> {
    try {
      const baseUrl = API_BASE_URL.replace('/api', '');
      const response = await fetch(`${baseUrl}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return { status: 'disconnected', connected: false };
      }

      const data = await response.json();
      return { status: data.status || 'connected', connected: true };
    } catch (error) {
      console.error('Backend health check failed:', error);
      return { status: 'disconnected', connected: false };
    }
  },

  async getDocuments(): Promise<{ documents: StatusResponse['documents'] }> {
    const response = await fetch(`${API_BASE_URL}/documents`);

    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }

    return response.json();
  },

  async deleteDocument(filename: string): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete document');
    }

    return response.json();
  },

  async clearAllDocuments(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to clear documents');
    }

    return response.json();
  },
};
