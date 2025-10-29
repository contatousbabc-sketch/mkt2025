#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Persistência de Sessões - APENAS LOCAL
Gerencia salvamento, pausa, continuação e renomeação de sessões de análise
ARMAZENAMENTO 100% LOCAL COM ARQUIVOS JSON
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import time
from pathlib import Path # Import Path for backup functionality

logger = logging.getLogger(__name__)

class SessionPersistenceManager:
    """Gerenciador de persistência de sessões - APENAS LOCAL"""

    def __init__(self):
        """Inicializa o gerenciador de persistência local"""
        # Múltiplos caminhos para garantir salvamento
        possible_paths = [
            os.path.join(os.getcwd(), "analyses_data", "sessions"),
            os.path.join(os.getcwd(), "src", "analyses_data", "sessions"),
            os.path.join(os.getcwd(), "src", "src", "analyses_data", "sessions"),
            os.path.join("/tmp", "analyses_data", "sessions")
        ]

        # Usa o primeiro caminho que conseguir criar
        self.sessions_dir = None
        for path in possible_paths:
            try:
                os.makedirs(path, exist_ok=True)
                # Testa se consegue escrever
                test_file = os.path.join(path, "test.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                self.sessions_dir = path
                break
            except Exception:
                continue

        if not self.sessions_dir:
            # Fallback para diretório temporário
            self.sessions_dir = "/tmp/sessions"
            os.makedirs(self.sessions_dir, exist_ok=True)

        logger.info(f"🗃️ Session Persistence Manager LOCAL inicializado: {self.sessions_dir}")

    def _get_session_file_path(self, session_id: str) -> str:
        """Retorna o caminho do arquivo da sessão"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega dados da sessão do arquivo local"""
        session_file = self._get_session_file_path(session_id)

        if not os.path.exists(session_file):
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Erro ao carregar sessão {session_id}: {e}")
            return None

    def _save_session_data(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Salva dados da sessão no arquivo local"""
        session_file = self._get_session_file_path(session_id)

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão {session_id}: {e}")
            return False

    def save_session(self, session_id: str, name: str, query: str, segmento: str, 
                    openrouter_model: str = None) -> Dict[str, Any]:
        """Salva uma nova sessão em arquivo local"""
        try:
            # Verifica se já existe uma sessão com este ID
            existing_session = self._load_session_data(session_id)
            
            if existing_session:
                # Atualiza sessão existente
                existing_session.update({
                    'name': name,
                    'query': query,
                    'segmento': segmento,
                    'openrouter_model': openrouter_model or existing_session.get('openrouter_model', 'anthropic/claude-3-haiku:beta'),
                    'updated_at': datetime.now().isoformat()
                })
                session_data = existing_session
            else:
                # Cria nova sessão
                session_data = {
                    'id': session_id,
                    'name': name,
                    'query': query,
                    'segmento': segmento,
                    'status': 'active',
                    'openrouter_model': openrouter_model or 'anthropic/claude-3-haiku:beta',
                    'progress_percentage': 0,
                    'current_step': 0,
                    'step1_data': None,
                    'step2_data': None,
                    'step3_data': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'paused_at': None,
                    'completed_at': None
                }

            if self._save_session_data(session_id, session_data):
                logger.info(f"💾 Sessão salva localmente: {session_id} - {name}")
                return {
                    'success': True,
                    'session_id': session_id,
                    'message': f'Sessão "{name}" salva com sucesso'
                }
            else:
                return {'success': False, 'error': 'Erro ao salvar arquivo da sessão'}

        except Exception as e:
            logger.error(f"❌ Erro ao salvar sessão: {e}")
            return {'success': False, 'error': str(e)}

    def pause_session(self, session_id: str) -> Dict[str, Any]:
        """Pausa uma sessão ativa"""
        try:
            session_data = self._load_session_data(session_id)

            if not session_data:
                return {
                    'success': False,
                    'error': 'Sessão não encontrada'
                }

            if session_data.get('status') != 'active':
                return {
                    'success': False,
                    'error': 'Sessão não está ativa'
                }

            session_data['status'] = 'paused'
            session_data['paused_at'] = datetime.now().isoformat()
            session_data['updated_at'] = datetime.now().isoformat()

            if self._save_session_data(session_id, session_data):
                logger.info(f"⏸️ Sessão pausada: {session_id}")
                return {
                    'success': True,
                    'message': 'Sessão pausada com sucesso'
                }
            else:
                return {'success': False, 'error': 'Erro ao salvar status da sessão'}

        except Exception as e:
            logger.error(f"❌ Erro ao pausar sessão: {e}")
            return {'success': False, 'error': str(e)}

    def continue_session(self, session_id: str) -> Dict[str, Any]:
        """Continua uma sessão pausada"""
        try:
            session_data = self._load_session_data(session_id)

            if not session_data:
                return {
                    'success': False,
                    'error': 'Sessão não encontrada'
                }

            if session_data.get('status') != 'paused':
                return {
                    'success': False,
                    'error': 'Sessão não está pausada'
                }

            session_data['status'] = 'active'
            session_data['updated_at'] = datetime.now().isoformat()
            session_data['paused_at'] = None

            if self._save_session_data(session_id, session_data):
                logger.info(f"▶️ Sessão continuada: {session_id}")
                return {
                    'success': True,
                    'session_data': session_data,
                    'message': 'Sessão continuada com sucesso'
                }
            else:
                return {'success': False, 'error': 'Erro ao salvar status da sessão'}

        except Exception as e:
            logger.error(f"❌ Erro ao continuar sessão: {e}")
            return {'success': False, 'error': str(e)}

    def rename_session(self, session_id: str, new_name: str) -> Dict[str, Any]:
        """Renomeia uma sessão"""
        try:
            session_data = self._load_session_data(session_id)

            if not session_data:
                return {
                    'success': False,
                    'error': 'Sessão não encontrada'
                }

            session_data['name'] = new_name
            session_data['updated_at'] = datetime.now().isoformat()

            if self._save_session_data(session_id, session_data):
                logger.info(f"✏️ Sessão renomeada: {session_id} -> {new_name}")
                return {
                    'success': True,
                    'message': f'Sessão renomeada para "{new_name}"'
                }
            else:
                return {'success': False, 'error': 'Erro ao salvar nome da sessão'}

        except Exception as e:
            logger.error(f"❌ Erro ao renomear sessão: {e}")
            return {'success': False, 'error': str(e)}

    def update_session_progress(self, session_id: str, step: int, progress: int, 
                               step_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Atualiza o progresso de uma sessão"""
        try:
            session_data = self._load_session_data(session_id)

            if not session_data:
                return {'success': False, 'error': 'Sessão não encontrada'}

            session_data['current_step'] = step
            session_data['progress_percentage'] = progress
            session_data['updated_at'] = datetime.now().isoformat()

            # Salva dados da etapa se fornecidos
            if step_data:
                step_key = f'step{step}_data'
                session_data[step_key] = step_data

            # Marca como concluída se progress = 100
            if progress >= 100:
                session_data['status'] = 'completed'
                session_data['completed_at'] = datetime.now().isoformat()

            if self._save_session_data(session_id, session_data):
                logger.info(f"📊 Progresso atualizado: {session_id} - Etapa {step} ({progress}%)")
                return {'success': True, 'message': 'Progresso atualizado'}
            else:
                return {'success': False, 'error': 'Erro ao salvar progresso'}

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar progresso: {e}")
            return {'success': False, 'error': str(e)}

    def get_sessions(self, status: str = None) -> List[Dict[str, Any]]:
        """Lista sessões salvas localmente"""
        try:
            sessions = []

            logger.info(f"🔍 DEBUG get_sessions: sessions_dir = {self.sessions_dir}")
            logger.info(f"🔍 DEBUG get_sessions: dir exists = {os.path.exists(self.sessions_dir)}")

            if not os.path.exists(self.sessions_dir):
                logger.warning(f"⚠️ Diretório de sessões não existe: {self.sessions_dir}")
                return sessions

            files = os.listdir(self.sessions_dir)
            logger.info(f"🔍 DEBUG get_sessions: files found = {files}")

            for filename in files:
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json
                    logger.info(f"🔍 DEBUG get_sessions: loading session {session_id}")
                    session_data = self._load_session_data(session_id)

                    if session_data:
                        logger.info(f"🔍 DEBUG get_sessions: session data loaded = {session_data.get('name')}")
                        # Filtra por status se especificado
                        if status and session_data.get('status') != status:
                            logger.info(f"🔍 DEBUG get_sessions: session filtered by status {status}")
                            continue

                        # Garante que session_id está presente nos dados
                        session_data['session_id'] = session_id
                        sessions.append(session_data)
                    else:
                        logger.warning(f"⚠️ Falha ao carregar sessão: {session_id}")

            # Ordena por data de atualização (mais recente primeiro)
            sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

            logger.info(f"📋 {len(sessions)} sessões encontradas localmente")
            return sessions

        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Remove uma sessão"""
        try:
            session_file = self._get_session_file_path(session_id)

            if not os.path.exists(session_file):
                return {
                    'success': False,
                    'error': 'Sessão não encontrada'
                }

            os.remove(session_file)
            logger.info(f"🗑️ Sessão removida: {session_id}")

            return {
                'success': True,
                'message': 'Sessão removida com sucesso'
            }

        except Exception as e:
            logger.error(f"❌ Erro ao remover sessão: {e}")
            return {'success': False, 'error': str(e)}

    def update_openrouter_model(self, session_id: str, model: str) -> Dict[str, Any]:
        """Atualiza o modelo OpenRouter de uma sessão"""
        try:
            session_data = self._load_session_data(session_id)

            if not session_data:
                return {
                    'success': False,
                    'error': 'Sessão não encontrada'
                }

            session_data['openrouter_model'] = model
            session_data['updated_at'] = datetime.now().isoformat()

            if self._save_session_data(session_id, session_data):
                logger.info(f"🤖 Modelo OpenRouter atualizado: {session_id} -> {model}")
                return {
                    'success': True,
                    'message': f'Modelo alterado para {model}'
                }
            else:
                return {'success': False, 'error': 'Erro ao salvar modelo'}

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar modelo: {e}")
            return {'success': False, 'error': str(e)}

# Instância global
session_persistence = SessionPersistenceManager()