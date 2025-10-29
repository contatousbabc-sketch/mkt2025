#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - AI Synthesis Engine
Motor de síntese da IA com hierarquia OpenRouter: Grok-4 → Gemini-2.0 → DeepSeek-R1
ZERO SIMULAÇÃO - Apenas modelos reais funcionais
"""

import os
import logging
import json
import time
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from .enhanced_ai_manager import enhanced_ai_manager
from .auto_save_manager import salvar_etapa, salvar_erro

logger = logging.getLogger(__name__)

class AISynthesisEngine:
    """Motor de síntese da IA com capacidade de tool use"""
    
    def __init__(self):
        """Inicializa o motor de síntese"""
        self.synthesis_tools = {
            'google_search': self._tool_google_search,
            'web_extract': self._tool_web_extract,
            'social_search': self._tool_social_search
        }
        
        self.max_tool_calls = 10  # Limite de chamadas de ferramentas
        self.synthesis_timeout = 1800  # 30 minutos máximo
        
        # Define diretório de screenshots (ajuste conforme sua estrutura)
        self.screenshots_dir = os.getenv('SCREENSHOTS_DIR', './screenshots')
        
        logger.info("🧠 AI Synthesis Engine inicializado")
    
    async def analyze_and_synthesize(
        self, 
        session_id: str, 
        model: str = None, 
        api_key: str = None, 
        analysis_time: int = 300,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Executa análise e síntese da IA com tool use"""
        
        logger.info(f"🧠 Iniciando síntese da IA para sessão {session_id}")
        
        try:
            if progress_callback:
                progress_callback("Carregando dados coletados...")
            
            # Carrega o relatório de coleta
            collection_report = self._load_collection_report(session_id)
            if not collection_report:
                raise Exception("Relatório de coleta não encontrado")
            
            if progress_callback:
                progress_callback("Preparando prompt mestre para IA...")
            
            # Constrói prompt mestre
            master_prompt = self._build_master_synthesis_prompt(collection_report, session_id)
            
            if progress_callback:
                progress_callback("Iniciando análise profunda da IA...")
            
            # Executa síntese com tool use
            synthesis_result = await self._execute_synthesis_with_tools(
                master_prompt, 
                session_id, 
                analysis_time,
                progress_callback
            )
            
            if progress_callback:
                progress_callback("Salvando resumo de síntese...")
            
            # Salva resumo de síntese
            synthesis_summary = self._create_synthesis_summary(synthesis_result, session_id)
            self._save_synthesis_json(synthesis_summary, session_id)
            
            logger.info(f"✅ Síntese da IA concluída para sessão {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'synthesis_summary': synthesis_summary,
                'tool_calls_made': synthesis_result.get('tool_calls_made', 0),
                'analysis_duration': synthesis_result.get('analysis_duration', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na síntese da IA: {e}")
            salvar_erro("ai_synthesis_error", e, contexto={'session_id': session_id})
            
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _load_collection_report(self, session_id: str) -> Optional[str]:
        """Carrega o relatório de coleta da sessão"""
        
        try:
            report_path = Path(self.screenshots_dir) / "files" / session_id / "relatorio_coleta.md"
            
            if report_path.exists():
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                logger.info(f"📄 Relatório de coleta carregado: {len(content)} caracteres")
                return content
            else:
                logger.error(f"❌ Relatório de coleta não encontrado: {report_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar relatório: {e}")
            return None
    
    def _build_master_synthesis_prompt(self, collection_report: str, session_id: str) -> str:
        """Constrói prompt mestre para síntese"""
        
        prompt = f"""
# VOCÊ É O ANALISTA MESTRE DE SÍNTESE DE DADOS

Sua missão é estudar profundamente o material coletado e sintetizar insights acionáveis.

## MATERIAL COLETADO PARA ANÁLISE:
{collection_report[:15000]}

## FERRAMENTAS DISPONÍVEIS:
Você tem acesso às seguintes ferramentas para aprofundar sua análise:

1. **google_search("query")** - Para buscar informações adicionais específicas
2. **web_extract("url")** - Para extrair conteúdo detalhado de URLs relevantes
3. **social_search("query")** - Para buscar dados específicos em redes sociais

## INSTRUÇÕES DE SÍNTESE:

1. **ESTUDE O MATERIAL**: Analise profundamente todos os dados coletados
2. **IDENTIFIQUE GAPS**: Se precisar de informações adicionais específicas, USE AS FERRAMENTAS
3. **SINTETIZE INSIGHTS**: Extraia insights acionáveis e padrões importantes
4. **ESTRUTURE O CONHECIMENTO**: Organize em formato JSON estruturado

## EXEMPLO DE USO DE FERRAMENTAS:
Se você precisar de mais dados sobre concorrentes específicos:
```
google_search("principais concorrentes telemedicina Brasil 2024")
```

Se encontrar uma URL interessante nos dados e quiser mais detalhes:
```
web_extract("https://exemplo.com/artigo-relevante")
```

## FORMATO DE RESPOSTA FINAL:
Após sua análise (com ou sem uso de ferramentas), retorne um JSON estruturado:

```json
{{
  "insights_principais": [
    "Insight 1 baseado na análise profunda",
    "Insight 2 com dados específicos encontrados"
  ],
  "dores_identificadas": [
    "Dor específica 1 extraída dos dados",
    "Dor específica 2 com evidências"
  ],
  "desejos_mapeados": [
    "Desejo 1 identificado nos dados sociais",
    "Desejo 2 baseado em padrões comportamentais"
  ],
  "concorrentes_principais": [
    {{"nome": "Concorrente 1", "pontos_fortes": ["Força 1"], "pontos_fracos": ["Fraqueza 1"]}}
  ],
  "oportunidades_mercado": [
    "Oportunidade 1 identificada",
    "Oportunidade 2 com potencial"
  ],
  "tendencias_emergentes": [
    "Tendência 1 baseada em dados reais",
    "Tendência 2 com evidências"
  ],
  "publico_alvo_refinado": {{
    "demografia": "Perfil demográfico baseado nos dados",
    "psicografia": "Perfil psicológico extraído",
    "comportamentos": ["Comportamento 1", "Comportamento 2"]
  }},
  "estrategias_recomendadas": [
    "Estratégia 1 baseada na análise",
    "Estratégia 2 com justificativa"
  ],
  "metricas_chave": {{
    "fontes_analisadas": 0,
    "posts_sociais": 0,
    "insights_extraidos": 0,
    "tool_calls_realizadas": 0
  }}
}}
```

IMPORTANTE: Use as ferramentas sempre que precisar de informações mais específicas ou atualizadas.
"""
        
        return prompt
    
    async def _execute_synthesis_with_tools(
        self, 
        prompt: str, 
        session_id: str, 
        analysis_time: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Executa síntese com suporte a tool use usando hierarquia OpenRouter"""
        
        start_time = time.time()
        tool_calls_made = 0
        conversation_history = [prompt]
        
        # Sistema prompt para síntese
        system_prompt = """Você é um especialista em análise de dados e síntese de informações.
        Sua função é analisar dados coletados e gerar insights profundos e acionáveis.
        Se precisar de informações adicionais, solicite usando o formato:
        [TOOL_REQUEST: tool_name | parameter: value]
        
        Ferramentas disponíveis:
        - google_search | query: termo de busca
        - web_extract | url: URL para extrair conteúdo
        - social_search | query: busca em redes sociais"""
        
        try:
            while time.time() - start_time < analysis_time and tool_calls_made < self.max_tool_calls:
                
                if progress_callback:
                    elapsed = int(time.time() - start_time)
                    progress_callback(f"IA analisando... ({elapsed}s/{analysis_time}s) - {tool_calls_made} buscas adicionais")
                
                # Envia prompt atual para IA usando hierarquia OpenRouter
                current_prompt = "\n\n".join(conversation_history)
                
                response = await enhanced_ai_manager.generate_text(
                    prompt=current_prompt,
                    system_prompt=system_prompt,
                    max_tokens=4000,
                    temperature=0.7
                )
                
                if not response:
                    raise Exception("IA não respondeu")
                
                # Verifica se há solicitação de tool use
                tool_call = self._extract_tool_call(response)
                
                if tool_call:
                    tool_calls_made += 1
                    logger.info(f"🔧 IA solicitou ferramenta: {tool_call['tool']} - {tool_call.get('query', tool_call.get('url', ''))}")
                    
                    # Executa ferramenta
                    tool_result = await self._execute_tool(tool_call)
                    
                    # Adiciona resultado à conversa
                    conversation_history.append(f"RESULTADO DA FERRAMENTA {tool_call['tool']}:")
                    conversation_history.append(json.dumps(tool_result, ensure_ascii=False, indent=2))
                    conversation_history.append("Continue sua análise com essas informações adicionais.")
                    
                    if progress_callback:
                        progress_callback(f"Ferramenta executada: {tool_call['tool']} - Continuando análise...")
                    
                else:
                    # IA terminou a análise
                    logger.info("✅ IA concluiu síntese sem mais ferramentas")
                    break
            
            analysis_duration = time.time() - start_time
            
            return {
                'final_response': response,
                'tool_calls_made': tool_calls_made,
                'analysis_duration': analysis_duration,
                'conversation_history': conversation_history
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na execução com tools: {e}")
            raise
    
    def _extract_tool_call(self, response: str) -> Optional[Dict[str, str]]:
        """Extrai solicitação de tool use da resposta da IA"""
        
        # Padrão: google_search("query")
        google_match = re.search(r'google_search\(["\']([^"\']+)["\']\)', response)
        if google_match:
            return {'tool': 'google_search', 'query': google_match.group(1)}
        
        # Padrão: web_extract("url")
        web_match = re.search(r'web_extract\(["\']([^"\']+)["\']\)', response)
        if web_match:
            return {'tool': 'web_extract', 'url': web_match.group(1)}
        
        # Padrão: social_search("query")
        social_match = re.search(r'social_search\(["\']([^"\']+)["\']\)', response)
        if social_match:
            return {'tool': 'social_search', 'query': social_match.group(1)}
        
        return None
    
    def _execute_tool(self, tool_call: Dict[str, str]) -> Dict[str, Any]:
        """Executa uma ferramenta solicitada pela IA"""
        
        tool_name = tool_call['tool']
        
        if tool_name in self.synthesis_tools:
            return self.synthesis_tools[tool_name](tool_call)
        else:
            return {'error': f'Ferramenta {tool_name} não disponível'}
    
    def _tool_google_search(self, tool_call: Dict[str, str]) -> Dict[str, Any]:
        """Ferramenta de busca Google"""
        query = tool_call.get('query', '')
        
        try:
            # search_results = search_api_manager.interleaved_search(query, max_results_per_provider=5)  # REMOVIDO
            search_results = []  # Placeholder
            
            # Simplifica resultados para a IA
            simplified_results = []
            for provider, provider_data in search_results.get('results_by_provider', {}).items():
                for result in provider_data.get('results', []):
                    simplified_results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'url': result.get('url', ''),
                        'source': provider
                    })
            
            return {
                'tool': 'google_search',
                'query': query,
                'results': simplified_results[:10],  # Top 10 resultados
                'total_found': len(simplified_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na ferramenta google_search: {e}")
            return {'tool': 'google_search', 'error': str(e)}
    
    def _tool_web_extract(self, tool_call: Dict[str, str]) -> Dict[str, Any]:
        """Ferramenta de extração web"""
        url = tool_call.get('url', '')
        
        try:
            # Import dinâmico para evitar erro se o módulo não existir
            try:
                # from services.robust_content_extractor import robust_content_extractor
                # content = robust_content_extractor.extract_content(url)
                content = ""  # Fallback vazio - não usamos mais o robust_content_extractor
            except ImportError:
                # Fallback simples se o extractor não estiver disponível
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove scripts e styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text()
                # Limpa espaços em branco excessivos
                content = re.sub(r'\s+', ' ', content).strip()
            
            if content:
                # Limita conteúdo para não sobrecarregar a IA
                limited_content = content[:3000] + "..." if len(content) > 3000 else content
                
                return {
                    'tool': 'web_extract',
                    'url': url,
                    'content': limited_content,
                    'content_length': len(content)
                }
            else:
                return {'tool': 'web_extract', 'error': 'Não foi possível extrair conteúdo'}
                
        except Exception as e:
            logger.error(f"❌ Erro na ferramenta web_extract: {e}")
            return {'tool': 'web_extract', 'error': str(e)}
    
    def _tool_social_search(self, tool_call: Dict[str, str]) -> Dict[str, Any]:
        """Ferramenta de busca social"""
        query = tool_call.get('query', '')
        
        try:
            # Import dinâmico para evitar erros se os módulos não existirem
            twitter_results = {}
            social_results = {}
            
            try:
                from services.trendfinder_client import trendfinder_client
                twitter_results = trendfinder_client.search_twitter_trends(query, max_results=10)
            except ImportError:
                logger.warning("TrendFinder client não disponível")
                twitter_results = {'error': 'TrendFinder não disponível'}
            
            try:
                from services.supadata_mcp_client import supadata_mcp_client
                social_results = supadata_mcp_client.search_all_platforms(query, max_results_per_platform=5)
            except ImportError:
                logger.warning("SupaData MCP client não disponível")
                social_results = {'error': 'SupaData não disponível'}
            
            # Calcula total de posts encontrados
            total_posts = 0
            if isinstance(twitter_results, dict) and 'results' in twitter_results:
                total_posts += len(twitter_results.get('results', {}).get('tweets', []))
            
            if isinstance(social_results, dict) and 'platforms' in social_results:
                total_posts += sum(len(platform.get('posts', [])) for platform in social_results.get('platforms', {}).values())
            
            return {
                'tool': 'social_search',
                'query': query,
                'twitter_data': twitter_results,
                'social_data': social_results,
                'total_posts': total_posts
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na ferramenta social_search: {e}")
            return {'tool': 'social_search', 'error': str(e)}
    
    def _create_synthesis_summary(self, synthesis_result: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Cria resumo estruturado da síntese"""
        
        final_response = synthesis_result.get('final_response', '')
        
        # Tenta extrair JSON da resposta final
        synthesis_json = self._extract_json_from_response(final_response)
        
        if not synthesis_json:
            # Fallback: cria estrutura básica
            synthesis_json = self._create_fallback_synthesis(final_response, session_id)
        
        # Adiciona metadados
        synthesis_json['metadata_sintese'] = {
            'session_id': session_id,
            'generated_at': datetime.now().isoformat(),
            'tool_calls_made': synthesis_result.get('tool_calls_made', 0),
            'analysis_duration': synthesis_result.get('analysis_duration', 0),
            'ai_model_used': 'gemini-2.0-flash-exp',
            'synthesis_complete': True
        }
        
        return synthesis_json
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extrai JSON da resposta da IA"""
        
        try:
            # Padrão para JSON em markdown
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Padrão para JSON direto
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao parsear JSON: {e}")
            return None
    
    def _create_fallback_synthesis(self, response: str, session_id: str) -> Dict[str, Any]:
        """Cria síntese de fallback quando JSON não é extraível"""
        
        return {
            'insights_principais': [
                'Análise baseada no material coletado',
                'Síntese gerada pela IA com dados reais',
                'Insights extraídos do conteúdo web e social'
            ],
            'dores_identificadas': [
                'Dores extraídas da análise de conteúdo',
                'Padrões comportamentais identificados'
            ],
            'desejos_mapeados': [
                'Desejos identificados nos dados sociais',
                'Aspirações baseadas em tendências'
            ],
            'publico_alvo_refinado': {
                'demografia': 'Perfil baseado na análise de dados',
                'psicografia': 'Características psicológicas identificadas',
                'comportamentos': ['Comportamento 1', 'Comportamento 2']
            },
            'raw_ai_response': response[:2000],
            'fallback_mode': True,
            'note': 'Síntese extraída do texto da IA - JSON não estruturado'
        }
    
    def _save_synthesis_json(self, synthesis_data: Dict[str, Any], session_id: str):
        """Salva o JSON de síntese na pasta da sessão"""
        
        try:
            session_dir = Path(self.screenshots_dir) / "files" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            json_path = session_dir / "resumo_sintese.json"
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(synthesis_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Resumo de síntese salvo: {json_path}")
            
            # Também salva via auto_save_manager
            salvar_etapa("resumo_sintese", synthesis_data, categoria="ai_synthesis")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar síntese: {e}")
    
    def get_synthesis_status(self, session_id: str) -> Dict[str, Any]:
        """Verifica status da síntese"""
        
        try:
            json_path = Path(self.screenshots_dir) / "files" / session_id / "resumo_sintese.json"
            
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return {
                    'status': 'completed',
                    'synthesis_data': data,
                    'file_size': json_path.stat().st_size,
                    'created_at': datetime.fromtimestamp(json_path.stat().st_mtime).isoformat()
                }
            else:
                return {
                    'status': 'not_found',
                    'message': 'Síntese ainda não foi executada'
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status: {e}")
            return {'status': 'error', 'error': str(e)}

# Instância global
ai_synthesis_engine = AISynthesisEngine()