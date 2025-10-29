#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - External AI Verifier Integration
Integração do módulo External AI Verifier ao app principal
"""

import os
import sys
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ExternalAIVerifierIntegration:
    """Integração do External AI Verifier com o app principal"""

    def __init__(self):
        """Inicializa a integração"""
        # Adiciona o caminho do módulo externo ao Python path
        external_module_path = os.path.join(os.getcwd(), "external_ai_verifier", "src")
        if external_module_path not in sys.path:
            sys.path.insert(0, external_module_path)

        self.module_available = self._check_module_availability()

        if self.module_available:
            logger.info("✅ External AI Verifier integrado com sucesso")
        else:
            logger.warning("⚠️ External AI Verifier não disponível - executando em modo fallback")

    def _check_module_availability(self) -> bool:
        """Verifica se o módulo External AI Verifier está disponível"""
        try:
            from external_review_agent import ExternalReviewAgent
            return True
        except ImportError as e:
            logger.warning(f"External AI Verifier não encontrado: {e}")
            return False

    async def verify_session_data(self, session_id: str) -> Dict[str, Any]:
        """
        Executa verificação dos dados de uma sessão específica

        Args:
            session_id (str): ID da sessão para verificar

        Returns:
            Dict[str, Any]: Resultado da verificação
        """
        try:
            if not self.module_available:
                return self._fallback_verification_result(session_id)

            logger.info(f"🔍 Iniciando verificação AI para sessão: {session_id}")

            # Importa o agente de verificação com caminho correto
            import sys
            import os
            external_path = os.path.join(os.getcwd(), "external_ai_verifier", "src")
            if external_path not in sys.path:
                sys.path.insert(0, external_path)

            from external_review_agent import ExternalReviewAgent

            # Cria instância do agente
            agent = ExternalReviewAgent()

            # Executa análise da sessão
            result = await agent.analyze_session_consolidacao(session_id)

            if result.get('success', False):
                logger.info(f"✅ Verificação AI concluída para sessão {session_id}")
                logger.info(f"📊 Items processados: {result.get('total_items', 0)}")
                logger.info(f"✅ Aprovados: {result.get('statistics', {}).get('approved_count', 0)}")
                logger.info(f"❌ Rejeitados: {result.get('statistics', {}).get('rejected_count', 0)}")
            else:
                logger.error(f"❌ Falha na verificação AI: {result.get('error', 'Erro desconhecido')}")

            return result

        except Exception as e:
            logger.error(f"❌ Erro durante verificação AI: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'fallback_used': True
            }

    async def verify_batch_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa verificação de um lote de dados

        Args:
            input_data (Dict[str, Any]): Dados para verificação

        Returns:
            Dict[str, Any]: Resultado da verificação
        """
        try:
            if not self.module_available:
                return self._fallback_batch_result(input_data)

            logger.info(f"🔍 Iniciando verificação AI em lote: {len(input_data.get('items', []))} itens")

            # Importa o agente de verificação com caminho correto
            import sys
            import os
            external_path = os.path.join(os.getcwd(), "external_ai_verifier", "src")
            if external_path not in sys.path:
                sys.path.insert(0, external_path)

            from external_review_agent import ExternalReviewAgent

            # Cria instância do agente
            agent = ExternalReviewAgent()

            # Executa análise em lote
            result = await agent.analyze_content_batch(input_data)

            if result.get('success', False):
                logger.info(f"✅ Verificação AI em lote concluída")
                logger.info(f"📊 Items processados: {result.get('total_items', 0)}")
                stats = result.get('statistics', {})
                logger.info(f"✅ Aprovados: {stats.get('approved_count', 0)}")
                logger.info(f"❌ Rejeitados: {stats.get('rejected_count', 0)}")
            else:
                logger.error(f"❌ Falha na verificação AI em lote")

            return result

        except Exception as e:
            logger.error(f"❌ Erro durante verificação AI em lote: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'fallback_used': True
            }

    def _fallback_verification_result(self, session_id: str) -> Dict[str, Any]:
        """Resultado fallback quando o módulo não está disponível"""
        return {
            'success': True,
            'session_id': session_id,
            'total_items': 0,
            'statistics': {
                'approved_count': 0,
                'rejected_count': 0,
                'flagged_count': 0,
                'average_confidence': 0.0
            },
            'items': [],
            'rejected_items': [],
            'metadata': {
                'fallback_mode': True,
                'message': 'External AI Verifier não disponível - modo fallback ativo',
                'timestamp': datetime.now().isoformat()
            },
            'fallback_used': True
        }

    def _fallback_batch_result(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resultado fallback para verificação em lote"""
        items_count = len(input_data.get('items', []))
        return {
            'success': True,
            'total_items': items_count,
            'statistics': {
                'approved_count': items_count,  # Aprova todos em modo fallback
                'rejected_count': 0,
                'flagged_count': 0,
                'average_confidence': 1.0
            },
            'items': input_data.get('items', []),
            'rejected_items': [],
            'metadata': {
                'fallback_mode': True,
                'message': 'External AI Verifier não disponível - todos os itens aprovados por fallback',
                'timestamp': datetime.now().isoformat()
            },
            'fallback_used': True
        }

    def get_status(self) -> Dict[str, Any]:
        """Retorna status da integração"""
        return {
            'module_available': self.module_available,
            'integration_active': True,
            'timestamp': datetime.now().isoformat()
        }

# Instância global
external_ai_integration = ExternalAIVerifierIntegration()