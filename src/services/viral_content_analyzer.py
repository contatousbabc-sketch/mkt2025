#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Viral Content Analyzer
Analisador de conteúdo viral usando instascrape
"""

import os
import logging
import asyncio
import time
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

# Instaloader imports (substitui instascrape)
try:
    import instaloader
    HAS_INSTALOADER = True
except ImportError:
    HAS_INSTALOADER = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ instaloader não encontrado. Instale com 'pip install instaloader'")

# Requests for fallback
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class ViralContentAnalyzer:
    """Analisador de conteúdo viral usando instascrape"""

    def __init__(self):
        """Inicializa o analisador"""
        self.viral_thresholds = {
            'youtube': {
                'min_views': 10000,
                'min_likes': 500,
                'min_comments': 50,
                'engagement_rate': 0.05
            },
            'instagram': {
                'min_likes': 1000,
                'min_comments': 50,
                'engagement_rate': 0.03
            },
            'facebook': {
                'min_likes': 1000,
                'min_comments': 50,
                'engagement_rate': 0.03
            },
            'twitter': {
                'min_retweets': 100,
                'min_likes': 500,
                'min_replies': 20
            },
            'tiktok': {
                'min_views': 50000,
                'min_likes': 2000,
                'min_shares': 100
            }
        }

        # Configurar diretórios
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        self.viral_data_dir = Path("viral_data")
        self.viral_data_dir.mkdir(exist_ok=True)

        # Inicializar instaloader se disponível
        if HAS_INSTALOADER:
            self.insta_loader = instaloader.Instaloader()
            logger.info("✅ Viral Content Analyzer inicializado com instaloader")
        else:
            self.insta_loader = None
            logger.warning("⚠️ Viral Content Analyzer inicializado sem instaloader - funcionalidade limitada")

    async def analyze_and_capture_viral_content(
        self,
        search_results: Dict[str, Any],
        session_id: str,
        max_captures: int = 15
    ) -> Dict[str, Any]:
        """Analisa e captura conteúdo viral dos resultados de busca"""

        logger.info(f"🔥 Analisando conteúdo viral para sessão: {session_id}")

        analysis_results = {
            'session_id': session_id,
            'analysis_started': datetime.now().isoformat(),
            'viral_content_identified': [],
            'screenshots_captured': [],
            'viral_metrics': {},
            'platform_analysis': {},
            'top_performers': [],
            'engagement_insights': {}
        }

        try:
            # FASE 1: Identificação de Conteúdo Viral
            logger.info("🎯 FASE 1: Identificando conteúdo viral")
            
            viral_urls = await self._identify_viral_content(search_results)
            analysis_results['viral_content_identified'] = viral_urls
            
            # FASE 2: Análise detalhada com instascrape
            logger.info("📊 FASE 2: Análise detalhada com instascrape")
            
            detailed_analysis = await self._analyze_with_instascrape(viral_urls[:max_captures])
            analysis_results['platform_analysis'] = detailed_analysis
            
            # FASE 3: Métricas e insights
            logger.info("📈 FASE 3: Calculando métricas e insights")
            
            metrics = self._calculate_viral_metrics(detailed_analysis)
            analysis_results['viral_metrics'] = metrics
            analysis_results['top_performers'] = self._get_top_performers(detailed_analysis)
            analysis_results['engagement_insights'] = self._generate_engagement_insights(detailed_analysis)
            
            analysis_results['analysis_completed'] = datetime.now().isoformat()
            analysis_results['success'] = True
            
            # Salvar resultados
            await self._save_analysis_results(analysis_results, session_id)
            
            logger.info(f"✅ Análise viral concluída: {len(viral_urls)} conteúdos identificados")
            
        except Exception as e:
            logger.error(f"❌ Erro na análise viral: {e}")
            analysis_results['error'] = str(e)
            analysis_results['success'] = False

        return analysis_results

    async def _identify_viral_content(self, search_results: Dict[str, Any]) -> List[Dict]:
        """Identifica conteúdo viral nos resultados de busca"""
        viral_content = []
        
        try:
            # Processar diferentes tipos de resultados
            for source, results in search_results.items():
                if isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict) and 'url' in result:
                            url = result['url']
                            platform = self._identify_platform(url)
                            
                            if platform and self._is_potentially_viral(result, platform):
                                viral_content.append({
                                    'url': url,
                                    'platform': platform,
                                    'source': source,
                                    'title': result.get('title', ''),
                                    'description': result.get('description', ''),
                                    'initial_score': self._calculate_initial_score(result, platform)
                                })
                                
        except Exception as e:
            logger.error(f"❌ Erro ao identificar conteúdo viral: {e}")
            
        logger.info(f"🎯 {len(viral_content)} conteúdos potencialmente virais identificados")
        return viral_content

    def _identify_platform(self, url: str) -> Optional[str]:
        """Identifica a plataforma baseada na URL"""
        url_lower = url.lower()
        
        if 'instagram.com' in url_lower:
            return 'instagram'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
            
        return None

    def _is_potentially_viral(self, result: Dict, platform: str) -> bool:
        """Verifica se o conteúdo é potencialmente viral"""
        try:
            # Verificar palavras-chave virais no título/descrição
            viral_keywords = [
                'viral', 'trending', 'popular', 'milhões', 'millions',
                'views', 'visualizações', 'curtidas', 'likes', 'shares',
                'compartilhamentos', 'comentários', 'comments'
            ]
            
            text_content = f"{result.get('title', '')} {result.get('description', '')}".lower()
            
            # Verificar presença de palavras-chave virais
            has_viral_keywords = any(keyword in text_content for keyword in viral_keywords)
            
            # Verificar números grandes no texto (indicativo de engajamento alto)
            numbers = re.findall(r'\d+', text_content)
            has_large_numbers = any(int(num) > 1000 for num in numbers if num.isdigit())
            
            return has_viral_keywords or has_large_numbers
            
        except Exception as e:
            logger.debug(f"Erro ao verificar viralidade: {e}")
            return False

    def _calculate_initial_score(self, result: Dict, platform: str) -> float:
        """Calcula score inicial baseado nos dados disponíveis"""
        score = 0.0
        
        try:
            # Score baseado em palavras-chave
            text_content = f"{result.get('title', '')} {result.get('description', '')}".lower()
            
            viral_keywords = {
                'viral': 10, 'trending': 8, 'popular': 6,
                'milhões': 15, 'millions': 15,
                'views': 5, 'visualizações': 5,
                'curtidas': 3, 'likes': 3
            }
            
            for keyword, points in viral_keywords.items():
                if keyword in text_content:
                    score += points
            
            # Score baseado em números encontrados
            numbers = re.findall(r'\d+', text_content)
            for num in numbers:
                if num.isdigit():
                    value = int(num)
                    if value > 1000000:  # Milhões
                        score += 20
                    elif value > 100000:  # Centenas de milhares
                        score += 15
                    elif value > 10000:  # Dezenas de milhares
                        score += 10
                    elif value > 1000:  # Milhares
                        score += 5
                        
        except Exception as e:
            logger.debug(f"Erro ao calcular score inicial: {e}")
            
        return min(score, 100.0)  # Máximo 100

    async def _analyze_with_instascrape(self, viral_urls: List[Dict]) -> Dict[str, List[Dict]]:
        """Analisa URLs usando instaloader (substitui instascrape)"""
        platform_analysis = {
            'instagram': [],
            'youtube': [],
            'facebook': [],
            'twitter': [],
            'tiktok': [],
            'other': []
        }
        
        if not HAS_INSTALOADER:
            logger.warning("⚠️ instaloader não disponível - usando análise básica")
            return await self._basic_analysis_fallback(viral_urls)
        
        for content in viral_urls:
            try:
                url = content['url']
                platform = content['platform']
                
                logger.info(f"📊 Analisando {platform}: {url}")
                
                if platform == 'instagram':
                    analysis = await self._analyze_instagram_post(url, content)
                    if analysis:
                        platform_analysis['instagram'].append(analysis)
                        
                elif platform == 'youtube':
                    analysis = await self._analyze_youtube_video(url, content)
                    if analysis:
                        platform_analysis['youtube'].append(analysis)
                        
                elif platform == 'tiktok':
                    analysis = await self._analyze_tiktok_video(url, content)
                    if analysis:
                        platform_analysis['tiktok'].append(analysis)
                        
                elif platform == 'facebook':
                    analysis = await self._analyze_facebook_post(url, content)
                    if analysis:
                        platform_analysis['facebook'].append(analysis)
                        
                elif platform == 'twitter':
                    analysis = await self._analyze_twitter_post(url, content)
                    if analysis:
                        platform_analysis['twitter'].append(analysis)
                        
                else:
                    # Para outras plataformas, usar análise básica
                    analysis = await self._basic_url_analysis(url, content)
                    if analysis:
                        platform_analysis.get(platform, platform_analysis['other']).append(analysis)
                        
                # Pequena pausa para evitar rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Erro ao analisar {content.get('url', 'URL desconhecida')}: {e}")
                continue
                
        return platform_analysis

    async def _analyze_instagram_post(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa post do Instagram usando instaloader com fallbacks robustos"""
        
        # Primeiro tenta com instaloader
        if HAS_INSTALOADER and self.insta_loader:
            try:
                logger.info(f"🔍 Tentando instaloader para: {url}")
                
                # Extrair shortcode da URL
                shortcode = self._extract_instagram_shortcode(url)
                if not shortcode:
                    logger.warning(f"⚠️ Não foi possível extrair shortcode de {url}")
                    return await self._analyze_basic_content(url, content)
                
                # Obter post usando instaloader
                post = instaloader.Post.from_shortcode(self.insta_loader.context, shortcode)
                
                # Verificar se conseguiu dados válidos
                if post:
                    # Extrair dados relevantes
                    analysis = {
                        'url': url,
                        'platform': 'instagram',
                        'title': content.get('title', ''),
                        'caption': post.caption or '',
                        'likes': post.likes,
                        'comments': post.comments,
                        'timestamp': post.date.isoformat() if post.date else '',
                        'owner': post.owner_username,
                        'hashtags': post.caption_hashtags,
                        'mentions': post.caption_mentions,
                        'is_video': post.is_video,
                        'engagement_rate': 0,
                        'viral_score': 0,
                        'analysis_timestamp': datetime.now().isoformat(),
                        'extraction_method': 'instaloader'
                    }
                    
                    # Calcular engagement rate (estimativa básica)
                    total_engagement = analysis['likes'] + analysis['comments']
                    if total_engagement > 0:
                        # Estimativa baseada no engajamento total
                        analysis['engagement_rate'] = min(total_engagement / 1000, 10.0)  # Máximo 10%
                    
                    # Calcular viral score
                    analysis['viral_score'] = self._calculate_viral_score(analysis, 'instagram')
                    
                    logger.info(f"✅ Instagram analisado via instaloader: {analysis['likes']} likes, {analysis['comments']} comentários")
                    return analysis
                else:
                    logger.warning(f"⚠️ instaloader não retornou dados válidos para {url}")
                    
            except Exception as e:
                logger.warning(f"⚠️ instaloader falhou para {url}: {e}")
        
        # Fallback: análise básica usando dados já coletados
        logger.info(f"🔄 Usando fallback para Instagram: {url}")
        return await self._instagram_fallback_analysis(url, content)

    async def _analyze_youtube_video(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa vídeo do YouTube usando yt-dlp com fallback para análise básica"""
        try:
            # Primeiro tenta com yt-dlp para dados reais
            try:
                import yt_dlp
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'skip_download': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    analysis = {
                        'url': url,
                        'platform': 'youtube',
                        'title': info.get('title', ''),
                        'description': info.get('description', '')[:500] if info.get('description') else '',
                        'views': info.get('view_count', 0),
                        'likes': info.get('like_count', 0),
                        'comments': info.get('comment_count', 0),
                        'duration': info.get('duration', 0),
                        'upload_date': info.get('upload_date', ''),
                        'uploader': info.get('uploader', ''),
                        'subscriber_count': info.get('uploader_subscriber_count', 0),
                        'engagement_rate': 0,
                        'viral_score': content.get('initial_score', 0),
                        'analysis_timestamp': datetime.now().isoformat(),
                        'analysis_method': 'yt_dlp_extraction'
                    }
                    
                    # Calcula engagement rate
                    if analysis['views'] > 0:
                        total_engagement = (analysis['likes'] or 0) + (analysis['comments'] or 0)
                        analysis['engagement_rate'] = (total_engagement / analysis['views']) * 100
                    
                    # Atualiza viral score baseado em métricas reais
                    if analysis['views'] > 1000000:  # 1M+ views
                        analysis['viral_score'] += 30
                    elif analysis['views'] > 100000:  # 100K+ views
                        analysis['viral_score'] += 20
                    elif analysis['views'] > 10000:  # 10K+ views
                        analysis['viral_score'] += 10
                    
                    if analysis['engagement_rate'] > 5:  # High engagement
                        analysis['viral_score'] += 15
                    elif analysis['engagement_rate'] > 2:
                        analysis['viral_score'] += 10
                    
                    logger.info(f"✅ YouTube análise yt-dlp: {analysis['views']} views, {analysis['likes']} likes")
                    return analysis
                    
            except ImportError:
                logger.warning("⚠️ yt-dlp não disponível, usando análise básica")
            except Exception as e:
                logger.warning(f"⚠️ Falha yt-dlp para {url}: {e}, usando fallback")
            
            # Fallback: análise básica usando dados já coletados
            analysis = {
                'url': url,
                'platform': 'youtube',
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'views': 0,
                'likes': 0,
                'comments': 0,
                'engagement_rate': 0,
                'viral_score': content.get('initial_score', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'basic_fallback'
            }
            
            # Tentar extrair números do título/descrição
            text_content = f"{analysis['title']} {analysis['description']}"
            numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(?:million|milhão|mil|k|thousand)', text_content.lower())
            
            for num_str in numbers:
                try:
                    num = float(num_str.replace(',', '.'))
                    if 'million' in text_content.lower() or 'milhão' in text_content.lower():
                        num *= 1000000
                    elif 'mil' in text_content.lower() or 'k' in text_content.lower() or 'thousand' in text_content.lower():
                        num *= 1000
                    
                    if analysis['views'] == 0:
                        analysis['views'] = int(num)
                    break
                except:
                    continue
            
            logger.info(f"📊 YouTube análise básica: {analysis['views']} views estimadas")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar YouTube video {url}: {e}")
            return None

    async def _analyze_tiktok_video(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa vídeo do TikTok com fallback para análise básica"""
        try:
            # TikTok API é complexa e requer configuração especial
            # Por enquanto, usar análise básica com extração de métricas do texto
            analysis = {
                'url': url,
                'platform': 'tiktok',
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'views': 0,
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'engagement_rate': 0,
                'viral_score': content.get('initial_score', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'basic_text_extraction'
            }
            
            # Extrair métricas do texto (TikTok frequentemente mostra números)
            text_content = f"{analysis['title']} {analysis['description']}"
            
            # Padrões para TikTok
            view_patterns = [r'(\d+(?:\.\d+)?)\s*(?:M|million|milhão|K|mil)\s*(?:views|visualizações)', 
                           r'(\d+(?:\.\d+)?)\s*(?:M|K)\s*views']
            like_patterns = [r'(\d+(?:\.\d+)?)\s*(?:M|K)\s*(?:likes|curtidas)']
            
            for pattern in view_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    try:
                        num = float(matches[0].replace(',', '.'))
                        if 'm' in text_content.lower() or 'million' in text_content.lower() or 'milhão' in text_content.lower():
                            num *= 1000000
                        elif 'k' in text_content.lower() or 'mil' in text_content.lower():
                            num *= 1000
                        analysis['views'] = int(num)
                        break
                    except:
                        continue
            
            # TikTok viral score boost
            if analysis['views'] > 10000000:  # 10M+ views (muito viral no TikTok)
                analysis['viral_score'] += 40
            elif analysis['views'] > 1000000:  # 1M+ views
                analysis['viral_score'] += 25
            elif analysis['views'] > 100000:  # 100K+ views
                analysis['viral_score'] += 15
            
            logger.info(f"📱 TikTok análise: {analysis['views']} views estimadas")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar TikTok video {url}: {e}")
            return None

    async def _analyze_facebook_post(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa post do Facebook com análise básica"""
        try:
            analysis = {
                'url': url,
                'platform': 'facebook',
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'reactions': 0,
                'engagement_rate': 0,
                'viral_score': content.get('initial_score', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'basic_text_extraction'
            }
            
            # Facebook tem métricas diferentes
            text_content = f"{analysis['title']} {analysis['description']}"
            
            # Procurar por números de engajamento
            engagement_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:likes|curtidas|reactions|reações)',
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:comments|comentários)',
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:shares|compartilhamentos)'
            ]
            
            for pattern in engagement_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    try:
                        num = float(matches[0].replace(',', '.'))
                        if 'm' in text_content.lower() or 'million' in text_content.lower() or 'milhão' in text_content.lower():
                            num *= 1000000
                        elif 'k' in text_content.lower() or 'mil' in text_content.lower():
                            num *= 1000
                        
                        if 'like' in pattern or 'curtida' in pattern or 'reaction' in pattern:
                            analysis['likes'] = int(num)
                        elif 'comment' in pattern or 'comentário' in pattern:
                            analysis['comments'] = int(num)
                        elif 'share' in pattern or 'compartilhamento' in pattern:
                            analysis['shares'] = int(num)
                        break
                    except:
                        continue
            
            # Facebook viral score
            total_engagement = analysis['likes'] + analysis['comments'] + analysis['shares']
            if total_engagement > 100000:
                analysis['viral_score'] += 30
            elif total_engagement > 10000:
                analysis['viral_score'] += 20
            elif total_engagement > 1000:
                analysis['viral_score'] += 10
            
            logger.info(f"📘 Facebook análise: {total_engagement} engajamento total estimado")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar Facebook post {url}: {e}")
            return None

    async def _analyze_twitter_post(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa post do Twitter/X com análise básica"""
        try:
            analysis = {
                'url': url,
                'platform': 'twitter',
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'likes': 0,
                'retweets': 0,
                'replies': 0,
                'views': 0,
                'engagement_rate': 0,
                'viral_score': content.get('initial_score', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'basic_text_extraction'
            }
            
            # Twitter/X métricas
            text_content = f"{analysis['title']} {analysis['description']}"
            
            # Padrões para Twitter
            twitter_patterns = [
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:likes|curtidas)',
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:retweets|RTs)',
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:replies|respostas)',
                r'(\d+(?:\.\d+)?)\s*(?:K|mil|M|million|milhão)\s*(?:views|visualizações)'
            ]
            
            for pattern in twitter_patterns:
                matches = re.findall(pattern, text_content.lower())
                if matches:
                    try:
                        num = float(matches[0].replace(',', '.'))
                        if 'm' in text_content.lower() or 'million' in text_content.lower() or 'milhão' in text_content.lower():
                            num *= 1000000
                        elif 'k' in text_content.lower() or 'mil' in text_content.lower():
                            num *= 1000
                        
                        if 'like' in pattern or 'curtida' in pattern:
                            analysis['likes'] = int(num)
                        elif 'retweet' in pattern or 'rt' in pattern:
                            analysis['retweets'] = int(num)
                        elif 'repl' in pattern or 'resposta' in pattern:
                            analysis['replies'] = int(num)
                        elif 'view' in pattern or 'visualização' in pattern:
                            analysis['views'] = int(num)
                        break
                    except:
                        continue
            
            # Twitter viral score
            total_engagement = analysis['likes'] + analysis['retweets'] + analysis['replies']
            if total_engagement > 50000:  # Twitter tem números menores que outras plataformas
                analysis['viral_score'] += 35
            elif total_engagement > 10000:
                analysis['viral_score'] += 25
            elif total_engagement > 1000:
                analysis['viral_score'] += 15
            
            if analysis['views'] > 1000000:
                analysis['viral_score'] += 20
            
            logger.info(f"🐦 Twitter análise: {total_engagement} engajamento, {analysis['views']} views")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar Twitter post {url}: {e}")
            return None

    async def _basic_url_analysis(self, url: str, content: Dict) -> Optional[Dict]:
        """Análise básica para URLs que não podem ser analisadas com instascrape"""
        try:
            analysis = {
                'url': url,
                'platform': content.get('platform', 'other'),
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'viral_score': content.get('initial_score', 0),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_method': 'basic_fallback'
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise básica de {url}: {e}")
            return None

    async def _instagram_fallback_analysis(self, url: str, content: Dict) -> Optional[Dict]:
        """Análise fallback para Instagram usando dados já coletados"""
        try:
            # Extrai informações básicas do conteúdo já coletado
            title = content.get('title', '')
            description = content.get('description', '')
            snippet = content.get('snippet', '')
            
            # Tenta extrair métricas do texto (se disponível)
            likes = self._extract_number_from_text(snippet + ' ' + description, ['likes', 'curtidas', 'gostei'])
            comments = self._extract_number_from_text(snippet + ' ' + description, ['comments', 'comentários', 'respostas'])
            
            # Análise básica do conteúdo textual
            hashtags = self._extract_hashtags(title + ' ' + description + ' ' + snippet)
            mentions = self._extract_mentions(title + ' ' + description + ' ' + snippet)
            
            analysis = {
                'url': url,
                'platform': 'instagram',
                'title': title,
                'caption': description or snippet,
                'likes': likes,
                'comments': comments,
                'timestamp': content.get('timestamp', ''),
                'owner': self._extract_username_from_url(url),
                'hashtags': hashtags,
                'mentions': mentions,
                'is_video': 'video' in (title + description).lower(),
                'engagement_rate': 0,
                'viral_score': 0,
                'analysis_timestamp': datetime.now().isoformat(),
                'extraction_method': 'fallback_analysis',
                'data_source': 'search_results'
            }
            
            # Calcular viral score baseado nos dados disponíveis
            analysis['viral_score'] = self._calculate_viral_score(analysis, 'instagram')
            
            logger.info(f"✅ Instagram analisado via fallback: {analysis['likes']} likes estimados")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise fallback do Instagram {url}: {e}")
            return None
    
    def _extract_number_from_text(self, text: str, keywords: List[str]) -> int:
        """Extrai números associados a palavras-chave do texto"""
        try:
            text_lower = text.lower()
            for keyword in keywords:
                # Procura padrões como "1.2K likes", "500 curtidas", etc.
                patterns = [
                    rf'(\d+(?:\.\d+)?[kmb]?)\s*{keyword}',
                    rf'{keyword}:\s*(\d+(?:\.\d+)?[kmb]?)',
                    rf'(\d+(?:\.\d+)?[kmb]?)\s+{keyword}'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        number_str = match.group(1)
                        return self._convert_number_string(number_str)
            return 0
        except:
            return 0
    
    def _convert_number_string(self, number_str: str) -> int:
        """Converte strings como '1.2K', '500', '2M' para números inteiros"""
        try:
            number_str = number_str.lower().strip()
            if 'k' in number_str:
                return int(float(number_str.replace('k', '')) * 1000)
            elif 'm' in number_str:
                return int(float(number_str.replace('m', '')) * 1000000)
            elif 'b' in number_str:
                return int(float(number_str.replace('b', '')) * 1000000000)
            else:
                return int(float(number_str))
        except:
            return 0
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extrai hashtags do texto"""
        try:
            hashtags = re.findall(r'#\w+', text)
            return [tag.lower() for tag in hashtags]
        except:
            return []
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extrai menções (@username) do texto"""
        try:
            mentions = re.findall(r'@\w+', text)
            return [mention.lower() for mention in mentions]
        except:
            return []
    
    def _extract_username_from_url(self, url: str) -> str:
        """Extrai username do Instagram da URL"""
        try:
            # Padrão: https://www.instagram.com/username/p/post_id/
            match = re.search(r'instagram\.com/([^/]+)/', url)
            if match:
                return match.group(1)
            return ''
        except:
            return ''

    async def _basic_analysis_fallback(self, viral_urls: List[Dict]) -> Dict[str, List[Dict]]:
        """Fallback para quando instascrape não está disponível"""
        platform_analysis = {
            'instagram': [],
            'youtube': [],
            'facebook': [],
            'twitter': [],
            'tiktok': [],
            'other': []
        }
        
        for content in viral_urls:
            try:
                platform = content.get('platform', 'other')
                analysis = await self._basic_url_analysis(content['url'], content)
                if analysis:
                    platform_analysis.get(platform, platform_analysis['other']).append(analysis)
                    
            except Exception as e:
                logger.error(f"❌ Erro na análise fallback: {e}")
                continue
                
        return platform_analysis

    def _extract_instagram_shortcode(self, url: str) -> Optional[str]:
        """Extrai shortcode de uma URL do Instagram"""
        try:
            # Padrões de URL do Instagram
            patterns = [
                r'instagram\.com/p/([A-Za-z0-9_-]+)',
                r'instagram\.com/reel/([A-Za-z0-9_-]+)',
                r'instagram\.com/tv/([A-Za-z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
                    
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair shortcode: {e}")
            return None

    def _calculate_viral_score(self, analysis: Dict, platform: str) -> float:
        """Calcula score viral baseado nas métricas da plataforma"""
        score = 0.0
        
        try:
            thresholds = self.viral_thresholds.get(platform, {})
            
            if platform == 'instagram':
                likes = analysis.get('likes', 0)
                comments = analysis.get('comments', 0)
                
                # Score baseado em likes
                if likes >= thresholds.get('min_likes', 1000):
                    score += 30
                elif likes >= thresholds.get('min_likes', 1000) * 0.5:
                    score += 15
                
                # Score baseado em comentários
                if comments >= thresholds.get('min_comments', 50):
                    score += 20
                elif comments >= thresholds.get('min_comments', 50) * 0.5:
                    score += 10
                
                # Score baseado em engagement rate
                engagement_rate = analysis.get('engagement_rate', 0)
                if engagement_rate >= thresholds.get('engagement_rate', 0.03) * 100:
                    score += 25
                elif engagement_rate >= thresholds.get('engagement_rate', 0.03) * 50:
                    score += 15
                
                # Bonus por hashtags e mentions
                hashtags = len(analysis.get('hashtags', []))
                mentions = len(analysis.get('mentions', []))
                score += min(hashtags * 2, 10)  # Máximo 10 pontos por hashtags
                score += min(mentions * 3, 15)  # Máximo 15 pontos por mentions
                
            elif platform == 'youtube':
                views = analysis.get('views', 0)
                likes = analysis.get('likes', 0)
                comments = analysis.get('comments', 0)
                
                # Score baseado em views
                if views >= thresholds.get('min_views', 10000):
                    score += 40
                elif views >= thresholds.get('min_views', 10000) * 0.5:
                    score += 20
                
                # Score baseado em likes
                if likes >= thresholds.get('min_likes', 500):
                    score += 20
                elif likes >= thresholds.get('min_likes', 500) * 0.5:
                    score += 10
                
                # Score baseado em comentários
                if comments >= thresholds.get('min_comments', 50):
                    score += 15
                elif comments >= thresholds.get('min_comments', 50) * 0.5:
                    score += 8
                    
        except Exception as e:
            logger.debug(f"Erro ao calcular viral score: {e}")
            
        return min(score, 100.0)  # Máximo 100

    def _calculate_viral_metrics(self, platform_analysis: Dict) -> Dict:
        """Calcula métricas gerais de viralidade"""
        metrics = {
            'total_content_analyzed': 0,
            'viral_content_count': 0,
            'average_viral_score': 0,
            'platform_distribution': {},
            'engagement_totals': {
                'total_likes': 0,
                'total_comments': 0,
                'total_shares': 0,
                'total_views': 0
            }
        }
        
        try:
            all_content = []
            viral_scores = []
            
            for platform, content_list in platform_analysis.items():
                if content_list:
                    metrics['platform_distribution'][platform] = len(content_list)
                    all_content.extend(content_list)
                    
                    for content in content_list:
                        viral_score = content.get('viral_score', 0)
                        viral_scores.append(viral_score)
                        
                        if viral_score >= 50:  # Considerado viral se score >= 50
                            metrics['viral_content_count'] += 1
                            
                        # Somar engajamento
                        metrics['engagement_totals']['total_likes'] += content.get('likes', 0)
                        metrics['engagement_totals']['total_comments'] += content.get('comments', 0)
                        metrics['engagement_totals']['total_shares'] += content.get('shares', 0)
                        metrics['engagement_totals']['total_views'] += content.get('views', 0)
            
            metrics['total_content_analyzed'] = len(all_content)
            
            if viral_scores:
                metrics['average_viral_score'] = sum(viral_scores) / len(viral_scores)
                
        except Exception as e:
            logger.error(f"❌ Erro ao calcular métricas virais: {e}")
            
        return metrics

    def _get_top_performers(self, platform_analysis: Dict, top_n: int = 10) -> List[Dict]:
        """Obtém os top performers por viral score"""
        all_content = []
        
        try:
            for platform, content_list in platform_analysis.items():
                all_content.extend(content_list)
            
            # Ordenar por viral score
            top_performers = sorted(
                all_content,
                key=lambda x: x.get('viral_score', 0),
                reverse=True
            )[:top_n]
            
            return top_performers
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter top performers: {e}")
            return []

    def _generate_engagement_insights(self, platform_analysis: Dict) -> Dict:
        """Gera insights sobre engajamento"""
        insights = {
            'best_performing_platform': '',
            'average_engagement_by_platform': {},
            'content_type_insights': {},
            'hashtag_insights': {},
            'timing_insights': {}
        }
        
        try:
            platform_scores = {}
            
            for platform, content_list in platform_analysis.items():
                if content_list:
                    scores = [content.get('viral_score', 0) for content in content_list]
                    platform_scores[platform] = sum(scores) / len(scores) if scores else 0
                    
                    # Engagement médio por plataforma
                    total_engagement = sum(
                        content.get('likes', 0) + content.get('comments', 0) + content.get('shares', 0)
                        for content in content_list
                    )
                    insights['average_engagement_by_platform'][platform] = total_engagement / len(content_list) if content_list else 0
            
            # Melhor plataforma
            if platform_scores:
                insights['best_performing_platform'] = max(platform_scores, key=platform_scores.get)
            
            # Insights sobre hashtags (apenas Instagram por enquanto)
            instagram_content = platform_analysis.get('instagram', [])
            hashtag_counts = {}
            
            for content in instagram_content:
                hashtags = content.get('hashtags', [])
                for hashtag in hashtags:
                    hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
            
            # Top 10 hashtags
            top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            insights['hashtag_insights'] = {
                'top_hashtags': top_hashtags,
                'total_unique_hashtags': len(hashtag_counts)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar insights de engajamento: {e}")
            
        return insights

    async def _save_analysis_results(self, results: Dict, session_id: str):
        """Salva os resultados da análise"""
        try:
            filename = f"viral_analysis_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.viral_data_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
            logger.info(f"💾 Análise viral salva: {filepath}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar análise viral: {e}")

    def get_analysis_summary(self, analysis_results: Dict) -> str:
        """Gera resumo textual da análise"""
        try:
            if not analysis_results.get('success', False):
                return "❌ Análise viral falhou"
            
            metrics = analysis_results.get('viral_metrics', {})
            total_analyzed = metrics.get('total_content_analyzed', 0)
            viral_count = metrics.get('viral_content_count', 0)
            avg_score = metrics.get('average_viral_score', 0)
            
            insights = analysis_results.get('engagement_insights', {})
            best_platform = insights.get('best_performing_platform', 'N/A')
            
            summary = f"""
🔥 ANÁLISE DE CONTEÚDO VIRAL - RESUMO

📊 Estatísticas Gerais:
• Total de conteúdos analisados: {total_analyzed}
• Conteúdos virais identificados: {viral_count}
• Score viral médio: {avg_score:.1f}/100
• Melhor plataforma: {best_platform}

📈 Engajamento Total:
• Likes: {metrics.get('engagement_totals', {}).get('total_likes', 0):,}
• Comentários: {metrics.get('engagement_totals', {}).get('total_comments', 0):,}
• Visualizações: {metrics.get('engagement_totals', {}).get('total_views', 0):,}

🏆 Top Performers:
"""
            
            top_performers = analysis_results.get('top_performers', [])[:3]
            for i, performer in enumerate(top_performers, 1):
                platform = performer.get('platform', 'N/A').title()
                score = performer.get('viral_score', 0)
                title = performer.get('title', 'Sem título')[:50]
                summary += f"  {i}. [{platform}] {title}... (Score: {score:.1f})\n"
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo: {e}")
            return "❌ Erro ao gerar resumo da análise"

# Instância global
viral_content_analyzer = ViralContentAnalyzer()