#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UBIE Conversation Memory
"""

import logging
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Gerenciador de memória de conversas UBIE"""

    def __init__(self, db_path: str = "analyses_data/conversation_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("✅ ConversationMemory inicializado")

    def _init_database(self):
        """Inicializa banco de dados SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        user_message TEXT,
                        ai_response TEXT
                    )
                """)

                # Verifica se as colunas existem e adiciona se necessário
                cursor = conn.execute("PRAGMA table_info(conversations)")
                columns = [row[1] for row in cursor.fetchall()]

                if 'role' not in columns:
                    conn.execute("ALTER TABLE conversations ADD COLUMN role TEXT")
                if 'content' not in columns:
                    conn.execute("ALTER TABLE conversations ADD COLUMN content TEXT")
                if 'user_message' not in columns:
                    conn.execute("ALTER TABLE conversations ADD COLUMN user_message TEXT")
                if 'ai_response' not in columns:
                    conn.execute("ALTER TABLE conversations ADD COLUMN ai_response TEXT")

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_session_id 
                    ON conversations(session_id)
                """)
                conn.commit()
                logger.info("✅ Banco de dados de conversas inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")

    def save_conversation(self, session_id: str, user_message: str, 
                         ai_response: str, metadata: Dict[str, Any] = None) -> bool:
        """Salva conversa no banco"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                timestamp = datetime.now().isoformat()
                metadata_json = json.dumps(metadata or {})

                # Salva mensagem do usuário
                conn.execute("""
                    INSERT INTO conversations 
                    (session_id, role, content, timestamp, metadata, user_message, ai_response)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    'user',
                    user_message,
                    timestamp,
                    metadata_json,
                    user_message,
                    None
                ))

                # Salva resposta do assistente
                conn.execute("""
                    INSERT INTO conversations 
                    (session_id, role, content, timestamp, metadata, user_message, ai_response)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    'assistant',
                    ai_response,
                    timestamp,
                    metadata_json,
                    None,
                    ai_response
                ))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar conversa: {e}")
            return False

    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera histórico de conversas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT role, content, timestamp, metadata
                    FROM conversations
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (session_id, limit))

                conversations = []
                for row in cursor.fetchall():
                    conversations.append({
                        'role': row[0],
                        'content': row[1],
                        'timestamp': row[2],
                        'metadata': json.loads(row[3]) if row[3] else {}
                    })

                return conversations
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar conversas: {e}")
            return []

    def clear_session_memory(self, session_id: str) -> bool:
        """Limpa memória de uma sessão"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao limpar memória: {e}")
            return False