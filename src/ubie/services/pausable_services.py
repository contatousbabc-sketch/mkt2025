#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO 3: Arquitetura de Serviços "Pausável"
Objetivo: Permitir que processos de longa duração possam ser pausados e retomados após reinicializações.

⚠️ AVISO DE PRIVACIDADE:
Este módulo processa dados localmente, mas pode interagir com APIs externas via Google Gemini Cloud.
"""

import os
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class PausableServiceBase(ABC):
    """
    Classe base para serviços pausáveis.
    
    Funcionalidades:
    - Salvamento de Estado: Ao pausar, salva estado em stepX.state.json
    - Carregamento de Estado: Ao retomar, lê estado salvo e continua de onde parou
    - Nova Thread: Sempre que retomado, nova thread é criada para isolamento
    """
    
    def __init__(self, session_id: str, service_name: str):
        """
        Inicializa o serviço pausável.
        
        Args:
            session_id: ID da sessão
            service_name: Nome do serviço
        """
        self.session_id = session_id
        self.service_name = service_name
        self.analyses_base_dir = os.getenv('ANALYSES_BASE_DIR', 'analyses_data')
        self.session_dir = os.path.join(self.analyses_base_dir, session_id)
        
        # Estado do serviço
        self.is_running = False
        self.is_paused = False
        self.current_step = 0
        self.total_steps = 0
        self.state_data = {}
        
        # Threading
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Callbacks
        self.on_progress_callback = None
        self.on_error_callback = None
        self.on_complete_callback = None
        
        # Cria diretório da sessão se não existir
        os.makedirs(self.session_dir, exist_ok=True)
        
        logger.info(f"🛠️ Serviço pausável inicializado: {service_name} (sessão: {session_id})")

    def set_callbacks(self, 
                     on_progress: Optional[Callable] = None,
                     on_error: Optional[Callable] = None, 
                     on_complete: Optional[Callable] = None):
        """
        Define callbacks para eventos do serviço.
        
        Args:
            on_progress: Callback para progresso (step, total, data)
            on_error: Callback para erros (error_message, step)
            on_complete: Callback para conclusão (final_data)
        """
        self.on_progress_callback = on_progress
        self.on_error_callback = on_error
        self.on_complete_callback = on_complete

    def start(self, initial_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Inicia o serviço em uma nova thread.
        
        Args:
            initial_data: Dados iniciais para o processamento
            
        Returns:
            bool: True se iniciado com sucesso
        """
        try:
            if self.is_running:
                logger.warning(f"⚠️ Serviço {self.service_name} já está executando")
                return False
            
            # Carrega estado anterior se existir
            saved_state = self._load_state()
            if saved_state:
                self.current_step = saved_state.get('current_step', 0)
                self.total_steps = saved_state.get('total_steps', 0) 
                self.state_data = saved_state.get('state_data', {})
                logger.info(f"🔄 Estado anterior carregado: step {self.current_step}/{self.total_steps}")
            else:
                # Novo processamento
                self.current_step = 0
                self.state_data = initial_data or {}
            
            # Reset eventos
            self.stop_event.clear()
            self.pause_event.clear()
            
            # Inicia nova thread
            self.worker_thread = threading.Thread(
                target=self._worker_loop,
                name=f"{self.service_name}-{self.session_id}",
                daemon=True
            )
            
            self.is_running = True
            self.is_paused = False
            self.worker_thread.start()
            
            logger.info(f"▶️ Serviço {self.service_name} iniciado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar serviço {self.service_name}: {e}")
            return False

    def pause(self) -> bool:
        """
        Pausa o serviço e salva o estado atual.
        
        Returns:
            bool: True se pausado com sucesso
        """
        try:
            if not self.is_running:
                logger.warning(f"⚠️ Serviço {self.service_name} não está executando")
                return False
            
            logger.info(f"⏸️ Pausando serviço {self.service_name}...")
            
            # Sinaliza para pausar
            self.pause_event.set()
            self.is_paused = True
            
            # Salva estado atual
            self._save_state()
            
            logger.info(f"✅ Serviço {self.service_name} pausado no step {self.current_step}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao pausar serviço {self.service_name}: {e}")
            return False

    def resume(self) -> bool:
        """
        Retoma o serviço de onde parou.
        
        Returns:
            bool: True se retomado com sucesso
        """
        try:
            if self.is_running and not self.is_paused:
                logger.warning(f"⚠️ Serviço {self.service_name} já está executando")
                return False
            
            logger.info(f"▶️ Retomando serviço {self.service_name}...")
            
            # Se estava pausado, apenas retoma
            if self.is_paused:
                self.pause_event.clear()
                self.is_paused = False
                logger.info(f"✅ Serviço {self.service_name} retomado")
                return True
            
            # Se não estava executando, inicia novamente
            return self.start()
            
        except Exception as e:
            logger.error(f"❌ Erro ao retomar serviço {self.service_name}: {e}")
            return False

    def stop(self) -> bool:
        """
        Para completamente o serviço.
        
        Returns:
            bool: True se parado com sucesso
        """
        try:
            if not self.is_running:
                logger.warning(f"⚠️ Serviço {self.service_name} não está executando")
                return False
            
            logger.info(f"⏹️ Parando serviço {self.service_name}...")
            
            # Sinaliza para parar
            self.stop_event.set()
            self.pause_event.set()
            
            # Espera thread finalizar (timeout de 5 segundos)
            if self.worker_thread and self.worker_thread.is_alive():
                self.worker_thread.join(timeout=5.0)
            
            self.is_running = False
            self.is_paused = False
            
            logger.info(f"✅ Serviço {self.service_name} parado")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar serviço {self.service_name}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual do serviço.
        
        Returns:
            Dicionário com informações de status
        """
        return {
            'service_name': self.service_name,
            'session_id': self.session_id,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'progress_percentage': (self.current_step / self.total_steps * 100) if self.total_steps > 0 else 0,
            'thread_alive': self.worker_thread.is_alive() if self.worker_thread else False
        }

    def _worker_loop(self):
        """Loop principal do worker thread."""
        try:
            logger.info(f"🔄 Worker iniciado para {self.service_name}")
            
            # Executa o processamento principal
            self.execute_processing()
            
            # Se chegou aqui, processamento foi concluído
            if not self.stop_event.is_set():
                self._on_complete()
            
        except Exception as e:
            logger.error(f"❌ Erro no worker {self.service_name}: {e}")
            self._on_error(str(e))
        finally:
            self.is_running = False
            self.is_paused = False
            logger.info(f"🔄 Worker finalizado para {self.service_name}")

    def _save_state(self):
        """Salva o estado atual do serviço."""
        try:
            state_file = os.path.join(self.session_dir, f"step{self.current_step}.state.json")
            
            state_data = {
                'service_name': self.service_name,
                'session_id': self.session_id,
                'current_step': self.current_step,
                'total_steps': self.total_steps,
                'state_data': self.state_data,
                'timestamp': datetime.now().isoformat(),
                'is_paused': self.is_paused
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"💾 Estado salvo: {state_file}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar estado: {e}")

    def _load_state(self) -> Optional[Dict[str, Any]]:
        """Carrega o estado salvo mais recente."""
        try:
            # Procura por arquivos de estado
            state_files = []
            for file in os.listdir(self.session_dir):
                if file.startswith(f"step") and file.endswith(".state.json"):
                    state_files.append(file)
            
            if not state_files:
                return None
            
            # Ordena por número do step (pega o mais recente)
            state_files.sort(key=lambda x: int(x.replace('step', '').replace('.state.json', '')))
            latest_state_file = state_files[-1]
            
            state_file_path = os.path.join(self.session_dir, latest_state_file)
            
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            logger.info(f"📄 Estado carregado: {state_file_path}")
            return state_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar estado: {e}")
            return None

    def _check_pause_stop(self):
        """Verifica se deve pausar ou parar o processamento."""
        # Verifica se deve parar
        if self.stop_event.is_set():
            logger.info(f"🛑 Processamento de {self.service_name} interrompido")
            return 'stop'
        
        # Verifica se deve pausar
        if self.pause_event.is_set():
            logger.info(f"⏸️ Processamento de {self.service_name} pausado")
            self._save_state()
            
            # Aguarda até ser retomado ou parado
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.5)
            
            if self.stop_event.is_set():
                return 'stop'
            else:
                logger.info(f"▶️ Processamento de {self.service_name} retomado")
                return 'resume'
        
        return 'continue'

    def _on_progress(self, step: int, data: Optional[Dict[str, Any]] = None):
        """Callback interno para progresso."""
        self.current_step = step
        
        if self.on_progress_callback:
            try:
                self.on_progress_callback(step, self.total_steps, data)
            except Exception as e:
                logger.error(f"❌ Erro no callback de progresso: {e}")

    def _on_error(self, error_message: str):
        """Callback interno para erros."""
        if self.on_error_callback:
            try:
                self.on_error_callback(error_message, self.current_step)
            except Exception as e:
                logger.error(f"❌ Erro no callback de erro: {e}")

    def _on_complete(self):
        """Callback interno para conclusão."""
        if self.on_complete_callback:
            try:
                self.on_complete_callback(self.state_data)
            except Exception as e:
                logger.error(f"❌ Erro no callback de conclusão: {e}")

    @abstractmethod
    def execute_processing(self):
        """
        Método abstrato que deve ser implementado pelas classes filhas.
        Contém a lógica principal de processamento do serviço.
        """
        pass


class DataCollectionService(PausableServiceBase):
    """
    Exemplo de implementação: Serviço de coleta massiva de dados.
    """
    
    def __init__(self, session_id: str):
        super().__init__(session_id, "DataCollectionService")
    
    def execute_processing(self):
        """Executa coleta massiva de dados de forma pausável."""
        try:
            # Exemplo de processamento em etapas
            data_sources = self.state_data.get('data_sources', [])
            collected_data = self.state_data.get('collected_data', [])
            
            self.total_steps = len(data_sources)
            
            # Retoma de onde parou
            start_index = self.current_step
            
            for i in range(start_index, len(data_sources)):
                # Verifica se deve pausar/parar
                status = self._check_pause_stop()
                if status == 'stop':
                    break
                
                # Simula coleta de dados
                source = data_sources[i]
                logger.info(f"🔍 Coletando dados de: {source}")
                
                # Aqui iria a lógica real de coleta
                # collected_item = collect_from_source(source)
                collected_item = f"data_from_{source}_{i}"
                
                collected_data.append(collected_item)
                
                # Atualiza estado
                self.state_data['collected_data'] = collected_data
                self._on_progress(i + 1)
                
                # Salva estado periodicamente
                if (i + 1) % 5 == 0:
                    self._save_state()
                
                # Simula tempo de processamento
                time.sleep(1)
            
            logger.info(f"✅ Coleta de dados concluída: {len(collected_data)} itens")
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta de dados: {e}")
            raise


# Factory para criar serviços pausáveis
class PausableServiceFactory:
    """Factory para criar diferentes tipos de serviços pausáveis."""
    
    @staticmethod
    def create_service(service_type: str, session_id: str, **kwargs) -> Optional[PausableServiceBase]:
        """
        Cria um serviço pausável do tipo especificado.
        
        Args:
            service_type: Tipo do serviço
            session_id: ID da sessão
            **kwargs: Argumentos adicionais
            
        Returns:
            Instância do serviço ou None se tipo inválido
        """
        if service_type == "data_collection":
            return DataCollectionService(session_id)
        
        # Adicione outros tipos de serviços aqui
        # elif service_type == "analysis":
        #     return AnalysisService(session_id)
        
        logger.error(f"❌ Tipo de serviço não reconhecido: {service_type}")
        return None