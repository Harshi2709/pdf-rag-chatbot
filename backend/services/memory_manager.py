"""
Memory Manager Module
Handles conversation history and session management
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class Message:
    """Represents a single message in conversation"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }


class ConversationSession:
    """Manages a single conversation session"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Message] = []
        self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        message = Message(role, content)
        self.messages.append(message)
        self.last_updated = datetime.now().isoformat()
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """Get the n most recent messages"""
        recent = self.messages[-n:] if len(self.messages) > n else self.messages
        return [msg.to_dict() for msg in recent]
    
    def get_all_messages(self) -> List[Dict[str, str]]:
        """Get all messages in the conversation"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message content"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def get_last_assistant_message(self) -> Optional[str]:
        """Get the last assistant message content"""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg.content
        return None
    
    def clear(self):
        """Clear all messages in the session"""
        self.messages = []
        self.last_updated = datetime.now().isoformat()


class MemoryManager:
    """
    Manages conversation sessions and memory
    In-memory storage (can be replaced with Redis/Database for production)
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = ConversationSession(session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a conversation session by ID"""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Create new session
        new_id = session_id or str(uuid.uuid4())
        self.sessions[new_id] = ConversationSession(new_id)
        return self.sessions[new_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to a session"""
        session = self.get_or_create_session(session_id)
        session.add_message(role, content)
    
    def get_conversation_history(
        self, 
        session_id: str, 
        n_recent: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        if n_recent:
            return session.get_recent_messages(n_recent)
        return session.get_all_messages()
    
    def clear_session(self, session_id: str):
        """Clear a conversation session"""
        session = self.get_session(session_id)
        if session:
            session.clear()
    
    def delete_session(self, session_id: str):
        """Delete a conversation session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        return len(self.sessions)
    
    def format_history_for_llm(self, session_id: str, n_recent: int = 5) -> str:
        """
        Format conversation history for LLM context
        Returns a formatted string of recent conversation
        """
        history = self.get_conversation_history(session_id, n_recent)
        
        if not history:
            return "No previous conversation."
        
        formatted = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        
        return "\n".join(formatted)


# Global singleton instance
memory_manager = MemoryManager()
