#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Intelligent API Rotation Manager
Sistema inteligente de rotação de APIs com detecção automática de créditos
Remove automaticamente APIs sem crédito para evitar spam de warnings
ZERO SIMULAÇÃO - Apenas rotação real e funcional
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import requests
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class APIStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    NO_CREDITS = "no_credits"
    ERROR = "error"
    OFFLINE = "offline"
    BLACKLISTED = "blacklisted"

class APIType(Enum):
    SEARCH = "search"
    AI_GENERATION = "ai_generation"
    CONTENT_EXTRACTION = "content_extraction"
    IMAGE_SEARCH = "image_search"

@dataclass
class APIEndpoint:
    name: str
    api_key: str
    base_url: str
    api_type: APIType
    status: APIStatus = APIStatus.ACTIVE
    last_used: datetime = None
    error_count: int = 0
    no_credits_count: int = 0
    rate_limit_reset: datetime = None
    requests_made: int = 0
    max_requests_per_minute: int = 60
    last_error_message: str = ""
    blacklisted_until: datetime = None
    success_count: int = 0
    total_requests: int = 0

@dataclass
class APIRotationStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blacklisted_apis: int = 0
    active_apis: int = 0
    last_rotation_time: datetime = field(default_factory=datetime.now)

class IntelligentAPIRotationManager:
    """
    Sistema inteligente de rotação de APIs
    Detecta automaticamente APIs sem crédito e remove da rotação
    """
    
    def __init__(self):
        """Inicializa o gerenciador inteligente de rotação"""
        self.apis: Dict[str, List[APIEndpoint]] = {
            'serper': [],
            'jina': [],
            'exa': [],
            'firecrawl': [],
            'openrouter': [],
            'gemini': [],
            'openai': [],
            'deepseek': []
        }
        
        self.stats = APIRotationStats()
        self.lock = threading.Lock()
        
        # Configurações de detecção
        self.no_credits_keywords = [
            'quota', 'credit', 'insufficient', 'exceeded', 'limit',
            'billing', 'payment', 'subscription', 'balance', 'usage'
        ]
        
        self.error_keywords = [
            'unauthorized', 'forbidden', 'invalid', 'expired',
            'authentication', 'permission', 'access denied'
        ]
        
        # Configurações de blacklist
        self.max_no_credits_attempts = 3
        self.max_error_attempts = 5
        self.blacklist_duration_hours = 24
        
        # Carregar configurações
        self._load_api_configurations()
        
        # Iniciar thread de limpeza
        self._start_cleanup_thread()
        
        logger.info("🧠 Intelligent API Rotation Manager inicializado")
    
    def _load_api_configurations(self):
        """Carrega configurações de APIs do .env"""
        try:
            # Serper APIs
            serper_keys = [
                os.getenv('SERPER_API_KEY'),
                os.getenv('SERPER_API_KEY_1'),
                os.getenv('SERPER_API_KEY_2'),
                os.getenv('SERPER_API_KEY_3')
            ]
            
            for i, key in enumerate(serper_keys, 1):
                if key and key.strip():
                    self.apis['serper'].append(APIEndpoint(
                        name=f"serper_{i}",
                        api_key=key,
                        base_url="https://google.serper.dev",
                        api_type=APIType.SEARCH,
                        max_requests_per_minute=100
                    ))
            
            # Jina APIs
            jina_keys = [
                os.getenv('JINA_API_KEY'),
                os.getenv('JINA_API_KEY_1'),
                os.getenv('JINA_API_KEY_2'),
                os.getenv('JINA_API_KEY_3'),
                os.getenv('JINA_API_KEY_4')
            ]
            
            for i, key in enumerate(jina_keys, 1):
                if key and key.strip():
                    self.apis['jina'].append(APIEndpoint(
                        name=f"jina_{i}",
                        api_key=key,
                        base_url="https://r.jina.ai",
                        api_type=APIType.CONTENT_EXTRACTION,
                        max_requests_per_minute=200
                    ))
            
            # EXA APIs
            exa_keys = [
                os.getenv('EXA_API_KEY'),
                os.getenv('EXA_API_KEY_1')
            ]
            
            for i, key in enumerate(exa_keys, 1):
                if key and key.strip():
                    self.apis['exa'].append(APIEndpoint(
                        name=f"exa_{i}",
                        api_key=key,
                        base_url="https://api.exa.ai",
                        api_type=APIType.SEARCH,
                        max_requests_per_minute=100
                    ))
            
            # Firecrawl APIs
            firecrawl_keys = [
                os.getenv('FIRECRAWL_API_KEY'),
                os.getenv('FIRECRAWL_API_KEY_1'),
                os.getenv('FIRECRAWL_API_KEY_2')
            ]
            
            for i, key in enumerate(firecrawl_keys, 1):
                if key and key.strip():
                    self.apis['firecrawl'].append(APIEndpoint(
                        name=f"firecrawl_{i}",
                        api_key=key,
                        base_url="https://api.firecrawl.dev",
                        api_type=APIType.CONTENT_EXTRACTION,
                        max_requests_per_minute=50
                    ))
            
            # OpenRouter APIs
            openrouter_keys = [
                os.getenv('OPENROUTER_API_KEY'),
                os.getenv('OPENROUTER_API_KEY_1'),
                os.getenv('OPENROUTER_API_KEY_2')
            ]
            
            for i, key in enumerate(openrouter_keys, 1):
                if key and key.strip():
                    self.apis['openrouter'].append(APIEndpoint(
                        name=f"openrouter_{i}",
                        api_key=key,
                        base_url="https://openrouter.ai/api/v1",
                        api_type=APIType.AI_GENERATION,
                        max_requests_per_minute=100
                    ))
            
            # Gemini APIs
            gemini_keys = [
                os.getenv('GEMINI_API_KEY'),
                os.getenv('GEMINI_API_KEY_1'),
                os.getenv('GEMINI_API_KEY_2')
            ]
            
            for i, key in enumerate(gemini_keys, 1):
                if key and key.strip():
                    self.apis['gemini'].append(APIEndpoint(
                        name=f"gemini_{i}",
                        api_key=key,
                        base_url="https://generativelanguage.googleapis.com/v1beta",
                        api_type=APIType.AI_GENERATION,
                        max_requests_per_minute=60
                    ))
            
            # OpenAI API
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.apis['openai'].append(APIEndpoint(
                    name="openai_1",
                    api_key=openai_key,
                    base_url="https://api.openai.com/v1",
                    api_type=APIType.AI_GENERATION,
                    max_requests_per_minute=60
                ))
            
            # DeepSeek API
            deepseek_key = os.getenv('DEEPSEEK_API_KEY')
            if deepseek_key:
                self.apis['deepseek'].append(APIEndpoint(
                    name="deepseek_1",
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com",
                    api_type=APIType.AI_GENERATION,
                    max_requests_per_minute=60
                ))
            
            # Atualizar estatísticas
            self._update_stats()
            
            logger.info(f"✅ APIs carregadas: {self._get_total_active_apis()} ativas")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configurações de API: {e}")
    
    def get_next_api(self, api_type: str, exclude_blacklisted: bool = True) -> Optional[APIEndpoint]:
        """
        Obtém próxima API disponível do tipo especificado
        
        Args:
            api_type: Tipo de API (serper, jina, etc.)
            exclude_blacklisted: Se deve excluir APIs blacklistadas
        """
        with self.lock:
            if api_type not in self.apis:
                logger.warning(f"⚠️ Tipo de API não encontrado: {api_type}")
                return None
            
            available_apis = []
            
            for api in self.apis[api_type]:
                # Verificar se API está blacklistada
                if exclude_blacklisted and self._is_blacklisted(api):
                    continue
                
                # Verificar se API está ativa
                if api.status in [APIStatus.ACTIVE, APIStatus.RATE_LIMITED]:
                    # Verificar rate limit
                    if self._check_rate_limit(api):
                        available_apis.append(api)
            
            if not available_apis:
                logger.warning(f"⚠️ Nenhuma API {api_type} disponível")
                return None
            
            # Selecionar API com menor uso recente
            selected_api = min(available_apis, key=lambda x: x.requests_made)
            
            # Atualizar estatísticas
            selected_api.last_used = datetime.now()
            selected_api.requests_made += 1
            selected_api.total_requests += 1
            
            logger.debug(f"🔄 API selecionada: {selected_api.name}")
            
            return selected_api
    
    def report_api_result(
        self,
        api: APIEndpoint,
        success: bool,
        error_message: str = "",
        response_data: Optional[Dict[str, Any]] = None
    ):
        """
        Reporta resultado de uso da API para análise inteligente
        
        Args:
            api: Endpoint da API usado
            success: Se a requisição foi bem-sucedida
            error_message: Mensagem de erro (se houver)
            response_data: Dados da resposta (para análise)
        """
        with self.lock:
            if success:
                api.success_count += 1
                api.error_count = 0  # Reset contador de erro
                api.no_credits_count = 0  # Reset contador de créditos
                api.status = APIStatus.ACTIVE
                self.stats.successful_requests += 1
                
                logger.debug(f"✅ API {api.name} - Sucesso")
                
            else:
                api.error_count += 1
                api.last_error_message = error_message
                self.stats.failed_requests += 1
                
                # Analisar tipo de erro
                error_type = self._analyze_error(error_message, response_data)
                
                if error_type == "no_credits":
                    api.no_credits_count += 1
                    logger.warning(f"💳 API {api.name} - Sem créditos ({api.no_credits_count}/{self.max_no_credits_attempts})")
                    
                    # Blacklistar se exceder limite
                    if api.no_credits_count >= self.max_no_credits_attempts:
                        self._blacklist_api(api, "Sem créditos")
                        
                elif error_type == "auth_error":
                    logger.error(f"🔐 API {api.name} - Erro de autenticação")
                    self._blacklist_api(api, "Erro de autenticação")
                    
                elif error_type == "rate_limit":
                    api.status = APIStatus.RATE_LIMITED
                    api.rate_limit_reset = datetime.now() + timedelta(minutes=5)
                    logger.warning(f"⏱️ API {api.name} - Rate limit")
                    
                else:
                    # Erro genérico
                    logger.error(f"❌ API {api.name} - Erro: {error_message}")
                    
                    # Blacklistar se muitos erros
                    if api.error_count >= self.max_error_attempts:
                        self._blacklist_api(api, f"Muitos erros ({api.error_count})")
            
            self.stats.total_requests += 1
            self._update_stats()
    
    def _analyze_error(self, error_message: str, response_data: Optional[Dict[str, Any]]) -> str:
        """Analisa mensagem de erro para determinar tipo"""
        
        error_lower = error_message.lower()
        
        # Verificar se é erro de créditos/quota
        for keyword in self.no_credits_keywords:
            if keyword in error_lower:
                return "no_credits"
        
        # Verificar se é erro de autenticação
        for keyword in self.error_keywords:
            if keyword in error_lower:
                return "auth_error"
        
        # Verificar códigos de status específicos
        if response_data:
            status_code = response_data.get('status_code', 0)
            if status_code == 429:
                return "rate_limit"
            elif status_code in [401, 403]:
                return "auth_error"
            elif status_code == 402:
                return "no_credits"
        
        # Verificar padrões específicos de APIs
        if "429" in error_message or "rate limit" in error_lower:
            return "rate_limit"
        
        return "generic_error"
    
    def _blacklist_api(self, api: APIEndpoint, reason: str):
        """Blacklista uma API por período determinado"""
        
        api.status = APIStatus.BLACKLISTED
        api.blacklisted_until = datetime.now() + timedelta(hours=self.blacklist_duration_hours)
        
        logger.warning(f"🚫 API {api.name} blacklistada por {self.blacklist_duration_hours}h - Razão: {reason}")
        
        # Salvar informação de blacklist
        self._save_blacklist_info(api, reason)
        
        self.stats.blacklisted_apis += 1
    
    def _is_blacklisted(self, api: APIEndpoint) -> bool:
        """Verifica se API está blacklistada"""
        
        if api.status != APIStatus.BLACKLISTED:
            return False
        
        if api.blacklisted_until and datetime.now() > api.blacklisted_until:
            # Remover da blacklist
            api.status = APIStatus.ACTIVE
            api.blacklisted_until = None
            api.error_count = 0
            api.no_credits_count = 0
            
            logger.info(f"✅ API {api.name} removida da blacklist")
            return False
        
        return True
    
    def _check_rate_limit(self, api: APIEndpoint) -> bool:
        """Verifica se API está dentro do rate limit"""
        
        if api.rate_limit_reset and datetime.now() < api.rate_limit_reset:
            return False
        
        # Reset rate limit se passou o tempo
        if api.rate_limit_reset and datetime.now() >= api.rate_limit_reset:
            api.status = APIStatus.ACTIVE
            api.rate_limit_reset = None
        
        return True
    
    def _save_blacklist_info(self, api: APIEndpoint, reason: str):
        """Salva informações de blacklist para análise"""
        
        try:
            blacklist_dir = Path("logs/api_blacklist")
            blacklist_dir.mkdir(parents=True, exist_ok=True)
            
            blacklist_file = blacklist_dir / f"{api.name}_blacklist.json"
            
            blacklist_data = {
                'api_name': api.name,
                'reason': reason,
                'blacklisted_at': datetime.now().isoformat(),
                'blacklisted_until': api.blacklisted_until.isoformat() if api.blacklisted_until else None,
                'error_count': api.error_count,
                'no_credits_count': api.no_credits_count,
                'last_error_message': api.last_error_message,
                'total_requests': api.total_requests,
                'success_count': api.success_count
            }
            
            with open(blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(blacklist_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erro ao salvar info de blacklist: {e}")
    
    def _update_stats(self):
        """Atualiza estatísticas gerais"""
        
        self.stats.active_apis = self._get_total_active_apis()
        self.stats.last_rotation_time = datetime.now()
    
    def _get_total_active_apis(self) -> int:
        """Conta total de APIs ativas"""
        
        total = 0
        for api_list in self.apis.values():
            for api in api_list:
                if not self._is_blacklisted(api):
                    total += 1
        return total
    
    def _start_cleanup_thread(self):
        """Inicia thread de limpeza periódica"""
        
        def cleanup_worker():
            while True:
                try:
                    # Limpar blacklists expiradas
                    self._cleanup_expired_blacklists()
                    
                    # Reset contadores diários
                    self._reset_daily_counters()
                    
                    # Aguardar 1 hora
                    threading.Event().wait(3600)
                    
                except Exception as e:
                    logger.error(f"❌ Erro na thread de limpeza: {e}")
                    threading.Event().wait(300)  # Aguardar 5 min em caso de erro
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        
        logger.info("🧹 Thread de limpeza iniciada")
    
    def _cleanup_expired_blacklists(self):
        """Remove blacklists expiradas"""
        
        with self.lock:
            cleaned_count = 0
            
            for api_list in self.apis.values():
                for api in api_list:
                    if self._is_blacklisted(api):
                        # _is_blacklisted já remove se expirou
                        pass
                    elif api.status == APIStatus.BLACKLISTED and not api.blacklisted_until:
                        # Blacklist sem tempo definido - remover
                        api.status = APIStatus.ACTIVE
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 {cleaned_count} APIs removidas da blacklist")
    
    def _reset_daily_counters(self):
        """Reset contadores diários"""
        
        now = datetime.now()
        if now.hour == 0 and now.minute < 5:  # Reset às 00:00-00:05
            with self.lock:
                for api_list in self.apis.values():
                    for api in api_list:
                        api.requests_made = 0
                
                logger.info("🔄 Contadores diários resetados")
    
    def get_rotation_status(self) -> Dict[str, Any]:
        """Retorna status completo da rotação"""
        
        with self.lock:
            status = {
                'stats': {
                    'total_requests': self.stats.total_requests,
                    'successful_requests': self.stats.successful_requests,
                    'failed_requests': self.stats.failed_requests,
                    'success_rate': (self.stats.successful_requests / max(self.stats.total_requests, 1)) * 100,
                    'active_apis': self.stats.active_apis,
                    'blacklisted_apis': self.stats.blacklisted_apis,
                    'last_rotation_time': self.stats.last_rotation_time.isoformat()
                },
                'apis': {}
            }
            
            for api_type, api_list in self.apis.items():
                status['apis'][api_type] = []
                
                for api in api_list:
                    api_status = {
                        'name': api.name,
                        'status': api.status.value,
                        'total_requests': api.total_requests,
                        'success_count': api.success_count,
                        'error_count': api.error_count,
                        'no_credits_count': api.no_credits_count,
                        'success_rate': (api.success_count / max(api.total_requests, 1)) * 100,
                        'last_used': api.last_used.isoformat() if api.last_used else None,
                        'blacklisted_until': api.blacklisted_until.isoformat() if api.blacklisted_until else None,
                        'last_error': api.last_error_message
                    }
                    
                    status['apis'][api_type].append(api_status)
            
            return status
    
    def force_unblacklist_api(self, api_name: str) -> bool:
        """Força remoção de API da blacklist"""
        
        with self.lock:
            for api_list in self.apis.values():
                for api in api_list:
                    if api.name == api_name:
                        if api.status == APIStatus.BLACKLISTED:
                            api.status = APIStatus.ACTIVE
                            api.blacklisted_until = None
                            api.error_count = 0
                            api.no_credits_count = 0
                            
                            logger.info(f"✅ API {api_name} forçadamente removida da blacklist")
                            return True
                        else:
                            logger.warning(f"⚠️ API {api_name} não está blacklistada")
                            return False
            
            logger.error(f"❌ API {api_name} não encontrada")
            return False

# Instância global do gerenciador
intelligent_api_rotation_manager = IntelligentAPIRotationManager()