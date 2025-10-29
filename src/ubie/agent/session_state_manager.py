
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UBIE Session State Manager
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionStateManager:
    """Gerenciador de estado de sessões UBIE"""
    
    def __init__(self, base_dir: str = "analyses_data/sessions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("✅ SessionStateManager inicializado")
    
    def create_session(self, session_id: str, initial_data: Dict[str, Any] = None) -> bool:
        """Cria nova sessão"""
        try:
            session_data = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'status': 'active',
                'data': initial_data or {}
            }
            
            self.sessions[session_id] = session_data
            self._save_session_to_file(session_id, session_data)
            
            logger.info(f"✅ Sessão criada: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Recupera dados da sessão"""
        try:
            if session_id in self.sessions:
                return self.sessions[session_id]
            
            # Tentar carregar do arquivo
            session_file = self.base_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    self.sessions[session_id] = session_data
                    return session_data
            
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar sessão: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Atualiza dados da sessão"""
        try:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"⚠️ Sessão não encontrada: {session_id}")
                return False
            
            session['data'].update(data)
            session['last_updated'] = datetime.now().isoformat()
            
            self.sessions[session_id] = session
            self._save_session_to_file(session_id, session)
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar sessão: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Remove sessão"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            session_file = self.base_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"✅ Sessão removida: {session_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao remover sessão: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """Lista todas as sessões"""
        try:
            # Sessões em memória
            session_ids = set(self.sessions.keys())
            
            # Sessões em arquivo
            for session_file in self.base_dir.glob("*.json"):
                session_ids.add(session_file.stem)
            
            return list(session_ids)
        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões: {e}")
            return []
    
    def _save_session_to_file(self, session_id: str, session_data: Dict[str, Any]):
        """Salva sessão em arquivo"""
        try:
            session_file = self.base_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão em arquivo: {e}")
