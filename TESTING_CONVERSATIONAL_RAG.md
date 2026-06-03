# Testing Conversational RAG - Quick Guide

## 🚀 Quick Start

### 1. Start Backend
```bash
cd backend
venv\Scripts\activate
python main.py
```
✅ Backend running on: `http://127.0.0.1:8001`

### 2. Start Frontend
```bash
cd frontend
npm run dev
```
✅ Frontend running on: `http://localhost:3000`

### 3. Open Browser
Navigate to: `http://localhost:3000`

---

## 🧪 Test Scenarios

### Scenario 1: Basic Conversational Flow
```
Step 1: Upload a PDF document
Step 2: Ask a specific question

User: "What does the document say about AI replacing developers?"
Expected: Direct answer from document with citations

Step 3: Ask a follow-up with reference

User: "Can you summarize that?"
Expected: Summary of previous answer (query rewritten to be specific)
Debug: Original: "Can you summarize that?"
       Rewritten: "Summarize what the document says about AI replacing developers"

Step 4: Ask about specific point

User: "What about the second point?"
Expected: Details about the second point mentioned
Debug: Query rewritten to include context
```

### Scenario 2: Reference Resolution
```
User: "Tell me about the revenue figures in the report"
Expected: Revenue information from document

User: "How does that compare to last quarter?"
Expected: Comparison with context from previous answer
Debug: "that" should be resolved to "revenue figures"

User: "What about the forecast?"
Expected: Forecast information
Debug: "forecast" context added from conversation
```

### Scenario 3: Intent Classification
```
Test: Greeting
User: "Hello"
Expected: Greeting response without document retrieval
Debug: Intent: greeting, Retrieval: false

Test: Meta Question
User: "Did you use the document to answer that?"
Expected: Response based on conversation memory
Debug: Intent: meta_question, Retrieval: false

Test: Document QA
User: "What is the revenue in Q3?"
Expected: Answer with document retrieval
Debug: Intent: document_qa, Retrieval: true

Test: Summarization
User: "Summarize the key findings"
Expected: Summary with retrieval
Debug: Intent: summarization, Retrieval: true

Test: Comparison
User: "Compare both PDFs"
Expected: Comparison across documents
Debug: Intent: comparison, Retrieval: true
```

### Scenario 4: Multiple Document Interaction
```
Step 1: Upload PDF 1 (e.g., "AI will replace developers")
Step 2: Upload PDF 2 (e.g., "AI will NOT replace developers")
Step 3: Test comparison

User: "What does the first document say about AI?"
Expected: Information from first PDF

User: "What does the second document say?"
Expected: Information from second PDF

User: "Compare both views"
Expected: Comparison across both documents
Debug: Retrieval should pull from both PDFs
```

### Scenario 5: Vague Queries
```
User: "Tell me about the main topic"
Expected: Answer about main document topic

User: "What's interesting about it?"
Expected: Interesting points with "it" resolved to main topic
Debug: "it" should be resolved

User: "Any concerns mentioned?"
Expected: Concerns from document
Debug: Query expanded with context
```

### Scenario 6: Conversation Memory
```
User: "What's the company's mission?"
Expected: Mission statement from document

User: "Who founded it?"
Expected: Founder information ("it" = the company)

User: "When was that?"
Expected: Founding date ("that" = founding event)

User: "Tell me more about them"
Expected: More about founders ("them" = founders)
```

---

## 🔍 Debug Mode Testing

### Enable Debug Mode
1. Click "🔍 Debug OFF" button
2. Button changes to "🔍 Debug ON"
3. Submit queries

### What to Check in Debug Info

For each response, verify:

```json
{
  "intent": "conversational_followup",          // ✅ Correct intent detected?
  "original_query": "Can you summarize that?",   // ✅ Original query preserved?
  "rewritten_query": "Summarize what...",        // ✅ Query properly rewritten?
  "was_rewritten": true,                         // ✅ Rewriting occurred when needed?
  "retrieval_performed": true,                   // ✅ Retrieval decision correct?
  "conversation_history_length": 2,              // ✅ History tracked?
  "temperature": 0.3                             // ✅ Appropriate temperature?
}
```

---

## ✅ Expected Behaviors

### ✓ Query Rewriting Should Work
```
❌ Bad: Using "Can you summarize that?" for retrieval
✅ Good: Rewritten to "Summarize what the PDF says about X" for retrieval
```

### ✓ References Should Resolve
```
"that" → resolved to specific entity from context
"this" → resolved to specific entity from context
"it" → resolved to specific entity from context
"they" → resolved to specific people/entities
"previous" → resolved to previous topic
```

### ✓ Intent Should Be Accurate
```
"Hello" → greeting (no retrieval)
"Thanks" → feedback (no retrieval)
"What does the PDF say about X?" → document_qa (retrieval)
"Summarize that" → summarization (retrieval)
"Compare both" → comparison (retrieval)
"Why did you say that?" → meta_question (no retrieval)
```

### ✓ Retrieval Should Be Smart
```
Greetings → NO retrieval
Meta questions → NO retrieval
Document questions → YES retrieval
Follow-ups → CONDITIONAL retrieval (based on context)
```

---

## ❌ Common Issues & Solutions

### Issue 1: Query Not Being Rewritten
**Symptom**: Debug shows `was_rewritten: false` when it should be true

**Check**:
1. Is conversation history being sent? (Check network tab)
2. Is Ollama running?
3. Is llama3 model loaded?

**Test**:
```bash
curl http://localhost:11434/api/generate -d "{\"model\":\"llama3\",\"prompt\":\"test\"}"
```

### Issue 2: Wrong Intent Detected
**Symptom**: Intent is always `document_qa`

**Check**:
1. Ollama is running
2. Temperature is set to 0.1 in intent classifier
3. LLM is responding correctly

**Debug**:
Enable backend logging to see intent classification prompt

### Issue 3: No Conversation Context
**Symptom**: Follow-up questions don't work

**Check**:
1. Session ID is being generated (check console)
2. Chat history is being sent to API
3. Memory manager is storing messages

**Verify**:
```
Console log should show:
"Chat session started: session_xxx"
```

### Issue 4: Session Not Persisting
**Expected Behavior**: Sessions are in-memory

**Note**: Sessions clear when backend restarts. This is intentional for the current implementation. For persistence, implement Redis/Database.

### Issue 5: Debug Info Not Appearing
**Solution**: Make sure debug mode is ON (button shows "🔍 Debug ON")

---

## 📊 Success Metrics

### Test Passed If:

✅ **Conversational Flow**: Can have multi-turn conversation with references
✅ **Query Rewriting**: Vague queries are rewritten before retrieval
✅ **Intent Detection**: Different query types detected correctly
✅ **Smart Retrieval**: Retrieval only happens when needed
✅ **Reference Resolution**: "that", "this", "it" are resolved correctly
✅ **Memory Tracking**: Conversation history is maintained
✅ **Debug Info**: All debug fields are populated correctly
✅ **Session Management**: New session button works
✅ **Multi-Document**: Can query across multiple PDFs

---

## 🎯 Test Checklist

```
[ ] Backend starts without errors
[ ] Frontend starts without errors
[ ] Can upload PDFs successfully
[ ] Can ask direct questions
[ ] Can ask follow-up questions with "that"
[ ] Can ask follow-up questions with "this"
[ ] Query rewriting works (check debug)
[ ] Intent classification works (check debug)
[ ] Greeting doesn't trigger retrieval
[ ] Meta questions don't trigger retrieval
[ ] Document questions trigger retrieval
[ ] Session ID is generated
[ ] Chat history is tracked
[ ] Debug mode can be toggled
[ ] New session button clears chat
[ ] Multiple PDFs can be uploaded
[ ] Can compare across documents
```

---

## 💡 Example Test Session

### Complete Test Flow

```
[Start Backend & Frontend]

1. Upload "AI_replace_developers.pdf"
   ✅ Success notification appears

2. Ask: "What does this document say about AI replacing developers?"
   ✅ Direct answer with citations
   Debug: Intent: document_qa, Retrieval: true

3. Ask: "Can you summarize that?"
   ✅ Summary of previous answer
   Debug: Original: "Can you summarize that?"
          Rewritten: "Summarize what the document says about AI replacing developers"
          Intent: summarization, Retrieval: true

4. Ask: "What about the main concerns?"
   ✅ Main concerns listed
   Debug: Query expanded with context
          Intent: conversational_followup, Retrieval: true

5. Ask: "Did you just use the document?"
   ✅ Meta answer without retrieval
   Debug: Intent: meta_question, Retrieval: false

6. Upload second PDF: "AI_NOT_replace_developers.pdf"
   ✅ Success notification, chat preserved

7. Ask: "Compare both PDFs on this topic"
   ✅ Comparison across both documents
   Debug: Intent: comparison, Retrieval: true

8. Ask: "Which argument is stronger?"
   ✅ Analysis with context
   Debug: Query rewritten with comparison context

9. Click "New Session" button
   ✅ Chat clears, new session ID generated

10. Ask: "Hello"
    ✅ Greeting response
    Debug: Intent: greeting, Retrieval: false
```

---

## 🎉 Success!

If all tests pass, your conversational RAG system is working correctly!

**Key Achievements:**
- ✅ Natural language understanding
- ✅ Follow-up question handling
- ✅ Reference resolution
- ✅ Smart retrieval decisions
- ✅ Conversation memory
- ✅ Multi-turn interactions
- ✅ Debug visibility

**You now have a production-grade conversational AI assistant!** 🚀
