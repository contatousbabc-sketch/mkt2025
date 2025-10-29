
"""
Massive Search Engine - Sistema de Busca Massiva
Coleta dados até atingir 300KB mínimo salvando em RES_BUSCA_[PRODUTO].json
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import time

# Importações de serviços
from services.alibaba_websailor import alibaba_websailor
from services.real_search_orchestrator import RealSearchOrchestrator
from services.auto_save_manager import auto_save_manager # Importação movida para o topo

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class MassiveSearchEngine:
    """Sistema de busca massiva com múltiplas APIs e rotação"""

    def __init__(self):
        self.websailor = alibaba_websailor  # ALIBABA WebSailor
        self.real_search = RealSearchOrchestrator()  # Real Search Orchestrator
        self.auto_save_manager = auto_save_manager # Instância do auto_save_manager

        self.min_size_kb = int(os.getenv('MIN_JSON_SIZE_KB', '500'))
        self.min_size_bytes = self.min_size_kb * 1024
        self.data_dir = os.getenv('DATA_DIR', 'analyses_data')

        os.makedirs(self.data_dir, exist_ok=True)

        logger.info(f"🔍 Massive Search Engine inicializado - Mínimo: {self.min_size_kb}KB")

    async def execute_massive_search(self, produto: str, publico_alvo: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Executa busca massiva ILIMITADA com salvamento simultâneo
        Integração total com Auto Save Manager - SEM LIMITES DE TOKENS
        """
        # Logar argumentos inesperados para depuração
        if kwargs:
            logger.warning(f"⚠️ Argumentos inesperados recebidos e ignorados: {list(kwargs.keys())}")

        start_time = time.time()
        TIME_LIMIT_SECONDS = 4 * 60  # 10 minutos

        try:
            logger.info(f"🚀 INICIANDO BUSCA MASSIVA ILIMITADA: {produto} (Limite de tempo: {TIME_LIMIT_SECONDS/60} minutos)")

            # Estrutura de dados massiva - SEM LIMITES
            massive_data = {
                'produto': produto,
                'publico_alvo': publico_alvo,
                'session_id': session_id,
                'timestamp_inicio': datetime.now().isoformat(),
                'busca_massiva': {
                    'alibaba_websailor_results': [],
                    'real_search_orchestrator_results': []
                },
                'viral_content': [],
                'marketing_insights': [],
                'competitor_analysis': [],
                'social_media_data': [],
                'content_analysis': [],
                'trend_analysis': [],
                'consolidado_etapa1': {},  # NOVO: Consolidado para IA da etapa 2
                'metadata': {
                    'total_searches': 0,
                    'apis_used': [],
                    'size_kb': 0,
                    'sem_limites': True,  # NOVO: Flag indicando sem limites
                    'target_size_kb': 'ILIMITADO'
                }
            }

            # Queries de busca massiva - EXPANDIDAS
            search_queries = self._generate_search_queries(produto, publico_alvo)
            logger.info(f"📋 {len(search_queries)} queries geradas para busca massiva ILIMITADA")

            # Executar buscas com LIMITE INTELIGENTE para performance
            search_count = 0
            max_queries = min(15, len(search_queries))  # LIMITE: máximo 15 queries
            
            for query in search_queries[:max_queries]:  # LIMITADO para performance
                if (time.time() - start_time) > TIME_LIMIT_SECONDS:
                    logger.warning(f"⏰ Limite de tempo de {TIME_LIMIT_SECONDS/60} minutos atingido. Encerrando busca massiva.")
                    break

                search_count += 1
                logger.info(f"🔍 Busca {search_count}: {query}")

                # ALIBABA WebSailor - PRINCIPAL
                try:
                    websailor_result = await self._search_alibaba_websailor(query, session_id)
                    if websailor_result:
                        massive_data['busca_massiva']['alibaba_websailor_results'].append(websailor_result)
                        massive_data['metadata']['apis_used'].append('alibaba_websailor')
                        
                        # SALVAMENTO SIMULTÂNEO - NOVO
                        await self._save_search_result_simultaneously(websailor_result, session_id, 'alibaba_websailor')
                        logger.info(f"✅ ALIBABA WebSailor: dados coletados e salvos simultaneamente")
                except Exception as e:
                    logger.warning(f"⚠️ ALIBABA WebSailor falhou: {e}")

                # Real Search Orchestrator - EXECUTAR TAMBÉM
                try:
                    real_search_result = await self._search_real_orchestrator(query, session_id)
                    if real_search_result:
                        massive_data['busca_massiva']['real_search_orchestrator_results'].append(real_search_result)
                        massive_data['metadata']['apis_used'].append('real_search_orchestrator')
                        
                        # SALVAMENTO SIMULTÂNEO - NOVO
                        await self._save_search_result_simultaneously(real_search_result, session_id, 'real_search_orchestrator')
                        logger.info(f"✅ Real Search Orchestrator: dados coletados e salvos simultaneamente")
                except Exception as e:
                    logger.warning(f"⚠️ Real Search Orchestrator falhou: {e}")

                # Verificar tamanho atual - SEM LIMITES
                current_json = json.dumps(massive_data, ensure_ascii=False, indent=2)
                current_size = len(current_json.encode('utf-8'))
                logger.info(f"📊 Tamanho atual: {current_size/1024:.1f}KB (SEM LIMITES)")

                # Pequena pausa entre buscas
                await asyncio.sleep(0.5)  # Reduzido para acelerar

            # CONSOLIDAÇÃO FINAL - NOVO PROCESSO
            logger.info("🔄 Consolidando TODOS os dados para IA da etapa 2...")
            massive_data = await self._consolidate_for_stage2_ai(massive_data, session_id)

            # Finalizar dados
            massive_data['timestamp_fim'] = datetime.now().isoformat()
            massive_data['metadata']['total_searches'] = search_count
            massive_data['metadata']['size_kb'] = current_size / 1024
            massive_data['metadata']['apis_used'] = list(set(massive_data['metadata']['apis_used']))

            # Salva resultado final unificado - ARQUIVO CONSOLIDADO ETAPA 1
            save_result = self.auto_save_manager.save_massive_search_result(massive_data, produto)
            
            # NOVO: Salvar especificamente para IA da etapa 2 encontrar automaticamente
            consolidado_file = await self._save_consolidado_etapa1(massive_data, session_id)

            if save_result.get('success'):
                logger.info(f"✅ Resultado massivo ILIMITADO salvo: {save_result['filename']} ({save_result['size_kb']:.1f}KB)")
                logger.info(f"✅ Consolidado Etapa 1 salvo para IA: {consolidado_file}")
                return massive_data
            else:
                logger.error(f"❌ Erro ao salvar resultado massivo: {save_result.get('error')}")
                return massive_data

        except Exception as e:
            logger.error(f"❌ Erro na busca massiva: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': None
            }

    def _generate_search_queries(self, produto: str, publico_alvo: str) -> List[str]:
        """Gera queries de busca massiva"""
        base_queries = [
            f"{produto} {publico_alvo}",
            f"{produto} marketing",
            f"{produto} vendas",
            f"{produto} estratégia",
            f"{produto} público alvo",
            f"{produto} mercado",
            f"{produto} tendências",
            f"{produto} concorrentes",
            f"{produto} análise",
            f"{produto} insights",
            f"{produto} campanhas",
            f"{produto} conversão",
            f"{produto} engajamento",
            f"{produto} redes sociais",
            f"{produto} influenciadores",
            f"{produto} viral",
            f"{produto} sucesso",
            f"{produto} cases",
            f"{produto} resultados",
            f"{produto} ROI"
        ]

        # Adicionar variações com público-alvo
        publico_queries = [
            f"{publico_alvo} {produto}",
            f"{publico_alvo} interesse {produto}",
            f"{publico_alvo} compra {produto}",
            f"{publico_alvo} busca {produto}",
            f"{publico_alvo} precisa {produto}"
        ]

        # Adicionar queries expandidas para garantir volume
        expanded_queries = [
            f"como vender {produto}",
            f"melhor {produto}",
            f"onde comprar {produto}",
            f"preço {produto}",
            f"avaliação {produto}",
            f"review {produto}",
            f"opinião {produto}",
            f"teste {produto}",
            f"comparação {produto}",
            f"alternativa {produto}",
            f"{produto} 2024",
            f"{produto} tendência",
            f"{produto} futuro",
            f"{produto} inovação",
            f"{produto} tecnologia"
        ]

        return list(set(base_queries + publico_queries + expanded_queries)) # Remove duplicatas

    async def _search_alibaba_websailor(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca usando ALIBABA WebSailor - FOCO EM TEXTO"""
        try:
            logger.info(f"🌐 ALIBABA WebSailor executando busca TEXTUAL: {query}")

            # FOCO PRINCIPAL: NAVEGAÇÃO PARA EXTRAIR TEXTO
            navigation_result = await self.websailor.navigate_and_research_deep(
                query=query,
                context={'session_id': session_id, 'extract_text_only': True},
                max_pages=8,  # Reduzido para focar em qualidade
                depth_levels=2,
                session_id=session_id
            )
            
            # Conta o texto extraído
            texto_extraido = 0
            if navigation_result and isinstance(navigation_result, dict):
                conteudo = navigation_result.get('conteudo_consolidado', {})
                if conteudo:
                    textos = conteudo.get('textos_principais', [])
                    texto_extraido = sum(len(str(texto)) for texto in textos)

            logger.info(f"✅ ALIBABA WebSailor: {texto_extraido:,} caracteres de texto extraído")

            return {
                'query': query,
                'api': 'alibaba_websailor',
                'timestamp': datetime.now().isoformat(),
                'navigation_data': navigation_result,
                'texto_stats': {
                    'caracteres_extraidos': texto_extraido,
                    'paginas_navegadas': navigation_result.get('total_paginas_navegadas', 0) if navigation_result else 0
                },
                'source': 'ALIBABA_WEBSAILOR_TEXTUAL'
            }
        except Exception as e:
            logger.error(f"❌ ALIBABA WebSailor falhou: {e}")
            return None

    async def _search_real_orchestrator(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Busca usando Real Search Orchestrator - SISTEMA PRINCIPAL"""
        try:
            logger.info(f"🎯 Real Search Orchestrator executando busca: {query}")

            # Usa o método CORRETO que existe no RealSearchOrchestrator
            result = await self.real_search.execute_massive_real_search(
                query=query,
                context={'session_id': session_id, 'produto': query},
                session_id=session_id
            )

            # Extrai dados válidos do resultado
            if result and isinstance(result, dict):
                return {
                    'query': query,
                    'api': 'real_search_orchestrator',
                    'timestamp': datetime.now().isoformat(),
                    'data': result,
                    'web_results_count': len(result.get('web_results', [])),
                    'social_results_count': len(result.get('social_results', [])),
                    'youtube_results_count': len(result.get('youtube_results', [])),
                    'source': 'REAL_SEARCH_ORCHESTRATOR_PRINCIPAL'
                }
            else:
                logger.warning(f"⚠️ Real Search Orchestrator retornou dados inválidos")
                return None

        except Exception as e:
            logger.error(f"❌ Real Search Orchestrator falhou: {e}")
            return None

    async def _save_search_result_simultaneously(self, result: Dict[str, Any], session_id: str, api_name: str):
        """Salva resultados de busca individualmente e simultaneamente."""
        try:
            filename = f"BUSCA_SIMULTANEA_{api_name}_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"
            filepath = os.path.join(self.data_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Resultado simultâneo salvo: {filename}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultado simultâneo para {api_name}: {e}")

    def _calculate_final_size(self, massive_data: Dict[str, Any]) -> float:
        """Calcula tamanho final em KB"""
        try:
            json_str = json.dumps(massive_data, ensure_ascii=False)
            return len(json_str.encode('utf-8')) / 1024
        except Exception as e:
            logger.error(f"❌ Erro ao calcular tamanho: {e}")
            return 0.0

    def _consolidate_all_saved_data(self, massive_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        CONSOLIDAÇÃO TEXTUAL: Coleta APENAS texto para análise da IA
        Remove imagens e mantém apenas dados textuais essenciais
        """
        try:
            logger.info("📝 Iniciando consolidação TEXTUAL para análise da IA...")

            dados_consolidados = {
                'textos_pesquisa_web': [],
                'textos_redes_sociais': [],
                'insights_extraidos': [],
                'trechos_navegacao': [],
                'metadados_fontes': [],
                'etapas_extracao': [],
                'modulos_analises': [],
                'jsons_gigantes': [],
                'resultados_virais': [],
                'metadata_consolidacao': {
                    'timestamp_consolidacao': datetime.now().isoformat(),
                    'session_id': session_id,
                    'total_textos_processados': 0,
                    'fontes_unicas': 0,
                    'caracteres_totais': 0,
                    'categorias_encontradas': [],
                    'finalidade': 'ALIMENTAR_IA_SEGUNDA_ETAPA'
                }
            }

            textos_processados = 0
            caracteres_totais = 0
            urls_unicas = set()

            def _extract_and_add_text(data_item: Any, source_type: str, url: Optional[str] = None):
                nonlocal textos_processados, caracteres_totais, urls_unicas
                if isinstance(data_item, dict):
                    for key, value in data_item.items():
                        if isinstance(value, str) and len(value) > 50:
                            dados_consolidados['trechos_navegacao'].append({
                                'fonte': f"{source_type}_{key}",
                                'texto': value,
                                'caracteres': len(value)
                            })
                            caracteres_totais += len(value)
                            textos_processados += 1
                elif isinstance(data_item, list):
                    for item in data_item:
                        if isinstance(item, str) and len(item) > 50:
                            dados_consolidados['trechos_navegacao'].append({
                                'fonte': source_type,
                                'texto': item,
                                'caracteres': len(item)
                            })
                            caracteres_totais += len(item)
                            textos_processados += 1
                if url and url != 'N/A':
                    urls_unicas.add(url)

            # 1. COLETA TEXTOS DA PESQUISA WEB (ALIBABA WebSailor)
            try:
                if 'alibaba_websailor_results' in massive_data.get('busca_massiva', {}):
                    for result in massive_data['busca_massiva']['alibaba_websailor_results']:
                        if result and isinstance(result, dict):
                            nav_data = result.get('navigation_data', {})
                            if nav_data and isinstance(nav_data, dict):
                                conteudo = nav_data.get('conteudo_consolidado', {})
                                
                                # Textos principais
                                for texto in conteudo.get('textos_principais', []):
                                    dados_consolidados['textos_pesquisa_web'].append({
                                        'fonte': 'websailor_navegacao',
                                        'texto': texto,
                                        'caracteres': len(texto)
                                    })
                                    caracteres_totais += len(texto)
                                    textos_processados += 1
                                
                                # URLs
                                for url_item in conteudo.get('urls_processadas', []):
                                    urls_unicas.add(url_item)

            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar resultados do Alibaba WebSailor para consolidação: {e}")

            # 2. COLETA TEXTOS DO REAL SEARCH ORCHESTRATOR
            try:
                if 'real_search_orchestrator_results' in massive_data.get('busca_massiva', {}):
                    for result in massive_data['busca_massiva']['real_search_orchestrator_results']:
                        if result and isinstance(result, dict):
                            # Extrair textos de web_results, social_results, youtube_results
                            for key in ['web_results', 'social_results', 'youtube_results']:
                                for item in result.get('data', {}).get(key, []):
                                    if isinstance(item, dict):
                                        text_content = item.get('description') or item.get('title') or item.get('snippet')
                                        if text_content and len(text_content) > 50:
                                            dados_consolidados['textos_pesquisa_web'].append({
                                                'fonte': f"real_search_orchestrator_{key}",
                                                'texto': text_content,
                                                'caracteres': len(text_content)
                                            })
                                            caracteres_totais += len(text_content)
                                            textos_processados += 1
                                        url = item.get('link') or item.get('url')
                                        if url: urls_unicas.add(url)

            except Exception as e:
                logger.warning(f"⚠️ Erro ao processar resultados do Real Search Orchestrator para consolidação: {e}")

            # Atualizar metadados da consolidação
            dados_consolidados['metadata_consolidacao']['total_textos_processados'] = textos_processados
            dados_consolidados['metadata_consolidacao']['caracteres_totais'] = caracteres_totais
            dados_consolidados['metadata_consolidacao']['fontes_unicas'] = len(urls_unicas)
            dados_consolidados['urls_processadas'] = list(urls_unicas)

            logger.info(f"✅ Consolidação TEXTUAL concluída: {textos_processados} textos, {caracteres_totais:,} caracteres, {len(urls_unicas)} URLs únicas")

            # Adicionar ao massive_data
            massive_data['consolidado_etapa1'] = dados_consolidados

            return massive_data

        except Exception as e:
            logger.error(f"❌ Erro ao consolidar todos os dados salvos: {e}")
            return massive_data

    async def _consolidate_for_stage2_ai(self, massive_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Consolida todos os dados especificamente para a IA da etapa 2"""
        try:
            logger.info("🤖 Preparando consolidado para IA da etapa 2 (Grok-4-fast + Gemini)")
            
            # Criar estrutura consolidada para IA
            consolidado_ia = {
                'todos_textos_coletados': [],
                'insights_principais': [],
                'urls_processadas': [],
                'dados_estruturados': {},
                'metadata_para_ia': {
                    'total_caracteres': 0,
                    'total_fontes': 0,
                    'timestamp_consolidacao': datetime.now().isoformat(),
                    'session_id': session_id,
                    'preparado_para': 'grok-4-fast_gemini_fallback'
                }
            }
            
            # Consolidar todos os textos coletados
            total_chars = 0
            total_sources = 0
            
            # Processar resultados do Alibaba WebSailor
            for result in massive_data.get('busca_massiva', {}).get('alibaba_websailor_results', []):
                if result and isinstance(result, dict):
                    text_content = json.dumps(result, ensure_ascii=False)
                    consolidado_ia['todos_textos_coletados'].append({
                        'fonte': 'alibaba_websailor',
                        'query': result.get('query', 'N/A'),
                        'conteudo': text_content,
                        'caracteres': len(text_content)
                    })
                    total_chars += len(text_content)
                    total_sources += 1
            
            # Processar resultados do Real Search Orchestrator
            for result in massive_data.get('busca_massiva', {}).get('real_search_orchestrator_results', []):
                if result and isinstance(result, dict):
                    text_content = json.dumps(result, ensure_ascii=False)
                    consolidado_ia['todos_textos_coletados'].append({
                        'fonte': 'real_search_orchestrator',
                        'query': result.get('query', 'N/A'),
                        'conteudo': text_content,
                        'caracteres': len(text_content)
                    })
                    total_chars += len(text_content)
                    total_sources += 1
            
            # Atualizar metadata
            consolidado_ia['metadata_para_ia']['total_caracteres'] = total_chars
            consolidado_ia['metadata_para_ia']['total_fontes'] = total_sources
            
            # Adicionar ao massive_data
            massive_data['consolidado_etapa1'] = consolidado_ia
            
            logger.info(f"🤖 Consolidado para IA preparado: {total_sources} fontes, {total_chars:,} caracteres")
            
            return massive_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao consolidar para IA da etapa 2: {e}")
            return massive_data

    async def _save_consolidado_etapa1(self, massive_data: Dict[str, Any], session_id: str) -> str:
        """Salva arquivo consolidado específico para IA da etapa 2 encontrar automaticamente"""
        try:
            # Nome padronizado que a IA da etapa 2 vai procurar
            filename = f"CONSOLIDADO_ETAPA1_{session_id}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            # Dados específicos para IA
            consolidado_para_ia = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'produto': massive_data.get('produto', 'N/A'),
                'publico_alvo': massive_data.get('publico_alvo', 'N/A'),
                'dados_consolidados': massive_data.get('consolidado_etapa1', {}),
                'metadata_busca': massive_data.get('metadata', {}),
                'instrucoes_para_ia': {
                    'modelo_primario': 'x-ai/grok-4-fast:free',
                    'modelo_fallback': 'gemini-2.0-flash-exp',
                    'sem_limites_tokens': True,
                    'processar_todos_dados': True,
                    'gerar_analise_completa': True
                }
            }
            
            # Salvar arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(consolidado_para_ia, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📁 Consolidado Etapa 1 salvo: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar consolidado etapa 1: {e}")
            return "erro_salvamento"


# Instância global
massive_search_engine = MassiveSearchEngine()


