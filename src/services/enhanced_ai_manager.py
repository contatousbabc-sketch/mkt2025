#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced AI Manager
Gerenciador de IA com suporte a ferramentas e busca ativa
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Imports condicionais
try:
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

# Adicionando suporte ao OpenRouter
try:
    import openai as openrouter_openai
    HAS_OPENROUTER = True
except ImportError:
    HAS_OPENROUTER = False

logger = logging.getLogger(__name__)

class EnhancedAIManager:
    """Gerenciador de IA aprimorado com ferramentas de busca ativa"""

    def __init__(self):
        """Inicializa o gerenciador aprimorado"""
        self.providers = {}
        self.current_provider = None
        self.search_orchestrator = None

        self._initialize_providers()
        self._initialize_search_tools()

        logger.info(f"🤖 Enhanced AI Manager inicializado com {len(self.providers)} provedores")

    def _initialize_providers(self):
        """Inicializa todos os provedores de IA"""

        # OpenRouter X-AI Grok-4-Fast:free (Prioridade 1 - PRIMÁRIA)
        if HAS_OPENROUTER:
            openrouter_keys = [
                os.getenv("OPENROUTER_API_KEY"),
                os.getenv("OPENROUTER_API_KEY_1"), 
                os.getenv("OPENROUTER_API_KEY_2"),
                os.getenv("OPENROUTER_API_KEY_3")
            ]
            openrouter_keys = [key for key in openrouter_keys if key]  # Remove None
            
            if openrouter_keys:
                try:
                    # Criar clientes para todas as chaves
                    openrouter_clients = []
                    for i, api_key in enumerate(openrouter_keys):
                        client = openrouter_openai.OpenAI(
                            api_key=api_key,
                            base_url="https://openrouter.ai/api/v1"
                        )
                        openrouter_clients.append(client)
                    
                    self.providers["openrouter_grok"] = {
                        "clients": openrouter_clients,  # Lista de clientes
                        "current_client_index": 0,  # Índice atual
                        "model": "x-ai/grok-4-fast:free",  # X-AI Grok-4-Fast FREE como primária
                        "available": True,  # Habilitado como primária
                        "supports_tools": True,
                        "priority": 1,  # PRIORIDADE MÁXIMA
                        "total_keys": len(openrouter_keys),
                        "max_tokens": None,  # SEM LIMITAÇÃO DE TOKENS
                        "description": "X-AI Grok-4-Fast FREE - IA Primária"
                    }
                    logger.info(f"✅ OpenRouter X-AI Grok-4-Fast:free configurado como PRIMÁRIA com {len(openrouter_keys)} chaves API")
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar OpenRouter Grok: {e}")

        # OpenRouter Gemini 2.0 Flash Exp:free (Prioridade 2 - FALLBACK)
        if HAS_OPENROUTER:
            openrouter_keys = [
                os.getenv("OPENROUTER_API_KEY"),
                os.getenv("OPENROUTER_API_KEY_1"), 
                os.getenv("OPENROUTER_API_KEY_2"),
                os.getenv("OPENROUTER_API_KEY_3")
            ]
            openrouter_keys = [key for key in openrouter_keys if key]  # Remove None
            
            if openrouter_keys:
                try:
                    # Criar clientes para todas as chaves (reutilizando as mesmas)
                    openrouter_clients = []
                    for i, api_key in enumerate(openrouter_keys):
                        client = openrouter_openai.OpenAI(
                            api_key=api_key,
                            base_url="https://openrouter.ai/api/v1"
                        )
                        openrouter_clients.append(client)
                    
                    self.providers["openrouter_gemini"] = {
                        "clients": openrouter_clients,  # Lista de clientes
                        "current_client_index": 0,  # Índice atual
                        "model": "google/gemini-2.0-flash-exp:free",  # Gemini 2.0 Flash Exp FREE como fallback
                        "available": True,  # Habilitado como fallback
                        "supports_tools": True,
                        "priority": 2,  # FALLBACK
                        "total_keys": len(openrouter_keys),
                        "max_tokens": None,  # SEM LIMITAÇÃO DE TOKENS
                        "description": "Gemini 2.0 Flash Exp FREE - IA Fallback"
                    }
                    logger.info(f"✅ OpenRouter Gemini 2.0 Flash Exp:free configurado como FALLBACK com {len(openrouter_keys)} chaves API")
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar OpenRouter Gemini: {e}")

        # Gemini Direto (Prioridade 3 - Backup)
        if HAS_GEMINI:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.providers["gemini"] = {
                        "client": genai,
                        "model": "gemini-2.0-flash-exp",
                        "available": True,  # Habilitado como backup
                        "supports_tools": True,
                        "priority": 3,
                        "max_tokens": None,  # SEM LIMITAÇÃO DE TOKENS
                        "description": "Gemini Direto - Backup"
                    }
                    logger.info("✅ Gemini 2.0 Flash Direto configurado como backup")
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar Gemini: {e}")

        # Groq (Prioridade 4 - Desabilitado conforme solicitado)
        if HAS_GROQ:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                try:
                    self.providers["groq"] = {
                        "client": Groq(api_key=api_key),
                        "model": "llama3-70b-8192",
                        "available": False,  # DESABILITADO conforme solicitado
                        "supports_tools": False,
                        "priority": 4,
                        "max_tokens": None,  # SEM LIMITAÇÃO DE TOKENS
                        "description": "Groq - Desabilitado"
                    }
                    logger.info("ℹ️ Groq configurado mas DESABILITADO")
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar Groq: {e}")

        # OpenAI (Prioridade 5 - Último recurso)
        if HAS_OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.providers["openai"] = {
                        "client": openai.OpenAI(api_key=api_key),
                        "model": "gpt-4o",
                        "available": True,
                        "supports_tools": True,
                        "priority": 5,  # Último recurso
                        "max_tokens": None,  # SEM LIMITAÇÃO DE TOKENS
                        "description": "OpenAI GPT-4o - Último recurso"
                    }
                    logger.info("✅ OpenAI GPT-4o configurado como último recurso")
                except Exception as e:
                    logger.error(f"❌ Erro ao configurar OpenAI: {e}")

    def _initialize_search_tools(self):
        """Inicializa ferramentas de busca"""
        try:
            from services.real_search_orchestrator import real_search_orchestrator
            self.search_orchestrator = real_search_orchestrator
            logger.info("✅ Ferramentas de busca ativa configuradas")
        except ImportError:
            logger.warning("⚠️ Search orchestrator não disponível")

    def _get_best_provider(self, require_tools: bool = False) -> Optional[str]:
        """Seleciona o melhor provedor disponível"""
        available = []

        for name, provider in self.providers.items():
            if not provider["available"]:
                continue

            # Se requer tools, pula provedores que não suportam
            if require_tools and not provider.get("supports_tools", False):
                 # Mas permite Qwen mesmo sem tools como fallback se necessário
                 if name != "openrouter": # Qwen pode ser usado mesmo sem tools se for o único
                    continue

            available.append((name, provider["priority"]))

        if available:
            # Ordena pela prioridade (menor número = maior prioridade)
            available.sort(key=lambda x: x[1])
            return available[0][0]

        # Se nenhum provedor com tools está disponível, mas precisamos de tools
        # Retorna o melhor provedor sem tools
        if require_tools:
            logger.warning("⚠️ Nenhum provedor com tools disponível, usando provedor simples")
            return self._get_best_provider(require_tools=False)

        return None

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
        Gera conteúdo com busca ativa - IA pode buscar informações online
        """
        logger.info(f"🔍 Iniciando geração com busca ativa (min_time: {min_processing_time}s)")
        
        # Registrar tempo de início para garantir tempo mínimo
        start_time = datetime.now()

        # Usar modelo preferido ou selecionar automaticamente
        if preferred_model == "grok" and "openrouter_grok" in self.providers and self.providers["openrouter_grok"]["available"]:
            provider_name = "openrouter_grok"
            logger.info(f"🚀 MODO GROK: Usando X-AI Grok-4-Fast:free como PRIMÁRIA")
            logger.info(f"🔥 Configurado para análise ULTRA-PROFUNDA sem limitação de tokens")
        elif "openrouter_grok" in self.providers and self.providers["openrouter_grok"]["available"]:
            provider_name = "openrouter_grok"
            logger.info(f"🚀 Usando X-AI Grok-4-Fast:free como IA PRIMÁRIA")
        elif "openrouter_gemini" in self.providers and self.providers["openrouter_gemini"]["available"]:
            provider_name = "openrouter_gemini"
            logger.info(f"🔄 FALLBACK: Usando Gemini 2.0 Flash Exp:free")
        else:
            # Caso contrário, usa a lógica padrão
            provider_name = self._get_best_provider(require_tools=True)
            if not provider_name:
                logger.warning("⚠️ Nenhum provedor com ferramentas disponível - usando fallback")
                return await self.generate_text(prompt + "\n\n" + context)

        provider = self.providers[provider_name]
        logger.info(f"🤖 Usando {provider_name} com busca ativa")

        # Prepara prompt com instruções de busca
        enhanced_prompt = f"""
{prompt}

CONTEXTO DISPONÍVEL:
{context}

INSTRUÇÕES ESPECIAIS:
- Analise o contexto fornecido detalhadamente
- Busque dados atualizados sobre o mercado brasileiro
- Procure por estatísticas, tendências e casos reais
- Forneça insights profundos baseados nos dados disponíveis

IMPORTANTE: Gere uma análise completa mesmo sem ferramentas de busca, baseando-se no contexto fornecido.
"""

        try:
            # Executa geração com ferramentas baseado no provedor
            if provider_name == "openrouter_grok":
                return await self._generate_openrouter_with_tools(enhanced_prompt, max_search_iterations, session_id, "openrouter_grok")
            elif provider_name == "openrouter_gemini":
                return await self._generate_openrouter_with_tools(enhanced_prompt, max_search_iterations, session_id, "openrouter_gemini")
            elif provider_name == "gemini":
                return await self._generate_gemini_with_tools(enhanced_prompt, max_search_iterations, session_id)
            elif provider_name == "openai":
                return await self._generate_openai_with_tools(enhanced_prompt, max_search_iterations, session_id)
            else:
                # Para outros provedores - SEM LIMITAÇÃO DE TOKENS
                logger.info(f"🎓 Usando {provider_name} para ANÁLISE PROFUNDA sem limitação de tokens")
                return await self.generate_text(enhanced_prompt, max_tokens=None, temperature=0.8)
        except Exception as e:
            logger.error(f"❌ Erro com {provider_name}: {e}")
            # Fallback para geração simples - SEM LIMITAÇÃO DE TOKENS
            logger.info("🔄 Usando fallback sem limitação de tokens")
            return await self.generate_text(enhanced_prompt, max_tokens=None, temperature=0.8)

    async def _generate_gemini_with_tools(
        self,
        prompt: str,
        max_iterations: int,
        session_id: str = None
    ) -> str:
        """Gera com Gemini usando ferramentas"""

        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

            # Define função de busca
            search_function = FunctionDeclaration(
                name="google_search",
                description="Busca informações atualizadas na internet",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Termo de busca"
                        }
                    },
                    "required": ["query"]
                }
            )

            tool = Tool(function_declarations=[search_function])

            # Inicia chat com ferramentas
            chat = model.start_chat(tools=[tool])

            iteration = 0
            conversation_history = []

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 Iteração {iteration}/{max_iterations}")

                try:
                    # Envia mensagem
                    if iteration == 1:
                        response = chat.send_message(prompt)
                    else:
                        # Continua conversa com resultados de busca
                        response = chat.send_message("Continue a análise com os dados obtidos.")

                    # Verifica se há function calls
                    if response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if part.function_call:
                                function_call = part.function_call

                                if function_call.name == "google_search":
                                    search_query = function_call.args.get("query", "")
                                    logger.info(f"🔍 IA solicitou busca: {search_query}")

                                    # Executa busca real
                                    search_results = await self._execute_real_search(search_query, session_id)

                                    # Envia resultados de volta para a IA
                                    search_response = chat.send_message(
                                        f"Resultados da busca para \'{search_query}\':\n{search_results}"
                                    )

                                    conversation_history.append({
                                        "search_query": search_query,
                                        "search_results": search_results[:1000] # Limita para log
                                    })

                                    continue

                    # Se chegou aqui, é resposta final
                    final_response = response.text

                    logger.info(f"✅ Geração com busca ativa concluída em {iteration} iterações")
                    logger.info(f"🔍 {len(conversation_history)} buscas realizadas")

                    # Garantir tempo mínimo de processamento se especificado
                    if min_processing_time > 0:
                        elapsed_time = (datetime.now() - start_time).total_seconds()
                        if elapsed_time < min_processing_time:
                            remaining_time = min_processing_time - elapsed_time
                            logger.info(f"⏱️ Aguardando {remaining_time:.1f}s para completar tempo mínimo de especialização")
                            await asyncio.sleep(remaining_time)

                    return final_response

                except Exception as e:
                    logger.error(f"❌ Erro na iteração {iteration}: {e}")
                    break

            # Se chegou ao limite de iterações
            logger.warning(f"⚠️ Limite de iterações atingido ({max_iterations})")
            return "Análise realizada com busca ativa, mas processo limitado por iterações."

        except Exception as e:
            logger.error(f"❌ Erro no Gemini com ferramentas: {e}")
            raise

    async def _generate_openai_with_tools(
        self,
        prompt: str,
        max_iterations: int,
        session_id: str = None
    ) -> str:
        """Gera com OpenAI usando ferramentas"""

        try:
            client = self.providers["openai"]["client"]

            # Define função de busca
            tools = [{
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "Busca informações atualizadas na internet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Termo de busca"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }]

            messages = [{"role": "user", "content": prompt}]
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 Iteração OpenAI {iteration}/{max_iterations}")

                try:
                    response = client.chat.completions.create(
                        model=self.providers["openai"]["model"],
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        max_tokens=4000
                    )

                    message = response.choices[0].message

                    # Verifica tool calls
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        tool_call = message.tool_calls[0]

                        if tool_call.function.name == "google_search":
                            args = json.loads(tool_call.function.arguments)
                            search_query = args.get("query", "")

                            logger.info(f"🔍 IA OpenAI solicitou busca: {search_query}")

                            # Executa busca real
                            search_results = await self._execute_real_search(search_query, session_id)

                            # Adiciona à conversa
                            messages.append({
                                "role": "assistant",
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": "google_search",
                                        "arguments": tool_call.function.arguments
                                    }
                                }]
                            })

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": search_results
                            })

                            continue

                    # Resposta final
                    final_response = message.content
                    logger.info(f"✅ OpenAI geração concluída em {iteration} iterações")
                    return final_response

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                        logger.error(f"❌ OpenAI quota excedida: {e}")
                        # Marca OpenAI como indisponível temporariamente
                        self.providers["openai"]["available"] = False
                        logger.info("🔄 Marcando OpenAI como indisponível e tentando outro provedor")

                        # Tenta usar outro provedor como fallback
                        fallback_provider = self._get_best_provider(require_tools=False)
                        if fallback_provider and fallback_provider != "openai":
                            logger.info(f"🔄 Usando {fallback_provider} como fallback para OpenAI")
                            return await self.generate_text(prompt)
                        else:
                            return "OpenAI quota excedida e nenhum provedor alternativo disponível. Por favor, configure uma chave API válida."
                    else:
                        logger.error(f"❌ Erro na iteração OpenAI {iteration}: {e}")
                    break

            return "Análise realizada com OpenAI e busca ativa."

        except Exception as e:
            logger.error(f"❌ Erro no OpenAI com ferramentas: {e}")
            raise

    async def _generate_openrouter_with_tools(
        self,
        prompt: str,
        max_iterations: int,
        session_id: str = None,
        provider_key: str = "openrouter_grok"
    ) -> str:
        """Gera com OpenRouter (Grok ou Gemini) usando ferramentas"""

        try:
            provider = self.providers[provider_key]
            clients = provider["clients"]
            current_index = provider["current_client_index"]
            model = provider["model"]
            
            logger.info(f"🚀 Usando {provider['description']} - Modelo: {model}")

            # Rotação de clientes OpenRouter
            client = clients[current_index]
            
            # Define função de busca
            tools = [{
                "type": "function",
                "function": {
                    "name": "google_search",
                    "description": "Busca informações atualizadas na internet sobre mercado brasileiro",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Termo de busca específico para o mercado brasileiro"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }]

            messages = [{"role": "user", "content": prompt}]
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                logger.info(f"🔄 Iteração OpenRouter {iteration}/{max_iterations}")

                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools,
                        tool_choice="auto",
                        max_tokens=None,  # SEM LIMITAÇÃO DE TOKENS
                        temperature=0.8
                    )

                    message = response.choices[0].message

                    # Verifica tool calls
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        tool_call = message.tool_calls[0]

                        if tool_call.function.name == "google_search":
                            args = json.loads(tool_call.function.arguments)
                            search_query = args.get("query", "")

                            logger.info(f"🔍 IA {provider['description']} solicitou busca: {search_query}")

                            # Executa busca real
                            search_results = await self._execute_real_search(search_query, session_id)

                            # Adiciona à conversa
                            messages.append({
                                "role": "assistant",
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": "google_search",
                                        "arguments": tool_call.function.arguments
                                    }
                                }]
                            })

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": search_results
                            })

                            continue

                    # Resposta final
                    final_response = message.content
                    logger.info(f"✅ {provider['description']} geração concluída em {iteration} iterações")
                    
                    # Atualiza índice para próxima chamada (rotação)
                    provider["current_client_index"] = (current_index + 1) % len(clients)
                    
                    return final_response

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
                        logger.warning(f"⚠️ {provider['description']} rate limit, tentando próxima chave")
                        
                        # Tenta próxima chave
                        provider["current_client_index"] = (current_index + 1) % len(clients)
                        
                        # Se já tentou todas as chaves, marca como indisponível temporariamente
                        if provider["current_client_index"] == current_index:
                            logger.error(f"❌ Todas as chaves {provider['description']} esgotadas")
                            provider["available"] = False
                            
                            # Tenta fallback para outro provedor
                            if provider_key == "openrouter_grok" and "openrouter_gemini" in self.providers:
                                logger.info("🔄 Fallback: Grok → Gemini")
                                return await self._generate_openrouter_with_tools(prompt, max_iterations, session_id, "openrouter_gemini")
                            elif provider_key == "openrouter_gemini" and "gemini" in self.providers:
                                logger.info("🔄 Fallback: OpenRouter Gemini → Gemini Direto")
                                return await self._generate_gemini_with_tools(prompt, max_iterations, session_id)
                            
                            raise Exception(f"Todos os provedores OpenRouter esgotados")
                        
                        continue
                    else:
                        logger.error(f"❌ Erro {provider['description']}: {e}")
                        break

            # Se chegou ao limite de iterações
            logger.warning(f"⚠️ Limite de iterações atingido ({max_iterations}) para {provider['description']}")
            return f"Análise realizada com {provider['description']} e busca ativa."

        except Exception as e:
            logger.error(f"❌ Erro no {provider_key} com ferramentas: {e}")
            
            # Fallback automático
            if provider_key == "openrouter_grok" and "openrouter_gemini" in self.providers:
                logger.info("🔄 Fallback automático: Grok → Gemini")
                return await self._generate_openrouter_with_tools(prompt, max_iterations, session_id, "openrouter_gemini")
            
            raise

    async def _execute_real_search(self, search_query: str, session_id: str = None) -> str:
        """Executa busca real usando o orquestrador"""

        if not self.search_orchestrator:
            return f"Busca não disponível para: {search_query}"

        try:
            # Executa busca massiva real
            search_results = await self.search_orchestrator.execute_massive_real_search(
                query=search_query,
                context={"ai_requested": True},
                session_id=session_id or "ai_search"
            )

            # Formata resultados para a IA
            formatted_results = self._format_search_results_for_ai(search_results)

            return formatted_results

        except Exception as e:
            logger.error(f"❌ Erro na busca real: {e}")
            return f"Erro na busca para \'{search_query}\': {str(e)}"

    def _format_search_results_for_ai(self, search_results: Dict[str, Any]) -> str:
        """Formata resultados de busca para consumo da IA"""

        formatted = """
RESULTADOS DA BUSCA REAL:
Query: {query}
Fontes encontradas: {total_sources}

""".format(
            query=search_results.get("query", ""),
            total_sources=search_results.get("statistics", {}).get("total_sources", 0)
        )

        # Web results
        web_results = search_results.get("web_results", [])
        if web_results:
            formatted += "=== RESULTADOS WEB ===\n"
            for i, result in enumerate(web_results[:10], 1):
                formatted += f"{i}. {result.get('title', 'Sem título')}\n"
                formatted += f"   URL: {result.get('url', '')}\n"
                formatted += f"   Resumo: {result.get('snippet', '')[:200]}...\n\n"

        # YouTube results
        youtube_results = search_results.get("youtube_results", [])
        if youtube_results:
            formatted += "=== RESULTADOS YOUTUBE ===\n"
            for i, result in enumerate(youtube_results[:5], 1):
                formatted += f"{i}. {result.get('title', 'Sem título')}\n"
                formatted += f"   Canal: {result.get('channel', '')}\n"
                formatted += f"   Views: {result.get('view_count', 0):,}\n"
                formatted += f"   Likes: {result.get('like_count', 0):,}\n\n"

        # Social results
        social_results = search_results.get("social_results", [])
        if social_results:
            formatted += "=== RESULTADOS REDES SOCIAIS ===\n"
            for i, result in enumerate(social_results[:5], 1):
                formatted += f"{i}. {result.get('title', 'Sem título')}\n"
                formatted += f"   Plataforma: {result.get('platform', '')}\n"
                formatted += f"   Engajamento: {result.get('viral_score', 0):.1f}/10\n\n"

        # Conteúdo viral
        viral_content = search_results.get("viral_content", [])
        if viral_content:
            formatted += "=== CONTEÚDO VIRAL ===\n"
            for i, content in enumerate(viral_content[:5], 1):
                formatted += f"{i}. {content.get('title', 'Sem título')}\n"
                formatted += f"   URL: {content.get('url', '')}\n"
                formatted += f"   Plataforma: {content.get('platform', '')}\n"
                formatted += f"   Viral Score: {content.get('viral_score', 0):.1f}/10\n\n"

        # Screenshots
        screenshots = search_results.get("screenshots_captured", [])
        if screenshots:
            formatted += "=== SCREENSHOTS CAPTURADOS ===\n"
            for i, screenshot_path in enumerate(screenshots[:5], 1):
                formatted += f"{i}. {screenshot_path}\n"
            formatted += "\n"

        return formatted

    # Método para 'generate_text' - SEM LIMITAÇÃO DE TOKENS
    async def generate_text(self, prompt: str, max_tokens: int = None, temperature: float = 0.7) -> str:
        """Gera texto usando o melhor provedor disponível - SEM LIMITAÇÃO DE TOKENS"""
        provider_name = self._get_best_provider(require_tools=False)

        if not provider_name:
            logger.warning("⚠️ Nenhum provedor disponível")
            return "Erro: Nenhum provedor de IA disponível para gerar texto."

        provider = self.providers[provider_name]
        logger.info(f"🚀 Usando {provider_name} para geração de texto SEM LIMITAÇÃO DE TOKENS")

        try:
            # OpenRouter Grok (Primária)
            if provider_name == "openrouter_grok":
                clients = provider["clients"]
                current_index = provider["current_client_index"]
                total_keys = provider["total_keys"]
                
                logger.info(f"🚀 X-AI GROK-4-FAST: SEM limitação de tokens, temp={temperature}")
                logger.info(f"📊 Modelo: {provider['model']}")
                logger.info(f"📝 Prompt size: {len(prompt)} chars")
                logger.info(f"🔄 Usando chave API {current_index + 1}/{total_keys}")
                
                for attempt in range(total_keys):
                    try:
                        client = clients[current_index]
                        response = client.chat.completions.create(
                            model=provider["model"],
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,  # None = sem limitação
                            temperature=temperature
                        )
                        
                        result = response.choices[0].message.content
                        logger.info(f"✅ Grok resposta gerada: {len(result)} chars, {len(result.split())} palavras")
                        return result
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Erro Grok chave {current_index + 1}: {e}")
                        current_index = (current_index + 1) % total_keys
                        provider["current_client_index"] = current_index
                        
                        if attempt == total_keys - 1:
                            logger.error("❌ Todas as chaves Grok falharam, tentando fallback")
                            raise e

            # OpenRouter Gemini (Fallback)
            elif provider_name == "openrouter_gemini":
                clients = provider["clients"]
                current_index = provider["current_client_index"]
                total_keys = provider["total_keys"]
                
                logger.info(f"🔄 GEMINI FALLBACK: SEM limitação de tokens, temp={temperature}")
                logger.info(f"📊 Modelo: {provider['model']}")
                logger.info(f"🔄 Usando chave API {current_index + 1}/{total_keys}")
                
                for attempt in range(total_keys):
                    try:
                        client = clients[current_index]
                        response = client.chat.completions.create(
                            model=provider["model"],
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=max_tokens,  # None = sem limitação
                            temperature=temperature
                        )
                        
                        result = response.choices[0].message.content
                        logger.info(f"✅ Gemini OpenRouter resposta: {len(result)} chars, {len(result.split())} palavras")
                        return result
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Erro Gemini OpenRouter chave {current_index + 1}: {e}")
                        current_index = (current_index + 1) % total_keys
                        provider["current_client_index"] = current_index
                        
                        if attempt == total_keys - 1:
                            raise e

            # Gemini Direto (Backup)
            elif provider_name == "gemini":
                model = genai.GenerativeModel("gemini-2.0-flash-exp")
                
                # Configuração sem limitação de tokens
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                )
                
                # Só define max_output_tokens se especificado
                if max_tokens is not None:
                    generation_config.max_output_tokens = max_tokens
                
                logger.info(f"🔄 GEMINI DIRETO: SEM limitação de tokens, temp={temperature}")
                
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                result = response.text
                logger.info(f"✅ Gemini Direto resposta: {len(result)} chars, {len(result.split())} palavras")
                return result

            # Groq (Desabilitado mas mantido para compatibilidade)
            elif provider_name == "groq":
                client = provider["client"]
                logger.info(f"🔄 GROQ: SEM limitação de tokens, temp={temperature}")
                
                response = client.chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,  # None = sem limitação
                    temperature=temperature
                )
                
                result = response.choices[0].message.content
                logger.info(f"✅ Groq resposta: {len(result)} chars, {len(result.split())} palavras")
                return result

            # OpenAI removido conforme solicitado - não está sendo usado

        except Exception as e:
            logger.error(f"❌ Erro na geração de texto com {provider_name}: {e}")
            
            # Fallback automático para próximo provedor disponível
            if provider_name == "openrouter_grok":
                logger.info("🔄 Fallback automático: Grok → Gemini OpenRouter")
                if "openrouter_gemini" in self.providers and self.providers["openrouter_gemini"]["available"]:
                    return await self.generate_text(prompt, max_tokens, temperature)
            elif provider_name == "openrouter_gemini":
                logger.info("🔄 Fallback automático: Gemini OpenRouter → Gemini Direto")
                if "gemini" in self.providers and self.providers["gemini"]["available"]:
                    return await self.generate_text(prompt, max_tokens, temperature)
            
            return f"Erro na geração: {str(e)}"

        return "Erro: Método de geração não implementado para este provedor"


# Instância global
enhanced_ai_manager = EnhancedAIManager()
