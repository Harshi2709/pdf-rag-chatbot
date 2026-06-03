# PDF RAG Workspace - Multi-Document AI Assistant

A production-quality Retrieval-Augmented Generation (RAG) workspace for multi-document PDF question answering using Next.js, FastAPI, and local LLMs via Ollama.

## 🎯 Project Overview

This application is a **professional multi-document AI workspace** that allows you to:
- **Upload unlimited PDFs** at any time
- **Chat continuously** without interruption
- **Manage documents** with full CRUD operations
- **Query across all documents** seamlessly
- **Track document metadata** (chunks, timestamps)
- **Delete or clear documents** as needed

### Key Features

- ✅ **Persistent Upload Button** - Always accessible, never disappears
- ✅ **Multi-Document Support** - Upload and manage multiple PDFs
- ✅ **Incremental Ingestion** - New documents append without overwriting
- ✅ **Continuous Chat** - Conversations preserved during uploads
- ✅ **Document Management** - View, delete, and clear documents
- ✅ **Source Citations** - Track answers back to specific documents
- ✅ **Debug Panel** - Visualize retrieval and similarity scores
- ✅ **Local LLM** - Privacy-first with Ollama (no API costs)

## 🏗️ Architecture

### Tech Stack

**Frontend:**
- Next.js 15+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Markdown

**Backend:**
- FastAPI (Python 3.11+)
- PyPDF for PDF parsing
- sentence-transformers (all-MiniLM-L6-v2)
- ChromaDB for vector storage
- Ollama for local LLM inference

### RAG Pipeline Stages

```
1. PDF Upload
   ↓
2. PDF Parsing (PyPDF)
   ↓
3. Text Chunking (RecursiveCharacterTextSplitter)
   ↓
4. Embedding Generation (sentence-transformers)
   ↓
5. Vector Storage (ChromaDB)
   ↓
6. Query Embedding
   ↓
7. Similarity Search
   ↓
8. Top-K Retrieval
   ↓
9. Context Assembly
   ↓
10. Prompt Construction
   ↓
11. LLM Inference (Ollama)
   ↓
12. Response with Citations
```

## 📁 Project Structure

```
pdf-rag-chat/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── requirements.txt        # Python dependencies
│   ├── api/
│   │   ├── upload.py          # PDF upload endpoint
│   │   └── chat.py            # Chat endpoint
│   ├── loaders/
│   │   └── pdf_loader.py      # PDF parsing
│   ├── chunking/
│   │   └── splitter.py        # Text chunking
│   ├── embeddings/
│   │   └── embedding_model.py # Embedding generation
│   ├── vectordb/
│   │   └── chroma_client.py   # Vector database
│   ├── retrieval/
│   │   └── retriever.py       # Semantic retrieval
│   ├── llm/
│   │   └── ollama_client.py   # LLM client
│   ├── prompts/
│   │   └── rag_prompt.py      # Prompt templates
│   ├── services/
│   │   └── rag_pipeline.py    # Complete RAG pipeline
│   ├── schemas/
│   │   └── request_models.py  # Pydantic models
│   ├── utils/
│   │   └── helpers.py         # Utility functions
│   ├── uploaded_docs/         # PDF storage
│   └── chroma_db/             # Vector database storage
│
└── frontend/
    ├── app/
    │   ├── page.tsx           # Main page
    │   └── globals.css        # Global styles
    ├── components/
    │   ├── PDFUpload.tsx      # Upload component
    │   ├── ChatInterface.tsx  # Chat UI
    │   ├── ChatMessage.tsx    # Message component
    │   ├── Sidebar.tsx        # Info sidebar
    │   └── RetrievalDebugPanel.tsx  # Debug panel
    ├── lib/
    │   └── api.ts             # API client
    └── package.json
```

## 🚀 Setup Instructions

### Prerequisites

1. **Python 3.11+**
2. **Node.js 18+**
3. **Ollama** - [Installation Guide](https://ollama.ai)

### Step 1: Install Ollama

**Windows:**
```bash
# Download from https://ollama.ai/download
# Run the installer
```

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Pull the LLM Model

```bash
ollama pull llama3
```

Verify Ollama is running:
```bash
ollama list
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

## 🎮 Running the Application

### Start Backend (Terminal 1)

```bash
cd backend
# Activate venv if not already activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: `http://localhost:8000`
API docs available at: `http://localhost:8000/docs`

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Frontend will run on: `http://localhost:3000`

## 📖 Usage Guide

### Upload Documents

1. **Click "Upload PDF"** button in the sidebar (always visible)
2. **Drag and drop** or click to select a PDF file
3. **Wait for processing** (5-30 seconds depending on size)
4. **Document appears** in the sidebar list
5. **Repeat** to upload more documents - chat is preserved!

### Chat with Documents

1. **Type your question** in the chat interface
2. **Press Enter** or click Send
3. **View AI response** with source citations
4. **Check debug panel** to see retrieved chunks
5. **Continue conversation** - upload more docs anytime!

### Manage Documents

1. **View all documents** in the sidebar list
2. **See metadata**: filename, chunk count, upload time
3. **Delete document**: Click trash icon next to document
4. **Clear all**: Click "Clear All Documents" button
5. **Upload more**: Click "Upload PDF" anytime

### Query Across Documents

The AI automatically searches across **all uploaded documents**:

```
User: "What are the main findings?"
AI: [Retrieves from ALL documents and synthesizes answer]
```

## 🎨 Features

### ✅ Multi-Document Workspace

- **Unlimited Uploads**: Add as many PDFs as you need
- **Persistent Button**: Upload button never disappears
- **Incremental Ingestion**: New docs append without overwriting
- **Document List**: View all uploaded documents
- **Metadata Tracking**: Chunks, timestamps, status
- **Delete Operations**: Remove individual or all documents

### ✅ Continuous Chat

- **Preserved History**: Chat messages stay during uploads
- **No Interruptions**: Upload mid-conversation seamlessly
- **No Page Refresh**: Everything happens in real-time
- **Seamless UX**: Professional workspace experience

### 🚧 Future Improvements

- [ ] Document filtering (select which docs to query)
- [ ] Document collections/projects
- [ ] Chat history persistence
- [ ] User authentication
- [ ] WebSocket streaming
- [ ] Hybrid retrieval (keyword + semantic)
- [ ] Document tags & categories
- [ ] Advanced search & filter
- [ ] Export conversations
- [ ] Multi-language support

## 📊 API Endpoints

### Document Management

#### POST /api/upload
Upload and process PDF document (incremental)

**Request:** `multipart/form-data` with PDF file

**Response:**
```json
{
  "status": "success",
  "filename": "document.pdf",
  "total_pages": 10,
  "total_chunks": 45,
  "vector_db_count": 120,
  "processing_time": "2.34s",
  "upload_timestamp": "2026-06-01T19:42:00"
}
```

#### GET /api/documents
List all uploaded documents

**Response:**
```json
{
  "documents": [
    {
      "filename": "research.pdf",
      "chunk_count": 45,
      "upload_timestamp": "2026-06-01T19:42:00"
    }
  ]
}
```

#### DELETE /api/documents/{filename}
Delete a specific document

**Response:**
```json
{
  "status": "success",
  "message": "Document deleted successfully",
  "vector_db_count": 75
}
```

#### DELETE /api/documents
Clear all documents

**Response:**
```json
{
  "status": "success",
  "message": "All documents cleared successfully",
  "vector_db_count": 0
}
```

### Chat

#### POST /api/chat
Ask question about uploaded documents

**Request:**
```json
{
  "question": "What is the main topic?",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "The main topic is...",
  "citations": [
    {"file": "document.pdf", "page": 3}
  ],
  "retrieved_chunks": [...],
  "processing_time": "1.2s",
  "metadata": {
    "num_chunks_retrieved": 5,
    "model": "llama3"
  }
}
```

### GET /api/status
Get pipeline status with document list

**Response:**
```json
{
  "vector_db_count": 120,
  "chunk_size": 500,
  "chunk_overlap": 100,
  "top_k": 5,
  "model": "llama3",
  "ollama_available": true,
  "documents": [
    {
      "filename": "research.pdf",
      "chunk_count": 45,
      "upload_timestamp": "2026-06-01T19:42:00"
    }
  ]
}
```

### GET /health
Backend health check

## 🔧 Configuration

### Backend Configuration

Edit `backend/services/rag_pipeline.py`:

```python
RAGPipeline(
    chunk_size=500,        # Chunk size in characters
    chunk_overlap=100,     # Overlap between chunks
    top_k=5,              # Number of chunks to retrieve
    model_name="llama3"   # Ollama model name
)
```

### Frontend Configuration

Edit `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🐛 Troubleshooting

See **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for detailed troubleshooting guide.

### Quick Fixes

**Ollama Connection Issues:**
```bash
ollama list  # Check if running
ollama serve  # Start if needed
```

**Backend Errors:**
```bash
pip install "numpy<2.0"  # Fix NumPy version
pip install -r requirements.txt
```

**Frontend Errors:**
```bash
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation

- **[README.md](README.md)** - This file
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[MULTI_DOCUMENT_UPGRADE.md](MULTI_DOCUMENT_UPGRADE.md)** - Multi-document features
- **[UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)** - Quick upgrade reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Developer guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Troubleshooting guide

## 🎓 Learning Objectives

This project teaches:

1. **RAG Fundamentals**: Understanding each stage of retrieval-augmented generation
2. **Vector Embeddings**: How semantic search works
3. **LLM Integration**: Working with local language models
4. **Full-Stack Development**: Building production-grade applications
5. **API Design**: RESTful API best practices
6. **Modern Frontend**: Next.js 15 and React patterns
7. **Type Safety**: TypeScript and Pydantic validation

## 📝 License

MIT License - feel free to use for learning and commercial projects

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues and questions, please open a GitHub issue.

---

**Built with ❤️ for learning RAG engineering fundamentals**
