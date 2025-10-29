#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Robust Content Extractor
Extrator de conteúdo robusto com remoção de duplicatas
"""

import os
import logging
import requests
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib
import re

# Sistema de remoção de duplicatas
from utils.duplicate_remover import remove_duplicates_from_results

logger = logging.getLogger(__name__)

class RobustContentExtractor:
    """Extrator de conteúdo robusto com anti-duplicatas"""
    
    def __init__(self):
        """Inicializa extrator"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Cache para evitar re-extrações
        self.content_cache = {}
        self.failed_urls = set()
        
        # Controle de tentativas e timeouts
        self.max_retries = 2
        self.default_timeout = 10  # Timeout mais agressivo
        self.problematic_domains = {
            'instagram.com', 'facebook.com', 'twitter.com', 'x.com',
            'linkedin.com', 'tiktok.com', 'youtube.com'
        }
        
        logger.info("🔧 RobustContentExtractor inicializado com timeouts otimizados")
    
    def extract_content(self, url: str, timeout: int = 15) -> Optional[str]:
        """Extrai conteúdo de uma URL"""
        if not url or url in self.failed_urls:
            return None
            
        # Verifica cache
        url_hash = hashlib.md5(url.encode()).hexdigest()
        if url_hash in self.content_cache:
            return self.content_cache[url_hash]
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles e outros elementos desnecessários
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extrai texto principal
            content_selectors = [
                'article', 'main', '.content', '.post-content', 
                '.entry-content', '.article-content', '.post-body'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            # Se não encontrou com seletores específicos, pega o body
            if not content:
                body = soup.find('body')
                if body:
                    content = body.get_text(strip=True)
            
            # Limpa e normaliza conteúdo
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Cache o resultado
            if content and len(content) > 100:  # Só cacheia conteúdo substancial
                self.content_cache[url_hash] = content
                return content
            else:
                self.failed_urls.add(url)
                return None
                
        except Exception as e:
            logger.warning(f"Erro ao extrair conteúdo de {url}: {e}")
            self.failed_urls.add(url)
            return None
    
    def extract_metadata(self, url: str, timeout: int = 15) -> Dict[str, Any]:
        """Extrai metadados de uma URL"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {
                'url': url,
                'title': '',
                'description': '',
                'keywords': [],
                'author': '',
                'published_date': '',
                'image': ''
            }
            
            # Título
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Meta tags
            meta_tags = soup.find_all('meta')
            for tag in meta_tags:
                name = tag.get('name', '').lower()
                property_attr = tag.get('property', '').lower()
                content = tag.get('content', '')
                
                if name in ['description', 'og:description'] or property_attr == 'og:description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = [k.strip() for k in content.split(',')]
                elif name == 'author' or property_attr == 'article:author':
                    metadata['author'] = content
                elif property_attr in ['article:published_time', 'og:published_time']:
                    metadata['published_date'] = content
                elif property_attr == 'og:image':
                    metadata['image'] = content
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Erro ao extrair metadados de {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    def batch_extract(self, urls: List[str], max_workers: int = 5) -> Dict[str, Optional[str]]:
        """Extrai conteúdo de múltiplas URLs em paralelo"""
        if not urls:
            return {}
        
        logger.info(f"🔄 Extraindo conteúdo de {len(urls)} URLs...")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete todas as tarefas
            future_to_url = {
                executor.submit(self.extract_content, url): url 
                for url in urls if url not in self.failed_urls
            }
            
            # Coleta resultados
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    content = future.result()
                    results[url] = content
                except Exception as e:
                    logger.warning(f"Erro ao processar {url}: {e}")
                    results[url] = None
        
        # Remove duplicatas dos resultados
        articles = []
        for url, content in results.items():
            if content:
                articles.append({
                    'url': url,
                    'content': content,
                    'text': content  # Alias para compatibilidade
                })
        
        # Aplica remoção de duplicatas
        unique_articles = remove_duplicates_from_results(articles, "articles")
        
        # Converte de volta para o formato esperado
        unique_results = {}
        for article in unique_articles:
            unique_results[article['url']] = article['content']
        
        # Adiciona URLs que falharam
        for url in urls:
            if url not in unique_results:
                unique_results[url] = None
        
        logger.info(f"✅ Extração concluída: {len(unique_articles)} artigos únicos de {len(urls)} URLs")
        
        return unique_results
    
    def batch_extract_with_metadata(self, urls: List[str], max_workers: int = 5) -> List[Dict[str, Any]]:
        """Extrai conteúdo e metadados de múltiplas URLs"""
        if not urls:
            return []
        
        logger.info(f"🔄 Extraindo conteúdo e metadados de {len(urls)} URLs...")
        
        articles = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submete tarefas para conteúdo e metadados
            future_to_url = {}
            
            for url in urls:
                if url not in self.failed_urls:
                    content_future = executor.submit(self.extract_content, url)
                    metadata_future = executor.submit(self.extract_metadata, url)
                    future_to_url[content_future] = ('content', url)
                    future_to_url[metadata_future] = ('metadata', url)
            
            # Coleta resultados
            url_data = {}
            for future in as_completed(future_to_url):
                data_type, url = future_to_url[future]
                try:
                    result = future.result()
                    if url not in url_data:
                        url_data[url] = {}
                    url_data[url][data_type] = result
                except Exception as e:
                    logger.warning(f"Erro ao processar {data_type} de {url}: {e}")
        
        # Combina dados
        for url, data in url_data.items():
            content = data.get('content')
            metadata = data.get('metadata', {})
            
            if content and len(content) > 100:  # Só inclui conteúdo substancial
                article = {
                    'url': url,
                    'content': content,
                    'text': content,  # Alias
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'author': metadata.get('author', ''),
                    'published_date': metadata.get('published_date', ''),
                    'keywords': metadata.get('keywords', []),
                    'image': metadata.get('image', '')
                }
                articles.append(article)
        
        # Remove duplicatas
        unique_articles = remove_duplicates_from_results(articles, "articles")
        
        logger.info(f"✅ Extração com metadados concluída: {len(unique_articles)} artigos únicos")
        
        return unique_articles
    
    def clear_cache(self):
        """Limpa cache de conteúdo"""
        self.content_cache.clear()
        self.failed_urls.clear()
        logger.info("🧹 Cache do extrator limpo")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do cache"""
        return {
            'cached_contents': len(self.content_cache),
            'failed_urls': len(self.failed_urls)
        }

# Instância global
robust_content_extractor = RobustContentExtractor()