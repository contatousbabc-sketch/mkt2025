#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced Instagram Content Extractor
Extrator melhorado de conteúdo do Instagram com múltiplas estratégias
ZERO SIMULAÇÃO - Apenas extração real e funcional
"""

import os
import logging
import re
import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import trafilatura
from bs4 import BeautifulSoup
try:
    import instaloader
    HAS_INSTALOADER = True
except ImportError:
    HAS_INSTALOADER = False
    logger.warning("⚠️ instaloader não encontrado. Instale com 'pip install instaloader'")

logger = logging.getLogger(__name__)

class EnhancedInstagramExtractor:
    """
    Extrator melhorado de conteúdo do Instagram
    Múltiplas estratégias para extrair conteúdo válido
    """
    
    def __init__(self):
        """Inicializa o extrator com múltiplas estratégias"""
        
        self.strategies = [
            ("Instaloader", self._extract_with_instaloader),
            ("Trafilatura Enhanced", self._extract_with_trafilatura_enhanced),
            ("BeautifulSoup Advanced", self._extract_with_beautifulsoup_advanced),
            ("Regex Pattern", self._extract_with_regex_patterns),
            ("API Simulation", self._extract_with_api_simulation)
        ]
        
        # Headers para simular navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        # Padrões regex para extração
        self.patterns = {
            'caption': [
                r'"caption":"([^"]*)"',
                r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"([^"]*)"',
                r'<meta property="og:description" content="([^"]*)"',
                r'"accessibility_caption":"([^"]*)"'
            ],
            'likes': [
                r'"edge_media_preview_like":\{"count":(\d+)',
                r'"edge_liked_by":\{"count":(\d+)',
                r'(\d+) likes'
            ],
            'comments': [
                r'"edge_media_to_comment":\{"count":(\d+)',
                r'(\d+) comments'
            ],
            'username': [
                r'"username":"([^"]*)"',
                r'@([a-zA-Z0-9_.]+)'
            ],
            'media_url': [
                r'"display_url":"([^"]*)"',
                r'"src":"([^"]*)"'
            ]
        }
        
        logger.info("🔍 Enhanced Instagram Extractor inicializado")
    
    def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extrai conteúdo do Instagram usando múltiplas estratégias
        
        Args:
            url: URL do post do Instagram
            
        Returns:
            Dict com conteúdo extraído
        """
        
        logger.info(f"🔍 Extraindo conteúdo do Instagram: {url}")
        
        # Validar URL
        if not self._is_valid_instagram_url(url):
            logger.warning(f"⚠️ URL inválida do Instagram: {url}")
            return self._empty_result()
        
        # Tentar cada estratégia
        for strategy_name, strategy_func in self.strategies:
            try:
                logger.debug(f"🔄 Tentando estratégia: {strategy_name}")
                
                result = strategy_func(url)
                
                if result and self._is_valid_content(result):
                    logger.info(f"✅ Conteúdo extraído com sucesso usando: {strategy_name}")
                    result['extraction_method'] = strategy_name
                    result['url'] = url
                    return result
                else:
                    logger.debug(f"❌ Estratégia {strategy_name} não retornou conteúdo válido")
                    
            except Exception as e:
                logger.error(f"❌ Erro na estratégia {strategy_name}: {e}")
                continue
        
        logger.warning(f"⚠️ Nenhuma estratégia conseguiu extrair conteúdo válido de: {url}")
        return self._empty_result()
    
    def _extract_with_instaloader(self, url: str) -> Optional[Dict[str, Any]]:
        """Extrai usando Instaloader"""
        
        if not HAS_INSTALOADER:
            return None
            
        try:
            # Extrair shortcode da URL
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                return None
            
            # Criar instância do instaloader
            loader = instaloader.Instaloader()
            
            # Obter post
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            
            # Extrair dados
            result = {
                'caption': post.caption or '',
                'likes': post.likes,
                'comments': post.comments,
                'username': post.owner_username,
                'hashtags': list(post.caption_hashtags),
                'mentions': list(post.caption_mentions),
                'media_type': 'video' if post.is_video else 'image',
                'timestamp': post.date.isoformat() if post.date else '',
                'media_url': post.url,
                'is_video': post.is_video
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"Instaloader falhou: {e}")
            return None
    
    def _extract_with_trafilatura_enhanced(self, url: str) -> Optional[Dict[str, Any]]:
        """Extrai usando Trafilatura com configurações otimizadas"""
        
        try:
            # Fazer download com headers customizados
            downloaded = trafilatura.fetch_url(
                url,
                config=trafilatura.settings.use_config(),
                headers=self.headers
            )
            
            if not downloaded:
                return None
            
            # Extrair conteúdo principal
            content = trafilatura.extract(
                downloaded,
                include_comments=True,
                include_tables=True,
                include_formatting=True,
                favor_precision=False,
                favor_recall=True,
                url=url,
                config=trafilatura.settings.use_config()
            )
            
            if not content:
                return None
            
            # Extrair metadados
            metadata = trafilatura.extract_metadata(downloaded)
            
            # Combinar dados
            result = {
                'caption': content.strip(),
                'title': metadata.title if metadata else '',
                'description': metadata.description if metadata else '',
                'author': metadata.author if metadata else '',
                'date': metadata.date if metadata else '',
                'url': metadata.url if metadata else url,
                'sitename': metadata.sitename if metadata else 'Instagram'
            }
            
            # Tentar extrair dados adicionais do HTML
            soup = BeautifulSoup(downloaded, 'html.parser')
            additional_data = self._extract_from_soup(soup)
            result.update(additional_data)
            
            return result
            
        except Exception as e:
            logger.debug(f"Trafilatura Enhanced falhou: {e}")
            return None
    
    def _extract_with_beautifulsoup_advanced(self, url: str) -> Optional[Dict[str, Any]]:
        """Extrai usando BeautifulSoup com seletores avançados"""
        
        try:
            # Fazer requisição
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrair dados usando múltiplos seletores
            result = self._extract_from_soup(soup)
            
            # Tentar extrair JSON-LD
            json_ld = self._extract_json_ld(soup)
            if json_ld:
                result.update(json_ld)
            
            # Tentar extrair dados do script
            script_data = self._extract_from_scripts(soup)
            if script_data:
                result.update(script_data)
            
            return result if result else None
            
        except Exception as e:
            logger.debug(f"BeautifulSoup Advanced falhou: {e}")
            return None
    
    def _extract_with_regex_patterns(self, url: str) -> Optional[Dict[str, Any]]:
        """Extrai usando padrões regex no HTML"""
        
        try:
            # Fazer requisição
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            html = response.text
            result = {}
            
            # Aplicar padrões regex
            for field, patterns in self.patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    if match:
                        value = match.group(1)
                        
                        # Processar valor
                        if field in ['likes', 'comments']:
                            try:
                                value = int(value)
                            except:
                                continue
                        elif field == 'caption':
                            value = self._clean_caption(value)
                        
                        result[field] = value
                        break
            
            return result if result else None
            
        except Exception as e:
            logger.debug(f"Regex Patterns falhou: {e}")
            return None
    
    def _extract_with_api_simulation(self, url: str) -> Optional[Dict[str, Any]]:
        """Simula chamadas de API do Instagram"""
        
        try:
            # Extrair shortcode
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                return None
            
            # Tentar diferentes endpoints
            endpoints = [
                f"https://www.instagram.com/p/{shortcode}/?__a=1",
                f"https://www.instagram.com/graphql/query/?query_hash=9f8827793ef34641b2fb195d4d41151c&variables=%7B%22shortcode%22%3A%22{shortcode}%22%7D"
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, headers=self.headers, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Processar resposta JSON
                        result = self._process_api_response(data)
                        if result:
                            return result
                            
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"API Simulation falhou: {e}")
            return None
    
    def _extract_from_soup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai dados usando BeautifulSoup"""
        
        result = {}
        
        try:
            # Meta tags
            meta_description = soup.find('meta', property='og:description')
            if meta_description:
                result['caption'] = meta_description.get('content', '')
            
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                result['title'] = meta_title.get('content', '')
            
            # Imagem
            meta_image = soup.find('meta', property='og:image')
            if meta_image:
                result['media_url'] = meta_image.get('content', '')
            
            # Tentar extrair do título da página
            title_tag = soup.find('title')
            if title_tag and not result.get('caption'):
                title_text = title_tag.get_text().strip()
                if 'Instagram' in title_text:
                    # Extrair caption do título
                    parts = title_text.split(' on Instagram: ')
                    if len(parts) > 1:
                        result['caption'] = parts[1].replace('"', '').strip()
                        result['username'] = parts[0].strip()
            
        except Exception as e:
            logger.debug(f"Erro ao extrair do soup: {e}")
        
        return result
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extrai dados JSON-LD"""
        
        try:
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    if isinstance(data, dict):
                        result = {}
                        
                        if 'description' in data:
                            result['caption'] = data['description']
                        
                        if 'author' in data:
                            if isinstance(data['author'], dict):
                                result['username'] = data['author'].get('name', '')
                            else:
                                result['username'] = str(data['author'])
                        
                        if 'datePublished' in data:
                            result['timestamp'] = data['datePublished']
                        
                        if 'image' in data:
                            if isinstance(data['image'], list):
                                result['media_url'] = data['image'][0]
                            else:
                                result['media_url'] = data['image']
                        
                        if result:
                            return result
                            
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair JSON-LD: {e}")
            return None
    
    def _extract_from_scripts(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extrai dados dos scripts JavaScript"""
        
        try:
            scripts = soup.find_all('script')
            
            for script in scripts:
                if not script.string:
                    continue
                
                script_text = script.string
                
                # Procurar por dados do Instagram
                if 'window._sharedData' in script_text:
                    # Tentar extrair _sharedData
                    match = re.search(r'window\._sharedData\s*=\s*({.*?});', script_text, re.DOTALL)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            return self._process_shared_data(data)
                        except:
                            continue
                
                # Procurar por outros padrões
                for field, patterns in self.patterns.items():
                    for pattern in patterns:
                        match = re.search(pattern, script_text)
                        if match:
                            value = match.group(1)
                            
                            if field in ['likes', 'comments']:
                                try:
                                    value = int(value)
                                except:
                                    continue
                            elif field == 'caption':
                                value = self._clean_caption(value)
                            
                            return {field: value}
            
            return None
            
        except Exception as e:
            logger.debug(f"Erro ao extrair dos scripts: {e}")
            return None
    
    def _process_shared_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa dados do _sharedData"""
        
        try:
            result = {}
            
            # Navegar pela estrutura do _sharedData
            entry_data = data.get('entry_data', {})
            post_page = entry_data.get('PostPage', [])
            
            if post_page:
                media = post_page[0].get('graphql', {}).get('shortcode_media', {})
                
                if media:
                    # Extrair dados
                    result['caption'] = media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                    result['likes'] = media.get('edge_media_preview_like', {}).get('count', 0)
                    result['comments'] = media.get('edge_media_to_comment', {}).get('count', 0)
                    result['username'] = media.get('owner', {}).get('username', '')
                    result['media_url'] = media.get('display_url', '')
                    result['is_video'] = media.get('is_video', False)
                    result['timestamp'] = media.get('taken_at_timestamp', '')
            
            return result if result else None
            
        except Exception as e:
            logger.debug(f"Erro ao processar _sharedData: {e}")
            return None
    
    def _process_api_response(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa resposta da API"""
        
        try:
            result = {}
            
            # Diferentes estruturas de resposta
            if 'graphql' in data:
                media = data['graphql'].get('shortcode_media', {})
            elif 'data' in data:
                media = data['data'].get('shortcode_media', {})
            else:
                media = data
            
            if media:
                # Extrair dados
                result['caption'] = media.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', '')
                result['likes'] = media.get('edge_media_preview_like', {}).get('count', 0)
                result['comments'] = media.get('edge_media_to_comment', {}).get('count', 0)
                result['username'] = media.get('owner', {}).get('username', '')
                result['media_url'] = media.get('display_url', '')
                result['is_video'] = media.get('is_video', False)
                result['timestamp'] = media.get('taken_at_timestamp', '')
            
            return result if result else None
            
        except Exception as e:
            logger.debug(f"Erro ao processar resposta da API: {e}")
            return None
    
    def _is_valid_instagram_url(self, url: str) -> bool:
        """Valida se é uma URL válida do Instagram"""
        
        try:
            parsed = urlparse(url)
            return (
                parsed.netloc in ['instagram.com', 'www.instagram.com'] and
                ('/p/' in parsed.path or '/reel/' in parsed.path or '/tv/' in parsed.path)
            )
        except:
            return False
    
    def _extract_shortcode(self, url: str) -> Optional[str]:
        """Extrai shortcode da URL do Instagram"""
        
        try:
            # Padrões para extrair shortcode
            patterns = [
                r'/p/([A-Za-z0-9_-]+)',
                r'/reel/([A-Za-z0-9_-]+)',
                r'/tv/([A-Za-z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except:
            return None
    
    def _clean_caption(self, caption: str) -> str:
        """Limpa e formata caption"""
        
        try:
            # Decodificar caracteres Unicode
            caption = caption.encode().decode('unicode_escape')
            
            # Remover caracteres de controle
            caption = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', caption)
            
            # Limpar espaços extras
            caption = ' '.join(caption.split())
            
            return caption.strip()
            
        except:
            return caption
    
    def _is_valid_content(self, content: Dict[str, Any]) -> bool:
        """Verifica se o conteúdo extraído é válido"""
        
        if not content:
            return False
        
        # Verificar se tem pelo menos um campo importante
        important_fields = ['caption', 'title', 'description', 'username']
        
        for field in important_fields:
            value = content.get(field, '')
            if value and len(str(value).strip()) > 0:
                return True
        
        return False
    
    def _empty_result(self) -> Dict[str, Any]:
        """Retorna resultado vazio padronizado"""
        
        return {
            'caption': '',
            'likes': 0,
            'comments': 0,
            'username': '',
            'hashtags': [],
            'mentions': [],
            'media_type': '',
            'timestamp': '',
            'media_url': '',
            'is_video': False,
            'extraction_method': 'none',
            'url': '',
            'success': False
        }

# Instância global do extrator
enhanced_instagram_extractor = EnhancedInstagramExtractor()