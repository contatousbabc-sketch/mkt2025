#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Auto Save Manager
Sistema de salvamento automático ultra-robusto
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import re
from collections import Counter
import hashlib # Importado para hashing de URL

logger = logging.getLogger(__name__)

# Import do serviço preditivo (lazy loading para evitar circular imports)
_predictive_service = None

def get_predictive_service():
    """Lazy loading do serviço preditivo"""
    global _predictive_service
    if _predictive_service is None:
        try:
            from services.predictive_analytics_service import predictive_analytics_service
            _predictive_service = predictive_analytics_service
        except ImportError as e:
            logger.warning(f"⚠️ Serviço preditivo não disponível: {e}")
            _predictive_service = None
    return _predictive_service

def serializar_dados_seguros(dados: Any) -> Dict[str, Any]:
    """
    Serializa dados de forma segura para JSON, lidando com tipos não serializáveis.
    Se os dados já forem um dict com a chave 'data', assume que já é um formato esperado.
    """
    if isinstance(dados, dict) and "data" in dados:
        return dados

    serializable_data = {}
    if isinstance(dados, dict):
        serializable_data["data"] = dados
    elif isinstance(dados, list):
        serializable_data["data"] = dados
    else:
        serializable_data["data"] = str(dados)

    serializable_data["timestamp"] = datetime.now().isoformat()
    return serializable_data

class AutoSaveManager:
    """Gerenciador automático de salvamento de dados - CENTRALIZADO"""

    def __init__(self):
        """Inicializa o gerenciador de salvamento automático"""
        self.enabled = True
        self.base_dir = "analyses_data"
        self.relatorios_dir = "relatorios_intermediarios"

        # Cria diretórios necessários
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.relatorios_dir, exist_ok=True)

        logger.info("🔧 Auto Save Manager CENTRALIZADO inicializado")

    # === INTERFACE UNIFICADA PARA SALVAMENTO DE DADOS EXTRAÍDOS ===

    def save_extracted_content(self, content_data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Interface unificada para salvar conteúdo extraído
        Recebe dados estruturados e se encarrega de todo o processo de salvamento

        Args:
            content_data: {
                'url': str,
                'titulo': str,
                'conteudo': str,
                'metodo_extracao': str,
                'qualidade': float,
                'platform': str (opcional),
                'metadata': dict (opcional)
            }
            session_id: ID da sessão para organização

        Returns:
            Dict com informações dos arquivos salvos
        """
        try:
            if not content_data.get('url') or not content_data.get('conteudo'):
                logger.warning("⚠️ Dados insuficientes para salvamento")
                return {'success': False, 'error': 'Dados insuficientes'}

            results = {}

            # Determina tipo de conteúdo e diretório
            platform = content_data.get('platform', 'web')
            if 'instagram.com' in content_data['url'] or 'facebook.com' in content_data['url']:
                content_type = 'viral_content'
                base_category = 'viral_images_data'
            else:
                content_type = 'web_content'
                base_category = 'pesquisa_web'

            # Salva arquivo individual
            individual_path = self._save_individual_content(content_data, session_id, base_category)
            if individual_path:
                results['individual_file'] = individual_path

            # Salva no arquivo consolidado da sessão
            if session_id:
                consolidated_path = self._save_to_consolidated(content_data, session_id, base_category)
                if consolidated_path:
                    results['consolidated_file'] = consolidated_path

            # Salva etapa intermediária
            etapa_path = self._save_extraction_step(content_data, session_id)
            if etapa_path:
                results['etapa_file'] = etapa_path

            logger.info(f"✅ Conteúdo salvo em {len(results)} locais - URL: {content_data['url'][:50]}...")

            return {
                'success': True,
                'files_saved': results,
                'content_type': content_type,
                'session_id': session_id
            }

        except Exception as e:
            logger.error(f"❌ Erro no salvamento centralizado: {e}")
            return {'success': False, 'error': str(e)}

    def save_viral_analysis_report(self, viral_data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Salva relatório de análise viral completo

        Args:
            viral_data: Dados compilados da análise viral
            session_id: ID da sessão

        Returns:
            Dict com caminho do arquivo salvo
        """
        try:
            # Gera nome do arquivo viral
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_suffix = f"_{session_id[:8]}" if session_id else ""
            filename = f"viral_results{session_suffix}_{timestamp}.json"

            # Diretório específico para dados virais
            viral_dir = os.path.join(self.base_dir, "viral_images_data")
            os.makedirs(viral_dir, exist_ok=True)

            filepath = os.path.join(viral_dir, filename)

            # Adiciona metadados do arquivo
            viral_data_with_meta = {
                **viral_data,
                'metadata': {
                    **viral_data.get('metadata', {}),
                    'generated_at': datetime.now().isoformat(),
                    'session_id': session_id,
                    'file_type': 'viral_analysis_report',
                    'agent': 'AutoSaveManager_Centralized'
                }
            }

            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(viral_data_with_meta, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(filepath) / 1024  # KB
            logger.info(f"✅ Relatório viral salvo: {filename} ({file_size:.1f}KB)")

            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'size_kb': file_size
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório viral: {e}")
            return {'success': False, 'error': str(e)}

    def save_massive_search_result(self, massive_data: Dict[str, Any], produto: str) -> Dict[str, Any]:
        """
        Salva resultado final da busca massiva

        Args:
            massive_data: Dados compilados da busca massiva
            produto: Nome do produto para o arquivo

        Returns:
            Dict com informações do arquivo salvo
        """
        try:
            # Gera nome do arquivo
            produto_clean = produto.replace(' ', '_').replace('/', '_')
            filename = f"RES_BUSCA_{produto_clean.upper()}.json"
            filepath = os.path.join(self.base_dir, filename)

            # Adiciona metadados finais
            massive_data_final = {
                **massive_data,
                'metadata': {
                    **massive_data.get('metadata', {}),
                    'finalized_at': datetime.now().isoformat(),
                    'file_type': 'massive_search_result',
                    'agent': 'AutoSaveManager_Centralized'
                }
            }

            # Salva arquivo final
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(massive_data_final, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(filepath) / 1024  # KB
            logger.info(f"✅ Resultado massivo salvo: {filename} ({file_size:.1f}KB)")

            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'size_kb': file_size,
                'data': massive_data_final
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultado massivo: {e}")
            return {'success': False, 'error': str(e)}

    def _save_individual_content(self, content_data: Dict[str, Any], session_id: str, category: str) -> Optional[str]:
        """Salva arquivo individual de conteúdo"""
        try:
            # Cria estrutura de diretórios
            if session_id:
                dir_path = os.path.join(self.base_dir, category, session_id)
            else:
                dir_path = os.path.join(self.base_dir, category)

            os.makedirs(dir_path, exist_ok=True)

            # Gera nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            url_hash = hashlib.md5(content_data['url'].encode()).hexdigest()[:8]
            filename = f"trecho_{url_hash}_{timestamp}.json"
            filepath = os.path.join(dir_path, filename)

            # Prepara dados para salvamento
            save_data = {
                'url': content_data['url'],
                'titulo': content_data.get('titulo', ''),
                'conteudo': content_data.get('conteudo', ''),
                'metodo_extracao': content_data.get('metodo_extracao', ''),
                'qualidade': content_data.get('qualidade', 0.0),
                'timestamp_extracao': datetime.now().isoformat(),
                'session_id': session_id,
                'metadata': content_data.get('metadata', {})
            }

            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            return filepath

        except Exception as e:
            logger.error(f"❌ Erro ao salvar arquivo individual: {e}")
            return None

    def _save_to_consolidated(self, content_data: Dict[str, Any], session_id: str, category: str) -> Optional[str]:
        """Adiciona conteúdo ao arquivo consolidado da sessão"""
        try:
            # Caminho do arquivo consolidado
            dir_path = os.path.join(self.base_dir, category, session_id)
            os.makedirs(dir_path, exist_ok=True)
            filepath = os.path.join(dir_path, "consolidado.json")

            # Carrega arquivo existente ou cria novo
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    consolidated_data = json.load(f)
            else:
                consolidated_data = {
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'trechos': []
                }

            # Adiciona novo trecho
            new_entry = {
                'url': content_data['url'],
                'titulo': content_data.get('titulo', ''),
                'conteudo': content_data.get('conteudo', ''),
                'metodo_extracao': content_data.get('metodo_extracao', ''),
                'qualidade': content_data.get('qualidade', 0.0),
                'timestamp_adicao': datetime.now().isoformat()
            }

            consolidated_data['trechos'].append(new_entry)
            consolidated_data['updated_at'] = datetime.now().isoformat()
            consolidated_data['total_trechos'] = len(consolidated_data['trechos'])

            # Salva arquivo consolidado
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=2)

            return filepath

        except Exception as e:
            logger.error(f"❌ Erro ao salvar no consolidado: {e}")
            return None

    def _save_extraction_step(self, content_data: Dict[str, Any], session_id: str) -> Optional[str]:
        """Salva etapa de extração nos relatórios intermediários"""
        try:
            step_name = f"extracao_{content_data.get('metodo_extracao', 'unknown')}"
            step_data = {
                'url': content_data['url'],
                'session_id': session_id,
                'metodo': content_data.get('metodo_extracao', ''),
                'qualidade': content_data.get('qualidade', 0.0),
                'tamanho_conteudo': len(content_data.get('conteudo', '')),
                'timestamp': datetime.now().isoformat()
            }

            return salvar_etapa(step_name, step_data, categoria='extração')

        except Exception as e:
            logger.error(f"❌ Erro ao salvar etapa de extração: {e}")
            return None

    def save_screenshot(self, screenshot_data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """
        Salva dados de screenshot com informações detalhadas.

        Args:
            screenshot_data: {
                'url': str,
                'image_base64': str,
                'descricao': str,
                'metodo_captura': str,
                'qualidade_imagem': float,
                'metadata': dict (opcional)
            }
            session_id: ID da sessão para organização.

        Returns:
            Dict com informações do arquivo salvo.
        """
        try:
            if not screenshot_data.get('url') or not screenshot_data.get('image_base64'):
                logger.warning("⚠️ Dados insuficientes para salvamento de screenshot")
                return {'success': False, 'error': 'Dados insuficientes'}

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            url_hash = hashlib.md5(screenshot_data['url'].encode()).hexdigest()[:8]
            filename = f"screenshot_{url_hash}_{timestamp}.json"

            # Diretório para screenshots
            screenshots_dir = os.path.join(self.base_dir, 'screenshots', screenshot_data.get('metodo_captura', 'unknown'))
            os.makedirs(screenshots_dir, exist_ok=True)
            filepath = os.path.join(screenshots_dir, filename)

            # Preparar dados para salvamento
            save_data = {
                'url': screenshot_data['url'],
                'descricao': screenshot_data.get('descricao', ''),
                'metodo_captura': screenshot_data.get('metodo_captura', ''),
                'qualidade_imagem': screenshot_data.get('qualidade_imagem', 0.0),
                'timestamp_captura': datetime.now().isoformat(),
                'session_id': session_id,
                'metadata': screenshot_data.get('metadata', {})
            }

            # Salva o arquivo JSON com os metadados
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            # Opcional: Salvar a imagem em si, se necessário (e se não for muito grande para o JSON)
            # Se a imagem for muito grande, é melhor mantê-la apenas no base64 dentro do JSON

            file_size = os.path.getsize(filepath) / 1024  # KB
            logger.info(f"📸 Screenshot salvo: {filename} ({file_size:.1f}KB)")

            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'size_kb': file_size
            }

        except Exception as e:
            logger.error(f"❌ Erro ao salvar screenshot: {e}")
            return {'success': False, 'error': str(e)}


    # === MÉTODOS AUXILIARES DE SALVAMENTO ===

    def _ensure_directories(self):
        """Garante que todos os diretórios necessários existem"""
        directories = [
            self.base_dir,
            self.relatorios_dir,
            f"{self.relatorios_dir}/analise_completa",
            f"{self.relatorios_dir}/pesquisa_web", # Para logs do WebSailor
            f"{self.relatorios_dir}/logs",
            f"{self.relatorios_dir}/erros",
            f"{self.relatorios_dir}/workflow", # Para etapas do workflow
            f"{self.base_dir}/analyses",
            f"{self.base_dir}/anti_objecao",
            f"{self.base_dir}/avatars",
            f"{self.base_dir}/completas",
            f"{self.base_dir}/concorrencia",
            f"{self.base_dir}/drivers_mentais",
            f"{self.base_dir}/files",
            f"{self.base_dir}/funil_vendas",
            f"{self.base_dir}/insights",
            f"{self.base_dir}/logs",
            f"{self.base_dir}/metadata",
            f"{self.base_dir}/metricas",
            f"{self.base_dir}/palavras_chave",
            f"{self.base_dir}/pesquisa_web", # *** NOVO: Diretório principal para trechos de texto ***
            f"{self.base_dir}/plano_acao",
            f"{self.base_dir}/posicionamento",
            f"{self.base_dir}/pre_pitch",
            f"{self.base_dir}/predicoes_futuro",
            f"{self.base_dir}/progress",
            f"{self.base_dir}/provas_visuais",
            f"{self.base_dir}/reports",
            f"{self.base_dir}/users",
            f"{self.base_dir}/screenshots", # Diretório base para screenshots
            f"{self.base_dir}/screenshots/puppeteer", # Exemplo de subdiretório
            f"{self.base_dir}/screenshots/selenium", # Exemplo de subdiretório
            f"{self.base_dir}/viral_images_data" # Diretório para dados virais
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                logger.error(f"❌ Erro ao criar diretório {directory}: {e}")


    def salvar_etapa(self, nome_etapa: str, dados: Any, categoria: str = "analise_completa", session_id: str = None) -> str:
        """Salva uma etapa do processo com timestamp"""
        try:
            # Gera timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            # Define diretório base
            if session_id:
                diretorio = f"{self.relatorios_dir}/{categoria}/{session_id}"
            else:
                diretorio = f"{self.relatorios_dir}/{categoria}"

            os.makedirs(diretorio, exist_ok=True)

            # Nome do arquivo
            nome_arquivo = f"{nome_etapa}_{timestamp}"

            # Salva como JSON se possível
            try:
                arquivo_json = f"{diretorio}/{nome_arquivo}.json"

                # Serializa dados de forma segura
                dados_serializaveis = serializar_dados_seguros(dados)

                # Valida se há conteúdo nos dados
                if not dados_serializaveis or (isinstance(dados_serializaveis, dict) and not dados_serializaveis.get("data")):
                    logger.warning(f"⚠️ Dados vazios para {nome_etapa}, criando placeholder")
                    dados_serializaveis = {
                        "status": "empty_data",
                        "message": "Dados não disponíveis no momento",
                        "timestamp": datetime.now().isoformat(),
                        "original_data": dados_serializaveis
                    }

                with open(arquivo_json, 'w', encoding='utf-8') as f:
                    json.dump(dados_serializaveis, f, ensure_ascii=False, indent=2)

                logger.info(f"💾 Etapa '{nome_etapa}' salva: {arquivo_json}")

                # INTEGRAÇÃO COM ANÁLISE PREDITIVA
                self._trigger_predictive_analysis(nome_etapa, dados_serializaveis, categoria, session_id)

                # TAMBÉM salva na pasta analyses_data se for um módulo
                # Lista de categorias que devem ser salvas em analyses_data
                modulos_para_analyses_data = [
                    "avatars", "drivers_mentais", "anti_objecao", "provas_visuais",
                    "pre_pitch", "predicoes_futuro", "posicionamento", "concorrencia",
                    "palavras_chave", "funil_vendas", "insights", "plano_acao",
                    "pesquisa_web", "viral_images_data" # Adicionado pesquisa_web e viral_images_data
                ]

                # Verifica se a categoria atual está na lista de módulos a serem salvos em analyses_data
                if categoria in modulos_para_analyses_data:
                    try:
                        # Assumindo que a categoria já é o nome base do módulo
                        nome_modulo_base = categoria

                        analyses_dir = f"{self.base_dir}/{categoria}"
                        os.makedirs(analyses_dir, exist_ok=True)

                        analyses_arquivo_nome = f"{nome_modulo_base}_{timestamp}.json" if session_id is None else f"{nome_modulo_base}_{session_id}_{timestamp}.json"
                        analyses_arquivo = os.path.join(analyses_dir, analyses_arquivo_nome)

                        with open(analyses_arquivo, 'w', encoding='utf-8') as f:
                            json.dump(dados_serializaveis, f, ensure_ascii=False, indent=2)

                        logger.info(f"💾 Módulo também salvo em analyses_data: {analyses_arquivo}")

                    except Exception as e:
                        logger.warning(f"⚠️ Não foi possível salvar em analyses_data para a etapa {nome_etapa} (categoria: {categoria}): {e}")

                return arquivo_json

            except Exception as json_error:
                logger.warning(f"⚠️ Falha ao salvar como JSON ({json_error}), tentando salvar como texto...")
                # Fallback para texto se falhar ao salvar como JSON
                arquivo_txt = f"{diretorio}/{nome_arquivo}.txt"
                with open(arquivo_txt, 'w', encoding='utf-8') as f:
                    if isinstance(dados, str):
                        f.write(dados)
                    else:
                        f.write(str(dados))

                logger.info(f"💾 Etapa '{nome_etapa}' salva: {arquivo_txt}")
                return arquivo_txt

        except Exception as e:
            logger.error(f"❌ Erro ao salvar etapa {nome_etapa}: {e}")
            return ""

    # === NOVA FUNÇÃO: salvar_trecho_pesquisa_web ===
    def salvar_trecho_pesquisa_web(self, url: str, titulo: str, conteudo: str, metodo_extracao: str, qualidade: float, session_id: str = None) -> str:
        """
        Salva um trecho de pesquisa web extraído com MÁXIMA CONSOLIDAÇÃO

        Args:
            url: URL do conteúdo extraído
            titulo: Título do conteúdo
            conteudo: Conteúdo extraído
            metodo_extracao: Método usado para extração (jina, firecrawl, etc.)
            qualidade: Score de qualidade (0-100)
            session_id: ID da sessão (opcional)

        Returns:
            Caminho do arquivo salvo
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

        # Cria nome do arquivo baseado na URL
        url_clean = re.sub(r'[^\w\-_.]', '_', url)[:100]  # Limita tamanho
        filename = f"trecho_{url_clean}_{timestamp}.json"

        # Estrutura de dados EXPANDIDA para consolidação
        trecho_data = {
            'url': url,
            'titulo': titulo,
            'conteudo': conteudo,
            'metodo_extracao': metodo_extracao,
            'qualidade': qualidade,
            'timestamp_extracao': timestamp,
            'session_id': session_id,
            # NOVOS CAMPOS PARA CONSOLIDAÇÃO
            'tamanho_conteudo': len(conteudo),
            'palavras_chave': self._extrair_palavras_chave(conteudo),
            'tipo_conteudo': self._identificar_tipo_conteudo(url, titulo),
            'plataforma': self._identificar_plataforma(url),
            'engajamento_estimado': self._calcular_engajamento_estimado(conteudo, qualidade),
            'relevancia_comercial': self._avaliar_relevancia_comercial(conteudo, titulo)
        }

        try:
            # 🔥 SALVA EM MÚLTIPLOS LOCAIS PARA GARANTIR CONSOLIDAÇÃO
            saved_paths = []

            # 1. Diretório específico da sessão
            if session_id:
                session_dir = os.path.join(self.base_dir, 'pesquisa_web', session_id) # Use analyses_path consistentemente
                os.makedirs(session_dir, exist_ok=True)
                session_path = os.path.join(session_dir, filename)

                with open(session_path, 'w', encoding='utf-8') as f:
                    json.dump(trecho_data, f, ensure_ascii=False, indent=2)
                saved_paths.append(session_path)

            # 2. Diretório geral de pesquisa web
            general_dir = os.path.join(self.base_dir, 'pesquisa_web') # Use analyses_path consistentemente
            os.makedirs(general_dir, exist_ok=True)
            general_path = os.path.join(general_dir, filename)

            with open(general_path, 'w', encoding='utf-8') as f:
                json.dump(trecho_data, f, ensure_ascii=False, indent=2)
            saved_paths.append(general_path)

            # 3. 🔥 TAMBÉM SALVA EM ARQUIVO CONSOLIDADO DA SESSÃO
            if session_id:
                self._adicionar_ao_arquivo_consolidado(session_id, trecho_data)

            logger.info(f"🔍 Trecho CONSOLIDADO salvo em {len(saved_paths)} locais (Qualidade: {qualidade})")
            return saved_paths[0] if saved_paths else ""

        except Exception as e:
            logger.error(f"❌ Erro ao salvar trecho consolidado: {e}")
            return ""

    def _extrair_palavras_chave(self, conteudo: str) -> List[str]:
        """Extrai palavras-chave do conteúdo"""
        try:
            # Palavras mais frequentes (simples)
            palavras = re.findall(r'\b\w{4,}\b', conteudo.lower())
            from collections import Counter
            palavras_freq = Counter(palavras)
            return [palavra for palavra, freq in palavras_freq.most_common(10)]
        except:
            return []

    def _identificar_tipo_conteudo(self, url: str, titulo: str) -> str:
        """Identifica o tipo de conteúdo baseado na URL e título"""
        url_lower = url.lower()
        titulo_lower = titulo.lower()

        if 'instagram.com' in url_lower:
            if '/reel/' in url_lower:
                return 'instagram_reel'
            elif '/p/' in url_lower:
                return 'instagram_post'
            else:
                return 'instagram_profile'
        elif 'facebook.com' in url_lower:
            return 'facebook_post'
        elif 'tiktok.com' in url_lower:
            return 'tiktok_video'
        elif 'youtube.com' in url_lower:
            return 'youtube_video'
        elif any(palavra in titulo_lower for palavra in ['curso', 'aula', 'tutorial']):
            return 'conteudo_educacional'
        elif any(palavra in titulo_lower for palavra in ['venda', 'compra', 'preço']):
            return 'conteudo_comercial'
        else:
            return 'conteudo_web'

    def _identificar_plataforma(self, url: str) -> str:
        """Identifica a plataforma baseada na URL"""
        url_lower = url.lower()

        if 'instagram.com' in url_lower:
            return 'Instagram'
        elif 'facebook.com' in url_lower:
            return 'Facebook'
        elif 'tiktok.com' in url_lower:
            return 'TikTok'
        elif 'youtube.com' in url_lower:
            return 'YouTube'
        elif 'linkedin.com' in url_lower:
            return 'LinkedIn'
        else:
            return 'Web'

    def _calcular_engajamento_estimado(self, conteudo: str, qualidade: float) -> float:
        """Calcula engajamento estimado baseado no conteúdo e qualidade"""
        try:
            # Fatores que indicam engajamento
            fatores_engajamento = 0
            conteudo_lower = conteudo.lower()

            # Palavras que indicam engajamento
            palavras_engajamento = ['like', 'compartilh', 'coment', 'view', 'seguir', 'inscrev']
            for palavra in palavras_engajamento:
                if palavra in conteudo_lower:
                    fatores_engajamento += 1

            # Tamanho do conteúdo
            if len(conteudo) > 1000:
                fatores_engajamento += 1

            # Qualidade
            fator_qualidade = qualidade / 100

            return min(10.0, (fatores_engajamento * 2 + fator_qualidade * 3))
        except:
            return 0.0

    def _avaliar_relevancia_comercial(self, conteudo: str, titulo: str) -> float:
        """Avalia relevância comercial do conteúdo"""
        try:
            texto_completo = (conteudo + " " + titulo).lower()

            # Palavras que indicam relevância comercial
            palavras_comerciais = [
                'vend', 'compr', 'preç', 'valor', 'custo', 'investir',
                'curso', 'aula', 'ensino', 'aprend', 'dica', 'tutorial',
                'negócio', 'empresa', 'marca', 'produto', 'serviço'
            ]

            relevancia = 0
            for palavra in palavras_comerciais:
                if palavra in texto_completo:
                    relevancia += 1

            return min(10.0, relevancia)
        except:
            return 0.0

    def _adicionar_ao_arquivo_consolidado(self, session_id: str, trecho_data: Dict[str, Any]):
        """Adiciona trecho ao arquivo consolidado da sessão"""
        try:
            consolidado_path = os.path.join(self.base_dir, 'pesquisa_web', session_id, 'consolidado.json') # Use analyses_path consistently

            # Carrega arquivo existente ou cria novo
            if os.path.exists(consolidado_path):
                with open(consolidado_path, 'r', encoding='utf-8') as f:
                    consolidado = json.load(f)
            else:
                consolidado = {
                    'session_id': session_id,
                    'trechos': [],
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }

            # Adiciona novo trecho
            consolidado['trechos'].append(trecho_data)
            consolidado['last_updated'] = datetime.now().isoformat()
            consolidado['total_trechos'] = len(consolidado['trechos'])

            # Salva arquivo consolidado
            with open(consolidado_path, 'w', encoding='utf-8') as f:
                json.dump(consolidado, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Trecho adicionado ao arquivo consolidado: {consolidado_path}")

        except Exception as e:
            logger.error(f"❌ Erro ao adicionar ao arquivo consolidado: {e}")

    def salvar_erro(self, nome_erro: str, erro: Exception, contexto: Dict[str, Any] = None, session_id: str = None) -> str:
        """Salva um erro com contexto"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            if session_id:
                diretorio = f"{self.relatorios_dir}/erros/{session_id}"
            else:
                diretorio = f"{self.relatorios_dir}/erros"

            os.makedirs(diretorio, exist_ok=True)

            erro_data = {
                "erro": str(erro),
                "tipo": type(erro).__name__,
                "timestamp": timestamp,
                "contexto": contexto or {}
            }

            arquivo_erro = f"{diretorio}/ERRO_{nome_erro}_{timestamp}.txt"
            with open(arquivo_erro, 'w', encoding='utf-8') as f:
                f.write(f"ERRO: {nome_erro}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Tipo: {type(erro).__name__}\n")
                f.write(f"Mensagem: {str(erro)}\n")
                if contexto:
                    f.write(f"Contexto: {json.dumps(contexto, ensure_ascii=False, indent=2)}\n")

            logger.error(f"💾 Erro '{nome_erro}' salvo: {arquivo_erro}")
            return arquivo_erro

        except Exception as e:
            logger.error(f"❌ Erro ao salvar erro {nome_erro}: {e}")
            return ""

    def salvar_modulo_analyses_data(self, nome_modulo: str, dados: Any, session_id: str = None) -> str:
        """Salva módulo na pasta analyses_data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            # Diretório específico do módulo - vamos usar a categoria 'geral' por padrão se não especificada
            # Ou, se quiser uma estrutura mais granular, pode passar a categoria como argumento
            categoria = "geral" # Valor padrão, pode ser ajustado se necessário

            # Tentativa de inferir categoria do nome_modulo se ele tiver o formato esperado
            if "_" in nome_modulo:
                parts = nome_modulo.split("_")
                if len(parts) > 1:
                    # Assumindo que a categoria é a parte antes do primeiro underscore, ex: "funil_vendas" -> "funil_vendas"
                    # Ou se for algo como "module_funil_vendas", a categoria seria "funil_vendas"
                    # Vamos simplificar e usar a categoria que foi passada na função salvar_etapa se ela existir.
                    # Se não, vamos usar uma categoria genérica ou o nome do módulo sem o prefixo se houver.
                    pass # Manteremos a lógica de categoria sendo passada de salvar_etapa

            diretorio = f"{self.base_dir}/{categoria}"
            os.makedirs(diretorio, exist_ok=True)

            # Nome do arquivo
            if session_id:
                nome_arquivo = f"{nome_modulo}_{session_id}_{timestamp}.json"
            else:
                nome_arquivo = f"{nome_modulo}_{timestamp}.json"

            arquivo_completo = f"{diretorio}/{nome_arquivo}"

            # Salva como JSON
            with open(arquivo_completo, 'w', encoding='utf-8') as f:
                if isinstance(dados, (dict, list)):
                    json.dump(dados, f, ensure_ascii=False, indent=2)
                else:
                    json.dump({"modulo": nome_modulo, "dados": str(dados), "timestamp": timestamp}, f, ensure_ascii=False, indent=2)

            logger.info(f"📁 Módulo '{nome_modulo}' salvo em analyses_data: {arquivo_completo}")
            return arquivo_completo

        except Exception as e:
            logger.error(f"❌ Erro ao salvar módulo {nome_modulo} em analyses_data: {e}")
            return ""

    def salvar_json_gigante(self, dados: Dict[str, Any], session_id: str) -> str:
        """Salva JSON gigante com dados massivos"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dados_massivos_{session_id}_{timestamp}.json"
            filepath = os.path.join(self.base_dir, "completas", filename)

            # Garante que o diretório existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Salva JSON com formatação
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)

            # Calcula estatísticas
            file_size = os.path.getsize(filepath)
            content_length = len(json.dumps(dados, ensure_ascii=False))

            logger.info(f"💾 JSON gigante salvo: {filepath}")
            logger.info(f"📊 Tamanho: {file_size:,} bytes ({content_length:,} caracteres)")

            return filepath

        except Exception as e:
            logger.error(f"❌ Erro ao salvar JSON gigante: {e}")
            raise

    def recuperar_etapa(self, nome_etapa: str, session_id: str = None) -> Dict[str, Any]:
        """Recupera dados de uma etapa salva"""
        try:
            if session_id:
                diretorio = f"{self.relatorios_dir}/{session_id}"
            else:
                diretorio = self.relatorios_dir

            # Procura arquivo da etapa
            import glob
            pattern = f"{diretorio}/*{nome_etapa}*.json"
            arquivos = glob.glob(pattern)

            if not arquivos:
                return {"status": "nao_encontrado", "dados": {}}

            # Pega o arquivo mais recente
            arquivo_mais_recente = max(arquivos, key=os.path.getctime)

            with open(arquivo_mais_recente, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            return {"status": "sucesso", "dados": dados, "arquivo": arquivo_mais_recente}

        except Exception as e:
            logger.error(f"❌ Erro ao recuperar etapa {nome_etapa}: {e}")
            return {"status": "erro", "erro": str(e), "dados": {}}

    def listar_etapas_salvas(self, session_id: str = None) -> Dict[str, str]:
        """Lista todas as etapas salvas"""
        etapas = {}

        try:
            if session_id:
                base_dir = f"{self.relatorios_dir}"
                for categoria in os.listdir(base_dir):
                    categoria_path = f"{base_dir}/{categoria}"
                    if os.path.isdir(categoria_path):
                        session_path = f"{categoria_path}/{session_id}"
                        if os.path.exists(session_path):
                            for arquivo in os.listdir(session_path):
                                if arquivo.endswith(('.json', '.txt')):
                                    nome_etapa = arquivo.split('_')[0]
                                    etapas[nome_etapa] = f"{session_path}/{arquivo}"

        except Exception as e:
            logger.error(f"❌ Erro ao listar etapas: {e}")

        return etapas

    def recuperar_etapa(self, nome_etapa: str, session_id: str = None) -> Dict[str, Any]:
        """Recupera dados de uma etapa salva"""
        try:
            etapas = self.listar_etapas_salvas(session_id)

            if nome_etapa in etapas:
                arquivo = etapas[nome_etapa]

                if arquivo.endswith('.json'):
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    return {"status": "sucesso", "dados": dados}
                else:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        dados = f.read()
                    return {"status": "sucesso", "dados": dados}

            return {"status": "erro", "mensagem": "Etapa não encontrada"}

        except Exception as e:
            logger.error(f"❌ Erro ao recuperar etapa {nome_etapa}: {e}")
            return {"status": "erro", "mensagem": str(e)}

    def salvar_json_gigante(self, dados_massivos: Dict[str, Any], session_id: str) -> str:
        """Salva o JSON gigante com todos os dados coletados"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            diretorio = f"{self.base_dir}/completas"
            os.makedirs(diretorio, exist_ok=True)

            arquivo = f"{diretorio}/dados_massivos_{session_id}_{timestamp}.json"

            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados_massivos, f, ensure_ascii=False, indent=2)

            logger.info(f"🗂️ JSON gigante salvo: {arquivo}")
            return arquivo

        except Exception as e:
            logger.error(f"❌ Erro ao salvar JSON gigante: {e}")
            return ""

    def salvar_relatorio_final(self, relatorio: str, session_id: str) -> str:
        """Salva o relatório final detalhado"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            diretorio = f"{self.base_dir}/reports" # Usando base_dir para relatórios finais também
            os.makedirs(diretorio, exist_ok=True)

            # Salva também como .md para facilitar visualização
            arquivo_md = f"{diretorio}/relatorio_final_{session_id}_{timestamp}.md"
            with open(arquivo_md, 'w', encoding='utf-8') as f:
                f.write(relatorio)

            # Salva como .txt também, mantendo compatibilidade
            arquivo_txt = f"{diretorio}/relatorio_final_{session_id}_{timestamp}.txt"
            with open(arquivo_txt, 'w', encoding='utf-8') as f:
                f.write(relatorio)

            logger.info(f"📄 Relatório final salvo: {arquivo_md}")
            return arquivo_md

        except Exception as e:
            logger.error(f"❌ Erro ao salvar relatório final: {e}")
            return ""

    def _clean_for_serialization(self, obj, seen=None, depth=0):
        """Limpa objeto para serialização JSON removendo referências circulares e tipos não serializáveis"""
        if seen is None:
            seen = set()

        # Limite de profundidade para evitar recursão infinita
        if depth > 15:
            return {"__max_depth__": f"Depth limit reached at {depth}"}

        # Verifica referência circular
        obj_id = id(obj)
        if obj_id in seen:
            return {"__circular_ref__": f"{type(obj).__name__}_{obj_id}"}

        seen.add(obj_id)

        try:
            # Tipos primitivos - retorna direto
            if obj is None or isinstance(obj, (bool, int, float, str)):
                return obj

            # Dicionários - TRATAMENTO ESPECIAL PARA EVITAR unhashable type
            elif isinstance(obj, dict):
                result = {}
                for key, value in obj.items():
                    # Converte chaves para string segura
                    try:
                        if isinstance(key, (dict, list, set)):
                            # Se a chave é um tipo não hashable, converte para string
                            safe_key = f"key_{hash(str(key))}"
                        else:
                            safe_key = str(key)[:100]  # Limita tamanho da chave
                    except Exception:
                        safe_key = f"key_{obj_id}_{len(result)}"

                    try:
                        result[safe_key] = self._clean_for_serialization(value, seen.copy(), depth + 1)
                    except Exception as e:
                        result[safe_key] = f"<Error serializing: {str(e)[:50]}>"
                return result

            # Listas e tuplas
            elif isinstance(obj, (list, tuple)):
                result = []
                for i, item in enumerate(obj[:100]):  # Limita a 100 itens para evitar listas enormes
                    try:
                        result.append(self._clean_for_serialization(item, seen.copy(), depth + 1))
                    except Exception as e:
                        result.append(f"<Error at index {i}: {str(e)[:50]}>")
                return result

            # Sets - converte para lista
            elif isinstance(obj, set):
                try:
                    return [self._clean_for_serialization(item, seen.copy(), depth + 1) for item in list(obj)[:50]]
                except Exception:
                    return [f"<Set item {i}>" for i in range(min(len(obj), 50))]

            # Objetos com __dict__
            elif hasattr(obj, '__dict__'):
                try:
                    return self._clean_for_serialization(obj.__dict__, seen.copy(), depth + 1)
                except Exception:
                    return {"__object__": f"{type(obj).__name__}"}

            # Funções e métodos
            elif callable(obj):
                return f"<function {getattr(obj, '__name__', 'unknown')}>"

            # Tipos especiais (datetime, etc)
            elif hasattr(obj, 'isoformat'):  # datetime objects
                try:
                    return obj.isoformat()
                except Exception:
                    return str(obj)

            # Outros tipos - converte para string segura
            else:
                try:
                    # Tenta serializar diretamente primeiro
                    import json
                    json.dumps(obj)
                    return obj
                except (TypeError, ValueError):
                    # Se não conseguir, converte para string
                    try:
                        str_repr = str(obj)[:500]  # Limita tamanho
                        return {"__string_repr__": str_repr, "__type__": type(obj).__name__}
                    except Exception:
                        return {"__unserializable__": type(obj).__name__}

        except Exception as e:
            logger.warning(f"Erro crítico ao limpar objeto: {e}")
            return {"__serialization_error__": str(e)[:100]}
        finally:
            seen.discard(obj_id)

    def make_serializable(self, data):
        """
        Converte objetos não serializáveis para formatos JSON-compatíveis
        Versão otimizada para resolver problemas específicos de 'unhashable type: dict'
        """
        try:
            # Testa se já é serializável
            import json
            json.dumps(data)
            return data
        except (TypeError, ValueError) as e:
            if "unhashable type" in str(e):
                logger.warning(f"⚠️ Detectado problema 'unhashable type', aplicando correção...")
            return self._clean_for_serialization(data)

    def _trigger_predictive_analysis(self, nome_etapa: str, dados: Dict[str, Any], categoria: str, session_id: str):
        """
        Aciona análises preditivas automaticamente após salvar dados-chave.
        Implementa as especificações dos aprimoramentos.
        """
        if not session_id:
            return

        try:
            predictive_service = get_predictive_service()
            if not predictive_service:
                return

            # Condição 1: Após salvar dados da categoria 'pesquisa_web'
            if categoria == "pesquisa_web" or "websailor" in nome_etapa.lower():
                try:
                    # Extrai conteúdo para análise
                    content = ""
                    if isinstance(dados, dict):
                        if "data" in dados:
                            content = str(dados["data"])
                        elif "content" in dados:
                            content = str(dados["content"])
                        else:
                            content = str(dados)
                    else:
                        content = str(dados)

                    # Calcula score de qualidade
                    qualidade_score = predictive_service.get_content_quality_score(content)

                    # Salva o score
                    self.salvar_etapa(
                        f"{nome_etapa}_qualidade",
                        {"score": qualidade_score, "content_length": len(content)},
                        "analise_qualidade",
                        session_id
                    )

                    logger.info(f"🔮 Score de qualidade calculado para {nome_etapa}: {qualidade_score:.1f}")

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao calcular qualidade para {nome_etapa}: {e}")

            # Condição 2: Após salvar dados da categoria 'conteudo_sintetizado'
            elif categoria == "conteudo_sintetizado" or "sintese" in nome_etapa.lower():
                try:
                    # Extrai conteúdo principal
                    conteudo_principal = ""
                    if isinstance(dados, dict):
                        if "data" in dados and isinstance(dados["data"], dict):
                            conteudo_principal = dados["data"].get("conteudo_principal", "")
                        elif "conteudo_principal" in dados:
                            conteudo_principal = dados["conteudo_principal"]
                        else:
                            conteudo_principal = str(dados)
                    else:
                        conteudo_principal = str(dados)

                    if conteudo_principal:
                        # Executa análise de chunk de forma assíncrona
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            insights_parciais = loop.run_until_complete(
                                predictive_service.analyze_content_chunk(conteudo_principal)
                            )

                            # Salva insights parciais
                            self.salvar_etapa(
                                f"{nome_etapa}_insights_parciais",
                                insights_parciais,
                                "insights_parciais",
                                session_id
                            )

                            logger.info(f"🔮 Insights parciais gerados para {nome_etapa}")

                        finally:
                            loop.close()

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao gerar insights parciais para {nome_etapa}: {e}")

        except Exception as e:
            logger.warning(f"⚠️ Erro na integração preditiva para {nome_etapa}: {e}")

# Instância global
auto_save_manager = AutoSaveManager()

# Funções de conveniência para importação direta
def salvar_etapa(nome_etapa: str, dados: Any, categoria: str = "analise_completa", session_id: str = None) -> str:
    """Função de conveniência para salvar etapa"""
    # A lógica de salvar em analyses_data já está dentro do método salvar_etapa
    return auto_save_manager.salvar_etapa(nome_etapa, dados, categoria, session_id)

# === NOVA FUNÇÃO DE CONVENIÊNCIA ===
def salvar_trecho_pesquisa_web(url: str, titulo: str, conteudo: str, metodo_extracao: str, qualidade: float, session_id: str = None) -> str:
    """Função de conveniência para salvar trecho de pesquisa web."""
    return auto_save_manager.salvar_trecho_pesquisa_web(url, titulo, conteudo, metodo_extracao, qualidade, session_id)

# Nova função de conveniência para salvar screenshots
def salvar_screenshot(screenshot_data: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
    """Função de conveniência para salvar dados de screenshot."""
    return auto_save_manager.save_screenshot(screenshot_data, session_id)


def salvar_erro(nome_erro: str, erro: Exception, contexto: Dict[str, Any] = None, session_id: str = None) -> str:
    """Função de conveniência para salvar erro"""
    return auto_save_manager.salvar_erro(nome_erro, erro, contexto, session_id)

def salvar_modulo_analyses_data(nome_modulo: str, dados: Any, session_id: str = None) -> str:
    """Função de conveniência para salvar módulo em analyses_data"""
    # Esta função pode ser mantida para uso explícito, mas a lógica principal está em salvar_etapa
    return auto_save_manager.salvar_modulo_analyses_data(nome_modulo, dados, session_id)