"""
REALTIME LOGGER - V380 Sistema de Log em Tempo Real
Registra todas as ações do aplicativo em tempo real
NÃO LIMPA O LOG - Mantém histórico completo
"""
import os
import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class RealtimeLogger:
    """
    Logger em tempo real que registra todas as ações do aplicativo
    Mantém histórico completo sem limpeza automática
    """
    
    def __init__(self, log_file: str = "app_runtime.log"):
        self.log_file = Path(__file__).parent.parent.parent / log_file
        self.lock = threading.Lock()
        
        # Configurar logging
        self.logger = logging.getLogger('V380_REALTIME')
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato personalizado
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Adicionar handlers se não existirem
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.log_startup()
    
    def log_startup(self):
        """Log de inicialização do sistema"""
        self.info("🚀 Sistema V380 - Logger em tempo real ativado")
        self.info("📁 Log salvo em: " + str(self.log_file))
    
    def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de informação"""
        with self.lock:
            full_message = f"ℹ️ {message}"
            if details:
                full_message += f" | Detalhes: {details}"
            self.logger.info(full_message)
    
    def success(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de sucesso"""
        with self.lock:
            full_message = f"✅ {message}"
            if details:
                full_message += f" | Detalhes: {details}"
            self.logger.info(full_message)
    
    def warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de aviso"""
        with self.lock:
            full_message = f"⚠️ {message}"
            if details:
                full_message += f" | Detalhes: {details}"
            self.logger.warning(full_message)
    
    def error(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log de erro"""
        with self.lock:
            full_message = f"❌ {message}"
            if details:
                full_message += f" | Detalhes: {details}"
            self.logger.error(full_message)
    
    def search_start(self, query: str, provider: str):
        """Log início de busca"""
        self.info(f"🔍 Iniciando busca: '{query}' via {provider}")
    
    def search_success(self, query: str, provider: str, results_count: int):
        """Log sucesso de busca"""
        self.success(f"🎯 Busca concluída: '{query}' via {provider} - {results_count} resultados")
    
    def search_fallback(self, query: str, from_provider: str, to_provider: str):
        """Log fallback de busca"""
        self.warning(f"🔄 Fallback: '{query}' de {from_provider} para {to_provider}")
    
    def api_call(self, api_name: str, endpoint: str, status: str):
        """Log chamada de API"""
        if status == "success":
            self.success(f"🌐 API {api_name}: {endpoint}")
        else:
            self.error(f"🌐 API {api_name}: {endpoint} - Status: {status}")
    
    def ai_request(self, model: str, prompt_length: int, response_length: int = None):
        """Log requisição de IA"""
        if response_length:
            self.success(f"🤖 IA {model}: Prompt({prompt_length} chars) → Resposta({response_length} chars)")
        else:
            self.info(f"🤖 IA {model}: Enviando prompt ({prompt_length} chars)")
    
    def data_extraction(self, source: str, data_type: str, count: int):
        """Log extração de dados"""
        self.success(f"📊 Extração {data_type}: {count} itens de {source}")
    
    def report_generation(self, report_type: str, status: str):
        """Log geração de relatório"""
        if status == "success":
            self.success(f"📋 Relatório {report_type} gerado com sucesso")
        else:
            self.error(f"📋 Falha na geração do relatório {report_type}")
    
    def system_status(self, component: str, status: str, details: Optional[str] = None):
        """Log status do sistema"""
        emoji = "✅" if status == "ok" else "❌" if status == "error" else "⚠️"
        message = f"{emoji} {component}: {status}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def performance_metric(self, operation: str, duration: float, details: Optional[Dict] = None):
        """Log métricas de performance"""
        self.info(f"⏱️ {operation}: {duration:.2f}s", details)
    
    def user_action(self, action: str, details: Optional[Dict] = None):
        """Log ação do usuário"""
        self.info(f"👤 Ação: {action}", details)
    
    def separator(self, title: str = None):
        """Adiciona separador visual no log"""
        with self.lock:
            self.logger.info("=" * 50)
            if title:
                self.logger.info(f"📌 {title}")
                self.logger.info("=" * 50)

# Instância global do logger
realtime_logger = RealtimeLogger()

# Funções de conveniência para uso direto
def log_info(message: str, details: Optional[Dict[str, Any]] = None):
    realtime_logger.info(message, details)

def log_success(message: str, details: Optional[Dict[str, Any]] = None):
    realtime_logger.success(message, details)

def log_warning(message: str, details: Optional[Dict[str, Any]] = None):
    realtime_logger.warning(message, details)

def log_error(message: str, details: Optional[Dict[str, Any]] = None):
    realtime_logger.error(message, details)

def log_search_start(query: str, provider: str):
    realtime_logger.search_start(query, provider)

def log_search_success(query: str, provider: str, results_count: int):
    realtime_logger.search_success(query, provider, results_count)

def log_search_fallback(query: str, from_provider: str, to_provider: str):
    realtime_logger.search_fallback(query, from_provider, to_provider)

def log_api_call(api_name: str, endpoint: str, status: str):
    realtime_logger.api_call(api_name, endpoint, status)

def log_ai_request(model: str, prompt_length: int, response_length: int = None):
    realtime_logger.ai_request(model, prompt_length, response_length)

def log_separator(title: str = None):
    realtime_logger.separator(title)