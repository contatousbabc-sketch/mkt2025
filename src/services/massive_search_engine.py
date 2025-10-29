
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
        Executa busca massiva até atingir 300KB mínimo
        Salva em RES_BUSCA_[PRODUTO].json

        Aceita **kwargs para evitar erros com argumentos inesperados (ex: 'query').
        """
        # Logar argumentos inesperados para depuração
        if kwargs:
            logger.warning(f"⚠️ Argumentos inesperados recebidos e ignorados: {list(kwargs.keys())}")

        try:
            logger.info(f"🚀 INICIANDO BUSCA MASSIVA: {produto}")

            # Arquivo de resultado
            produto_clean = produto.replace(' ', '_').replace('/', '_')
            resultado_file = os.path.join(self.data_dir, f"RES_BUSCA_{produto_clean.upper()}.json")

            # Estrutura de dados massiva
            massive_data = {
                'produto': produto,
                'publico_alvo': publico_alvo,
                'session_id': session_id,
                'timestamp_inicio': datetime.now().isoformat(),
                'busca_massiva': {
                    'alibaba_websailor_results': [],  # ALIBABA WebSailor
                    'real_search_orchestrator_results': []  # Real Search Orchestrator
                },
                'viral_content': [],
                'marketing_insights': [],
                'competitor_analysis': [],
                'social_media_data': [],
                'content_analysis': [],
                'trend_analysis': [],
                'metadata': {
                    'total_searches': 0,
                    'apis_used': [],
                    'size_kb': 0,
                    'target_size_kb': self.min_size_kb
                }
            }

            # Queries de busca massiva
            search_queries = self._generate_search_queries(produto, publico_alvo)

            logger.info(f"📋 {len(search_queries)} queries geradas para busca massiva")

            # Executar buscas com limite fixo para evitar loop infinito
            current_size = 0
            search_count = 0
            max_searches = min(len(search_queries), 10)  # Máximo 10 buscas para evitar loop

            for query in search_queries[:max_searches]:  # Processa apenas as primeiras queries
                search_count += 1
                logger.info(f"🔍 Busca {search_count}: {query[:50]}...")

                # ALIBABA WebSailor - PRINCIPAL
                try:
                    websailor_result = await self._search_alibaba_websailor(query, session_id)
                    if websailor_result:
                        massive_data['busca_massiva']['alibaba_websailor_results'].append(websailor_result)
                        massive_data['metadata']['apis_used'].append('alibaba_websailor')
                        logger.info(f"✅ ALIBABA WebSailor: dados coletados")
                except Exception as e:
                    logger.warning(f"⚠️ ALIBABA WebSailor falhou: {e}")

                # REAL SEARCH ORCHESTRATOR JÁ FOI EXECUTADO NO WORKFLOW - EVITAR LOOP
                # Apenas registra que os dados já foram coletados
                # massive_data['metadata']['apis_used'].append('real_search_orchestrator_already_executed') # Removido para evitar poluição de metadados
                logger.info(f"✅ Real Search Orchestrator: dados já coletados no workflow principal (se aplicável)")

                # Verificar tamanho atual
                current_json = json.dumps(massive_data, ensure_ascii=False, indent=2)
                current_size = len(current_json.encode('utf-8'))

                logger.info(f"📊 Tamanho atual: {current_size/1024:.1f}KB / {self.min_size_kb}KB")

                # Pequena pausa entre buscas
                await asyncio.sleep(1)

            # Finalizar dados
            massive_data['timestamp_fim'] = datetime.now().isoformat()
            massive_data['metadata']['total_searches'] = search_count
            massive_data['metadata']['size_kb'] = current_size / 1024
            massive_data['metadata']['apis_used'] = list(set(massive_data['metadata']['apis_used']))

            # CONSOLIDAÇÃO: Coleta todos os dados salvos para arquivo único
            logger.info("🔄 Consolidando todos os dados salvos...")
            massive_data = self._consolidate_all_saved_data(massive_data, session_id)

            # Salva resultado final unificado
            save_result = self.auto_save_manager.save_massive_search_result(massive_data, produto)

            if save_result.get('success'):
                logger.info(f"✅ Resultado massivo CONSOLIDADO salvo: {save_result['filename']} ({save_result['size_kb']:.1f}KB)")
                return massive_data # Retorna o massive_data consolidado
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
        """Busca usando ALIBABA WebSailor com fallback simplificado"""
        try:
            logger.info(f"🌐 Tentando ALIBABA WebSailor para: {query}")

            # Tenta usar o websailor se disponível
            if self.websailor and hasattr(self.websailor, 'navigate_and_research_deep'):
                try:
                    navigation_result = await asyncio.wait_for(
                        self.websailor.navigate_and_research_deep(
                            query=query,
                            context={'session_id': session_id},
                            max_pages=3,
                            depth_levels=1,
                            session_id=session_id
                        ),
                        timeout=30.0
                    )
                    
                    if navigation_result:
                        logger.info(f"✅ ALIBABA WebSailor executado com sucesso")
                        return {
                            'query': query,
                            'api': 'alibaba_websailor',
                            'timestamp': datetime.now().isoformat(),
                            'navigation_data': navigation_result,
                            'source': 'ALIBABA_WEBSAILOR_SUCCESS',
                            'success': True
                        }
                
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Timeout no Alibaba WebSailor")
                except Exception as e:
                    logger.warning(f"⚠️ Erro no Alibaba WebSailor: {e}")
            
            # FALLBACK: Busca simples usando APIs disponíveis
            logger.info(f"🔄 Usando fallback para Alibaba WebSailor")
            
            # Tenta usar Jina como fallback
            jina_key = os.getenv('JINA_API_KEY')
            if jina_key:
                try:
                    import aiohttp
                    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    jina_url = f"https://r.jina.ai/{search_url}"
                    
                    headers = {
                        'Authorization': f'Bearer {jina_key}',
                        'Accept': 'text/plain'
                    }
                    
                    timeout = aiohttp.ClientTimeout(total=15)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(jina_url, headers=headers) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                return {
                                    'query': query,
                                    'api': 'alibaba_websailor_fallback',
                                    'timestamp': datetime.now().isoformat(),
                                    'fallback_data': content[:2000],
                                    'source': 'ALIBABA_WEBSAILOR_FALLBACK',
                                    'success': True
                                }
                                
                except Exception as e:
                    logger.warning(f"⚠️ Fallback Jina falhou: {e}")
            
            return {
                'query': query,
                'api': 'alibaba_websailor',
                'timestamp': datetime.now().isoformat(),
                'error': 'Não foi possível executar busca',
                'source': 'ALIBABA_WEBSAILOR_FAILED',
                'success': False
            }
            
        except Exception as e:
            logger.error(f"❌ ALIBABA WebSailor falhou completamente: {e}")
            return {
                'query': query,
                'api': 'alibaba_websailor',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'source': 'ALIBABA_WEBSAILOR_ERROR',
                'success': False
            }

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
                'trechos_pesquisa_web': [],  # Chave ausente adicionada
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

            # 1. COLETA TEXTOS DA PESQUISA WEB (ALIBABA WebSailor) E SALVA NO AUTO_SAVE_MANAGER
            try:
                if 'alibaba_websailor_results' in massive_data.get('busca_massiva', {}):
                    for result in massive_data['busca_massiva']['alibaba_websailor_results']:
                        if result and isinstance(result, dict):
                            nav_data = result.get('navigation_data', {})
                            if nav_data and isinstance(nav_data, dict):
                                conteudo = nav_data.get('conteudo_consolidado', {})
                                
                                # Textos principais - SALVA NO AUTO_SAVE_MANAGER
                                for i, texto in enumerate(conteudo.get('textos_principais', [])):
                                    texto_str = str(texto)
                                    if len(texto_str) > 50:  # Só salva textos relevantes
                                        # Salva no auto_save_manager para consolidação
                                        self.auto_save_manager.salvar_trecho_pesquisa_web(
                                            url=result.get('query', f'websailor_query_{i}'),
                                            titulo=f"WebSailor Texto Principal {i+1}",
                                            conteudo=texto_str,
                                            metodo_extracao='alibaba_websailor',
                                            qualidade=85.0,  # Alta qualidade para WebSailor
                                            session_id=session_id
                                        )
                                        
                                        # Também adiciona ao consolidado local
                                        dados_consolidados['textos_pesquisa_web'].append({
                                            'fonte': 'websailor_navegacao',
                                            'url': result.get('query', 'N/A'),
                                            'texto': texto_str,
                                            'caracteres': len(texto_str)
                                        })
                                        caracteres_totais += len(texto_str)
                                        textos_processados += 1
                                        if result.get('query') and result.get('query') != 'N/A':
                                            urls_unicas.add(result['query'])
                                
                                # Insights extraídos - SALVA NO AUTO_SAVE_MANAGER
                                for i, insight in enumerate(conteudo.get('insights_principais', [])):
                                    insight_str = str(insight)
                                    if len(insight_str) > 30:  # Só salva insights relevantes
                                        # Salva no auto_save_manager para consolidação
                                        self.auto_save_manager.salvar_trecho_pesquisa_web(
                                            url=result.get('query', f'websailor_insight_{i}'),
                                            titulo=f"WebSailor Insight {i+1}",
                                            conteudo=insight_str,
                                            metodo_extracao='alibaba_websailor_insights',
                                            qualidade=90.0,  # Muito alta qualidade para insights
                                            session_id=session_id
                                        )
                                        
                                        # Também adiciona ao consolidado local
                                        dados_consolidados['insights_extraidos'].append({
                                            'fonte': 'websailor_insights',
                                            'insight': insight_str,
                                            'caracteres': len(insight_str)
                                        })
                                        caracteres_totais += len(insight_str)
                
                logger.info(f"✅ Coletados {textos_processados} textos da pesquisa web (WebSailor) - SALVOS NO AUTO_SAVE_MANAGER")
            except Exception as e:
                logger.error(f"❌ Erro ao coletar textos web (WebSailor): {e}")

            # 1.5. COLETA DADOS DO REAL SEARCH ORCHESTRATOR E SALVA NO AUTO_SAVE_MANAGER
            try:
                if 'real_search_orchestrator_results' in massive_data.get('busca_massiva', {}):
                    for result in massive_data['busca_massiva']['real_search_orchestrator_results']:
                        if result and isinstance(result, dict):
                            result_data = result.get('data', {})
                            
                            # Processa web_results
                            for i, web_result in enumerate(result_data.get('web_results', [])):
                                if isinstance(web_result, dict):
                                    content = web_result.get('content', '') or web_result.get('snippet', '')
                                    title = web_result.get('title', f'Web Result {i+1}')
                                    url = web_result.get('url', f'real_search_web_{i}')
                                    
                                    if len(content) > 50:
                                        # Salva no auto_save_manager
                                        self.auto_save_manager.salvar_trecho_pesquisa_web(
                                            url=url,
                                            titulo=title,
                                            conteudo=content,
                                            metodo_extracao='real_search_orchestrator_web',
                                            qualidade=80.0,
                                            session_id=session_id
                                        )
                                        
                                        # Adiciona ao consolidado local
                                        dados_consolidados['textos_pesquisa_web'].append({
                                            'fonte': 'real_search_web',
                                            'url': url,
                                            'texto': content,
                                            'caracteres': len(content)
                                        })
                                        caracteres_totais += len(content)
                                        textos_processados += 1
                                        urls_unicas.add(url)
                            
                            # Processa social_results
                            for i, social_result in enumerate(result_data.get('social_results', [])):
                                if isinstance(social_result, dict):
                                    content = social_result.get('content', '') or social_result.get('text', '')
                                    title = social_result.get('title', f'Social Result {i+1}')
                                    url = social_result.get('url', f'real_search_social_{i}')
                                    
                                    if len(content) > 30:
                                        # Salva no auto_save_manager
                                        self.auto_save_manager.salvar_trecho_pesquisa_web(
                                            url=url,
                                            titulo=title,
                                            conteudo=content,
                                            metodo_extracao='real_search_orchestrator_social',
                                            qualidade=75.0,
                                            session_id=session_id
                                        )
                                        
                                        # Adiciona ao consolidado local
                                        dados_consolidados['textos_redes_sociais'].append({
                                            'fonte': 'real_search_social',
                                            'url': url,
                                            'texto': content,
                                            'caracteres': len(content)
                                        })
                                        caracteres_totais += len(content)
                                        textos_processados += 1
                                        urls_unicas.add(url)
                            
                            # Processa youtube_results
                            for i, youtube_result in enumerate(result_data.get('youtube_results', [])):
                                if isinstance(youtube_result, dict):
                                    content = youtube_result.get('description', '') or youtube_result.get('content', '')
                                    title = youtube_result.get('title', f'YouTube Result {i+1}')
                                    url = youtube_result.get('url', f'real_search_youtube_{i}')
                                    
                                    if len(content) > 40:
                                        # Salva no auto_save_manager
                                        self.auto_save_manager.salvar_trecho_pesquisa_web(
                                            url=url,
                                            titulo=title,
                                            conteudo=content,
                                            metodo_extracao='real_search_orchestrator_youtube',
                                            qualidade=70.0,
                                            session_id=session_id
                                        )
                                        
                                        # Adiciona ao consolidado local
                                        dados_consolidados['textos_pesquisa_web'].append({
                                            'fonte': 'real_search_youtube',
                                            'url': url,
                                            'texto': content,
                                            'caracteres': len(content)
                                        })
                                        caracteres_totais += len(content)
                                        textos_processados += 1
                                        urls_unicas.add(url)
                
                logger.info(f"✅ Coletados dados do Real Search Orchestrator - SALVOS NO AUTO_SAVE_MANAGER")
            except Exception as e:
                logger.error(f"❌ Erro ao coletar dados do Real Search Orchestrator: {e}")

            # 2. COLETA DADOS SALVOS EM ETAPAS ANTERIORES (do auto_save_manager)
            try:
                session_data = self.auto_save_manager.recuperar_etapa(session_id)
                if session_data and isinstance(session_data, dict):
                    extraction_steps = session_data.get('extraction_steps', [])
                    for step in extraction_steps:
                        try:
                            step_data = step.get('dados', {})
                            _extract_and_add_text(step_data, f"etapa_extracao_{step.get('nome', 'step')}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao processar step do auto_save_manager: {e}")
                logger.info(f"✅ Processados steps salvos do auto_save_manager")
            except Exception as e:
                logger.error(f"❌ Erro ao coletar etapas salvas do auto_save_manager: {e}")

            # 3. COLETA DADOS DE DIRETÓRIOS ESPECÍFICOS (relatorios_intermediarios, modulos_analises, jsons_gigantes, resultados_virais, pesquisa_web)
            data_categories = {
                'relatorios_intermediarios': 'etapas_extracao',
                'modulos_analises': 'modulos_analises',
                'jsons_gigantes': 'jsons_gigantes',
                'resultados_virais': 'resultados_virais',
                'pesquisa_web': 'trechos_pesquisa_web'
            }

            for category_dir, target_list_name in data_categories.items():
                try:
                    base_path = os.path.join(self.data_dir, category_dir)
                    if os.path.exists(base_path):
                        session_path = os.path.join(base_path, session_id)
                        if os.path.exists(session_path):
                            for arquivo in os.listdir(session_path):
                                if arquivo.endswith('.json'):
                                    arquivo_path = os.path.join(session_path, arquivo)
                                    try:
                                        with open(arquivo_path, 'r', encoding='utf-8') as f:
                                            dados_arquivo = json.load(f)
                                            
                                            # Adiciona ao massive_data['dados_consolidados_texto'] diretamente
                                            dados_consolidados[target_list_name].append({
                                                'arquivo_origem': arquivo,
                                                'tipo': category_dir,
                                                'dados': dados_arquivo
                                            })
                                            _extract_and_add_text(dados_arquivo, f"{category_dir}_file")

                                    except Exception as e:
                                        logger.warning(f"⚠️ Erro ao ler {arquivo_path} na categoria {category_dir}: {e}")
                    logger.info(f"✅ Coletados dados da categoria: {category_dir}")
                except Exception as e:
                    logger.error(f"❌ Erro ao coletar dados da categoria {category_dir}: {e}")

            # 4. ADICIONA METADADOS PARA A IA
            dados_consolidados['metadata_consolidacao'].update({
                'total_textos_processados': textos_processados,
                'caracteres_totais': caracteres_totais,
                'fontes_unicas': len(urls_unicas),
                'tamanho_kb': caracteres_totais / 1024,
                'urls_fonte': list(urls_unicas)[:10],  # Máximo 10 URLs para contexto
                'resumo_coleta': f"{textos_processados} textos, {caracteres_totais:,} chars, {len(urls_unicas)} fontes"
            })
            
            logger.info(f"📊 CONSOLIDAÇÃO TEXTUAL FINAL: {textos_processados} textos, {caracteres_totais:,} caracteres")
            
            # Adiciona dados consolidados ao massive_data (APENAS TEXTO)
            massive_data['dados_consolidados_texto'] = dados_consolidados

            logger.info(f"✅ CONSOLIDAÇÃO TEXTUAL CONCLUÍDA: {textos_processados} textos processados")
            logger.info(f"📝 Total: {caracteres_totais:,} caracteres para análise da IA")

            return massive_data

        except Exception as e:
            logger.error(f"❌ Erro na consolidação de dados: {e}")
            # Retorna dados originais se falhar
            return massive_data


# Instância global
massive_search_engine = MassiveSearchEngine()

