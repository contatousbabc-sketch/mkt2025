#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced AI Manager
Gerenciador de IA com hierarquia OpenRouter: Grok-4 → Gemini-2.0 e fallbacks robustos
ZERO SIMULAÇÃO - Apenas modelos reais funcionais
"""

import os
import logging
import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedAIManager:
    """Gerenciador de IA aprimorado com hierarquia OpenRouter e fallbacks"""

    def __init__(self):
        """Inicializa o gerenciador aprimorado com hierarquia OpenRouter"""
        # Carregar chaves OpenRouter
        self.openrouter_keys = self._load_openrouter_keys()
        self.current_key_index = 0
        
        # Carregar chaves Gemini para fallback
        self.gemini_keys = self._load_gemini_keys()
        self.current_gemini_key_index = 0
        
        # Configurar hierarquia de modelos
        self.model_hierarchy = [
            {
                'name': 'x-ai/grok-4-fast:free',
                'provider': 'openrouter',
                'priority': 1,
                'max_tokens': 4000,
                'temperature': 0.7
            },
            {
                'name': 'google/gemini-2.0-flash-exp:free',
                'provider': 'openrouter',
                'priority': 2,
                'max_tokens': 8000,
                'temperature': 0.7
            },
            {
                'name': 'gemini-2.0-flash-exp',
                'provider': 'gemini_direct',
                'priority': 3,
                'max_tokens': 4000,
                'temperature': 0.7
            }
        ]
        
        self.search_orchestrator = None
        
        # Importar search orchestrator se disponível
        try:
            from .real_search_orchestrator import RealSearchOrchestrator
            self.search_orchestrator = RealSearchOrchestrator()
            logger.info("✅ Search Orchestrator carregado")
        except ImportError:
            logger.warning("⚠️ Search Orchestrator não disponível")

        logger.info("🤖 Enhanced AI Manager inicializado com hierarquia Grok-4 → Gemini-2.0")
        logger.info(f"🔑 {len(self.openrouter_keys)} chaves OpenRouter carregadas")
        logger.info(f"🔑 {len(self.gemini_keys)} chaves Gemini carregadas")
    
    def _load_openrouter_keys(self) -> List[str]:
        """Carrega múltiplas chaves OpenRouter"""
        keys = []
        
        # Chave principal
        main_key = os.getenv('OPENROUTER_API_KEY')
        if main_key and main_key.strip():
            keys.append(main_key.strip())
            
        # Chaves numeradas
        for i in range(1, 6):
            key = os.getenv(f'OPENROUTER_API_KEY_{i}')
            if key and key.strip():
                keys.append(key.strip())
                
        logger.info(f"✅ {len(keys)} chaves OpenRouter carregadas")
        return keys
    
    def _load_gemini_keys(self) -> List[str]:
        """Carrega múltiplas chaves Gemini"""
        keys = []
        
        # Chave principal
        main_key = os.getenv('GEMINI_API_KEY')
        if main_key and main_key.strip():
            keys.append(main_key.strip())
            
        # Chaves numeradas
        for i in range(1, 4):
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key and key.strip():
                keys.append(key.strip())
                
        logger.info(f"✅ {len(keys)} chaves Gemini carregadas")
        return keys
    
    def _get_next_openrouter_key(self) -> Optional[str]:
        """Obtém próxima chave OpenRouter com rotação"""
        if not self.openrouter_keys:
            return None
            
        key = self.openrouter_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.openrouter_keys)
        return key
    
    def _get_next_gemini_key(self) -> Optional[str]:
        """Obtém próxima chave Gemini com rotação"""
        if not self.gemini_keys:
            return None
            
        key = self.gemini_keys[self.current_gemini_key_index]
        self.current_gemini_key_index = (self.current_gemini_key_index + 1) % len(self.gemini_keys)
        return key

    async def _generate_with_openrouter(
        self,
        prompt: str,
        model_name: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """Gera conteúdo usando OpenRouter com rotação de chaves"""
        
        # Preparar mensagens
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Tentar com todas as chaves disponíveis
        for attempt in range(len(self.openrouter_keys)):
            api_key = self._get_next_openrouter_key()
            if not api_key:
                continue
                
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/joscarmao/v1800finalv2",
                    "X-Title": "ARQV30 Enhanced v3.0"
                }
                
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            logger.info(f"✅ OpenRouter {model_name} sucesso")
                            return content
                        else:
                            error_text = await response.text()
                            logger.warning(f"⚠️ OpenRouter key {attempt + 1} falhou: {response.status}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Erro OpenRouter key {attempt + 1}: {str(e)[:100]}")
                continue
        
        logger.error(f"❌ Todas as chaves OpenRouter falharam para {model_name}")
        return None
    
    async def _generate_with_gemini_direct(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """Gera conteúdo usando Gemini direto com rotação de chaves"""
        
        try:
            import google.generativeai as genai
            
            # Tentar com todas as chaves Gemini
            for attempt in range(len(self.gemini_keys)):
                api_key = self._get_next_gemini_key()
                if not api_key:
                    continue
                    
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.0-flash-exp")
                    
                    # Combinar system prompt e user prompt se necessário
                    full_prompt = prompt
                    if system_prompt:
                        full_prompt = f"{system_prompt}\n\n{prompt}"
                    
                    generation_config = {
                        'temperature': temperature,
                        'top_p': 0.95,
                        'top_k': 64,
                        'max_output_tokens': max_tokens,
                    }
                    
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config
                    )
                    
                    if response.text:
                        logger.info(f"✅ Gemini direto sucesso")
                        return response.text
                        
                except Exception as e:
                    logger.warning(f"⚠️ Erro Gemini key {attempt + 1}: {str(e)[:100]}")
                    continue
            
            logger.error("❌ Todas as chaves Gemini falharam")
            return None
            
        except ImportError:
            logger.error("❌ google-generativeai não instalado")
            return None
    
    def generate_response(
        self,
        prompt: str,
        model: str = "x-ai/grok-4-fast:free",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Gera resposta síncrona usando hierarquia de modelos"""
        try:
            # Executar geração assíncrona de forma síncrona
            import asyncio
            
            async def _async_generate():
                return await self.generate_text(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model_override=model
                )
            
            # Tentar obter loop existente ou criar novo
            try:
                loop = asyncio.get_running_loop()
                # Se já há um loop rodando, criar task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _async_generate())
                    content = future.result(timeout=180)
            except RuntimeError:
                # Nenhum loop rodando, executar diretamente
                content = asyncio.run(_async_generate())
            
            return {
                'success': True,
                'content': content,
                'model': model,
                'provider': 'hierarchy',
                'tokens_used': len(content.split()) * 1.3  # Estimativa
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de resposta: {e}")
            return {
                'success': False,
                'content': 'Erro interno ao gerar resposta',
                'error': str(e)
            }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model_override: Optional[str] = None
    ) -> str:
        """
        Gera texto usando hierarquia de modelos: Grok-4 → Gemini-2.0 → Gemini Direct
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt do sistema (opcional)
            max_tokens: Máximo de tokens (opcional)
            temperature: Temperatura (opcional)
            model_override: Modelo específico (opcional)
        
        Returns:
            String com a resposta da IA
        """
        max_tokens = max_tokens or 4000
        temperature = temperature or 0.7
        
        # Se modelo específico foi solicitado, tentar apenas ele
        if model_override:
            target_models = [m for m in self.model_hierarchy if m['name'] == model_override]
            if not target_models:
                # Se modelo não encontrado, usar hierarquia normal
                target_models = self.model_hierarchy
        else:
            target_models = self.model_hierarchy
        
        # Tentar cada modelo na hierarquia
        for model_config in target_models:
            try:
                logger.info(f"🤖 Tentando {model_config['name']} ({model_config['provider']})")
                
                if model_config['provider'] == 'openrouter':
                    result = await self._generate_with_openrouter(
                        prompt=prompt,
                        model_name=model_config['name'],
                        max_tokens=min(max_tokens, model_config['max_tokens']),
                        temperature=temperature,
                        system_prompt=system_prompt
                    )
                    
                elif model_config['provider'] == 'gemini_direct':
                    result = await self._generate_with_gemini_direct(
                        prompt=prompt,
                        max_tokens=min(max_tokens, model_config['max_tokens']),
                        temperature=temperature,
                        system_prompt=system_prompt
                    )
                else:
                    logger.warning(f"⚠️ Provider desconhecido: {model_config['provider']}")
                    continue
                
                if result:
                    logger.info(f"✅ Sucesso com {model_config['name']}")
                    return result
                else:
                    logger.warning(f"⚠️ {model_config['name']} não retornou resultado")
                    
            except Exception as e:
                logger.error(f"❌ Erro com {model_config['name']}: {str(e)[:100]}")
                continue
        
        # Se todos os modelos falharam, usar fallback básico
        logger.error("❌ Todos os modelos da hierarquia falharam")
        raise Exception("Todos os modelos de IA falharam. Verifique as configurações das APIs.")
    
    def generate_text_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model_override: Optional[str] = None
    ) -> str:
        """Versão síncrona da geração de texto"""
        try:
            return generate_with_gemini_direct_sync(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens or 4000,
                temperature=temperature or 0.7
            )
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"❌ Erro de conexão ao gerar texto (sync): {str(e)}")
            raise
        except (ValueError, KeyError) as e:
            logger.error(f"❌ Erro de parâmetros ao gerar texto (sync): {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar texto (sync): {str(e)}")
            raise

    async def _perform_smart_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Realiza busca inteligente com fallbacks Serper → Jina → EXA"""
        
        if not self.search_orchestrator:
            logger.warning("⚠️ Search Orchestrator não disponível")
            return []
        
        try:
            # 1. Tentar Serper primeiro
            logger.info(f"🔍 Tentando busca Serper para: {query}")
            serper_results = await self.search_orchestrator.search_serper(query, max_results)
            
            if serper_results:
                logger.info(f"✅ Serper retornou {len(serper_results)} resultados")
                return serper_results
            
            # 2. Fallback para Jina
            logger.info(f"🔍 Fallback: Tentando busca Jina para: {query}")
            jina_results = await self.search_orchestrator.search_jina(query, max_results)
            
            if jina_results:
                logger.info(f"✅ Jina retornou {len(jina_results)} resultados")
                return jina_results
            
            # 3. Fallback para EXA
            logger.info(f"🔍 Fallback: Tentando busca EXA para: {query}")
            exa_results = await self.search_orchestrator.search_exa(query, max_results)
            
            if exa_results:
                logger.info(f"✅ EXA retornou {len(exa_results)} resultados")
                return exa_results
            
            logger.warning("⚠️ Todos os serviços de busca falharam")
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro na busca inteligente: {e}")
            return []

    async def generate_with_active_search(
        self,
        prompt: str,
        context: str = "",
        session_id: str = None,
        max_search_iterations: int = 3,
        preferred_model: str = None,
        min_processing_time: int = 0
    ) -> str:
        """
        Gera conteúdo com busca ativa usando hierarquia Grok-4 → Gemini
        """
        logger.info(f"🔍 Iniciando geração com busca ativa (modelo: {preferred_model or 'hierarquia'})")
        
        # Registrar tempo de início para garantir tempo mínimo
        start_time = datetime.now()

        # Realizar buscas complementares se necessário
        additional_context = ""
        if max_search_iterations > 0:
            # Extrair termos de busca do prompt
            search_queries = self._extract_search_terms(prompt)
            
            for i, query in enumerate(search_queries[:max_search_iterations]):
                logger.info(f"🔍 Busca {i+1}/{len(search_queries)}: {query}")
                search_results = await self._perform_smart_search(query, max_results=3)
                
                if search_results:
                    additional_context += f"\n\n=== DADOS DE BUSCA: {query} ===\n"
                    for result in search_results:
                        additional_context += f"- {result.get('title', 'Sem título')}: {result.get('snippet', result.get('description', ''))}\n"

        # Prepara prompt com instruções de busca e contexto
        enhanced_prompt = f"""
{prompt}

CONTEXTO PRINCIPAL:
{context}

{additional_context if additional_context else ""}

INSTRUÇÕES ESPECIAIS:
- Analise o contexto fornecido detalhadamente
- Use os dados de busca complementares para enriquecer a análise
- Procure por estatísticas, tendências e casos reais
- Forneça insights profundos baseados nos dados disponíveis
- Combine informações de múltiplas fontes para criar análise robusta

IMPORTANTE: Gere uma análise completa e profissional baseando-se em TODOS os dados fornecidos.
"""

        # Sistema prompt para busca ativa
        system_prompt = """Você é um especialista em análise de mercado e tendências digitais com acesso a dados em tempo real.
        Sua função é gerar análises profundas e insights valiosos baseados nos dados fornecidos.
        Sempre forneça informações precisas, atualizadas e acionáveis.
        Combine dados de múltiplas fontes para criar análises robustas e confiáveis."""

        try:
            # Usar modelo preferido ou hierarquia
            logger.info(f"🤖 Gerando com modelo: {preferred_model or 'hierarquia Grok-4 → Gemini'}")
            
            # Gerar resposta usando hierarquia
            response = await self.generate_text(
                prompt=enhanced_prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.7,
                model_override=preferred_model
            )
            
            # Garantir tempo mínimo de processamento se especificado
            if min_processing_time > 0:
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if elapsed_time < min_processing_time:
                    remaining_time = min_processing_time - elapsed_time
                    logger.info(f"⏱️ Aguardando {remaining_time:.1f}s para completar tempo mínimo")
                    await asyncio.sleep(remaining_time)
            
            logger.info("✅ Geração com busca ativa concluída")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na geração com busca ativa: {e}")
            # Fallback simples
            try:
                return await self.generate_text(enhanced_prompt, system_prompt)
            except Exception as e2:
                logger.error(f"❌ Erro no fallback: {e2}")
                raise
    
    def _extract_search_terms(self, prompt: str) -> List[str]:
        """Extrai termos de busca relevantes do prompt"""
        # Implementação básica - pode ser melhorada
        search_terms = []
        
        # Buscar por palavras-chave comuns
        keywords = ['mercado', 'brasil', 'tendências', 'estatísticas', 'dados', 'análise']
        
        for keyword in keywords:
            if keyword in prompt.lower():
                # Extrair contexto ao redor da palavra-chave
                words = prompt.lower().split()
                for i, word in enumerate(words):
                    if keyword in word:
                        # Pegar 2 palavras antes e depois
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        search_term = ' '.join(words[start:end])
                        search_terms.append(search_term)
                        break
        
        # Se não encontrou termos específicos, usar primeiras palavras
        if not search_terms:
            words = prompt.split()[:5]
            search_terms.append(' '.join(words))
        
        return search_terms[:3]  # Máximo 3 buscas

    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "comprehensive",
        target_audience: str = "general",
        model_preference: str = None
    ) -> str:
        """
        Analisa conteúdo usando hierarquia OpenRouter
        
        Args:
            content: Conteúdo para análise
            analysis_type: Tipo de análise (comprehensive, viral, market, etc.)
            target_audience: Público-alvo
            model_preference: Preferência de modelo
        
        Returns:
            Análise detalhada do conteúdo
        """
        system_prompt = f"""Você é um especialista em análise de conteúdo digital e marketing.
        Sua função é analisar conteúdo de forma {analysis_type} para o público {target_audience}.
        Forneça insights acionáveis, tendências identificadas e recomendações estratégicas."""
        
        analysis_prompt = f"""
Analise o seguinte conteúdo de forma {analysis_type}:

CONTEÚDO:
{content}

PÚBLICO-ALVO: {target_audience}

FORNEÇA:
1. Análise detalhada do conteúdo
2. Pontos fortes e fracos identificados
3. Potencial viral e engajamento
4. Recomendações de melhoria
5. Estratégias de distribuição
6. Insights de mercado relevantes

Seja específico, prático e acionável em suas recomendações.
"""
        
        try:
            return await self.generate_text(
                prompt=analysis_prompt,
                system_prompt=system_prompt,
                max_tokens=3000,
                temperature=0.7,
                model_override=model_preference
            )
        except Exception as e:
            logger.error(f"❌ Erro na análise de conteúdo: {e}")
            raise

    async def generate_insights(
        self,
        data: Dict[str, Any],
        insight_type: str = "market_trends",
        depth: str = "deep"
    ) -> str:
        """
        Gera insights baseados em dados usando hierarquia OpenRouter
        
        Args:
            data: Dados para análise
            insight_type: Tipo de insight desejado
            depth: Profundidade da análise (shallow, medium, deep)
        
        Returns:
            Insights gerados
        """
        system_prompt = f"""Você é um analista de dados especializado em {insight_type}.
        Sua função é gerar insights {depth} baseados nos dados fornecidos.
        Sempre forneça análises precisas, tendências identificadas e recomendações acionáveis."""
        
        data_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        insights_prompt = f"""
Analise os seguintes dados e gere insights {depth} sobre {insight_type}:

DADOS:
{data_str}

FORNEÇA:
1. Principais tendências identificadas
2. Padrões e correlações importantes
3. Oportunidades de mercado
4. Riscos e desafios
5. Recomendações estratégicas
6. Previsões baseadas nos dados

Seja específico, use números quando relevante e forneça insights acionáveis.
"""
        
        try:
            return await self.generate_text(
                prompt=insights_prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.6
            )
        except Exception as e:
            logger.error(f"❌ Erro na geração de insights: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do gerenciador"""
        return {
            "gemini_status": self.gemini_client.get_status(),
            "search_orchestrator_available": self.search_orchestrator is not None,
            "timestamp": datetime.now().isoformat()
        }

    def reset_failed_models(self):
        """Reseta estatísticas do cliente Gemini"""
        self.gemini_client.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "key_rotations": 0,
            "last_used_key": None
        }
        logger.info("✅ Estatísticas Gemini resetadas")

# Instância global para uso em todo o projeto
enhanced_ai_manager = EnhancedAIManager()

# Funções de conveniência para uso direto
async def generate_ai_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    model_override: Optional[str] = None
) -> str:
    """Função de conveniência para geração de texto"""
    return await enhanced_ai_manager.generate_text(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

def generate_ai_text_sync(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    model_override: Optional[str] = None
) -> str:
    """Função de conveniência síncrona para geração de texto"""
    return enhanced_ai_manager.generate_text_sync(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

if __name__ == "__main__":
    # Teste básico
    async def test():
        try:
            manager = EnhancedAIManager()
            
            response = await manager.generate_text(
                prompt="Explique brevemente o que é inteligência artificial",
                system_prompt="Você é um especialista em tecnologia"
            )
            print(f"Resposta: {response}")
            
            # Status
            status = manager.get_status()
            print(f"Status: {json.dumps(status, indent=2, default=str)}")
            
        except Exception as e:
            print(f"Erro no teste: {e}")
    
    asyncio.run(test())