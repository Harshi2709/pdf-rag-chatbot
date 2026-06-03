# 🚀 Quick Reference - Multi-Document RAG Workspace

## ⚡ Quick Start

```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev

# Open: http://localhost:3000
```

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| **Persistent Upload** | Upload button always visible in sidebar |
| **Multi-Document** | Upload unlimited PDFs |
| **Incremental** | New docs append, don't overwrite |
| **Continuous Chat** | Chat preserved during uploads |
| **Document Management** | View, delete, clear documents |
| **Cross-Document Query** | Search across all uploaded PDFs |

---

## 📱 UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│  PDF RAG Workspace - Multi-document AI assistant            │
├──────────┬────────────────────────────────┬─────────────────┤
│ SIDEBAR  │      CHAT INTERFACE            │  DEBUG PANEL    │
│          │                                │                 │
│ [Upload] │  User: What are the findings? │  Retrieved:     │
│          │                                │  • Doc 1, p.3   │
│ Docs (3) │  AI: Based on the documents... │  • Doc 2, p.7   │
│ • doc1   │                                │  • Doc 1, p.5   │
│ • doc2   │  [Type your question...]       │                 │
│ • doc3   │                                │  Similarity:    │
│          │                                │  • 0.89         │
│ [Clear]  │                                │  • 0.85         │
│          │                                │  • 0.82         │
│ Vector   │                                │                 │
│ DB: 120  │                                │                 │
└──────────┴────────────────────────────────┴─────────────────┘
```

---

## 🔄 Workflow

### Upload Documents
```
1. Click "Upload PDF" (sidebar)
2. Select or drag PDF
3. Wait for processing
4. Document appears in list
5. Repeat for more docs
```

### Chat
```
1. Type question
2. Press Enter
3. View answer + citations
4. Check debug panel
5. Continue conversation
```

### Manage Documents
```
1. View list in sidebar
2. Click 🗑️ to delete one
3. Click "Clear All" to reset
4. Upload more anytime
```

---

## 🔌 API Quick Reference

### Upload
```bash
POST /api/upload
Content-Type: multipart/form-data
Body: file=document.pdf
```

### List Documents
```bash
GET /api/documents
```

### Delete Document
```bash
DELETE /api/documents/filename.pdf
```

### Clear All
```bash
DELETE /api/documents
```

### Chat
```bash
POST /api/chat
Content-Type: application/json
Body: {"question": "What is...?"}
```

### Status
```bash
GET /api/status
```

---

## 🐛 Quick Fixes

### Backend Won't Start
```bash
pip install "numpy<2.0"
pip install -r requirements.txt
```

### Frontend Can't Connect
```bash
# Check backend is running
curl http://localhost:8000/health
```

### Ollama Issues
```bash
ollama list
ollama serve
ollama pull llama3
```

---

## 📊 File Structure

```
pdf-rag-chat/
├── backend/
│   ├── api/
│   │   ├── upload.py      # Upload + document management
│   │   └── chat.py        # Chat endpoint
│   ├── services/
│   │   └── rag_pipeline.py # Multi-doc pipeline
│   ├── vectordb/
│   │   └── chroma_client.py # Enhanced with doc mgmt
│   └── main.py
│
└── frontend/
    ├── app/
    │   └── page.tsx       # Main workspace
    ├── components/
    │   ├── Sidebar.tsx    # Upload + doc list
    │   ├── DocumentList.tsx # Document management
    │   ├── UploadModal.tsx  # Upload interface
    │   ├── ChatInterface.tsx
    │   └── RetrievalDebugPanel.tsx
    └── lib/
        └── api.ts         # API client
```

---

## ✅ Testing Checklist

- [ ] Upload first PDF
- [ ] Chat with it
- [ ] Upload second PDF (chat preserved!)
- [ ] Chat with both
- [ ] Delete one document
- [ ] Upload another
- [ ] Clear all documents
- [ ] Upload and chat again

---

## 🎯 Key Differences from Before

| Before | After |
|--------|-------|
| Upload button disappears | ✅ Always visible |
| Single PDF only | ✅ Unlimited PDFs |
| Chat resets on upload | ✅ Chat preserved |
| No document management | ✅ Full CRUD operations |
| One-time demo | ✅ Production workspace |

---

## 📚 Documentation

- **README.md** - Complete documentation
- **QUICKSTART.md** - 5-minute setup
- **MULTI_DOCUMENT_UPGRADE.md** - Upgrade details
- **UPGRADE_SUMMARY.md** - Change summary
- **TROUBLESHOOTING.md** - Problem solving
- **ARCHITECTURE.md** - System design
- **DEVELOPMENT.md** - Developer guide

---

## 💡 Pro Tips

1. **First query is slow** - Models loading into memory
2. **Upload during chat** - Seamless, no interruption
3. **Check debug panel** - See what's being retrieved
4. **Delete unused docs** - Keep workspace clean
5. **Multiple small PDFs** - Better than one huge PDF

---

## 🎓 What's New

### Backend
- ✅ Incremental ingestion
- ✅ Document tracking
- ✅ Delete operations
- ✅ Enhanced metadata
- ✅ Multi-doc support

### Frontend
- ✅ Persistent upload button
- ✅ Document list component
- ✅ Upload modal
- ✅ Delete functionality
- ✅ Clear all feature

### UX
- ✅ No page refresh
- ✅ Chat preservation
- ✅ Real-time updates
- ✅ Professional workspace

---

## 🚀 Next Steps

1. **Try it out** - Upload multiple PDFs
2. **Test chat** - Ask questions across docs
3. **Manage docs** - Delete and re-upload
4. **Explore debug** - See retrieval in action
5. **Read docs** - Learn advanced features

---

**Enjoy your multi-document RAG workspace!** 🎉
