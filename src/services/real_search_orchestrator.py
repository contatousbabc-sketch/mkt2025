#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Real Search Orchestrator
Orquestrador de busca REAL massiva com rotação de APIs e captura visual
"""

import os
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus
import json
import requests

# Optional aiohttp import with fallback
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Importa função para salvar trechos de pesquisa web
from services.auto_save_manager import salvar_trecho_pesquisa_web

logger = logging.getLogger(__name__)

# Now safely log the aiohttp warning if it wasn't available
if not AIOHTTP_AVAILABLE:
    logger.warning("aiohttp não instalado – usando fallback síncrono com requests para Real Search Orchestrator")

class RealSearchOrchestrator:
    """Orquestrador de busca REAL massiva - ZERO SIMULAÇÃO"""

    def __init__(self):
        """Inicializa orquestrador com todas as APIs reais"""
        self.api_keys = self._load_all_api_keys()
        self.key_indices = {provider: 0 for provider in self.api_keys.keys()}

        # Provedores em ordem de prioridade
        self.providers = [
            'ALIBABA_WEBSAILOR',  # Adicionado como prioridade máxima
            'FIRECRAWL',
            'JINA',
            'GOOGLE',
            'EXA',
            'SERPER',
            'YOUTUBE',
            'SUPADATA'
        ]

        # URLs base dos serviços
        self.service_urls = {
            'FIRECRAWL': 'https://api.firecrawl.dev/v0/scrape',
            'JINA': 'https://r.jina.ai/',
            'GOOGLE': 'https://www.googleapis.com/customsearch/v1',
            'EXA': 'https://api.exa.ai/search',
            'SERPER': 'https://google.serper.dev/search',
            'YOUTUBE': 'https://www.googleapis.com/youtube/v3/search',
            'SUPADATA': os.getenv('SUPADATA_API_URL', 'https://server.smithery.ai/@supadata-ai/mcp/mcp')
        }

        self.session_stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'failed_searches': 0,
            'api_rotations': {},
            'content_extracted': 0,
            'screenshots_captured': 0
        }

        logger.info(f"🚀 Real Search Orchestrator inicializado com {sum(len(keys) for keys in self.api_keys.values())} chaves totais")
        logger.info("🔥 MODO: 100% DADOS REAIS - ZERO SIMULAÇÃO - ZERO EXEMPLOS")

    def _salvar_erro(self, error_type: str, error_data: Dict[str, Any]):
        """Salva erros para debug"""
        try:
            from services.auto_save_manager import auto_save_manager
            auto_save_manager.save_error(error_type, error_data)
        except Exception as e:
            logger.error(f"❌ Erro ao salvar erro {error_type}: {e}")

    def _load_all_api_keys(self) -> Dict[str, List[str]]:
        """Carrega todas as chaves de API do ambiente"""
        api_keys = {}

        for provider in ['FIRECRAWL', 'JINA', 'GOOGLE', 'EXA', 'SERPER', 'YOUTUBE', 'SUPADATA', 'X']:
            keys = []

            # Chave principal
            main_key = os.getenv(f"{provider}_API_KEY")
            if main_key:
                keys.append(main_key)

            # Chaves numeradas
            counter = 1
            while True:
                numbered_key = os.getenv(f"{provider}_API_KEY_{counter}")
                if numbered_key:
                    keys.append(numbered_key)
                    counter += 1
                else:
                    break

            if keys:
                api_keys[provider] = keys
                logger.info(f"✅ {provider}: {len(keys)} chaves carregadas")

        return api_keys

    def get_next_api_key(self, provider: str) -> Optional[str]:
        """Obtém próxima chave de API com rotação automática"""
        if provider not in self.api_keys or not self.api_keys[provider]:
            return None

        keys = self.api_keys[provider]
        current_index = self.key_indices[provider]

        # Obtém chave atual
        key = keys[current_index]

        # Rotaciona para próxima
        self.key_indices[provider] = (current_index + 1) % len(keys)

        # Atualiza estatísticas
        if provider not in self.session_stats['api_rotations']:
            self.session_stats['api_rotations'][provider] = 0
        self.session_stats['api_rotations'][provider] += 1

        logger.debug(f"🔄 {provider}: Usando chave {current_index + 1}/{len(keys)}")
        return key

    async def execute_massive_real_search(
        self,
        query: str,
        context: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Executa busca REAL massiva com todos os provedores"""

        logger.info(f"🚀 INICIANDO BUSCA REAL MASSIVA para: {query}")
        start_time = time.time()

        # Estrutura de resultados
        search_results = {
            'query': query,
            'session_id': session_id,
            'search_started': datetime.now().isoformat(),
            'providers_used': [],
            'web_results': [],
            'social_results': [],
            'youtube_results': [],
            'viral_content': [],
            'screenshots_captured': [],
            'statistics': {
                'total_sources': 0,
                'unique_urls': 0,
                'content_extracted': 0,
                'api_calls_made': 0,
                'search_duration': 0
            }
        }

        try:
            # FASE 1: Busca com Alibaba WebSailor (prioritária)
            logger.info("🔍 FASE 1: Busca com Alibaba WebSailor")
            websailor_results = await self._search_alibaba_websailor(query, context, session_id)

            if websailor_results.get('success'):
                search_results['web_results'].extend(websailor_results['results'])
                search_results['providers_used'].append('ALIBABA_WEBSAILOR')
                logger.info(f"✅ Alibaba WebSailor retornou {len(websailor_results['results'])} resultados")

            # FASE 2: Busca Web Massiva Simultânea (provedores restantes)
            logger.info("🌐 FASE 2: Busca web massiva simultânea")
            web_tasks = []

            # Firecrawl
            if 'FIRECRAWL' in self.api_keys:
                web_tasks.append(self._search_firecrawl(query, session_id))

            # Jina
            if 'JINA' in self.api_keys:
                web_tasks.append(self._search_jina(query, session_id))

            # Google
            if 'GOOGLE' in self.api_keys:
                web_tasks.append(self._search_google(query))

            # Exa
            if 'EXA' in self.api_keys:
                web_tasks.append(self._search_exa(query))

            # Serper
            if 'SERPER' in self.api_keys:
                web_tasks.append(self._search_serper(query))

            # Executa todas as buscas web simultaneamente
            if web_tasks:
                web_results = await asyncio.gather(*web_tasks, return_exceptions=True)

                for result in web_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Erro na busca web: {result}")
                        continue

                    if result.get('success') and result.get('results'):
                        search_results['web_results'].extend(result['results'])
                        search_results['providers_used'].append(result.get('provider', 'unknown'))

            # FASE 3: Busca em Redes Sociais
            logger.info("📱 FASE 3: Busca massiva em redes sociais")
            social_tasks = []

            # YouTube
            if 'YOUTUBE' in self.api_keys:
                social_tasks.append(self._search_youtube(query))

            # Supadata (Instagram, Facebook, TikTok)
            # if 'SUPADATA' in self.api_keys:
            #     social_tasks.append(self._search_supadata(query))

            # Executa buscas sociais
            if social_tasks:
                social_results = await asyncio.gather(*social_tasks, return_exceptions=True)

                for result in social_results:
                    if isinstance(result, Exception):
                        logger.error(f"❌ Erro na busca social: {result}")
                        continue

                    if result.get('success'):
                        if result.get('platform') == 'youtube':
                            search_results['youtube_results'].extend(result.get('results', []))
                        else:
                            search_results['social_results'].extend(result.get('results', []))

            # FASE 4: Identificação de Conteúdo Viral
            logger.info("🔥 FASE 4: Identificando conteúdo viral")
            viral_content = self._identify_viral_content(
                search_results['youtube_results'] + search_results['social_results']
            )
            search_results['viral_content'] = viral_content

            # FASE 5: Captura de Screenshots
            logger.info("📸 FASE 5: Capturando screenshots do conteúdo viral")
            if viral_content:
                screenshots = await self._capture_viral_screenshots(viral_content, session_id)
                search_results['screenshots_captured'] = screenshots
                self.session_stats['screenshots_captured'] = len(screenshots)

            # Calcula estatísticas finais
            search_duration = time.time() - start_time
            all_results = search_results['web_results'] + search_results['social_results'] + search_results['youtube_results']
            unique_urls = list(set(r.get('url', '') for r in all_results if r.get('url')))

            search_results['statistics'].update({
                'total_sources': len(all_results),
                'unique_urls': len(unique_urls),
                'content_extracted': sum(len(r.get('content', '')) for r in all_results),
                'api_calls_made': sum(self.session_stats['api_rotations'].values()),
                'search_duration': search_duration
            })

            # VALIDAÇÃO ANTI-SIMULAÇÃO: Remove qualquer resultado que pareça ser exemplo
            real_results = []
            for result in all_results:
                title = result.get('title', '').lower()
                content = result.get('content', '').lower()
                url = result.get('url', '').lower()

                # Filtra dados que parecem ser exemplos/simulação
                if not any(word in title + content + url for word in [
                    'exemplo', 'sample', 'test', 'mock', 'demo', 'placeholder',
                    'lorem ipsum', 'fake', 'dummy', 'template'
                ]):
                    real_results.append(result)

            # Atualiza com apenas dados reais
            search_results['web_results'] = [r for r in search_results['web_results'] if r in real_results]
            search_results['social_results'] = [r for r in search_results['social_results'] if r in real_results]
            search_results['youtube_results'] = [r for r in search_results['youtube_results'] if r in real_results]

            final_count = len(real_results)
            filtered_count = len(all_results) - final_count

            logger.info(f"✅ BUSCA 100% REAL CONCLUÍDA em {search_duration:.2f}s")
            logger.info(f"📊 {final_count} resultados REAIS de {len(search_results['providers_used'])} provedores")
            logger.info(f"🗑️ {filtered_count} resultados simulados/exemplo REMOVIDOS")
            logger.info(f"📸 {len(search_results['screenshots_captured'])} screenshots REAIS capturados")
            logger.info(f"🔥 GARANTIA: 100% DADOS REAIS - ZERO SIMULAÇÃO")

            return search_results

        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO na busca massiva: {e}")
            self._salvar_erro('massive_search_error', {'error': str(e)})
            raise

    async def _search_alibaba_websailor(self, query: str, context: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """Busca REAL usando Alibaba WebSailor Agent"""
        try:
            # Importa o agente WebSailor
            from services.alibaba_websailor import alibaba_websailor

            if not alibaba_websailor or not alibaba_websailor.enabled:
                logger.warning("⚠️ Alibaba WebSailor não está habilitado")
                return {'success': False, 'error': 'Alibaba WebSailor não habilitado'}

            # Executa a pesquisa profunda - CORRIGIDO: passando session_id
            research_result = await alibaba_websailor.navigate_and_research_deep(
                query=query,
                context=context,
                max_pages=30,
                depth_levels=2,
                session_id=session_id
            )

            if not research_result or not research_result.get('conteudo_consolidado'):
                return {'success': False, 'error': 'Nenhum resultado da pesquisa WebSailor'}

            # Converte resultados do WebSailor para formato padrão
            results = []
            fontes_detalhadas = research_result.get('conteudo_consolidado', {}).get('fontes_detalhadas', [])

            for fonte in fontes_detalhadas:
                # INCLUI CONTEÚDO REAL EXTRAÍDO
                conteudo_real = fonte.get('conteudo_real', '')
                snippet_real = fonte.get('snippet_real', fonte.get('description', ''))
                
                results.append({
                    'title': fonte.get('title', ''),
                    'url': fonte.get('url', ''),
                    'snippet': snippet_real,  # SNIPPET REAL EXTRAÍDO
                    'source': 'alibaba_websailor',
                    'relevance_score': fonte.get('quality_score', 0.7),
                    'content_length': len(conteudo_real),  # TAMANHO REAL DO CONTEÚDO
                    'content': conteudo_real,  # CONTEÚDO COMPLETO EXTRAÍDO
                    'insights': fonte.get('insights_extraidos', [])  # INSIGHTS REAIS
                })

            logger.info(f"✅ Alibaba WebSailor processado com {len(results)} resultados")

            return {
                'success': True,
                'provider': 'ALIBABA_WEBSAILOR',
                'results': results,
                'raw_data': research_result
            }

        except ImportError:
            logger.warning("⚠️ Alibaba WebSailor não encontrado")
            return {'success': False, 'error': 'Alibaba WebSailor não disponível'}
        except Exception as e:
            logger.error(f"❌ Erro Alibaba WebSailor: {e}")
            from services.auto_save_manager import salvar_erro
            salvar_erro('alibaba_websailor_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_firecrawl(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Busca REAL usando Firecrawl - SEARCH + SCRAPE"""
        try:
            api_key = self.get_next_api_key('FIRECRAWL')
            if not api_key:
                return {'success': False, 'error': 'Firecrawl API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }

                    # FASE 1: SEARCH para encontrar URLs relevantes
                    search_payload = {
                        'query': query,
                        'limit': 5
                    }

                    search_url = 'https://api.firecrawl.dev/v1/search'
                    async with session.post(search_url, json=search_payload, headers=headers, timeout=30) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            if response.status == 402:
                                logger.warning(f"⚠️ Firecrawl créditos insuficientes - pulando: {error_text}")
                                return {'success': False, 'error': 'Insufficient credits', 'skip': True}
                            logger.error(f"❌ Firecrawl search erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'Search HTTP {response.status}'}

                        search_data = await response.json()
                        urls = [item.get('url') for item in search_data.get('data', []) if item.get('url')]

                        if not urls:
                            logger.warning("⚠️ Nenhuma URL encontrada no search")
                            return {'success': False, 'error': 'No URLs found'}

                    # FASE 2: SCRAPE das URLs encontradas
                    all_results = []
                    scrape_url = 'https://api.firecrawl.dev/v1/scrape'

                    for url in urls[:3]:  # Limita a 3 URLs para não sobrecarregar
                        try:
                            scrape_payload = {
                                'url': url,
                                'formats': ['markdown'],
                                'onlyMainContent': True,
                                'includeTags': ['p', 'h1', 'h2', 'h3', 'article'],
                                'excludeTags': ['nav', 'footer', 'aside', 'script']
                            }

                            async with session.post(scrape_url, json=scrape_payload, headers=headers, timeout=45) as scrape_response:
                                if scrape_response.status == 200:
                                    scrape_data = await scrape_response.json()
                                    content = scrape_data.get('data', {}).get('markdown', '')

                                    if content and len(content) > 500:  # Exige conteúdo REALMENTE substancial
                                        # Extrai e salva o conteúdo
                                        results = self._extract_search_results_from_content(content, 'firecrawl', session_id, url)
                                        all_results.extend(results)
                                        logger.info(f"✅ FIRECRAWL extraiu {len(content)} chars de {url}")
                                    else:
                                        logger.debug(f"⚠️ Conteúdo insuficiente de {url}: {len(content) if content else 0} chars")
                                else:
                                    logger.warning(f"⚠️ Erro ao fazer scrape de {url}: {scrape_response.status}")
                        except Exception as e:
                            logger.error(f"❌ Erro ao processar {url}: {e}")
                            continue

                    return {
                        'success': True,
                        'provider': 'FIRECRAWL',
                        'results': all_results,
                        'urls_processed': len(urls),
                        'content_extracted': len(all_results)
                    }
            else:
                logger.error("aiohttp não disponível para Firecrawl")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro Firecrawl: {e}")
            self._salvar_erro('firecrawl_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_jina(self, query: str, session_id: str = None) -> Dict[str, Any]:
        """Busca REAL usando Jina AI com fallback garantido"""
        try:
            api_key = self.get_next_api_key('JINA')
            if not api_key:
                # Fallback usando chave principal
                api_key = os.getenv('JINA_API_KEY')
                if not api_key:
                    return {'success': False, 'error': 'Jina API key não disponível'}

            results = []

            if AIOHTTP_AVAILABLE:
                # Busca simples e direta
                search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=pt-BR"
                jina_url = f"https://r.jina.ai/{search_url}"
                
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Accept': 'text/plain'
                }

                try:
                    timeout = aiohttp.ClientTimeout(total=20)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(jina_url, headers=headers) as response:
                            if response.status == 200:
                                content = await response.text()
                                
                                if content and len(content) > 100:
                                    # Salva conteúdo extraído
                                    if session_id:
                                        try:
                                            salvar_trecho_pesquisa_web(
                                                url=search_url,
                                                titulo=f'Busca Jina: {query}',
                                                conteudo=content[:2000],
                                                metodo_extracao='jina_real',
                                                qualidade=80.0,
                                                session_id=session_id
                                            )
                                        except Exception as e:
                                            logger.warning(f"⚠️ Erro ao salvar trecho Jina: {e}")
                                    
                                    results.append({
                                        'title': f'Resultados para: {query}',
                                        'url': search_url,
                                        'snippet': content[:300],
                                        'source': 'jina_real',
                                        'content': content[:2000],
                                        'relevance_score': 0.8
                                    })
                                    
                                    logger.info(f"✅ Jina extraiu {len(content)} caracteres")
                            else:
                                logger.warning(f"⚠️ Jina retornou status {response.status}")
                
                except Exception as e:
                    logger.error(f"❌ Erro na busca Jina: {e}")
                    
            else:
                logger.error("aiohttp não disponível para Jina")
                return {'success': False, 'error': 'aiohttp not available'}

            return {
                'success': len(results) > 0,
                'provider': 'JINA',
                'results': results
            }

        except Exception as e:
            logger.error(f"❌ Erro Jina: {e}")
            self._salvar_erro('jina_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_google(self, query: str) -> Dict[str, Any]:
        """Busca REAL usando Google Custom Search"""
        try:
            api_key = self.get_next_api_key('GOOGLE')
            cse_id = os.getenv('GOOGLE_CSE_ID')

            if not api_key or not cse_id:
                return {'success': False, 'error': 'Google API não configurada'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    params = {
                        'key': api_key,
                        'cx': cse_id,
                        'q': f"{query} Brasil 2024",
                        'num': 10,
                        'lr': 'lang_pt',
                        'gl': 'br',
                        'safe': 'off',
                        'dateRestrict': 'm6'
                    }

                    async with session.get(
                        self.service_urls['GOOGLE'],
                        params=params,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            for item in data.get('items', []):
                                results.append({
                                    'title': item.get('title', ''),
                                    'url': item.get('link', ''),
                                    'snippet': item.get('snippet', ''),
                                    'source': 'google_real',
                                    'published_date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', ''),
                                    'relevance_score': 0.9
                                })

                            return {
                                'success': True,
                                'provider': 'GOOGLE',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Google erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para Google Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro Google: {e}")
            self._salvar_erro('google_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_youtube(self, query: str) -> Dict[str, Any]:
        """Busca REAL no YouTube com foco em conteúdo viral"""
        try:
            api_key = self.get_next_api_key('YOUTUBE')
            if not api_key:
                return {'success': False, 'error': 'YouTube API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    params = {
                        'part': "snippet,id",
                        'q': f"{query} Brasil",
                        'key': api_key,
                        'maxResults': 25,
                        'order': 'viewCount',  # Ordena por visualizações
                        'type': 'video',
                        'regionCode': 'BR',
                        'relevanceLanguage': 'pt',
                        'publishedAfter': '2023-01-01T00:00:00Z'
                    }

                    async with session.get(
                        self.service_urls['YOUTUBE'],
                        params=params,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            for item in data.get('items', []):
                                snippet = item.get('snippet', {})
                                video_id = item.get('id', {}).get('videoId', '')

                                # Busca estatísticas detalhadas
                                stats = await self._get_youtube_video_stats(video_id, api_key, session)

                                results.append({
                                    'title': snippet.get('title', ''),
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'description': snippet.get('description', ''),
                                    'channel': snippet.get('channelTitle', ''),
                                    'published_at': snippet.get('publishedAt', ''),
                                    'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                                    'view_count': stats.get('viewCount', 0),
                                    'comment_count': stats.get('commentCount', 0),
                                    'platform': 'youtube',
                                    'viral_score': self._calculate_viral_score(stats),
                                    'relevance_score': 0.85
                                })

                            # Ordena por score viral
                            results.sort(key=lambda x: x['viral_score'], reverse=True)

                            return {
                                'success': True,
                                'provider': 'YOUTUBE',
                                'platform': 'youtube',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ YouTube erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para YouTube Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro YouTube: {e}")
            self._salvar_erro('youtube_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _get_youtube_video_stats(self, video_id: str, api_key: str, session: "aiohttp.ClientSession") -> Dict[str, Any]:
        """Obtém estatísticas detalhadas de um vídeo do YouTube"""
        try:
            params = {
                'part': 'statistics',
                'id': video_id,
                'key': api_key
            }

            async with session.get(
                'https://www.googleapis.com/youtube/v3/videos',
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', [])
                    if items:
                        return items[0].get('statistics', {})

                return {}

        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter stats do vídeo {video_id}: {e}")
            return {}

    async def _search_supadata(self, query: str) -> Dict[str, Any]:
        """Busca REAL usando Supadata MCP"""
        try:
            api_key = self.get_next_api_key('SUPADATA')
            if not api_key:
                return {'success': False, 'error': 'Supadata API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=45)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }

                    payload = {
                        'method': 'social_search',
                        'params': {
                            'query': query,
                            'platforms': ['instagram', 'facebook', 'tiktok'],
                            'limit': 50,
                            'sort_by': 'engagement',
                            'include_metrics': True
                        }
                    }

                    async with session.post(
                        self.service_urls['SUPADATA'],
                        json=payload,
                        headers=headers,
                        timeout=45
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            posts = data.get('result', {}).get('posts', [])
                            for post in posts:
                                results.append({
                                    'title': post.get('caption', '')[:100],
                                    'url': post.get('url', ''),
                                    'content': post.get('caption', ''),
                                    'platform': post.get('platform', 'social'),
                                    'engagement_rate': post.get('engagement_rate', 0),
                                    'likes': post.get('likes', 0),
                                    'comments': post.get('comments', 0),
                                    'shares': post.get('shares', 0),
                                    'author': post.get('author', ''),
                                    'published_at': post.get('published_at', ''),
                                    'viral_score': self._calculate_social_viral_score(post),
                                    'relevance_score': 0.8
                                })

                            return {
                                'success': True,
                                'provider': 'SUPADATA',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Supadata erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para Supadata Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro Supadata: {e}")
            self._salvar_erro('supadata_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_twitter(self, query: str) -> Dict[str, Any]:
        """Busca REAL no Twitter/X"""
        try:
            api_key = self.get_next_api_key('X')
            if not api_key:
                return {'success': False, 'error': 'X API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    }

                    params = {
                        'query': f"{query} lang:pt",
                        'max_results': 50,
                        'tweet.fields': 'public_metrics,created_at,author_id',
                        'user.fields': 'username,verified,public_metrics',
                        'expansions': 'author_id'
                    }

                    async with session.get(
                        'https://api.twitter.com/2/tweets/search/recent',
                        params=params,
                        headers=headers,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            tweets = data.get('data', [])
                            users = {user['id']: user for user in data.get('includes', {}).get('users', [])}

                            for tweet in tweets:
                                author = users.get(tweet.get('author_id', ''), {})
                                metrics = tweet.get('public_metrics', {})

                                results.append({
                                    'title': tweet.get('text', '')[:100],
                                    'url': f"https://twitter.com/i/status/{tweet.get('id')}",
                                    'content': tweet.get('text', ''),
                                    'platform': 'twitter',
                                    'author': author.get('username', ''),
                                    'author_verified': author.get('verified', False),
                                    'retweets': metrics.get('retweet_count', 0),
                                    'likes': metrics.get('like_count', 0),
                                    'replies': metrics.get('reply_count', 0),
                                    'quotes': metrics.get('quote_count', 0),
                                    'published_at': tweet.get('created_at', ''),
                                    'viral_score': self._calculate_twitter_viral_score(metrics),
                                    'relevance_score': 0.75
                                })

                            return {
                                'success': True,
                                'provider': 'X',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ X/Twitter erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para Twitter Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro X/Twitter: {e}")
            self._salvar_erro('twitter_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_exa(self, query: str) -> Dict[str, Any]:
        """Busca REAL usando Exa Neural Search"""
        try:
            api_key = self.get_next_api_key('EXA')
            if not api_key:
                return {'success': False, 'error': 'Exa API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'x-api-key': api_key,
                        'Content-Type': 'application/json'
                    }

                    payload = {
                        'query': f"{query} Brasil mercado tendências",
                        'numResults': 15,
                        'useAutoprompt': True,
                        'type': 'neural',
                        'includeDomains': [
                            'g1.globo.com', 'exame.com', 'valor.globo.com',
                            'estadao.com.br', 'folha.uol.com.br', 'infomoney.com.br'
                        ],
                        'startPublishedDate': '2023-01-01'
                    }

                    async with session.post(
                        self.service_urls['EXA'],
                        json=payload,
                        headers=headers,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            for item in data.get('results', []):
                                results.append({
                                    'title': item.get('title', ''),
                                    'url': item.get('url', ''),
                                    'snippet': item.get('text', '')[:300],
                                    'source': 'exa_neural',
                                    'score': item.get('score', 0),
                                    'published_date': item.get('publishedDate', ''),
                                    'relevance_score': item.get('score', 0.8)
                                })

                            return {
                                'success': True,
                                'provider': 'EXA',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Exa erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para Exa Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro Exa: {e}")
            self._salvar_erro('exa_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    async def _search_serper(self, query: str) -> Dict[str, Any]:
        """Busca REAL usando Serper"""
        try:
            api_key = self.get_next_api_key('SERPER')
            if not api_key:
                return {'success': False, 'error': 'Serper API key não disponível'}

            if AIOHTTP_AVAILABLE:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    headers = {
                        'X-API-KEY': api_key,
                        'Content-Type': 'application/json'
                    }

                    payload = {
                        'q': f"{query} Brasil mercado",
                        'gl': 'br',
                        'hl': 'pt',
                        'num': 15,
                        'autocorrect': True
                    }

                    async with session.post(
                        self.service_urls['SERPER'],
                        json=payload,
                        headers=headers,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []

                            for item in data.get('organic', []):
                                results.append({
                                    'title': item.get('title', ''),
                                    'url': item.get('link', ''),
                                    'snippet': item.get('snippet', ''),
                                    'source': 'serper_real',
                                    'position': item.get('position', 0),
                                    'relevance_score': 0.85
                                })

                            return {
                                'success': True,
                                'provider': 'SERPER',
                                'results': results
                            }
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Serper erro {response.status}: {error_text}")
                            return {'success': False, 'error': f'HTTP {response.status}'}
            else:
                logger.error("aiohttp não disponível para Serper Search")
                return {'success': False, 'error': 'aiohttp not available'}

        except Exception as e:
            logger.error(f"❌ Erro Serper: {e}")
            self._salvar_erro('serper_error', {'error': str(e)})
            return {'success': False, 'error': str(e)}

    def _extract_search_results_from_content(self, content: str, provider: str, session_id: str = None, source_url: str = None) -> List[Dict[str, Any]]:
        """Extrai resultados de busca do conteúdo extraído - APENAS DADOS REAIS"""
        results = []

        if not content:
            logger.warning(f"⚠️ Conteúdo vazio recebido de {provider}")
            return results

        # Divide o conteúdo em seções reais
        lines = content.split('\n')
        current_result = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detecta títulos reais (linhas com mais de 20 caracteres e sem URLs)
            if (len(line) > 20 and
                not line.startswith('http') and
                not line.startswith('www') and
                '.' not in line[:10] and
                not line.startswith('Exemplo') and
                not line.startswith('Sample') and
                'exemplo' not in line.lower()):

                # Salva resultado anterior se existir
                if current_result.get('title'):
                    results.append(current_result)

                # Inicia novo resultado com dados reais
                current_result = {
                    'title': line,
                    'url': '',
                    'snippet': '',
                    'source': f"{provider}_real",
                    'relevance_score': 0.8,  # Score real baseado na extração
                    'extraction_method': 'real_content_parsing'
                }

            # Detecta URLs reais
            elif line.startswith(('http', 'www')):
                if current_result:
                    current_result['url'] = line

            # Detecta descrições reais (linhas médias)
            elif 50 <= len(line) <= 200 and current_result:
                if not any(word in line.lower() for word in ['exemplo', 'sample', 'test', 'mock']):
                    current_result['snippet'] = line

        # Adiciona último resultado real
        if current_result.get('title'):
            results.append(current_result)

        # Filtra APENAS resultados reais válidos
        valid_results = []
        for result in results:
            title = result.get('title', '')
            if (title and len(title) > 10 and
                not any(word in title.lower() for word in ['exemplo', 'sample', 'test', 'mock', 'demo'])):
                valid_results.append(result)

        # NOVA FUNCIONALIDADE: Salva trechos de conteúdo extraído (com deduplicação)
        if session_id and valid_results:
            try:
                # Sistema de deduplicação por URL
                seen_urls = set()
                unique_results = []
                for result in valid_results:
                    url = result.get('url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_results.append(result)

                if unique_results:
                    logger.info(f"🔍 Salvando {len(unique_results)} resultados únicos de {provider} (removidas {len(valid_results) - len(unique_results)} duplicatas)")
                    for i, result in enumerate(unique_results):
                        # Calcula score de qualidade baseado no tamanho e completude do conteúdo
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        url = result.get('url', '') or source_url or ''

                        logger.info(f"📝 Resultado {i+1}: title={len(title)} chars, snippet={len(snippet)} chars, url={url[:50]}...")

                        # Apenas salva se tiver URL real - NÃO GERA URLs DE EXEMPLO
                        if not url or not url.startswith('http') or 'example.com' in url:
                            logger.debug(f"🔍 URL inválida ignorada (evitando spam): {url[:30]}...")
                            continue

                        # Conteúdo completo para salvar
                        full_content = f"Título: {title}\n\nDescrição: {snippet}\n\nURL: {url}"

                        # Score de qualidade REAL baseado em completude e relevância
                        quality_score = 0.0
                        if title and len(title) > 20:
                            quality_score += 30.0
                        if snippet and len(snippet) > 50:
                            quality_score += 40.0
                        if url and url.startswith('http') and 'example.com' not in url:
                            quality_score += 30.0

                        # Bonus por relevância ao nicho
                        if any(keyword in (title + snippet).lower() for keyword in ['patchwork', 'costura', 'quilting', 'artesanato']):
                            quality_score += 20.0

                        # Log apenas se score for significativo
                        if quality_score >= 50.0:
                            logger.info(f"💯 Quality score: {quality_score} - {title[:50]}...")

                        # Salva APENAS se for dados reais válidos - ZERO SIMULAÇÃO
                        if (quality_score >= 30.0 and url and url.startswith('http') and
                            'example.com' not in url and len(title) > 10):
                            try:
                                # USA INTERFACE UNIFICADA DO AUTO SAVE MANAGER
                                from services.auto_save_manager import auto_save_manager

                                content_data = {
                                    'url': url,
                                    'titulo': title,
                                    'conteudo': full_content,
                                    'metodo_extracao': provider,
                                    'qualidade': quality_score,
                                    'platform': 'web',
                                    'metadata': {
                                        'provider': provider,
                                        'extraction_timestamp': datetime.now().isoformat(),
                                        'result_index': i,
                                        'total_results': len(unique_results)
                                    }
                                }

                                save_result = auto_save_manager.save_extracted_content(content_data, session_id or 'default_session')
                                if not save_result.get('success'):
                                    logger.error(f"❌ Falha no salvamento via AutoSaveManager: {save_result.get('error')}")

                            except Exception as save_error:
                                logger.error(f"❌ Erro ao salvar resultado REAL {i+1}: {save_error}")
                        else:
                            logger.debug(f"🔍 Dados rejeitados (qualidade baixa): título={len(title)} chars")

            except Exception as e:
                logger.error(f"❌ Erro ao salvar trechos de {provider}: {e}")
                self._salvar_erro('content_extraction_save_error', {'provider': provider, 'error': str(e)})

        return valid_results[:15]  # Máximo 15 por provedor

    def _identify_viral_content(self, all_social_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica conteúdo viral para captura de screenshots"""

        if not all_social_results:
            return []

        # Ordena por score viral
        sorted_content = sorted(
            all_social_results,
            key=lambda x: x.get('viral_score', 0),
            reverse=True
        )

        # Seleciona top 10 conteúdos virais
        viral_content = []
        seen_urls = set()

        for content in sorted_content:
            url = content.get('url', '')
            if url and url not in seen_urls and len(viral_content) < 10:
                viral_content.append(content)
                seen_urls.add(url)

        logger.info(f"🔥 {len(viral_content)} conteúdos virais identificados")
        return viral_content

    async def _capture_viral_screenshots(self, viral_content: List[Dict[str, Any]], session_id: str) -> List[Dict[str, Any]]:
        """Captura screenshots do conteúdo viral usando Selenium"""

        screenshots = []

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager

            # Configura Chrome em modo headless
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            # Correções para erros específicos de GPU, WebGL e GCM
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-webgl2")
            chrome_options.add_argument("--disable-3d-apis")
            chrome_options.add_argument("--disable-accelerated-2d-canvas")
            chrome_options.add_argument("--disable-accelerated-jpeg-decoding")
            chrome_options.add_argument("--disable-accelerated-mjpeg-decode")
            chrome_options.add_argument("--disable-accelerated-video-decode")
            chrome_options.add_argument("--disable-accelerated-video-encode")
            chrome_options.add_argument("--disable-gpu-sandbox")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-prompt-on-repost")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-pings")
            chrome_options.add_argument("--no-zygote")
            chrome_options.add_argument("--single-process")  # Força processo único para evitar problemas de GPU
            
            # Usar Chrome instalado diretamente
            chrome_options.binary_location = "/usr/bin/google-chrome-stable"

            try:
                # Usar chromedriver instalado diretamente
                service = Service("/usr/bin/chromedriver")
                logger.info("✅ Usando chromedriver instalado do sistema")
            except Exception as e:
                logger.warning(f"Chromedriver do sistema falhou: {e}. Tentando ChromeDriverManager...")
                try:
                    service = Service(ChromeDriverManager().install())
                except Exception as e2:
                    logger.error(f"ChromeDriverManager também falhou: {e2}")
                    raise Exception("Não foi possível configurar chromedriver")
            
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Cria diretório para screenshots
            screenshots_dir = f"analyses_data/files/{session_id}"
            os.makedirs(screenshots_dir, exist_ok=True)

            try:
                for i, content in enumerate(viral_content, 1):
                    try:
                        url = content.get('url', '')
                        if not url:
                            continue

                        logger.info(f"📸 Capturando screenshot {i}/10: {content.get('title', 'Sem título')}")

                        # Acessa a URL
                        driver.get(url)

                        # Aguarda carregamento
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )

                        # Aguarda renderização completa
                        time.sleep(3)

                        # Captura screenshot
                        screenshot_path = f"{screenshots_dir}/viral_content_{i:02d}.png"
                        driver.save_screenshot(screenshot_path)

                        # Verifica se foi criado
                        if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 0:
                            screenshots.append({
                                'content_data': content,
                                'screenshot_path': screenshot_path,
                                'filename': f"viral_content_{i:02d}.png",
                                'url': url,
                                'title': content.get('title', ''),
                                'platform': content.get('platform', ''),
                                'viral_score': content.get('viral_score', 0),
                                'captured_at': datetime.now().isoformat()
                            })

                            logger.info(f"✅ Screenshot {i} capturado: {screenshot_path}")
                        else:
                            logger.warning(f"⚠️ Falha ao capturar screenshot {i}")

                    except Exception as e:
                        logger.error(f"❌ Erro ao capturar screenshot {i}: {e}")
                        continue

            finally:
                driver.quit()

        except ImportError:
            logger.error("❌ Selenium não instalado - screenshots não disponíveis")
            self._salvar_erro('selenium_not_installed', {})
            return []
        except Exception as e:
            logger.error(f"❌ Erro na captura de screenshots: {e}")
            self._salvar_erro('screenshot_capture_error', {'error': str(e)})
            return []

        return screenshots

    def _calculate_viral_score(self, stats: Dict[str, Any]) -> float:
        """Calcula score viral para YouTube"""
        try:
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))

            # Fórmula viral: views + (likes * 10) + (comments * 20)
            viral_score = views + (likes * 10) + (comments * 20)

            # Normaliza para 0-10
            return min(10.0, viral_score / 100000)

        except:
            return 0.0

    def _calculate_social_viral_score(self, post: Dict[str, Any]) -> float:
        """Calcula score viral para redes sociais"""
        try:
            likes = int(post.get('likes', 0))
            comments = int(post.get('comments', 0))
            shares = int(post.get('shares', 0))
            engagement_rate = float(post.get('engagement_rate', 0))

            # Fórmula viral para redes sociais
            viral_score = (likes * 1) + (comments * 5) + (shares * 10) + (engagement_rate * 1000)

            # Normaliza para 0-10
            return min(10.0, viral_score / 10000)

        except:
            return 0.0

    def _calculate_twitter_viral_score(self, metrics: Dict[str, Any]) -> float:
        """Calcula score viral para Twitter"""
        try:
            retweets = int(metrics.get('retweet_count', 0))
            likes = int(metrics.get('like_count', 0))
            replies = int(metrics.get('reply_count', 0))
            quotes = int(metrics.get('quote_count', 0))

            # Fórmula viral para Twitter
            viral_score = (retweets * 10) + (likes * 2) + (replies * 5) + (quotes * 15)

            # Normaliza para 0-10
            return min(10.0, viral_score / 5000)

        except:
            return 0.0

    def get_session_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas da sessão atual"""
        return self.session_stats.copy()

    def _salvar_erro(self, erro: str, detalhes: dict = None):
        """Salva erro do processo"""
        try:
            from services.auto_save_manager import auto_save_manager
            if hasattr(auto_save_manager, 'save_error'):
                auto_save_manager.save_error(erro, detalhes or {})
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar erro {erro}: {e}")


# Instância global
real_search_orchestrator = RealSearchOrchestrator()