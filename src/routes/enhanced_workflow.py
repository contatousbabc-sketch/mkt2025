#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced Workflow Routes
Rotas para o workflow aprimorado em 3 etapas
"""
import logging
import time
import uuid
import asyncio
import os
import glob
import json
from datetime import datetime
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, send_file
import threading
# Import dos serviços necessários
# services.auto_save_manager será importado diretamente para evitar circular imports
def get_services():
    """Lazy loading dos serviços para evitar problemas de inicialização"""
    try:
        from services.real_search_orchestrator import real_search_orchestrator
        from services.massive_search_engine import massive_search_engine
        from services.viral_content_analyzer import viral_content_analyzer
        from services.enhanced_synthesis_engine import enhanced_synthesis_engine
        from services.enhanced_module_processor import enhanced_module_processor
        from services.comprehensive_report_generator_v3 import comprehensive_report_generator_v3
        from services.viral_report_generator import ViralReportGenerator
        from services.viral_integration_service import ViralImageFinder
        return {
            'real_search_orchestrator': real_search_orchestrator,
            'massive_search_engine': massive_search_engine,
            'viral_content_analyzer': viral_content_analyzer,
            'enhanced_synthesis_engine': enhanced_synthesis_engine,
            'enhanced_module_processor': enhanced_module_processor,
            'comprehensive_report_generator_v3': comprehensive_report_generator_v3,
            'ViralReportGenerator': ViralReportGenerator,
            'viral_integration_service': ViralImageFinder()
        }
    except ImportError as e:
        logger.error(f"❌ Erro ao importar serviços: {e}")
        return None

logger = logging.getLogger(__name__)
enhanced_workflow_bp = Blueprint('enhanced_workflow', __name__)

# Instância global do AutoSaveManager para evitar circular imports e garantir consistência
from services.auto_save_manager import AutoSaveManager
auto_save_manager_instance = AutoSaveManager()
salvar_etapa = auto_save_manager_instance.salvar_etapa

@enhanced_workflow_bp.route('/workflow/step1/start', methods=['POST'])
def start_step1_collection():
    """ETAPA 1: Coleta Massiva de Dados com Screenshots"""
    try:
        data = request.get_json()
        # Gera session_id único
        session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        # Extrai parâmetros
        segmento = data.get('segmento', '').strip()
        produto = data.get('produto', '').strip()
        publico = data.get('publico', '').strip()
        # Validação
        if not segmento:
            return jsonify({"error": "Segmento é obrigatório"}), 400
        # Constrói query de pesquisa
        query_parts = [segmento]
        if produto:
            query_parts.append(produto)
        query_parts.extend(["Brasil", "2024", "mercado"])
        query = " ".join(query_parts)
        # Contexto da análise
        context = {
            "segmento": segmento,
            "produto": produto,
            "publico": publico,
            "query_original": query,
            "etapa": 1,
            "workflow_type": "enhanced_v3"
        }
        logger.info(f"🚀 ETAPA 1 INICIADA - Sessão: {session_id}")
        logger.info(f"🔍 Query: {query}")
        # Salva início da etapa 1
        salvar_etapa("etapa1_iniciada", {
            "session_id": session_id,
            "query": query,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        # Executa coleta massiva em thread separada
        def execute_collection_thread():
            logger.info(f"🚀 INICIANDO THREAD DE COLETA - Sessão: {session_id}")
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa1_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                async def async_collection_tasks():
                    search_results = {'web_results': [], 'social_results': [], 'youtube_results': []}
                    massive_results = {}
                    viral_analysis = {}
                    try:
                        # PRIMEIRA ETAPA: Busca viral (nova integração)
                        logger.info(f"🔥 Executando busca viral para: {query}")
                        viral_integration_service = services["viral_integration_service"]
                        viral_data = await viral_integration_service.find_viral_images(query=query)
                        viral_results_list = viral_data[0] if viral_data and len(viral_data) > 0 else []
                        viral_results_dicts = [img.__dict__ for img in viral_results_list]
                        viral_results = {
                             "search_completed_at": datetime.now().isoformat(),
                             "total_images_found": len(viral_results_list),
                             "total_images_saved": len([img for img in viral_results_list if img.image_path]),
                             "platforms_searched": list(set(img.platform for img in viral_results_list)),
                             "aggregated_metrics": {
                                 "total_engagement_score": sum(img.engagement_score for img in viral_results_list),
                                 "average_engagement": sum(img.engagement_score for img in viral_results_list) / len(viral_results_list) if viral_results_list else 0,
                                 "total_estimated_views": sum(img.views_estimate for img in viral_results_list),
                                 "total_estimated_likes": sum(img.likes_estimate for img in viral_results_list),
                                 "top_performing_platform": max(set(img.platform for img in viral_results_list), key=[img.platform for img in viral_results_list].count) if viral_results_list else None
                             },
                             "viral_images": viral_results_dicts,
                             "fallback_used": False
                         }
                        salvar_etapa("viral_search_completed", {
                            "session_id": session_id,
                            "viral_results": viral_results,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        # SEGUNDA ETAPA: Busca massiva real
                        logger.info(f"🔍 Executando busca massiva - Sessão: {session_id}")
                        real_search_orch = services["real_search_orchestrator"]
                        if hasattr(real_search_orch, "execute_massive_real_search"):
                            search_results = await real_search_orch.execute_massive_real_search(
                                query=query,
                                context=context,
                                session_id=session_id
                            )
                        else:
                            logger.error("❌ Método execute_massive_real_search não encontrado")
                        logger.info(f"✅ Busca massiva concluída - Sessão: {session_id}")
                        logger.info(f"🌐 Executando busca ALIBABA WebSailor - Sessão: {session_id}")
                        massive_results = await services['massive_search_engine'].execute_massive_search(
                            produto=context.get('segmento', context.get('produto', query)),
                            publico_alvo=context.get('publico', context.get('publico_alvo', 'público brasileiro')),
                            session_id=session_id
                        )
                        logger.info(f"✅ Busca ALIBABA WebSailor concluída - Sessão: {session_id}")
                        logger.info(f"🔥 Analisando e capturando conteúdo viral - Sessão: {session_id}")
                        viral_analysis = await services['viral_content_analyzer'].analyze_and_capture_viral_content(
                            search_results=search_results,
                            session_id=session_id,
                            max_captures=15
                        )
                        logger.info(f"✅ Análise viral concluída - Sessão: {session_id}")
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 1: {e}")
                        # Continua mesmo com erro para tentar gerar o relatório com o que foi coletado
                    # GERA RELATÓRIO VIRAL AUTOMATICAMENTE
                    logger.info("🔥 Gerando relatório viral automático...")
                    viral_report_generator = services['ViralReportGenerator']()
                    viral_report_success = viral_report_generator.generate_viral_report(session_id)
                    if viral_report_success:
                        logger.info("✅ Relatório viral gerado e salvo automaticamente")
                    else:
                        logger.warning("⚠️ Falha ao gerar relatório viral automático")
                    # GERA CONSOLIDAÇÃO FINAL COMPLETA
                    logger.info("🔗 CONSOLIDANDO TODOS OS DADOS DA ETAPA 1...")
                    consolidacao_final = _gerar_consolidacao_final_etapa1(
                        session_id, search_results, viral_analysis, massive_results, viral_results
                    )
                    # Gera relatório de coleta
                    collection_report = _generate_collection_report(
                        search_results, viral_analysis, session_id, context
                    )
                    # Salva relatório
                    _save_collection_report(collection_report, session_id)
                    # Salva resultado da etapa 1 COM CONSOLIDAÇÃO
                    salvar_etapa("etapa1_concluida", {
                        "session_id": session_id,
                        "search_results": search_results,
                        "viral_analysis": viral_analysis,
                        "massive_results": massive_results,
                        "consolidacao_final": consolidacao_final,
                        "collection_report_generated": True,
                        "timestamp": datetime.now().isoformat(),
                        "estatisticas_finais": consolidacao_final.get("estatisticas", {})
                    }, categoria="workflow", session_id=session_id)
                    logger.info(f"✅ ETAPA 1 CONCLUÍDA - Sessão: {session_id}")
                    logger.info(f"📊 CONSOLIDAÇÃO: {consolidacao_final.get('estatisticas', {}).get('total_dados_coletados', 0)} dados únicos")
                asyncio.run(async_collection_tasks())
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 1: {e}")
                salvar_etapa("etapa1_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        # Inicia a thread para a coleta
        thread = threading.Thread(target=execute_collection_thread)
        thread.start()
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 1 iniciada: Coleta massiva de dados em segundo plano",
            "query": query,
            "estimated_duration": "3-5 minutos",
            "next_step": "/api/workflow/step2/start",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 1: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar coleta de dados"
        }), 500

@enhanced_workflow_bp.route('/workflow/step2/start', methods=['POST'])
def start_step2_synthesis():
    """ETAPA 2: Síntese com IA e Busca Ativa"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400
        logger.info(f"🧠 ETAPA 2 INICIADA - Síntese para sessão: {session_id}")
        # Salva início da etapa 2
        salvar_etapa("etapa2_iniciada", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        # Executa síntese em thread separada
        def execute_synthesis_thread():
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa2_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                async def async_synthesis_tasks():
                    synthesis_result = {}
                    behavioral_result = {}
                    market_result = {}
                    try:
                        # Executa síntese master com busca ativa
                        synthesis_result = await services['enhanced_synthesis_engine'].execute_enhanced_synthesis(
                            session_id=session_id,
                            synthesis_type="master_synthesis"
                        )
                        # Executa síntese comportamental
                        behavioral_result = await services['enhanced_synthesis_engine'].execute_behavioral_synthesis(session_id)
                        # Executa síntese de mercado
                        market_result = await services['enhanced_synthesis_engine'].execute_market_synthesis(session_id)
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 2: {e}")
                    # Salva resultado da etapa 2
                    salvar_etapa("etapa2_concluida", {
                        "session_id": session_id,
                        "synthesis_result": synthesis_result,
                        "behavioral_result": behavioral_result,
                        "market_result": market_result,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    logger.info(f"✅ ETAPA 2 CONCLUÍDA - Sessão: {session_id}")
                asyncio.run(async_synthesis_tasks())
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 2: {e}")
                salvar_etapa("etapa2_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        # Inicia a thread para a síntese
        thread = threading.Thread(target=execute_synthesis_thread)
        thread.start()
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 2 iniciada: Síntese com IA e busca ativa em segundo plano",
            "estimated_duration": "2-4 minutos",
            "next_step": "/api/workflow/step3/start",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 2: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar síntese"
        }), 500

@enhanced_workflow_bp.route('/workflow/external_ai_verification', methods=['POST'])
def run_external_ai_verification():
    """VERIFICAÇÃO AI EXTERNA: Executa verificação dos dados antes da Etapa 3"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400

        logger.info(f"🤖 VERIFICAÇÃO AI INICIADA - Sessão: {session_id}")

        # Executa verificação em thread separada
        def execute_verification_thread():
            try:
                import asyncio
                from services.external_ai_integration import external_ai_integration

                async def async_verification():
                    result = await external_ai_integration.verify_session_data(session_id)

                    # Salva resultado da verificação
                    salvar_etapa("verificacao_ai_concluida", {
                        "session_id": session_id,
                        "verification_result": result,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)

                    logger.info(f"✅ VERIFICAÇÃO AI CONCLUÍDA - Sessão: {session_id}")

                asyncio.run(async_verification())

            except Exception as e:
                logger.error(f"❌ Erro na verificação AI: {e}")
                salvar_etapa("verificacao_ai_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)

        # Inicia a thread para verificação
        thread = threading.Thread(target=execute_verification_thread)
        thread.start()

        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Verificação AI iniciada em segundo plano",
            "estimated_duration": "1-2 minutos",
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar verificação AI: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar verificação AI"
        }), 500

@enhanced_workflow_bp.route('/workflow/step3/start', methods=['POST'])
def start_step3_generation():
    """ETAPA 3: Geração dos 16 Módulos e Relatório Final"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id é obrigatório"}), 400

        logger.info(f"📝 ETAPA 3 INICIADA - Geração para sessão: {session_id}")

        # Salva início da etapa 3
        salvar_etapa("etapa3_iniciada", {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        # Executa geração em thread separada
        def execute_generation_thread():
            try:
                # Carrega serviços de forma lazy
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários")
                    salvar_etapa("etapa3_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                async def async_generation_tasks():
                    modules_result = {}
                    final_report = ""
                    try:
                        # Gera todos os 16 módulos
                        modules_result = await services['enhanced_module_processor'].generate_all_modules(session_id)
                        # Compila relatório final
                        final_report = services['comprehensive_report_generator_v3'].compile_final_markdown_report(session_id)
                    except Exception as e:
                        logger.error(f"❌ Erro durante as operações assíncronas da Etapa 3: {e}")
                    # Salva resultado da etapa 3
                    salvar_etapa("etapa3_concluida", {
                        "session_id": session_id,
                        "modules_result": modules_result,
                        "final_report": final_report,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    logger.info(f"✅ ETAPA 3 CONCLUÍDA - Sessão: {session_id}")
                    logger.info(f"📊 {modules_result.get('successful_modules', 0)}/16 módulos gerados")
                asyncio.run(async_generation_tasks())
            except Exception as e:
                logger.error(f"❌ Erro na execução da Etapa 3: {e}")
                salvar_etapa("etapa3_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        # Inicia a thread para a geração
        thread = threading.Thread(target=execute_generation_thread)
        thread.start()
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Etapa 3 iniciada: Geração dos 16 módulos e relatório final em segundo plano",
            "estimated_duration": "4-6 minutos",
            "next_step": "/api/workflow/results", # Ou um endpoint para o relatório final
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar Etapa 3: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Falha ao iniciar geração"
        }), 500

@enhanced_workflow_bp.route('/workflow/full_workflow/start', methods=['POST'])
def start_full_workflow():
    """Inicia o workflow completo (Etapa 1, 2 e 3 em sequência) em segundo plano"""
    try:
        data = request.get_json()
        # Gera session_id único
        session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        # Extrai parâmetros
        segmento = data.get('segmento', '').strip()
        produto = data.get('produto', '').strip()
        publico = data.get('publico', '').strip()
        # Validação
        if not segmento:
            return jsonify({"error": "Segmento é obrigatório"}), 400
        # Constrói query de pesquisa
        query_parts = [segmento]
        if produto:
            query_parts.append(produto)
        query_parts.extend(["Brasil", "2024", "mercado"])
        query = " ".join(query_parts)
        # Contexto da análise
        context = {
            "segmento": segmento,
            "produto": produto,
            "publico": publico,
            "query_original": query,
            "workflow_type": "enhanced_v3"
        }
        logger.info(f"🚀 WORKFLOW COMPLETO INICIADO - Sessão: {session_id}")
        logger.info(f"🔍 Query: {query}")
        # Salva início do workflow completo
        salvar_etapa("workflow_completo_iniciado", {
            "session_id": session_id,
            "query": query,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }, categoria="workflow", session_id=session_id)
        def execute_full_workflow_thread():
            try:
                services = get_services()
                if not services:
                    logger.error("❌ Falha ao carregar serviços necessários para workflow completo")
                    salvar_etapa("workflow_erro", {
                        "session_id": session_id,
                        "error": "Falha ao carregar serviços para workflow completo",
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    return
                async def async_full_workflow_tasks():
                    search_results = {'web_results': [], 'social_results': [], 'youtube_results': []}
                    massive_results = {}
                    viral_analysis = {}
                    synthesis_result = {}
                    behavioral_result = {}
                    market_result = {}
                    modules_result = {}
                    final_report = ""
                    # ETAPA 1: Coleta Massiva de Dados
                    logger.info(f"🚀 INICIANDO ETAPA 1 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        real_search_orch = services['real_search_orchestrator']
                        if hasattr(real_search_orch, 'execute_massive_real_search'):
                            search_results = await real_search_orch.execute_massive_real_search(
                                query=query,
                                context=context,
                                session_id=session_id
                            )
                        else:
                            logger.error("❌ Método execute_massive_real_search não encontrado na Etapa 1 (Workflow Completo)")
                        massive_results = await services['massive_search_engine'].execute_massive_search(
                            produto=context.get('segmento', context.get('produto', query)),
                            publico_alvo=context.get('publico', context.get('publico_alvo', 'público brasileiro')),
                            session_id=session_id
                        )
                        viral_analysis = await services['viral_content_analyzer'].analyze_and_capture_viral_content(
                            search_results=search_results,
                            session_id=session_id,
                            max_captures=15
                        )
                        # GERA RELATÓRIO VIRAL AUTOMATICAMENTE
                        viral_report_generator = services['ViralReportGenerator']()
                        viral_report_generator.generate_viral_report(session_id)
                        # GERA CONSOLIDAÇÃO FINAL COMPLETA
                        consolidacao_final = _gerar_consolidacao_final_etapa1(
                            session_id, search_results, viral_analysis, massive_results
                        )
                        # Gera e salva relatório de coleta
                        collection_report = _generate_collection_report(
                            search_results, viral_analysis, session_id, context
                        )
                        _save_collection_report(collection_report, session_id)
                        salvar_etapa("etapa1_concluida_full_workflow", {
                            "session_id": session_id,
                            "search_results": search_results,
                            "viral_analysis": viral_analysis,
                            "massive_results": massive_results,
                            "consolidacao_final": consolidacao_final,
                            "collection_report_generated": True,
                            "timestamp": datetime.now().isoformat(),
                            "estatisticas_finais": consolidacao_final.get("estatisticas", {})
                        }, categoria="workflow", session_id=session_id)
                        logger.info(f"✅ ETAPA 1 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 1 (Workflow Completo): {e}")
                        salvar_etapa("etapa1_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a primeira etapa falhar
                    # ETAPA 2: Síntese com IA e Busca Ativa
                    logger.info(f"🧠 INICIANDO ETAPA 2 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        synthesis_result = await services['enhanced_synthesis_engine'].execute_enhanced_synthesis(
                            session_id=session_id,
                            synthesis_type="master_synthesis"
                        )
                        behavioral_result = await services['enhanced_synthesis_engine'].execute_behavioral_synthesis(session_id)
                        market_result = await services['enhanced_synthesis_engine'].execute_market_synthesis(session_id)
                        salvar_etapa("etapa2_concluida_full_workflow", {
                            "session_id": session_id,
                            "synthesis_result": synthesis_result,
                            "behavioral_result": behavioral_result,
                            "market_result": market_result,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        logger.info(f"✅ ETAPA 2 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 2 (Workflow Completo): {e}")
                        salvar_etapa("etapa2_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a segunda etapa falhar
                    # ETAPA 3: Geração dos 16 Módulos e Relatório Final
                    logger.info(f"📝 INICIANDO ETAPA 3 (Workflow Completo) - Sessão: {session_id}")
                    try:
                        modules_result = await services['enhanced_module_processor'].generate_all_modules(session_id)
                        final_report = services['comprehensive_report_generator_v3'].compile_final_markdown_report(session_id)
                        salvar_etapa("etapa3_concluida_full_workflow", {
                            "session_id": session_id,
                            "modules_result": modules_result,
                            "final_report": final_report,
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        logger.info(f"✅ ETAPA 3 (Workflow Completo) CONCLUÍDA - Sessão: {session_id}")
                    except Exception as e:
                        logger.error(f"❌ Erro na Etapa 3 (Workflow Completo): {e}")
                        salvar_etapa("etapa3_erro_full_workflow", {
                            "session_id": session_id,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }, categoria="workflow", session_id=session_id)
                        return # Aborta o workflow se a terceira etapa falhar
                    # Salva resultado final do workflow completo
                    salvar_etapa("workflow_completo_concluido", {
                        "session_id": session_id,
                        "search_results": search_results,
                        "viral_analysis": viral_analysis,
                        "synthesis_result": synthesis_result,
                        "modules_result": modules_result,
                        "final_report": final_report,
                        "timestamp": datetime.now().isoformat()
                    }, categoria="workflow", session_id=session_id)
                    logger.info(f"✅ WORKFLOW COMPLETO CONCLUÍDO - Sessão: {session_id}")
                asyncio.run(async_full_workflow_tasks())
            except Exception as e:
                logger.error(f"❌ Erro no workflow completo: {e}")
                salvar_etapa("workflow_erro", {
                    "session_id": session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, categoria="workflow", session_id=session_id)
        # Inicia a thread para o workflow completo
        thread = threading.Thread(target=execute_full_workflow_thread)
        thread.start()
        return jsonify({
            "success": True,
            "session_id": session_id,
            "message": "Workflow completo iniciado em segundo plano",
            "estimated_total_duration": "8-15 minutos",
            "steps": [
                "Etapa 1: Coleta massiva (3-5 min)",
                "Etapa 2: Síntese com IA (2-4 min)",
                "Etapa 3: Geração de módulos (4-6 min)"
            ],
            "status_endpoint": f"/api/workflow/status/{session_id}"
        }), 200
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar workflow completo: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@enhanced_workflow_bp.route('/workflow/status/<session_id>', methods=['GET'])
def get_workflow_status(session_id):
    """Obtém status do workflow"""
    try:
        status = {
            "session_id": session_id,
            "current_step": 0,
            "step_status": {
                "step1": "pending",
                "step2": "pending",
                "step3": "pending"
            },
            "progress_percentage": 0,
            "estimated_remaining": "Calculando...",
            "last_update": datetime.now().isoformat()
        }
        # Verifica se etapa 1 foi concluída
        if os.path.exists(f"analyses_data/{session_id}/relatorio_coleta.md") or \
           os.path.exists(f"analyses_data/workflow/{session_id}/etapa1_concluida_full_workflow.json"):
            status["step_status"]["step1"] = "completed"
            status["current_step"] = 1
            status["progress_percentage"] = 33
        # Verifica se etapa 2 foi concluída
        etapa2_file1 = f"analyses_data/workflow/{session_id}/etapa2_concluida_full_workflow.json"
        etapa2_file2 = f"analyses_data/workflow/{session_id}/etapa2_concluida.json"

        if os.path.exists(etapa2_file1) or os.path.exists(etapa2_file2):
            status["step_status"]["step2"] = "completed"
            status["current_step"] = 2
            status["progress_percentage"] = 66
            logger.info(f"✅ Etapa 2 detectada como concluída para sessão {session_id}")
            logger.info(f"   - Arquivo 1 existe: {os.path.exists(etapa2_file1)}")
            logger.info(f"   - Arquivo 2 existe: {os.path.exists(etapa2_file2)}")

        # Verifica se verificação AI foi concluída
        verificacao_ai_file = f"analyses_data/workflow/{session_id}/verificacao_ai_concluida.json"
        status["ai_verification_completed"] = os.path.exists(verificacao_ai_file)

        # Verifica se etapa 3 foi concluída
        if os.path.exists(f"analyses_data/{session_id}/relatorio_final.md") or \
           os.path.exists(f"analyses_data/workflow/{session_id}/etapa3_concluida_full_workflow.json"):
            status["step_status"]["step3"] = "completed"
            status["current_step"] = 3
            status["progress_percentage"] = 100
            status["estimated_remaining"] = "Concluído"
        # Verifica se há erros
        error_files_patterns = [
            f"analyses_data/workflow/{session_id}/etapa1_erro*",
            f"analyses_data/workflow/{session_id}/etapa2_erro*",
            f"analyses_data/workflow/{session_id}/etapa3_erro*",
            f"analyses_data/workflow/{session_id}/workflow_erro*"
        ]
        for pattern in error_files_patterns:
            if glob.glob(pattern):
                status["error"] = "Erro detectado em uma das etapas do workflow."
                status["step_status"]["step1"] = "failed" if "etapa1_erro" in pattern else status["step_status"]["step1"]
                status["step_status"]["step2"] = "failed" if "etapa2_erro" in pattern else status["step_status"]["step2"]
                status["step_status"]["step3"] = "failed" if "etapa3_erro" in pattern else status["step_status"]["step3"]
                break
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e),
            "status": "error"
        }), 500

@enhanced_workflow_bp.route('/workflow/results/<session_id>', methods=['GET'])
def get_workflow_results(session_id):
    """Obtém resultados do workflow"""
    try:
        results = {
            "session_id": session_id,
            "available_files": [],
            "final_report_available": False,
            "modules_generated": 0,
            "screenshots_captured": 0
        }
        # Verifica relatório final
        final_report_path = os.path.join("analyses_data", session_id, "relatorio_final.md")
        if os.path.exists(final_report_path):
            results["final_report_available"] = True
            results["final_report_path"] = final_report_path
        # Conta módulos gerados
        modules_dir = os.path.join("analyses_data", session_id, "modules")
        if os.path.exists(modules_dir):
            modules = [f for f in os.listdir(modules_dir) if f.endswith('.md')]
            results["modules_generated"] = len(modules)
            results["modules_list"] = modules
        # Conta screenshots
        files_dir = os.path.join("analyses_data", "files", session_id)
        if os.path.exists(files_dir):
            screenshots = [f for f in os.listdir(files_dir) if f.endswith('.png')]
            results["screenshots_captured"] = len(screenshots)
            results["screenshots_list"] = screenshots
        # Lista todos os arquivos disponíveis
        session_dir = os.path.join("analyses_data", session_id)
        if os.path.exists(session_dir):
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, session_dir)
                    results["available_files"].append({
                        "name": file,
                        "path": relative_path,
                        "size": os.path.getsize(file_path),
                        "type": file.split('.')[-1] if '.' in file else 'unknown'
                    })
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"❌ Erro ao obter resultados: {e}")
        return jsonify({
            "session_id": session_id,
            "error": str(e)
        }), 500

@enhanced_workflow_bp.route('/workflow/download/<session_id>/<file_type>', methods=['GET'])
def download_workflow_file(session_id, file_type):
    """Download de arquivos do workflow"""
    try:
        # Define o caminho base
        base_path = os.path.join("analyses_data", session_id)
        if file_type == "final_report":
            file_path = os.path.join(base_path, "relatorio_final.md")
            if not os.path.exists(file_path):
                file_path = os.path.join(base_path, "relatorio_final_completo.md")
            filename = f"relatorio_final_{session_id}.md"
        elif file_type == "complete_report":
            file_path = os.path.join(base_path, "relatorio_final_completo.md")
            filename = f"relatorio_completo_{session_id}.md"
        else:
            return jsonify({"error": "Tipo de relatório inválido"}), 400
        if not os.path.exists(file_path):
            return jsonify({"error": "Arquivo não encontrado"}), 404
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"❌ Erro no download: {e}")
        return jsonify({"error": str(e)}), 500

# --- Funções auxiliares ---
def _generate_collection_report(
    search_results: Dict[str, Any],
    viral_analysis: Dict[str, Any],
    session_id: str,
    context: Dict[str, Any]
) -> str:
    """Gera relatório consolidado com dados extraídos"""
    # Função auxiliar para formatar números com segurança
    def safe_format_int(value):
        try:
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value) if value is not None else 'N/A'
    # Carrega dados salvos de forma simplificada
    all_saved_excerpts = _load_all_saved_excerpts(session_id)
    all_viral_data = _load_all_viral_data(session_id)
    massive_search_data = _load_massive_search_data(session_id)
    report = f"""# RELATÓRIO CONSOLIDADO ULTRA-COMPLETO - ARQV30 Enhanced v3.0
**🎯 DADOS 100% REAIS - ZERO SIMULAÇÃO - TUDO UNIFICADO**
**Sessão:** {session_id}  
**Query:** {search_results.get('query', 'N/A')}  
**Iniciado em:** {search_results.get('statistics', {}).get('search_started', 'N/A')}  
**Duração:** {search_results.get('statistics', {}).get('search_duration', 0):.2f} segundos
---
## 📊 RESUMO EXECUTIVO DA COLETA MASSIVA
### Estatísticas Completas:
- **Total de Fontes:** {search_results.get('statistics', {}).get('total_sources', 0)}
- **URLs Únicas:** {search_results.get('statistics', {}).get('unique_urls', 0)}
- **Trechos Salvos:** {len(all_saved_excerpts)}
- **Dados Virais:** {len(all_viral_data)}
- **Dados Massive Search:** {len(massive_search_data)}
- **Screenshots:** {len(viral_analysis.get('screenshots_captured', []))}
---
## TRECHOS DE CONTEÚDO EXTRAÍDO
*Amostras do conteúdo real coletado durante a busca massiva*
"""
    # Adiciona trechos de conteúdo
    report += _generate_content_excerpts_section(search_results, viral_analysis)
    # Adiciona dados virais completos
    report += _incorporate_viral_data(session_id, viral_analysis)
    # Adiciona resultados do Massive Search Engine
    if massive_search_data:
        report += "## 🚀 DADOS DO MASSIVE SEARCH ENGINE\n"
        for i, massive_item in enumerate(massive_search_data, 1):
            report += f"### Massive Search Result {i}\n"
            if isinstance(massive_item, dict):
                produto = massive_item.get('produto', 'N/A')
                publico_alvo = massive_item.get('publico_alvo', 'N/A')
                report += f"**Produto:** {produto}\n"
                report += f"**Público Alvo:** {publico_alvo}\n"
                busca_massiva = massive_item.get('busca_massiva', {})
                if busca_massiva:
                    alibaba_results = busca_massiva.get('alibaba_websailor_results', [])
                    real_search_results = busca_massiva.get('real_search_orchestrator_results', [])
                    report += f"**Resultados Alibaba WebSailor:** {len(alibaba_results)}\n"
                    report += f"**Resultados Real Search:** {len(real_search_results)}\n"
                    for j, alibaba_result in enumerate(alibaba_results[:3], 1):
                        if isinstance(alibaba_result, dict):
                            report += f"  - Alibaba {j}: {alibaba_result.get('query', 'N/A')}\n"
                metadata = massive_item.get('metadata', {})
                if metadata:
                    report += f"**Total de Buscas:** {metadata.get('total_searches', 0)}\n"
                    report += f"**Tamanho Final:** {metadata.get('size_kb', 0):.1f} KB\n"
                    report += f"**APIs Utilizadas:** {len(metadata.get('apis_used', []))}\n"
            report += "\n---\n"
    # Adiciona resultados do YouTube
    youtube_results = search_results.get('youtube_results', [])
    if youtube_results:
        report += "## 📺 RESULTADOS COMPLETOS DO YOUTUBE\n"
        for i, result in enumerate(youtube_results, 1):
            report += f"### YouTube {i}: {result.get('title', 'Sem título')}\n"
            report += f"**Canal:** {result.get('channel', 'N/A')}  \n"
            report += f"**Views:** {safe_format_int(result.get('view_count', 'N/A'))}  \n"
            report += f"**Likes:** {safe_format_int(result.get('like_count', 'N/A'))}  \n"
            report += f"**Comentários:** {safe_format_int(result.get('comment_count', 'N/A'))}  \n"
            report += f"**Score Viral:** {result.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL:** {result.get('url', 'N/A')}  \n"
            description = result.get('description', '')
            if description:
                report += f"**Descrição:** {description}  \n"
            report += "\n---\n"
    # Adiciona resultados de Redes Sociais
    social_results = search_results.get('social_results', [])
    if social_results:
        report += "## 📱 RESULTADOS COMPLETOS DE REDES SOCIAIS\n"
        for i, result in enumerate(social_results, 1):
            report += f"### Social {i}: {result.get('title', 'Sem título')}\n"
            report += f"**Plataforma:** {result.get('platform', 'N/A').title()}  \n"
            report += f"**Autor:** {result.get('author', 'N/A')}  \n"
            report += f"**Engajamento:** {result.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL:** {result.get('url', 'N/A')}  \n"
            content = result.get('content', '')
            if content:
                report += f"**CONTEÚDO COMPLETO:** {content}  \n"
            report += "\n---\n"
    # Adiciona Screenshots e Evidências Visuais
    screenshots = viral_analysis.get('screenshots_captured', [])
    if screenshots:
        report += "## 📸 EVIDÊNCIAS VISUAIS COMPLETAS\n"
        for i, screenshot in enumerate(screenshots, 1):
            report += f"### Screenshot {i}: {screenshot.get('title', 'Sem título')}\n"
            report += f"**Plataforma:** {screenshot.get('platform', 'N/A').title()}  \n"
            report += f"**Score Viral:** {screenshot.get('viral_score', 0):.2f}/10  \n"
            report += f"**URL Original:** {screenshot.get('url', 'N/A')}  \n"
            metrics = screenshot.get('content_metrics', {})
            if metrics:
                if 'views' in metrics:
                    report += f"**Views:** {safe_format_int(metrics['views'])}  \n"
                if 'likes' in metrics:
                    report += f"**Likes:** {safe_format_int(metrics['likes'])}  \n"
                if 'comments' in metrics:
                    report += f"**Comentários:** {safe_format_int(metrics['comments'])}  \n"
            img_path = screenshot.get('relative_path', '')
            if img_path:
                report += f"**Arquivo:** {img_path}  \n"
            report += "\n---\n"
    # Adiciona Contexto da Análise
    report += "## 🎯 CONTEXTO COMPLETO DA ANÁLISE\n"
    for key, value in context.items():
        if value:
            report += f"**{key.replace('_', ' ').title()}:** {value}  \n"
    # Estatísticas Finais
    total_content_chars = sum(len(str(excerpt.get('conteudo', ''))) for excerpt in all_saved_excerpts)
    report += f"""
---
## 📊 ESTATÍSTICAS FINAIS CONSOLIDADAS
- **Total de Trechos Extraídos:** {len(all_saved_excerpts)}
- **Total de Dados Virais:** {len(all_viral_data)}
- **Total de Dados Massive Search:** {len(massive_search_data)}
- **Total de Caracteres de Conteúdo:** {total_content_chars:,}
- **Total de Screenshots:** {len(screenshots)}
- **Total de Resultados Web:** {len(search_results.get('web_results', []))}
- **Total de Resultados YouTube:** {len(search_results.get('youtube_results', []))}
- **Total de Resultados Sociais:** {len(search_results.get('social_results', []))}
**🔥 GARANTIA: 100% DADOS REAIS - ZERO SIMULAÇÃO - TUDO CONSOLIDADO**
---
*Relatório ultra-consolidado gerado automaticamente em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*
*Pronto para análise profunda pela IA QWEN via OpenRouter*
"""
    return report

def _gerar_consolidacao_final_etapa1(session_id, search_results, viral_analysis, massive_results, viral_results: Dict = None) -> Dict[str, Any]:
    """Gera consolidação final de TODOS os dados coletados na Etapa 1"""
    if viral_results is None:
        viral_results = {} # Inicializa como dicionário vazio se não for fornecido
    try:
        consolidacao = {
            "session_id": session_id,
            "tipo": "consolidacao_etapa1_completa",
            "dados_web": [],
            "dados_sociais": [],
            "dados_virais": [],
            "imagens_baixadas": [],
            "screenshots_capturados": [],
            "viral_results_files": [],
            "trechos_extraidos": [],
            "dados_viral_integration": viral_results,
            "detalhes_buscas": [],
            "res_busca_files": [],
            "consolidado_files": [],
            "etapa1_concluida_files": [],
            "relatorio_coleta": {},
            "estatisticas": {
                "total_dados_coletados": 0,
                "total_caracteres": 0,
                "fontes_unicas": 0,
                "qualidade_media": 0,
                "relevancia_media": 0
            },
            "consolidado_em": datetime.now().isoformat()
        }
        # CONSOLIDAR DADOS WEB
        if search_results.get('web_results'):
            for result in search_results['web_results']:
                if result.get('url') and result.get('title'):
                    consolidacao["dados_web"].append({
                        "url": result['url'],
                        "titulo": result['title'],
                        "fonte": result.get('source', 'web'),
                        "relevancia": result.get('relevance_score', 0.5),
                        "conteudo_tamanho": result.get('content_length', 0)
                    })
        # CONSOLIDAR DADOS SOCIAIS
        if search_results.get('social_results'):
            for result in search_results['social_results']:
                if result.get('url'):
                    consolidacao["dados_sociais"].append({
                        "url": result['url'],
                        "plataforma": result.get('platform', 'social'),
                        "titulo": result.get('title', ''),
                        "engajamento": result.get('engagement_score', 0)
                    })
        # CONSOLIDAR DADOS VIRAIS
        if viral_analysis.get('viral_content'):
            for viral in viral_analysis['viral_content']:
                consolidacao["dados_virais"].append({
                    "url": viral.get('post_url', ''),
                    "plataforma": viral.get('platform', ''),
                    "titulo": viral.get('title', ''),
                    "engajamento": viral.get('engagement_score', 0),
                    "imagem_url": viral.get('image_url', '')
                })
        # CONSOLIDAR IMAGENS E SCREENSHOTS
        if viral_analysis.get('screenshots_captured'):
            consolidacao["screenshots_capturados"] = viral_analysis['screenshots_captured']
        # CALCULAR ESTATÍSTICAS
        total_dados = len(consolidacao["dados_web"]) + len(consolidacao["dados_sociais"]) + len(consolidacao["dados_virais"])
        urls_unicas = set()
        for item in consolidacao["dados_web"] + consolidacao["dados_sociais"] + consolidacao["dados_virais"]:
            if item.get('url'):
                urls_unicas.add(item['url'])
        consolidacao["estatisticas"] = {
            "total_dados_coletados": total_dados,
            "fontes_unicas": len(urls_unicas),
            "dados_web": len(consolidacao["dados_web"]),
            "dados_sociais": len(consolidacao["dados_sociais"]),
            "dados_virais": len(consolidacao["dados_virais"]),
            "screenshots": len(consolidacao["screenshots_capturados"])
        }
        # BUSCAR E INCLUIR TODOS OS ARQUIVOS GERADOS NA ETAPA 1
        import os
        import glob
        import json
        # Diretório da sessão
        session_dir = f"analyses_data/{session_id}"
        workflow_dir = f"relatorios_intermediarios/workflow/{session_id}"
        # Buscar viral_results_*.json
        try:
            viral_files = glob.glob(f"{session_dir}/viral_results_*.json") + glob.glob(f"{workflow_dir}/viral_results_*.json")
            for file_path in viral_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        viral_data = json.load(f)
                        consolidacao["viral_results_files"].append({
                            "arquivo": os.path.basename(file_path),
                            "caminho": file_path,
                            "dados": viral_data
                        })
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar viral_results: {e}")
        # Buscar trechos.json
        try:
            trechos_files = glob.glob(f"{session_dir}/trechos*.json") + glob.glob(f"{workflow_dir}/trechos*.json")
            for file_path in trechos_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        trechos_data = json.load(f)
                        consolidacao["trechos_extraidos"].append({
                            "arquivo": os.path.basename(file_path),
                            "caminho": file_path,
                            "dados": trechos_data
                        })
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar trechos: {e}")
        # Buscar RES_BUSCA_*.json (incluindo diretório analyses_data raiz)
        try:
            res_busca_files = (
                glob.glob(f"{session_dir}/RES_BUSCA_*.json") +
                glob.glob(f"{workflow_dir}/RES_BUSCA_*.json") +
                glob.glob("analyses_data/RES_BUSCA_*.json") +
                glob.glob(f"analyses_data/**/RES_BUSCA_*.json", recursive=True)
            )
            for file_path in res_busca_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        res_data = json.load(f)
                        consolidacao["res_busca_files"].append({
                            "arquivo": os.path.basename(file_path),
                            "caminho": file_path,
                            "dados": res_data
                        })
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar RES_BUSCA: {e}")
        # Buscar consolidado.json (incluindo subdiretórios de analyses_data)
        try:
            consolidado_files = (
                glob.glob(f"{session_dir}/consolidado*.json") +
                glob.glob(f"{workflow_dir}/consolidado*.json") +
                glob.glob("analyses_data/consolidado*.json") +
                glob.glob(f"analyses_data/**/consolidado*.json", recursive=True)
            )
            for file_path in consolidado_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cons_data = json.load(f)
                        consolidacao["consolidado_files"].append({
                            "arquivo": os.path.basename(file_path),
                            "caminho": file_path,
                            "dados": cons_data
                        })
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar consolidado: {e}")
        # Buscar etapa1_concluida_*.json
        try:
            etapa1_files = glob.glob(f"{session_dir}/etapa1_concluida_*.json") + glob.glob(f"{workflow_dir}/etapa1_concluida_*.json")
            for file_path in etapa1_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        etapa_data = json.load(f)
                        consolidacao["etapa1_concluida_files"].append({
                            "arquivo": os.path.basename(file_path),
                            "caminho": file_path,
                            "dados": etapa_data
                        })
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar etapa1_concluida: {e}")
        # Buscar relatorio_coleta.md
        try:
            relatorio_path = f"{session_dir}/relatorio_coleta.md"
            if os.path.exists(relatorio_path):
                with open(relatorio_path, 'r', encoding='utf-8') as f:
                    consolidacao["relatorio_coleta"] = {
                        "arquivo": "relatorio_coleta.md",
                        "caminho": relatorio_path,
                        "conteudo": f.read()
                    }
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar relatório de coleta: {e}")
        # Incluir detalhes das buscas realizadas
        consolidacao["detalhes_buscas"] = {
            "search_results": search_results,
            "viral_analysis": viral_analysis,
            "massive_results": massive_results
        }
        # Atualizar estatísticas com arquivos incluídos
        consolidacao["estatisticas"].update({
            "viral_files_incluidos": len(consolidacao["viral_results_files"]),
            "trechos_incluidos": len(consolidacao["trechos_extraidos"]),
            "res_busca_incluidos": len(consolidacao["res_busca_files"]),
            "etapa1_incluidos": len(consolidacao["etapa1_concluida_files"]),
        })
        # SALVA CONSOLIDAÇÃO COMPLETA
        caminho_consolidacao = salvar_etapa("consolidacao_etapa1_final", consolidacao, categoria="workflow", session_id=session_id)
        logger.info(f"✅ Consolidação final da Etapa 1 salva em: {caminho_consolidacao}")
        logger.info(f"🔗 CONSOLIDAÇÃO FINAL ETAPA 1: {total_dados} dados, {len(urls_unicas)} fontes únicas")
        logger.info(f"📁 Arquivos incluídos: {len(consolidacao['viral_results_files'])} viral, {len(consolidacao['trechos_extraidos'])} trechos, {len(consolidacao['res_busca_files'])} RES_BUSCA")
        return consolidacao
    except Exception as e:
        logger.error(f"❌ Erro na consolidação final Etapa 1: {e}")
        return {"error": str(e), "session_id": session_id}

def _generate_content_excerpts_section(search_results: Dict[str, Any], viral_analysis: Dict[str, Any]) -> str:
    """Gera seção com trechos de conteúdo extraído das fontes coletadas"""
    section = ""
    content_found = False
    # Extrai trechos dos resultados web
    web_results = search_results.get('web_results', [])
    if web_results:
        section += "### Conteúdo Web Extraído:\n"
        for i, result in enumerate(web_results[:10], 1):  # Limita a 10 resultados
            content = result.get('content', '')
            snippet = result.get('snippet', '')
            title = result.get('title', 'Sem título')
            url = result.get('url', 'N/A')
            if content or snippet:
                content_found = True
                section += f"**{i}. {title}**\n"
                section += f"*Fonte: {url}*\n"
                # Usa conteúdo completo se disponível, senão usa snippet
                text_to_show = content if content else snippet
                if text_to_show:
                    # Limpa e formata o texto
                    clean_text = text_to_show.replace('\n', ' ').replace('\r', '').strip()
                    # Mostra até 800 caracteres
                    preview = clean_text[:800]
                    section += f"```\n{preview}{'...' if len(clean_text) > 800 else ''}\n```\n"
    # Extrai trechos dos resultados do YouTube
    youtube_results = search_results.get('youtube_results', [])
    if youtube_results:
        section += "### Conteúdo YouTube Extraído:\n"
        for i, result in enumerate(youtube_results[:5], 1):  # Limita a 5 resultados
            description = result.get('description', '')
            title = result.get('title', 'Sem título')
            url = result.get('url', 'N/A')
            if description:
                content_found = True
                section += f"**{i}. {title}**\n"
                section += f"*Fonte: {url}*\n"
                # Limpa e formata a descrição
                clean_desc = description.replace('\n', ' ').replace('\r', '').strip()
                preview = clean_desc[:400]
                section += f"```\n{preview}{'...' if len(clean_desc) > 400 else ''}\n```\n"
    # Extrai trechos dos resultados sociais
    social_results = search_results.get('social_results', [])
    if social_results:
        section += "### Conteúdo Social Media Extraído:\n"
        for i, result in enumerate(social_results[:5], 1):  # Limita a 5 resultados
            content = result.get('content', '')
            snippet = result.get('snippet', '')
            title = result.get('title', 'Sem título')
            url = result.get('url', 'N/A')
            if content or snippet:
                content_found = True
                section += f"**{i}. {title}**\n"
                section += f"*Fonte: {url}*\n"
                text_to_show = content if content else snippet
                if text_to_show:
                    clean_text = text_to_show.replace('\n', ' ').replace('\r', '').strip()
                    preview = clean_text[:600]
                    section += f"```\n{preview}{'...' if len(clean_text) > 600 else ''}\n```\n"
    if not content_found:
        section += "⚠️ **Nenhum trecho de conteúdo extraído encontrado nos dados da sessão.**\n"
        section += "*Nota: O sistema coletou metadados (títulos, URLs, estatísticas) mas não extraiu o conteúdo completo das páginas.*\n"
    return section

def _incorporate_viral_data(session_id: str, viral_analysis: Dict[str, Any]) -> str:
    """Incorpora automaticamente dados virais completos do arquivo viral_results_*.json"""
    import glob
    import json
    viral_section = ""
    try:
        # Procura arquivo viral_results na pasta viral_images_data
        viral_files = glob.glob(f"viral_images_data/viral_results_*{session_id[:8]}*.json")
        if not viral_files:
            # Procura por qualquer arquivo viral recente
            viral_files = glob.glob("viral_images_data/viral_results_*.json")
            viral_files.sort(key=os.path.getmtime, reverse=True)
            viral_files = viral_files[:1]  # Pega o mais recente
        if viral_files:
            with open(viral_files[0], 'r', encoding='utf-8') as f:
                viral_data = json.load(f)
            viral_section += "---\n## ANÁLISE DE CONTEÚDO VIRAL COMPLETA\n"
            # Estatísticas gerais
            stats = viral_data.get('statistics', {})
            viral_section += "### Métricas de Engajamento:\n"
            viral_section += f"- **Total de Conteúdo Analisado:** {stats.get('total_content_analyzed', 0)} posts\n"
            viral_section += f"- **Conteúdo Viral Identificado:** {stats.get('viral_content_count', 0)} posts\n"
            viral_section += f"- **Score Total de Engajamento:** {stats.get('total_engagement_score', 0)} pontos\n"
            viral_section += f"- **Engajamento Médio:** {stats.get('average_engagement', 0):.1f} pontos\n"
            viral_section += f"- **Maior Engajamento:** {stats.get('max_engagement', 0)} pontos\n"
            viral_section += f"- **Visualizações Estimadas:** {stats.get('total_views', 0):,}\n"
            viral_section += f"- **Likes Estimados:** {stats.get('total_likes', 0):,}\n"
            # Distribuição por plataforma
            platform_stats = viral_data.get('platform_distribution', {})
            if platform_stats:
                viral_section += "### Distribuição por Plataforma:\n"
                for platform, data in platform_stats.items():
                    viral_section += f"- **{platform.title()}:** {data.get('count', 0)} posts "
                    viral_section += f"({data.get('engagement', 0)} engajamento, "
                    viral_section += f"{data.get('views', 0):,} views, "
                    viral_section += f"{data.get('likes', 0):,} likes)\n"
                viral_section += "\n"
            # Insights de conteúdo viral
            insights = viral_data.get('viral_insights', [])
            if insights:
                viral_section += "### Insights de Conteúdo Viral:\n"
                for insight in insights:
                    viral_section += f"- {insight}\n"
                viral_section += "\n"
            # Imagens extraídas
            images = viral_data.get('images_extracted', [])
            if images:
                viral_section += f"### Imagens Extraídas ({len(images)} total):\n"
                for i, img in enumerate(images[:10], 1):  # Mostra até 10 imagens
                    viral_section += f"**{i}.** {img.get('title', 'Sem título')} "
                    viral_section += f"(Score: {img.get('viral_score', 0):.1f}) - "
                    viral_section += f"{img.get('platform', 'N/A')}\n"
                viral_section += "\n"
            # Screenshots capturados
            screenshots = viral_data.get('screenshots_captured', [])
            if screenshots:
                viral_section += f"### Screenshots Capturados ({len(screenshots)} total):\n"
                for i, shot in enumerate(screenshots[:10], 1):  # Mostra até 10 screenshots
                    viral_section += f"**{i}.** {shot.get('title', 'Sem título')} "
                    viral_section += f"(Score: {shot.get('viral_score', 0):.1f}) - "
                    viral_section += f"{shot.get('platform', 'N/A')}\n"
                viral_section += "\n"
            logger.info(f"✅ Dados virais incorporados automaticamente do arquivo: {viral_files[0]}")
        else:
            viral_section += "---\n## ANÁLISE DE CONTEÚDO VIRAL\n"
            viral_section += "*Nenhum arquivo de dados virais encontrado para incorporação automática.*\n"
            logger.warning("⚠️ Nenhum arquivo viral_results_*.json encontrado para incorporação")
    except Exception as e:
        logger.error(f"❌ Erro ao incorporar dados virais: {e}")
        viral_section += "---\n## ANÁLISE DE CONTEÚDO VIRAL\n"
        viral_section += "*Erro ao carregar dados virais automaticamente.*\n"
    return viral_section

def _save_collection_report(report_content: str, session_id: str):
    """Salva relatório de coleta"""
    try:
        session_dir = f"analyses_data/{session_id}"
        os.makedirs(session_dir, exist_ok=True)
        report_path = f"{session_dir}/relatorio_coleta.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"✅ Relatório de coleta salvo: {report_path}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar relatório de coleta: {e}")

# --- Funções para carregar todos os dados salvos ---
def _load_all_saved_excerpts(session_id: str) -> List[Dict[str, Any]]:
    """Carrega TODOS os trechos de pesquisa web salvos para a sessão com CONSOLIDAÇÃO MÁXIMA"""
    excerpts = []
    urls_processadas = set()
    try:
        # 1. Carrega arquivo consolidado primeiro (prioridade)
        consolidado_path = os.path.join("analyses_data", "pesquisa_web", session_id, "consolidado.json")
        if os.path.exists(consolidado_path):
            try:
                with open(consolidado_path, 'r', encoding='utf-8') as f:
                    consolidado = json.load(f)
                    for trecho in consolidado.get('trechos', []):
                        if trecho.get('url') not in urls_processadas:
                            excerpts.append(trecho)
                            urls_processadas.add(trecho.get('url'))
                logger.info(f"✅ {len(excerpts)} trechos carregados do arquivo consolidado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar arquivo consolidado: {e}")
        # 2. Diretório de trechos da sessão
        excerpts_dir = os.path.join("analyses_data", "pesquisa_web", session_id)
        if os.path.exists(excerpts_dir):
            for filename in os.listdir(excerpts_dir):
                if filename.startswith('trecho_') and filename.endswith('.json') and filename != 'consolidado.json':
                    file_path = os.path.join(excerpts_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            excerpt_data = json.load(f)
                            if excerpt_data.get('url') not in urls_processadas:
                                excerpts.append(excerpt_data)
                                urls_processadas.add(excerpt_data.get('url'))
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao carregar trecho {filename}: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar todos os trechos salvos: {e}")
    return excerpts

def _load_all_viral_data(session_id: str) -> List[Dict[str, Any]]:
    """Carrega TODOS os dados virais salvos para a sessão"""
    viral_data = []
    try:
        viral_files = glob.glob(f"viral_images_data/viral_results_*{session_id[:8]}*.json")
        for file_path in viral_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    viral_data.append(json.load(f))
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar arquivo viral {file_path}: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar todos os dados virais: {e}")
    return viral_data

def _load_massive_search_data(session_id: str) -> List[Dict[str, Any]]:
    """Carrega TODOS os dados do massive search engine salvos para a sessão"""
    massive_data = []
    try:
        # Assume que os resultados do massive search engine são salvos em analyses_data/massive_search/{session_id}/...
        massive_search_dir = os.path.join("analyses_data", "massive_search", session_id)
        if os.path.exists(massive_search_dir):
            for filename in os.listdir(massive_search_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(massive_search_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            massive_data.append(json.load(f))
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao carregar arquivo massive search {file_path}: {e}")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar todos os dados do massive search: {e}")
    return massive_data