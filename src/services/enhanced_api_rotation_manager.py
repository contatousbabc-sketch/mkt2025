"""
Sistema Avançado de Rotação de APIs - V3.0
Garante alta disponibilidade com fallback automático entre múltiplas APIs
ATUALIZADO: Implementa fallbacks Jina->EXA, Qwen->Gemini, Supadata para insights sociais
"""

import os
import time
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import threading
import requests
import asyncio
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

# Now safely log the aiohttp warning if it wasn't available
if not AIOHTTP_AVAILABLE:
    logger.warning("aiohttp não instalado – usando fallback síncrono com requests")

class APIStatus(Enum):
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class APIEndpoint:
    name: str
    api_key: str
    base_url: str
    status: APIStatus = APIStatus.ACTIVE
    last_used: datetime = None
    error_count: int = 0
    rate_limit_reset: datetime = None
    requests_made: int = 0
    max_requests_per_minute: int = 60

class EnhancedAPIRotationManager:
    """
    Gerenciador avançado de rotação de APIs com:
    - Fallback automático entre modelos
    - Rate limiting inteligente
    - Health checking
    - Balanceamento de carga
    """
    
    def __init__(self):
        self.apis = {
            'qwen': [],
            'gemini': [],
            'groq': [],
            'openai': [],
            'deepseek': [],
            'jina': [],
            'exa': [],
            'serper': [],
            'serpapi': [],
            'tavily': [],
            'supadata': [],
            'firecrawl': [],
            'scrapingant': [],
            'youtube': [],
            'rapidapi': [],
            'apify': []  # Adicionado Apify
        }
        
        # Definir cadeias de fallback (cada grupo é uma prioridade)
        self.fallback_chains = {
            'ai_models': [['qwen'], ['gemini'], ['openai'], ['groq'], ['deepseek']],
            'ai_generation': [['qwen'], ['gemini'], ['openai'], ['groq'], ['deepseek']],
            'search': [['jina'], ['exa'], ['serper'], ['serpapi'], ['firecrawl'], ['tavily'], ['apify']],
            'social_insights': [['supadata'], ['apify'], ['serper'], ['serpapi'], ['firecrawl'], ['tavily']],
            'web_scraping': [['firecrawl'], ['apify'], ['scrapingant'], ['jina'], ['serper'], ['serpapi']],
            'content_extraction': [['firecrawl'], ['jina'], ['apify'], ['scrapingant'], ['serper'], ['rapidapi']],
            'url_analysis': [['firecrawl'], ['jina'], ['exa'], ['apify'], ['serper'], ['serpapi']]
        }
        self.current_api_index = {}
        self.lock = threading.Lock()
        self.health_check_interval = 300  # 5 minutos
        self.last_health_check = {}
        
        self._load_api_configurations()
        self._initialize_health_monitoring()
    
    def _load_api_configurations(self):
        """Carrega configurações de APIs do .env"""
        try:
            # OpenRouter - Usar as chaves reais do .env na ordem correta
            openrouter_keys = [
                os.getenv('OPENROUTER_API_KEY'),
                os.getenv('OPENROUTER_API_KEY_1'), 
                os.getenv('OPENROUTER_API_KEY_2')
            ]
            
            for i, key in enumerate(openrouter_keys, 1):
                if key and key.strip():
                    self.apis['qwen'].append(APIEndpoint(
                        name=f"openrouter_{i}",
                        api_key=key,
                        base_url='https://openrouter.ai/api/v1',
                        max_requests_per_minute=100
                    ))
                    logger.info(f"✅ OpenRouter API {i} carregada")
            
            # Gemini - Usar as chaves reais do .env
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
                        max_requests_per_minute=60
                    ))
                    logger.info(f"✅ Gemini API {i} carregada")
            
            # OpenAI
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.apis['openai'].append(APIEndpoint(
                    name="openai_1",
                    api_key=openai_key,
                    base_url="https://api.openai.com/v1",
                    max_requests_per_minute=60
                ))
            
            # DeepSeek
            deepseek_key = os.getenv('DEEPSEEK_API_KEY')
            if deepseek_key:
                self.apis['deepseek'].append(APIEndpoint(
                    name="deepseek_1",
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com",
                    max_requests_per_minute=60
                ))
            
            # Jina AI - Primário para busca - TODAS as chaves do .env
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
                        max_requests_per_minute=200
                    ))
                    logger.info(f"✅ Jina API {i} carregada")
            
            # EXA - Fallback para Jina
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
                        max_requests_per_minute=100
                    ))
                    logger.info(f"✅ EXA API {i} carregada")
            
            # Serper - Apenas chaves válidas (testadas em 2025-09-21)
            # ✅ Usando apenas a chave principal que tem créditos
            serper_key = os.getenv('SERPER_API_KEY')
            if serper_key and serper_key.strip():
                # Verifica se a chave tem créditos antes de adicionar
                if self._test_serper_key(serper_key):
                    self.apis['serper'].append(APIEndpoint(
                        name="serper_main",
                        api_key=serper_key,
                        base_url="https://google.serper.dev",
                        max_requests_per_minute=100
                    ))
                    logger.info("✅ Serper API principal carregada e validada")
                else:
                    logger.warning("⚠️ Serper API principal sem créditos - removida da rotação")
            
            # SerpAPI - Nova adição para busca Google
            serpapi_keys = [
                os.getenv('SERP_API_KEY'),
                os.getenv('SERP_API_KEY_1')
            ]
            
            for i, key in enumerate(serpapi_keys, 1):
                if key and key.strip():
                    self.apis['serpapi'].append(APIEndpoint(
                        name=f"serpapi_{i}",
                        api_key=key,
                        base_url="https://serpapi.com",
                        max_requests_per_minute=100
                    ))
                    logger.info(f"✅ SerpAPI {i} carregada")
            
            # Supadata - Para insights de redes sociais
            supadata_keys = [
                os.getenv('SUPADATA_API_KEY'),
                os.getenv('SUPADATA_API_KEY_1')
            ]
            
            for i, key in enumerate(supadata_keys, 1):
                if key and key.strip():
                    self.apis['supadata'].append(APIEndpoint(
                        name=f"supadata_{i}",
                        api_key=key,
                        base_url=os.getenv('SUPADATA_API_URL', 'https://api.supadata.ai/v1'),
                        max_requests_per_minute=50
                    ))
                    logger.info(f"✅ Supadata API {i} carregada")
            
            # Groq
            groq_keys = [
                os.getenv('GROQ_API_KEY'),
                os.getenv('GROQ_API_KEY_1')
            ]
            
            for i, key in enumerate(groq_keys, 1):
                if key and key.strip():
                    self.apis['groq'].append(APIEndpoint(
                        name=f"groq_{i}",
                        api_key=key,
                        base_url="https://api.groq.com/openai/v1",
                        max_requests_per_minute=30
                    ))
                    logger.info(f"✅ Groq API {i} carregada")
            
            # Tavily
            tavily_key = os.getenv('TAVILY_API_KEY')
            if tavily_key:
                self.apis['tavily'].append(APIEndpoint(
                    name="tavily_1",
                    api_key=tavily_key,
                    base_url="https://api.tavily.com",
                    max_requests_per_minute=100
                ))
            
            # Firecrawl - TODAS as chaves do .env
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
                        max_requests_per_minute=60
                    ))
                    logger.info(f"✅ Firecrawl API {i} carregada")
            
            # ScrapingAnt
            scrapingant_key = os.getenv('SCRAPINGANT_API_KEY')
            if scrapingant_key:
                self.apis['scrapingant'].append(APIEndpoint(
                    name="scrapingant_1",
                    api_key=scrapingant_key,
                    base_url="https://api.scrapingant.com",
                    max_requests_per_minute=60
                ))
            
            # YouTube
            youtube_key = os.getenv('YOUTUBE_API_KEY')
            if youtube_key:
                self.apis['youtube'].append(APIEndpoint(
                    name="youtube_1",
                    api_key=youtube_key,
                    base_url="https://www.googleapis.com/youtube/v3",
                    max_requests_per_minute=100
                ))
            
            # RapidAPI - Para APIs múltiplas
            rapidapi_key = os.getenv('RAPIDAPI_KEY')
            if rapidapi_key:
                self.apis['rapidapi'].append(APIEndpoint(
                    name="rapidapi_1",
                    api_key=rapidapi_key,
                    base_url="https://rapidapi.com",
                    max_requests_per_minute=200
                ))
                logger.info("✅ RapidAPI carregada")
            
            # Apify - TODAS as chaves do .env
            apify_keys = [
                os.getenv('APIFY_API_KEY'),
                os.getenv('APIFY_API_KEY_1'),
                os.getenv('APIFY_API_KEY_2'),
                os.getenv('APIFY_API_KEY_3')
            ]
            
            for i, key in enumerate(apify_keys, 1):
                if key and key.strip():
                    self.apis.setdefault('apify', []).append(APIEndpoint(
                        name=f"apify_{i}",
                        api_key=key,
                        base_url="https://api.apify.com/v2",
                        max_requests_per_minute=100
                    ))
                    logger.info(f"✅ Apify API {i} carregada")
            
            # Inicializar índices
            for service in self.apis:
                self.current_api_index[service] = 0
                
            total_apis = sum(len(apis) for apis in self.apis.values())
            logger.info(f"✅ APIs carregadas: {total_apis} endpoints")
            
            # Log detalhado das APIs carregadas
            for service, apis in self.apis.items():
                if apis:
                    logger.info(f"  - {service}: {len(apis)} APIs")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar configurações de API: {e}")
    
    def _get_base_url(self, service: str) -> str:
        """Retorna URL base para cada serviço"""
        urls = {
            'tavily': 'https://api.tavily.com',
            'exa': 'https://api.exa.ai',
            'serpapi': 'https://serpapi.com/search',
            'rapidapi': 'https://rapidapi.com',
            'serper': 'https://google.serper.dev'
        }
        return urls.get(service, '')
    
    def _initialize_health_monitoring(self):
        """Inicializa monitoramento de saúde das APIs"""
        for service in self.apis:
            self.last_health_check[service] = datetime.now() - timedelta(minutes=10)
    
    def _test_serper_key(self, api_key: str) -> bool:
        """
        Testa se uma chave Serper tem créditos disponíveis
        Retorna True se a chave funciona, False caso contrário
        """
        try:
            response = requests.post(
                'https://google.serper.dev/search',
                headers={'X-API-KEY': api_key, 'Content-Type': 'application/json'},
                json={'q': 'test'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Chave Serper validada com sucesso")
                return True
            elif response.status_code == 400:
                error_msg = response.text
                if "Not enough credits" in error_msg:
                    logger.warning(f"❌ Chave Serper sem créditos: {error_msg}")
                else:
                    logger.warning(f"❌ Chave Serper inválida: {error_msg}")
                return False
            else:
                logger.warning(f"❌ Chave Serper erro {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar chave Serper: {str(e)}")
            return False
    
    def get_active_api(self, service: str, force_check: bool = False) -> Optional[APIEndpoint]:
        """
        Retorna API ativa para o serviço especificado com rotação automática
        """
        with self.lock:
            if service not in self.apis or not self.apis[service]:
                logger.warning(f"⚠️ Nenhuma API disponível para {service}")
                return None
            
            # Health check se necessário
            if force_check or self._needs_health_check(service):
                self._perform_health_check(service)
            
            # Encontrar API ativa com rotação automática
            apis = self.apis[service]
            start_index = self.current_api_index[service]
            
            # Verificar se a API atual está disponível
            current_api = apis[start_index]
            if self._is_api_available(current_api):
                current_api.last_used = datetime.now()
                current_api.requests_made += 1
                logger.info(f"🔄 Continuando com API {current_api.name} para {service}")
                return current_api
            
            # Se API atual não está disponível, rotar automaticamente
            logger.info(f"🔄 API atual indisponível, rotacionando {service}...")
            for i in range(1, len(apis)):  # Começar da próxima API
                index = (start_index + i) % len(apis)
                api = apis[index]
                
                if self._is_api_available(api):
                    self.current_api_index[service] = index
                    api.last_used = datetime.now()
                    api.requests_made += 1
                    logger.info(f"✅ Rotação automática: API {api.name} para {service}")
                    return api
            
            logger.error(f"❌ Nenhuma API disponível para {service} após rotação")
            return None
    
    def _needs_health_check(self, service: str) -> bool:
        """Verifica se precisa fazer health check"""
        last_check = self.last_health_check.get(service)
        if not last_check:
            return True
        return datetime.now() - last_check > timedelta(seconds=self.health_check_interval)
    
    def _perform_health_check(self, service: str):
        """Executa health check nas APIs do serviço"""
        try:
            for api in self.apis[service]:
                if api.status == APIStatus.OFFLINE:
                    continue
                
                # Reset rate limit se expirou
                if api.rate_limit_reset and datetime.now() > api.rate_limit_reset:
                    api.status = APIStatus.ACTIVE
                    api.rate_limit_reset = None
                    api.requests_made = 0
                
                # Verificar se está rate limited
                if api.requests_made >= api.max_requests_per_minute:
                    api.status = APIStatus.RATE_LIMITED
                    api.rate_limit_reset = datetime.now() + timedelta(minutes=1)
            
            self.last_health_check[service] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Erro no health check de {service}: {e}")
    
    def _is_api_available(self, api: APIEndpoint) -> bool:
        """Verifica se API está disponível para uso"""
        if api.status == APIStatus.OFFLINE:
            return False
        
        if api.status == APIStatus.RATE_LIMITED:
            if api.rate_limit_reset and datetime.now() > api.rate_limit_reset:
                api.status = APIStatus.ACTIVE
                api.requests_made = 0
                return True
            return False
        
        if api.status == APIStatus.ERROR and api.error_count > 5:
            return False
        
        return True
    
    def mark_api_error(self, service: str, api_name: str, error: Exception):
        """Marca API como com erro e força rotação imediata"""
        with self.lock:
            for i, api in enumerate(self.apis[service]):
                if api.name == api_name:
                    api.error_count += 1
                    
                    # ROTAÇÃO INTELIGENTE: Diferentes estratégias baseadas no tipo de erro
                    error_str = str(error).lower()
                    
                    if "rate limit" in error_str or "429" in error_str:
                        # Rate limit: marcar como rate limited por 1 minuto
                        api.status = APIStatus.RATE_LIMITED
                        api.rate_limit_reset = datetime.now() + timedelta(minutes=1)
                        logger.warning(f"⚠️ API {api_name} rate limited - aguardando 1 minuto")
                    elif "credits" in error_str or "quota" in error_str or "billing" in error_str:
                        # Sem créditos: marcar como offline permanentemente
                        api.status = APIStatus.OFFLINE
                        logger.error(f"❌ API {api_name} sem créditos - marcada como OFFLINE")
                    elif "401" in error_str or "403" in error_str or "unauthorized" in error_str:
                        # Erro de autenticação: marcar como offline
                        api.status = APIStatus.OFFLINE
                        logger.error(f"❌ API {api_name} erro de autenticação - marcada como OFFLINE")
                    else:
                        # Erro temporário: marcar como erro mas permitir retry
                        api.status = APIStatus.ERROR
                        logger.warning(f"⚠️ API {api_name} erro temporário - tentará novamente")
                    
                    # Forçar rotação IMEDIATA para próxima API disponível
                    if len(self.apis[service]) > 1:
                        # Encontrar próxima API ativa
                        next_api_found = False
                        for j in range(1, len(self.apis[service])):
                            next_index = (i + j) % len(self.apis[service])
                            next_api = self.apis[service][next_index]
                            
                            # Verificar se a próxima API está disponível
                            if self._is_api_available(next_api) or next_api.status != APIStatus.ERROR:
                                self.current_api_index[service] = next_index
                                logger.info(f"🔄 ROTAÇÃO AUTOMÁTICA: {service} → {next_api.name}")
                                next_api_found = True
                                break
                        
                        if not next_api_found:
                            logger.error(f"❌ Nenhuma API alternativa disponível para {service}")
                    
                    # Recuperação mais rápida - 1 minuto para tentar novamente
                    self._schedule_api_recovery(service, api_name, recovery_time=60)
                    break
    
    def _schedule_api_recovery(self, service: str, api_name: str, recovery_time: int = 60):
        """Agenda recuperação automática da API após período de cooldown"""
        def recover_api():
            time.sleep(recovery_time)  # Cooldown configurável (padrão 1 minuto)
            with self.lock:
                for api in self.apis[service]:
                    if api.name == api_name:
                        api.status = APIStatus.ACTIVE
                        api.error_count = 0
                        logger.info(f"✅ API {api_name} RECUPERADA automaticamente após {recovery_time}s")
                        break
        
        import threading
        threading.Thread(target=recover_api, daemon=True).start()
        logger.info(f"⏱️ Recuperação de {api_name} agendada para {recovery_time} segundos")
    
    def mark_api_rate_limited(self, service: str, api_name: str, reset_time: Optional[datetime] = None):
        """Marca API como rate limited"""
        with self.lock:
            for api in self.apis[service]:
                if api.name == api_name:
                    api.status = APIStatus.RATE_LIMITED
                    api.rate_limit_reset = reset_time or (datetime.now() + timedelta(minutes=1))
                    logger.warning(f"⚠️ API {api_name} rate limited até {api.rate_limit_reset}")
                    break
    
    def get_fallback_api(self, service_type: str, failed_service: str = None) -> Optional[APIEndpoint]:
        """
        Retorna API de fallback baseada nas cadeias configuradas
        """
        if service_type not in self.fallback_chains:
            logger.warning(f"⚠️ Tipo de serviço desconhecido: {service_type}")
            return None
        
        chain = self.fallback_chains[service_type]
        
        # Se um serviço específico falhou, começar do próximo na cadeia
        start_index = 0
        if failed_service:
            for i, services in enumerate(chain):
                if failed_service in services:
                    start_index = i + 1
                    break
        
        # Percorrer cadeia de fallback a partir do índice calculado
        for i in range(start_index, len(chain)):
            for service_name in chain[i]:
                if service_name in self.apis and self.apis[service_name]:
                    # Usar get_active_api para obter API disponível
                    api = self.get_active_api(service_name)
                    if api:
                        logger.info(f"🔄 Fallback para {service_name} (tipo: {service_type})")
                        return api
        
        logger.error(f"❌ Nenhum fallback disponível para {service_type}")
        return None

    def get_api_with_fallback(self, service_type: str) -> Optional[APIEndpoint]:
        """
        Obtém API com fallback automático
        """
        # Tentar obter API primária
        api = self.get_active_api_by_type(service_type)
        if api:
            return api
        
        # Se falhou, tentar fallback
        return self.get_fallback_api(service_type)
    
    def get_best_api_for_load_balancing(self, service: str) -> Optional[APIEndpoint]:
        """
        NOVO: Balanceamento de carga inteligente
        Seleciona a API com menor carga atual para distribuir requisições
        """
        with self.lock:
            if service not in self.apis or not self.apis[service]:
                return None
            
            available_apis = [api for api in self.apis[service] if self._is_api_available(api)]
            
            if not available_apis:
                logger.warning(f"⚠️ Nenhuma API disponível para balanceamento em {service}")
                return None
            
            # Calcular score de carga para cada API (menor é melhor)
            def calculate_load_score(api: APIEndpoint) -> float:
                score = 0.0
                
                # Penalizar por número de requisições recentes
                score += api.requests_made * 0.1
                
                # Penalizar por erros recentes
                score += api.error_count * 0.5
                
                # Bonificar APIs que não foram usadas recentemente
                if api.last_used:
                    minutes_since_use = (datetime.now() - api.last_used).total_seconds() / 60
                    score -= minutes_since_use * 0.05  # Bonus por descanso
                
                # Penalizar se está próximo do rate limit
                if api.requests_made > (api.max_requests_per_minute * 0.8):
                    score += 2.0  # Penalidade alta se próximo do limite
                
                return score
            
            # Selecionar API com menor score (menor carga)
            best_api = min(available_apis, key=calculate_load_score)
            
            # Atualizar estatísticas
            best_api.last_used = datetime.now()
            best_api.requests_made += 1
            
            # Atualizar índice atual para essa API
            for i, api in enumerate(self.apis[service]):
                if api.name == best_api.name:
                    self.current_api_index[service] = i
                    break
            
            logger.info(f"⚖️ Balanceamento: {best_api.name} selecionada para {service} (carga: {calculate_load_score(best_api):.2f})")
            return best_api
    
    def get_api_statistics(self, service: str = None) -> Dict[str, Any]:
        """
        NOVO: Retorna estatísticas detalhadas das APIs
        """
        stats = {}
        
        services_to_check = [service] if service else self.apis.keys()
        
        for svc in services_to_check:
            if svc not in self.apis:
                continue
                
            svc_stats = {
                'total_apis': len(self.apis[svc]),
                'active_apis': len([api for api in self.apis[svc] if api.status == APIStatus.ACTIVE]),
                'rate_limited_apis': len([api for api in self.apis[svc] if api.status == APIStatus.RATE_LIMITED]),
                'error_apis': len([api for api in self.apis[svc] if api.status == APIStatus.ERROR]),
                'offline_apis': len([api for api in self.apis[svc] if api.status == APIStatus.OFFLINE]),
                'total_requests': sum(api.requests_made for api in self.apis[svc]),
                'total_errors': sum(api.error_count for api in self.apis[svc]),
                'apis_detail': []
            }
            
            for api in self.apis[svc]:
                api_detail = {
                    'name': api.name,
                    'status': api.status.value,
                    'requests_made': api.requests_made,
                    'error_count': api.error_count,
                    'last_used': api.last_used.isoformat() if api.last_used else None,
                    'rate_limit_reset': api.rate_limit_reset.isoformat() if api.rate_limit_reset else None
                }
                svc_stats['apis_detail'].append(api_detail)
            
            stats[svc] = svc_stats
        
        return stats
    
    def get_fallback_model(self, model_name: str) -> tuple[str, Optional[APIEndpoint]]:
        """
        Método de compatibilidade para get_fallback_model
        Retorna tupla (model_name, api_endpoint)
        """
        # Mapear nomes de modelos para tipos de serviço
        model_to_service = {
            'qwen': 'ai_generation',
            'gpt': 'ai_generation', 
            'claude': 'ai_generation',
            'gemini': 'ai_generation',
            'llama': 'ai_generation'
        }
        
        service_type = model_to_service.get(model_name, 'ai_generation')
        api = self.get_api_with_fallback(service_type)
        
        if api:
            logger.info(f"✅ Fallback model encontrado: {model_name} via {api.name}")
            return model_name, api
        else:
            logger.warning(f"⚠️ Nenhuma API disponível para {model_name}")
            return model_name, None

    def get_active_api_by_type(self, service_type: str) -> Optional[APIEndpoint]:
        """
        Obtém API ativa baseada no tipo de serviço
        """
        if service_type not in self.fallback_chains:
            return None
        
        # Tentar primeiro serviço da cadeia
        primary_services = self.fallback_chains[service_type][0]
        
        for service_name in primary_services:
            if service_name in self.apis and self.apis[service_name]:
                # Usar o método get_active_api existente
                api = self.get_active_api(service_name)
                if api:
                    return api
        
        return None
    
    def get_api_status_report(self) -> Dict[str, Any]:
        """Retorna relatório de status das APIs"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for service, apis in self.apis.items():
            service_status = {
                'total_apis': len(apis),
                'active': 0,
                'rate_limited': 0,
                'error': 0,
                'offline': 0,
                'apis': []
            }
            
            for api in apis:
                service_status[api.status.value] += 1
                service_status['apis'].append({
                    'name': api.name,
                    'status': api.status.value,
                    'error_count': api.error_count,
                    'requests_made': api.requests_made,
                    'last_used': api.last_used.isoformat() if api.last_used else None
                })
            
            report['services'][service] = service_status
        
        return report
    
    def reset_api_errors(self, service: str = None):
        """Reset contadores de erro"""
        services_to_reset = [service] if service else self.apis.keys()
        
        for svc in services_to_reset:
            for api in self.apis[svc]:
                api.error_count = 0
                if api.status == APIStatus.ERROR:
                    api.status = APIStatus.ACTIVE
        
        logger.info(f"✅ Erros resetados para: {', '.join(services_to_reset)}")

# Instância global
api_rotation_manager = EnhancedAPIRotationManager()

def get_api_manager() -> EnhancedAPIRotationManager:
    """Retorna instância do gerenciador de APIs"""
    return api_rotation_manager