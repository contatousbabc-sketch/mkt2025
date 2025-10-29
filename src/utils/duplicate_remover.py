"""
Sistema de Remoção de Dados Duplicados
Detecta e remove dados duplicados durante a coleta e processamento
"""

import hashlib
import re
from typing import List, Dict, Any, Set, Tuple
from urllib.parse import urlparse, parse_qs
import difflib
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DuplicateStats:
    """Estatísticas de remoção de duplicatas"""
    total_items: int = 0
    duplicates_removed: int = 0
    unique_items: int = 0
    similarity_threshold: float = 0.85

class DuplicateRemover:
    """Sistema inteligente de remoção de duplicatas"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.url_hashes: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.title_hashes: Set[str] = set()
        self.stats = DuplicateStats(similarity_threshold=similarity_threshold)
        
    def normalize_url(self, url: str) -> str:
        """Normaliza URL para comparação"""
        try:
            parsed = urlparse(url.lower().strip())
            
            # Remove parâmetros de tracking comuns
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'ref', 'source', 'campaign_id', 'ad_id',
                'mc_cid', 'mc_eid', '_ga', '_gid', 'msclkid'
            }
            
            query_params = parse_qs(parsed.query)
            clean_params = {k: v for k, v in query_params.items() 
                          if k.lower() not in tracking_params}
            
            # Reconstrói query string limpa
            clean_query = '&'.join([f"{k}={v[0]}" for k, v in clean_params.items()])
            
            # Remove fragmentos (#)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean_query:
                normalized += f"?{clean_query}"
                
            return normalized
            
        except Exception as e:
            logger.warning(f"Erro ao normalizar URL {url}: {e}")
            return url.lower().strip()
    
    def get_content_hash(self, content: str) -> str:
        """Gera hash do conteúdo normalizado"""
        if not content:
            return ""
            
        # Normaliza conteúdo
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get_title_hash(self, title: str) -> str:
        """Gera hash do título normalizado"""
        if not title:
            return ""
            
        # Remove pontuação e normaliza
        normalized = re.sub(r'[^\w\s]', '', title.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos"""
        if not text1 or not text2:
            return 0.0
            
        # Normaliza textos
        norm1 = re.sub(r'\s+', ' ', text1.lower().strip())
        norm2 = re.sub(r'\s+', ' ', text2.lower().strip())
        
        # Usa SequenceMatcher para calcular similaridade
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def is_duplicate_url(self, url: str) -> bool:
        """Verifica se URL é duplicata"""
        normalized_url = self.normalize_url(url)
        url_hash = hashlib.md5(normalized_url.encode('utf-8')).hexdigest()
        
        if url_hash in self.url_hashes:
            return True
            
        self.url_hashes.add(url_hash)
        return False
    
    def is_duplicate_content(self, content: str, existing_contents: List[str] = None) -> bool:
        """Verifica se conteúdo é duplicata"""
        content_hash = self.get_content_hash(content)
        
        if not content_hash:
            return False
            
        # Verifica hash exato
        if content_hash in self.content_hashes:
            return True
            
        # Verifica similaridade com conteúdos existentes
        if existing_contents:
            for existing in existing_contents:
                similarity = self.calculate_similarity(content, existing)
                if similarity >= self.similarity_threshold:
                    return True
        
        self.content_hashes.add(content_hash)
        return False
    
    def is_duplicate_title(self, title: str, existing_titles: List[str] = None) -> bool:
        """Verifica se título é duplicata"""
        title_hash = self.get_title_hash(title)
        
        if not title_hash:
            return False
            
        # Verifica hash exato
        if title_hash in self.title_hashes:
            return True
            
        # Verifica similaridade com títulos existentes
        if existing_titles:
            for existing in existing_titles:
                similarity = self.calculate_similarity(title, existing)
                if similarity >= 0.9:  # Threshold mais alto para títulos
                    return True
        
        self.title_hashes.add(title_hash)
        return False
    
    def remove_duplicate_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas de resultados de busca"""
        if not results:
            return results
            
        unique_results = []
        seen_urls = set()
        seen_titles = []
        seen_contents = []
        
        self.stats.total_items = len(results)
        
        for result in results:
            url = result.get('url', '')
            title = result.get('title', '')
            content = result.get('content', '') or result.get('snippet', '')
            
            # Verifica duplicata por URL
            if url and self.is_duplicate_url(url):
                self.stats.duplicates_removed += 1
                continue
                
            # Verifica duplicata por título
            if title and self.is_duplicate_title(title, seen_titles):
                self.stats.duplicates_removed += 1
                continue
                
            # Verifica duplicata por conteúdo
            if content and self.is_duplicate_content(content, seen_contents):
                self.stats.duplicates_removed += 1
                continue
            
            # Adiciona aos únicos
            unique_results.append(result)
            if url:
                seen_urls.add(self.normalize_url(url))
            if title:
                seen_titles.append(title)
            if content:
                seen_contents.append(content)
        
        self.stats.unique_items = len(unique_results)
        
        logger.info(f"Remoção de duplicatas: {self.stats.total_items} → {self.stats.unique_items} "
                   f"({self.stats.duplicates_removed} duplicatas removidas)")
        
        return unique_results
    
    def remove_duplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas de artigos extraídos"""
        if not articles:
            return articles
            
        unique_articles = []
        seen_urls = set()
        seen_contents = []
        
        self.stats.total_items = len(articles)
        
        for article in articles:
            url = article.get('url', '')
            content = article.get('content', '') or article.get('text', '')
            
            # Verifica duplicata por URL
            if url:
                normalized_url = self.normalize_url(url)
                if normalized_url in seen_urls:
                    self.stats.duplicates_removed += 1
                    continue
                seen_urls.add(normalized_url)
            
            # Verifica duplicata por conteúdo
            if content and len(content) > 100:  # Só verifica conteúdos substanciais
                is_duplicate = False
                for existing_content in seen_contents:
                    similarity = self.calculate_similarity(content, existing_content)
                    if similarity >= self.similarity_threshold:
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    self.stats.duplicates_removed += 1
                    continue
                    
                seen_contents.append(content)
            
            unique_articles.append(article)
        
        self.stats.unique_items = len(unique_articles)
        
        logger.info(f"Remoção de duplicatas de artigos: {self.stats.total_items} → {self.stats.unique_items}")
        
        return unique_articles
    
    def merge_similar_items(self, items: List[Dict[str, Any]], 
                           merge_threshold: float = 0.95) -> List[Dict[str, Any]]:
        """Mescla itens muito similares mantendo o mais completo"""
        if not items or len(items) < 2:
            return items
            
        merged_items = []
        processed_indices = set()
        
        for i, item1 in enumerate(items):
            if i in processed_indices:
                continue
                
            # Encontra itens similares
            similar_items = [item1]
            similar_indices = {i}
            
            content1 = item1.get('content', '') or item1.get('text', '')
            
            for j, item2 in enumerate(items[i+1:], i+1):
                if j in processed_indices:
                    continue
                    
                content2 = item2.get('content', '') or item2.get('text', '')
                
                if content1 and content2:
                    similarity = self.calculate_similarity(content1, content2)
                    if similarity >= merge_threshold:
                        similar_items.append(item2)
                        similar_indices.add(j)
            
            # Mescla itens similares
            if len(similar_items) > 1:
                merged_item = self._merge_items(similar_items)
                merged_items.append(merged_item)
                logger.info(f"Mesclados {len(similar_items)} itens similares")
            else:
                merged_items.append(item1)
            
            processed_indices.update(similar_indices)
        
        return merged_items
    
    def _merge_items(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mescla múltiplos itens similares"""
        if not items:
            return {}
            
        # Escolhe o item com mais conteúdo como base
        base_item = max(items, key=lambda x: len(str(x.get('content', '') or x.get('text', ''))))
        
        # Mescla informações adicionais
        merged = base_item.copy()
        
        # Coleta URLs adicionais
        urls = set()
        for item in items:
            if item.get('url'):
                urls.add(item['url'])
        
        if len(urls) > 1:
            merged['additional_urls'] = list(urls - {merged.get('url', '')})
        
        # Mescla tags/categorias
        all_tags = set()
        for item in items:
            tags = item.get('tags', []) or item.get('categories', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                all_tags.add(tags)
        
        if all_tags:
            merged['tags'] = list(all_tags)
        
        return merged
    
    def get_stats(self) -> DuplicateStats:
        """Retorna estatísticas de remoção"""
        return self.stats
    
    def reset_stats(self):
        """Reseta estatísticas"""
        self.stats = DuplicateStats(similarity_threshold=self.similarity_threshold)
    
    def clear_cache(self):
        """Limpa cache de hashes"""
        self.url_hashes.clear()
        self.content_hashes.clear()
        self.title_hashes.clear()
        self.reset_stats()

# Instância global para uso em todo o sistema
duplicate_remover = DuplicateRemover()

def remove_duplicates_from_results(results: List[Dict[str, Any]], 
                                 result_type: str = "search") -> List[Dict[str, Any]]:
    """Função utilitária para remover duplicatas"""
    if result_type == "search":
        return duplicate_remover.remove_duplicate_search_results(results)
    elif result_type == "articles":
        return duplicate_remover.remove_duplicate_articles(results)
    else:
        return duplicate_remover.remove_duplicate_search_results(results)

def get_duplicate_stats() -> DuplicateStats:
    """Retorna estatísticas globais de duplicatas"""
    return duplicate_remover.get_stats()