#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes para gerenciamento de sessões persistidas
APENAS SALVAMENTO LOCAL DE ARQUIVOS
"""

from flask import Blueprint, request, jsonify
import logging
from typing import Dict, Any

from services.session_persistence import session_persistence
from services.openrouter_models import openrouter_models

logger = logging.getLogger(__name__)

sessions_bp = Blueprint('sessions', __name__)

@sessions_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """Lista todas as sessões salvas localmente"""
    print("🔍 PRINT DEBUG: Entrando na função list_sessions")
    logger.info("🔍 LOG DEBUG: Entrando na função list_sessions")
    
    # Teste direto do session_persistence
    from services.session_persistence import SessionPersistenceManager
    test_manager = SessionPersistenceManager()
    test_sessions = test_manager.get_sessions()
    print(f"🔍 PRINT DEBUG: test_manager sessions: {len(test_sessions)}")
    
    try:
        status_filter = request.args.get('status')
        
        # Debug: verificar se session_persistence está funcionando
        print(f"🔍 PRINT DEBUG: session_persistence type: {type(session_persistence)}")
        print(f"🔍 PRINT DEBUG: sessions_dir: {session_persistence.sessions_dir}")
        logger.info(f"🔍 DEBUG: session_persistence type: {type(session_persistence)}")
        logger.info(f"🔍 DEBUG: sessions_dir: {session_persistence.sessions_dir}")
        
        sessions = session_persistence.get_sessions(status=status_filter)
        
        print(f"🔍 PRINT DEBUG: sessions returned: {len(sessions)}")
        logger.info(f"📋 Listando {len(sessions)} sessões para o frontend")
        logger.info(f"🔍 DEBUG: sessions data: {sessions}")
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        })
        
    except Exception as e:
        print(f"❌ PRINT ERROR: {e}")
        logger.error(f"❌ Erro ao listar sessões: {e}")
        import traceback
        print(f"❌ PRINT TRACEBACK: {traceback.format_exc()}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'sessions': []
        }), 200  # Retorna 200 com lista vazia em caso de erro

@sessions_bp.route('/sessions/save', methods=['POST'])
def save_session():
    """Salva uma sessão localmente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        # Gera session_id se não fornecido
        session_id = data.get('session_id')
        if not session_id:
            import uuid
            import time
            session_id = f"session_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        name = data.get('name', f'Análise {session_id[:8]}')
        segmento = data.get('segmento', '')
        
        if not segmento:
            return jsonify({
                'success': False,
                'error': 'Segmento é obrigatório'
            }), 400
        
        # Constrói query se não fornecida
        query = data.get('query', '')
        if not query:
            produto = data.get('produto', '')
            query_parts = [segmento]
            if produto:
                query_parts.append(produto)
            query_parts.extend(["Brasil", "2024", "mercado"])
            query = " ".join(query_parts)
        
        openrouter_model = data.get('openrouter_model', 'anthropic/claude-3-haiku:beta')
        
        result = session_persistence.save_session(
            session_id=session_id,
            name=name,
            query=query,
            segmento=segmento,
            openrouter_model=openrouter_model
        )
        
        if result['success']:
            logger.info(f"💾 Sessão salva: {name}")
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ Erro ao salvar sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/sessions/<session_id>/pause', methods=['POST'])
def pause_session(session_id: str):
    """Pausa uma sessão ativa"""
    try:
        result = session_persistence.pause_session(session_id)
        
        if result['success']:
            logger.info(f"⏸️ Sessão pausada: {session_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao pausar sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/sessions/<session_id>/continue', methods=['POST'])
def continue_session(session_id: str):
    """Continua uma sessão pausada"""
    try:
        result = session_persistence.continue_session(session_id)
        
        if result['success']:
            logger.info(f"▶️ Sessão continuada: {session_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao continuar sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/sessions/<session_id>/rename', methods=['POST'])
def rename_session(session_id: str):
    """Renomeia uma sessão"""
    try:
        data = request.get_json()
        new_name = data.get('name')
        
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'Nome é obrigatório'
            }), 400
        
        result = session_persistence.rename_session(session_id, new_name)
        
        if result['success']:
            logger.info(f"✏️ Sessão renomeada: {session_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao renomear sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/sessions/<session_id>/delete', methods=['DELETE'])
def delete_session(session_id: str):
    """Remove uma sessão"""
    try:
        result = session_persistence.delete_session(session_id)
        
        if result['success']:
            logger.info(f"🗑️ Sessão removida: {session_id}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao remover sessão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/sessions/<session_id>/model', methods=['POST'])
def update_session_model(session_id: str):
    """Atualiza o modelo OpenRouter de uma sessão"""
    try:
        data = request.get_json()
        model = data.get('model')
        
        if not model:
            return jsonify({
                'success': False,
                'error': 'Modelo é obrigatório'
            }), 400
        
        # Aceita qualquer modelo informado (campo livre)
        # Validação removida para permitir flexibilidade total
        
        result = session_persistence.update_openrouter_model(session_id, model)
        
        if result['success']:
            logger.info(f"🤖 Modelo atualizado: {session_id} -> {model}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar modelo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sessions_bp.route('/openrouter-models', methods=['GET'])
def get_openrouter_models():
    """Lista modelos OpenRouter disponíveis (LOCAL)"""
    try:
        models = openrouter_models.get_available_models()
        
        return jsonify({
            'success': True,
            'models': models,
            'total': len(models)
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar modelos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500