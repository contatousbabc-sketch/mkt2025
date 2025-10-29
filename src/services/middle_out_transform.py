#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Middle Out Transform
Sistema de compressão inteligente para evitar limite de 2 milhões de tokens
Implementa algoritmo de compressão hierárquica preservando informações críticas
"""

import os
import json
import logging
import asyncio
import hashlib
import zlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class MiddleOutTransform:
    """
    Sistema de compressão inteligente Middle Out Transform
    Reduz dados massivos preservando informações críticas
    """
    
    def __init__(self):
        """Inicializa o sistema de transformação"""
        self.compression_stats = {
            'original_size': 0,
            'compressed_size': 0,
            'compression_ratio': 0.0,
            'tokens_saved': 0,
            'critical_data_preserved': 0
        }
        
        # Configurações de compressão
        self.config = {
            'max_tokens_per_chunk': 50000,  # Máximo por chunk
            'critical_keywords': [
                'resultado', 'conversão', 'engajamento', 'viral', 'trending',
                'performance', 'roi', 'ctr', 'impressões', 'alcance',
                'vendas', 'leads', 'cliques', 'visualizações', 'shares',
                'comentários', 'likes', 'seguidores', 'crescimento'
            ],
            'preserve_patterns': [
                r'\d+%',  # Percentuais
                r'\d+[kKmM]',  # Números com K/M
                r'R\$\s*\d+',  # Valores monetários
                r'\d+\.\d+',  # Números decimais
                r'#\w+',  # Hashtags
                r'@\w+',  # Menções
            ],
            'compression_levels': {
                'high': 0.3,    # Mantém 30% do conteúdo
                'medium': 0.5,  # Mantém 50% do conteúdo
                'low': 0.7      # Mantém 70% do conteúdo
            }
        }
        
        logger.info("🔄 Middle Out Transform inicializado")
    
    async def compress_data(self, data: Dict[str, Any], session_id: str, 
                          compression_level: str = 'medium') -> Dict[str, Any]:
        """
        Comprime dados usando algoritmo Middle Out Transform
        
        Args:
            data: Dados para comprimir
            session_id: ID da sessão
            compression_level: Nível de compressão (high/medium/low)
        
        Returns:
            Dados comprimidos com metadados
        """
        try:
            logger.info(f"🔄 Iniciando Middle Out Transform - Nível: {compression_level}")
            
            # Calcular tamanho original
            original_json = json.dumps(data, ensure_ascii=False)
            original_size = len(original_json.encode('utf-8'))
            original_tokens = self._estimate_tokens(original_json)
            
            self.compression_stats['original_size'] = original_size
            
            logger.info(f"📊 Dados originais: {original_size:,} bytes (~{original_tokens:,} tokens)")
            
            # Verificar se precisa de compressão
            if original_tokens < 1500000:  # Menos que 1.5M tokens
                logger.info("✅ Dados dentro do limite - compressão desnecessária")
                return {
                    'compressed_data': data,
                    'compression_applied': False,
                    'original_tokens': original_tokens,
                    'final_tokens': original_tokens,
                    'compression_ratio': 1.0,
                    'metadata': {
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat(),
                        'compression_level': compression_level
                    }
                }
            
            # Aplicar compressão Middle Out
            compressed_data = await self._apply_middle_out_compression(
                data, compression_level
            )
            
            # Calcular estatísticas finais
            compressed_json = json.dumps(compressed_data, ensure_ascii=False)
            compressed_size = len(compressed_json.encode('utf-8'))
            compressed_tokens = self._estimate_tokens(compressed_json)
            
            compression_ratio = compressed_size / original_size
            tokens_saved = original_tokens - compressed_tokens
            
            self.compression_stats.update({
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'tokens_saved': tokens_saved
            })
            
            logger.info(f"✅ Compressão concluída:")
            logger.info(f"   📉 Redução: {(1-compression_ratio)*100:.1f}%")
            logger.info(f"   🎯 Tokens salvos: {tokens_saved:,}")
            logger.info(f"   📊 Final: {compressed_tokens:,} tokens")
            
            # Salvar dados comprimidos
            await self._save_compressed_data(compressed_data, session_id, compression_level)
            
            return {
                'compressed_data': compressed_data,
                'compression_applied': True,
                'original_tokens': original_tokens,
                'final_tokens': compressed_tokens,
                'compression_ratio': compression_ratio,
                'tokens_saved': tokens_saved,
                'metadata': {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'compression_level': compression_level,
                    'algorithm': 'middle_out_transform_v1.0'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na compressão Middle Out: {e}")
            raise
    
    async def _apply_middle_out_compression(self, data: Dict[str, Any], 
                                          level: str) -> Dict[str, Any]:
        """Aplica algoritmo de compressão Middle Out"""
        try:
            compression_ratio = self.config['compression_levels'][level]
            
            # Fase 1: Identificar dados críticos
            critical_data = await self._extract_critical_data(data)
            
            # Fase 2: Comprimir dados não-críticos
            compressed_sections = {}
            
            for section_key, section_data in data.items():
                if section_key in ['metadata', 'session_info', 'timestamp']:
                    # Preservar metadados sempre
                    compressed_sections[section_key] = section_data
                    continue
                
                if isinstance(section_data, dict):
                    compressed_sections[section_key] = await self._compress_section(
                        section_data, compression_ratio, critical_data.get(section_key, {})
                    )
                elif isinstance(section_data, list):
                    compressed_sections[section_key] = await self._compress_list(
                        section_data, compression_ratio
                    )
                else:
                    compressed_sections[section_key] = section_data
            
            # Fase 3: Adicionar dados críticos preservados
            compressed_sections['_critical_data_preserved'] = critical_data
            compressed_sections['_compression_metadata'] = {
                'level': level,
                'ratio': compression_ratio,
                'timestamp': datetime.now().isoformat(),
                'algorithm': 'middle_out_v1.0'
            }
            
            return compressed_sections
            
        except Exception as e:
            logger.error(f"❌ Erro na aplicação do algoritmo: {e}")
            raise
    
    async def _extract_critical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai dados críticos que devem ser preservados"""
        critical_data = {}
        
        try:
            for section_key, section_data in data.items():
                section_critical = {}
                
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if self._is_critical_data(key, value):
                            section_critical[key] = value
                
                elif isinstance(section_data, list):
                    critical_items = []
                    for item in section_data:
                        if isinstance(item, dict):
                            critical_item = {}
                            for k, v in item.items():
                                if self._is_critical_data(k, v):
                                    critical_item[k] = v
                            if critical_item:
                                critical_items.append(critical_item)
                        elif self._is_critical_value(str(item)):
                            critical_items.append(item)
                    
                    if critical_items:
                        section_critical = critical_items
                
                if section_critical:
                    critical_data[section_key] = section_critical
            
            logger.info(f"🎯 Dados críticos extraídos: {len(critical_data)} seções")
            return critical_data
            
        except Exception as e:
            logger.error(f"❌ Erro na extração de dados críticos: {e}")
            return {}
    
    def _is_critical_data(self, key: str, value: Any) -> bool:
        """Verifica se um dado é crítico e deve ser preservado"""
        try:
            key_lower = str(key).lower()
            value_str = str(value).lower()
            
            # Verificar palavras-chave críticas na chave
            for keyword in self.config['critical_keywords']:
                if keyword in key_lower:
                    return True
            
            # Verificar padrões críticos no valor
            if self._is_critical_value(value_str):
                return True
            
            # Verificar se é métrica importante
            if any(metric in key_lower for metric in [
                'views', 'likes', 'shares', 'comments', 'followers',
                'engagement', 'reach', 'impressions', 'clicks', 'ctr',
                'conversion', 'sales', 'revenue', 'roi', 'performance'
            ]):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _is_critical_value(self, value_str: str) -> bool:
        """Verifica se um valor contém informações críticas"""
        try:
            # Verificar padrões preservados
            for pattern in self.config['preserve_patterns']:
                if re.search(pattern, value_str):
                    return True
            
            # Verificar números grandes (possíveis métricas)
            if re.search(r'\d{4,}', value_str):  # Números com 4+ dígitos
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _compress_section(self, section: Dict[str, Any], ratio: float, 
                              critical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprime uma seção preservando dados críticos"""
        try:
            compressed = {}
            
            # Sempre preservar dados críticos
            compressed.update(critical_data)
            
            # Comprimir dados não-críticos
            non_critical_items = []
            for key, value in section.items():
                if key not in critical_data:
                    non_critical_items.append((key, value))
            
            # Selecionar itens para manter baseado na razão de compressão
            items_to_keep = int(len(non_critical_items) * ratio)
            
            # Priorizar itens com mais informação
            sorted_items = sorted(non_critical_items, 
                                key=lambda x: len(str(x[1])), reverse=True)
            
            for key, value in sorted_items[:items_to_keep]:
                compressed[key] = value
            
            return compressed
            
        except Exception as e:
            logger.error(f"❌ Erro na compressão de seção: {e}")
            return section
    
    async def _compress_list(self, data_list: List[Any], ratio: float) -> List[Any]:
        """Comprime uma lista preservando itens mais importantes"""
        try:
            if not data_list:
                return data_list
            
            # Calcular quantos itens manter
            items_to_keep = max(1, int(len(data_list) * ratio))
            
            # Se todos os itens cabem, retornar todos
            if items_to_keep >= len(data_list):
                return data_list
            
            # Priorizar itens com mais conteúdo ou dados críticos
            scored_items = []
            for i, item in enumerate(data_list):
                score = 0
                item_str = str(item)
                
                # Pontuação por tamanho
                score += len(item_str) / 100
                
                # Pontuação por conteúdo crítico
                if self._is_critical_value(item_str.lower()):
                    score += 1000
                
                # Pontuação por palavras-chave
                for keyword in self.config['critical_keywords']:
                    if keyword in item_str.lower():
                        score += 100
                
                scored_items.append((score, i, item))
            
            # Ordenar por pontuação e selecionar os melhores
            scored_items.sort(reverse=True)
            selected_items = [item for _, _, item in scored_items[:items_to_keep]]
            
            return selected_items
            
        except Exception as e:
            logger.error(f"❌ Erro na compressão de lista: {e}")
            return data_list
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens em um texto"""
        try:
            # Estimativa aproximada: 1 token ≈ 4 caracteres para português
            return len(text) // 4
        except Exception:
            return 0
    
    async def _save_compressed_data(self, data: Dict[str, Any], session_id: str, 
                                  level: str) -> None:
        """Salva dados comprimidos em arquivo"""
        try:
            # Criar diretório de compressão
            compression_dir = Path(f"relatorios_intermediarios/compressed/{session_id}")
            compression_dir.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"middle_out_compressed_{level}_{timestamp}.json"
            filepath = compression_dir / filename
            
            # Salvar dados comprimidos
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Dados comprimidos salvos: {filepath}")
            
            # Salvar estatísticas
            stats_file = compression_dir / f"compression_stats_{timestamp}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.compression_stats, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados comprimidos: {e}")
    
    async def decompress_data(self, compressed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Descomprime dados (se necessário para análise detalhada)
        """
        try:
            if not compressed_data.get('compression_applied', False):
                return compressed_data.get('compressed_data', compressed_data)
            
            # Extrair dados principais
            main_data = compressed_data.get('compressed_data', {})
            
            # Remover metadados de compressão para limpeza
            clean_data = {}
            for key, value in main_data.items():
                if not key.startswith('_compression'):
                    clean_data[key] = value
            
            logger.info("🔄 Dados descomprimidos para análise")
            return clean_data
            
        except Exception as e:
            logger.error(f"❌ Erro na descompressão: {e}")
            return compressed_data
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de compressão"""
        return self.compression_stats.copy()

# Instância global
middle_out_transform = MiddleOutTransform()

def get_middle_out_transform() -> MiddleOutTransform:
    """Retorna instância do Middle Out Transform"""
    return middle_out_transform