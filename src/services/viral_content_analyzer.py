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

# Instascrape imports
try:
    from instascrape import Post, Profile, Hashtag
    HAS_INSTASCRAPE = True
except ImportError:
    HAS_INSTASCRAPE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ instascrape não encontrado. Instale com 'pip install instascrape'")

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

        if HAS_INSTASCRAPE:
            logger.info("✅ Viral Content Analyzer inicializado com instascrape")
        else:
            logger.warning("⚠️ Viral Content Analyzer inicializado sem instascrape - funcionalidade limitada")

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
        """Analisa URLs usando instascrape"""
        platform_analysis = {
            'instagram': [],
            'youtube': [],
            'facebook': [],
            'twitter': [],
            'tiktok': [],
            'other': []
        }
        
        if not HAS_INSTASCRAPE:
            logger.warning("⚠️ instascrape não disponível - usando análise básica")
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
        """Analisa post do Instagram usando instascrape"""
        try:
            # Criar objeto Post do instascrape
            post = Post(url)
            
            # Fazer scraping dos dados
            post.scrape()
            
            # Extrair dados relevantes
            analysis = {
                'url': url,
                'platform': 'instagram',
                'title': content.get('title', ''),
                'caption': getattr(post, 'caption', ''),
                'likes': getattr(post, 'likes', 0),
                'comments': getattr(post, 'comments', 0),
                'timestamp': getattr(post, 'timestamp', ''),
                'owner': getattr(post, 'owner', ''),
                'hashtags': getattr(post, 'hashtags', []),
                'mentions': getattr(post, 'mentions', []),
                'is_video': getattr(post, 'is_video', False),
                'engagement_rate': 0,
                'viral_score': 0,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Calcular engagement rate
            if hasattr(post, 'owner') and hasattr(post.owner, 'followers'):
                followers = getattr(post.owner, 'followers', 1)
                if followers > 0:
                    analysis['engagement_rate'] = (analysis['likes'] + analysis['comments']) / followers * 100
            
            # Calcular viral score
            analysis['viral_score'] = self._calculate_viral_score(analysis, 'instagram')
            
            logger.info(f"✅ Instagram analisado: {analysis['likes']} likes, {analysis['comments']} comentários")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar Instagram post {url}: {e}")
            return None

    async def _analyze_youtube_video(self, url: str, content: Dict) -> Optional[Dict]:
        """Analisa vídeo do YouTube (análise básica - instascrape não suporta YouTube diretamente)"""
        try:
            # Para YouTube, usar análise básica por enquanto
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
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar YouTube video {url}: {e}")
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