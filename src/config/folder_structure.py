#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Estrutura de Pastas Organizada
Configuração centralizada para organização de dados e salvamentos
"""

import os
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FolderStructureManager:
    """Gerenciador da estrutura de pastas do sistema"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent.parent
        self.structure = self._define_folder_structure()
        self._ensure_folders_exist()
        
        logger.info("📁 FolderStructureManager inicializado")
        logger.info(f"📂 Base path: {self.base_path}")
    
    def _define_folder_structure(self) -> Dict[str, Path]:
        """Define a estrutura completa de pastas"""
        
        structure = {
            # === DADOS BRUTOS ===
            "data_raw": self.base_path / "data" / "raw",
            "data_raw_websailor": self.base_path / "data" / "raw" / "websailor",
            "data_raw_viral_images": self.base_path / "data" / "raw" / "viral_images",
            "data_raw_market_research": self.base_path / "data" / "raw" / "market_research",
            "data_raw_social_media": self.base_path / "data" / "raw" / "social_media",
            "data_raw_competitors": self.base_path / "data" / "raw" / "competitors",
            
            # === DADOS PROCESSADOS ===
            "data_processed": self.base_path / "data" / "processed",
            "data_processed_analysis": self.base_path / "data" / "processed" / "analysis",
            "data_processed_synthesis": self.base_path / "data" / "processed" / "synthesis",
            "data_processed_insights": self.base_path / "data" / "processed" / "insights",
            
            # === ANÁLISES ===
            "analysis": self.base_path / "data" / "analysis",
            "analysis_market": self.base_path / "data" / "analysis" / "market",
            "analysis_competitors": self.base_path / "data" / "analysis" / "competitors",
            "analysis_trends": self.base_path / "data" / "analysis" / "trends",
            "analysis_opportunities": self.base_path / "data" / "analysis" / "opportunities",
            
            # === RELATÓRIOS ===
            "reports": self.base_path / "data" / "reports",
            "reports_executive": self.base_path / "data" / "reports" / "executive",
            "reports_technical": self.base_path / "data" / "reports" / "technical",
            "reports_marketing": self.base_path / "data" / "reports" / "marketing",
            "reports_automated": self.base_path / "data" / "reports" / "automated",
            
            # === WEBSAILOR V2 ===
            "websailor_v2": self.base_path / "data" / "websailor_v2",
            "websailor_v2_navigation": self.base_path / "data" / "websailor_v2" / "navigation",
            "websailor_v2_reasoning": self.base_path / "data" / "websailor_v2" / "reasoning",
            "websailor_v2_dual_env": self.base_path / "data" / "websailor_v2" / "dual_environment",
            "websailor_v2_knowledge_graph": self.base_path / "data" / "websailor_v2" / "knowledge_graph",
            
            # === IMAGENS VIRAIS ===
            "viral_images": self.base_path / "data" / "viral_images",
            "viral_images_downloaded": self.base_path / "data" / "viral_images" / "downloaded",
            "viral_images_analysis": self.base_path / "data" / "viral_images" / "analysis",
            "viral_images_metadata": self.base_path / "data" / "viral_images" / "metadata",
            
            # === OUTPUTS ===
            "outputs": self.base_path / "outputs",
            "outputs_json": self.base_path / "outputs" / "json",
            "outputs_csv": self.base_path / "outputs" / "csv",
            "outputs_html": self.base_path / "outputs" / "html",
            "outputs_images": self.base_path / "outputs" / "images",
            "outputs_screenshots": self.base_path / "outputs" / "screenshots",
            "outputs_reports": self.base_path / "outputs" / "reports",
            
            # === TEMPORÁRIOS ===
            "temp": self.base_path / "temp",
            "temp_downloads": self.base_path / "temp" / "downloads",
            "temp_processing": self.base_path / "temp" / "processing",
            "temp_cache": self.base_path / "temp" / "cache",
            "temp_websailor": self.base_path / "temp" / "websailor",
            
            # === LOGS ===
            "logs": self.base_path / "logs",
            "logs_system": self.base_path / "logs" / "system",
            "logs_api": self.base_path / "logs" / "api",
            "logs_errors": self.base_path / "logs" / "errors",
            "logs_performance": self.base_path / "logs" / "performance",
            "logs_websailor_v2": self.base_path / "logs" / "websailor_v2",
            
            # === SESSÕES ===
            "sessions": self.base_path / "sessions",
            "sessions_active": self.base_path / "sessions" / "active",
            "sessions_completed": self.base_path / "sessions" / "completed",
            "sessions_archived": self.base_path / "sessions" / "archived",
        }
        
        return structure
    
    def _ensure_folders_exist(self):
        """Garante que todas as pastas existam"""
        
        created_count = 0
        for folder_name, folder_path in self.structure.items():
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
                if not folder_path.exists():
                    logger.warning(f"⚠️ Falha ao criar pasta: {folder_path}")
                else:
                    created_count += 1
            except Exception as e:
                logger.error(f"❌ Erro ao criar pasta {folder_name}: {e}")
        
        logger.info(f"✅ {created_count}/{len(self.structure)} pastas verificadas/criadas")
    
    def get_path(self, folder_key: str) -> Path:
        """Retorna o caminho para uma pasta específica"""
        
        if folder_key not in self.structure:
            logger.warning(f"⚠️ Pasta não encontrada: {folder_key}")
            # Retorna pasta temp como fallback
            return self.structure.get("temp", self.base_path / "temp")
        
        return self.structure[folder_key]
    
    def get_save_path(self, category: str, filename: str, create_subdir: bool = True) -> Path:
        """
        Retorna caminho completo para salvamento baseado na categoria
        
        Args:
            category: Categoria do arquivo (ex: 'websailor_v2', 'viral_images', 'reports')
            filename: Nome do arquivo
            create_subdir: Se deve criar subdiretório baseado na data
        """
        
        # Mapeia categorias para pastas
        category_mapping = {
            "websailor_v2": "websailor_v2",
            "websailor_v2_navigation": "websailor_v2_navigation",
            "websailor_v2_reasoning": "websailor_v2_reasoning",
            "viral_images": "viral_images",
            "viral_images_downloaded": "viral_images_downloaded",
            "viral_images_analysis": "viral_images_analysis",
            "market_research": "data_raw_market_research",
            "analysis": "analysis",
            "reports": "reports",
            "reports_automated": "reports_automated",
            "outputs_json": "outputs_json",
            "outputs_csv": "outputs_csv",
            "outputs_html": "outputs_html",
            "temp": "temp",
            "temp_processing": "temp_processing",
            "logs": "logs_system"
        }
        
        folder_key = category_mapping.get(category, "temp")
        base_folder = self.get_path(folder_key)
        
        # Cria subdiretório baseado na data se solicitado
        if create_subdir:
            from datetime import datetime
            date_subdir = datetime.now().strftime("%Y-%m-%d")
            save_folder = base_folder / date_subdir
            save_folder.mkdir(parents=True, exist_ok=True)
        else:
            save_folder = base_folder
        
        return save_folder / filename
    
    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Remove arquivos temporários antigos"""
        
        import time
        from datetime import datetime, timedelta
        
        cutoff_time = time.time() - (older_than_hours * 3600)
        cleaned_count = 0
        
        temp_folders = [
            self.structure["temp_downloads"],
            self.structure["temp_processing"],
            self.structure["temp_cache"],
            self.structure["temp_websailor"]
        ]
        
        for temp_folder in temp_folders:
            if not temp_folder.exists():
                continue
                
            try:
                for file_path in temp_folder.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            except Exception as e:
                logger.error(f"❌ Erro ao limpar {temp_folder}: {e}")
        
        logger.info(f"🧹 {cleaned_count} arquivos temporários removidos")
        return cleaned_count
    
    def get_folder_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das pastas"""
        
        stats = {}
        
        for folder_name, folder_path in self.structure.items():
            try:
                if folder_path.exists():
                    file_count = len(list(folder_path.rglob("*")))
                    total_size = sum(f.stat().st_size for f in folder_path.rglob("*") if f.is_file())
                    
                    stats[folder_name] = {
                        "exists": True,
                        "file_count": file_count,
                        "total_size_mb": round(total_size / (1024 * 1024), 2),
                        "path": str(folder_path)
                    }
                else:
                    stats[folder_name] = {
                        "exists": False,
                        "file_count": 0,
                        "total_size_mb": 0,
                        "path": str(folder_path)
                    }
            except Exception as e:
                stats[folder_name] = {
                    "exists": False,
                    "error": str(e),
                    "path": str(folder_path)
                }
        
        return stats


# Instância global do gerenciador
folder_manager = FolderStructureManager()

# Funções de conveniência
def get_save_path(category: str, filename: str, create_subdir: bool = True) -> Path:
    """Função de conveniência para obter caminho de salvamento"""
    return folder_manager.get_save_path(category, filename, create_subdir)

def get_folder_path(folder_key: str) -> Path:
    """Função de conveniência para obter caminho de pasta"""
    return folder_manager.get_path(folder_key)

def cleanup_temp_files(older_than_hours: int = 24) -> int:
    """Função de conveniência para limpeza de arquivos temporários"""
    return folder_manager.cleanup_temp_files(older_than_hours)

def get_folder_stats() -> Dict[str, Any]:
    """Função de conveniência para estatísticas das pastas"""
    return folder_manager.get_folder_stats()