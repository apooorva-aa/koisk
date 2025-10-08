"""
Database Models for Koisk LLM System.
Consolidated database schema and models.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Centralized database management for all Koisk LLM data."""
    
    def __init__(self, db_path: str = "data/koisk.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        
    def connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def initialize_schema(self):
        """Initialize all database tables."""
        try:
            cursor = self.connection.cursor()
            
            # Knowledge Base Documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    metadata TEXT,
                    category TEXT,
                    language TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User Sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    interaction_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)
            
            # Conversation History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    system_response TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_time_ms INTEGER,
                    model_used TEXT,
                    confidence_score REAL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Face Detection Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    event_type TEXT NOT NULL,  -- 'detected', 'lost', 'timeout'
                    confidence REAL,
                    bbox_x INTEGER,
                    bbox_y INTEGER,
                    bbox_width INTEGER,
                    bbox_height INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Audio Processing Events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    event_type TEXT NOT NULL,  -- 'recording_start', 'recording_end', 'transcription'
                    audio_file_path TEXT,
                    transcription_text TEXT,
                    language_detected TEXT,
                    confidence REAL,
                    duration_seconds REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # System Performance Metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    component TEXT NOT NULL,  -- 'face_detection', 'asr', 'llm', 'tts', 'rag'
                    metric_name TEXT NOT NULL,  -- 'processing_time', 'memory_usage', 'cpu_usage'
                    metric_value REAL NOT NULL,
                    unit TEXT,  -- 'ms', 'MB', '%'
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_language ON documents(language)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_events_session_id ON face_events(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_events_session_id ON audio_events(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_session_id ON performance_metrics(session_id)")
            
            self.connection.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise


class DocumentModel:
    """Model for knowledge base documents."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_document(self, title: str, content: str, embedding: List[float], 
                    metadata: Optional[Dict] = None, category: str = "general", 
                    language: str = "en") -> int:
        """Add a document to the knowledge base."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO documents (title, content, embedding, metadata, category, language)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, content, json.dumps(embedding), json.dumps(metadata or {}), category, language))
            
            doc_id = cursor.lastrowid
            self.db.connection.commit()
            logger.debug(f"Added document: {title} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def search_documents(self, query_embedding: List[float], limit: int = 5, 
                        category: Optional[str] = None, language: Optional[str] = None) -> List[Dict]:
        """Search documents by embedding similarity."""
        try:
            cursor = self.db.connection.cursor()
            
            # Build query with optional filters
            query = """
                SELECT id, title, content, embedding, metadata, category, language, created_at
                FROM documents
            """
            params = []
            conditions = []
            
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if language:
                conditions.append("language = ?")
                params.append(language)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Calculate similarities
            results = []
            for row in rows:
                doc_embedding = json.loads(row['embedding'])
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'similarity': similarity,
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'category': row['category'],
                    'language': row['language'],
                    'created_at': row['created_at']
                })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class SessionModel:
    """Model for user sessions."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_session(self, session_id: str, user_id: Optional[str] = None, 
                      metadata: Optional[Dict] = None) -> bool:
        """Create a new session."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO sessions (id, user_id, metadata)
                VALUES (?, ?, ?)
            """, (session_id, user_id, json.dumps(metadata or {})))
            
            self.db.connection.commit()
            logger.debug(f"Created session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False
    
    def end_session(self, session_id: str) -> bool:
        """End a session."""
        try:
            cursor = self.db.connection.cursor()
            
            # Get session start time
            cursor.execute("SELECT started_at FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                started_at = datetime.fromisoformat(row['started_at'])
                ended_at = datetime.now()
                duration = (ended_at - started_at).total_seconds()
                
                cursor.execute("""
                    UPDATE sessions 
                    SET ended_at = ?, duration_seconds = ?
                    WHERE id = ?
                """, (ended_at.isoformat(), duration, session_id))
                
                self.db.connection.commit()
                logger.debug(f"Ended session: {session_id} (duration: {duration}s)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
    
    def add_conversation(self, session_id: str, user_input: str, system_response: str,
                        processing_time_ms: Optional[int] = None, model_used: Optional[str] = None,
                        confidence_score: Optional[float] = None) -> int:
        """Add a conversation to the session."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id, user_input, system_response, 
                                        processing_time_ms, model_used, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_input, system_response, processing_time_ms, model_used, confidence_score))
            
            # Update interaction count
            cursor.execute("""
                UPDATE sessions 
                SET interaction_count = interaction_count + 1
                WHERE id = ?
            """, (session_id,))
            
            conv_id = cursor.lastrowid
            self.db.connection.commit()
            logger.debug(f"Added conversation to session {session_id}")
            return conv_id
            
        except Exception as e:
            logger.error(f"Error adding conversation: {e}")
            raise


class AnalyticsModel:
    """Model for analytics and performance tracking."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_face_event(self, session_id: Optional[str], event_type: str, 
                      confidence: Optional[float] = None, bbox: Optional[Dict] = None):
        """Add a face detection event."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO face_events (session_id, event_type, confidence, bbox_x, bbox_y, bbox_width, bbox_height)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, event_type, confidence, 
                  bbox.get('x') if bbox else None,
                  bbox.get('y') if bbox else None,
                  bbox.get('width') if bbox else None,
                  bbox.get('height') if bbox else None))
            
            self.db.connection.commit()
            
        except Exception as e:
            logger.error(f"Error adding face event: {e}")
    
    def add_audio_event(self, session_id: Optional[str], event_type: str,
                       audio_file_path: Optional[str] = None, transcription_text: Optional[str] = None,
                       language_detected: Optional[str] = None, confidence: Optional[float] = None,
                       duration_seconds: Optional[float] = None):
        """Add an audio processing event."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO audio_events (session_id, event_type, audio_file_path, transcription_text,
                                       language_detected, confidence, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, event_type, audio_file_path, transcription_text,
                  language_detected, confidence, duration_seconds))
            
            self.db.connection.commit()
            
        except Exception as e:
            logger.error(f"Error adding audio event: {e}")
    
    def add_performance_metric(self, session_id: Optional[str], component: str,
                              metric_name: str, metric_value: float, unit: Optional[str] = None):
        """Add a performance metric."""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (session_id, component, metric_name, metric_value, unit)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, component, metric_name, metric_value, unit))
            
            self.db.connection.commit()
            
        except Exception as e:
            logger.error(f"Error adding performance metric: {e}")
    
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a specific session."""
        try:
            cursor = self.db.connection.cursor()
            
            # Session info
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            
            if not session:
                return {}
            
            # Conversation count
            cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE session_id = ?", (session_id,))
            conv_count = cursor.fetchone()['count']
            
            # Face events
            cursor.execute("SELECT * FROM face_events WHERE session_id = ? ORDER BY timestamp", (session_id,))
            face_events = [dict(row) for row in cursor.fetchall()]
            
            # Audio events
            cursor.execute("SELECT * FROM audio_events WHERE session_id = ? ORDER BY timestamp", (session_id,))
            audio_events = [dict(row) for row in cursor.fetchall()]
            
            # Performance metrics
            cursor.execute("SELECT * FROM performance_metrics WHERE session_id = ? ORDER BY timestamp", (session_id,))
            performance_metrics = [dict(row) for row in cursor.fetchall()]
            
            return {
                'session': dict(session),
                'conversation_count': conv_count,
                'face_events': face_events,
                'audio_events': audio_events,
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting session analytics: {e}")
            return {}
