#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UBIE - Agente IA ARQ-Mestre v6.0
Módulo Paralelo - Dados Locais com Processamento via Gemini Cloud

⚠️ AVISO DE PRIVACIDADE:
Este módulo utiliza a API do Google Gemini para processamento de linguagem natural.
Dados enviados para processamento passam pela nuvem da Google.
NÃO use com informações confidenciais ou sensíveis.

Todos os dados de análise permanecem armazenados localmente.
"""

__version__ = "6.0"
__author__ = "ARQ-Mestre Agent System"

# Módulos principais
from .agent import session_state_manager, agent_tools
# from .services import internal_proxy  # Não implementado ainda

__all__ = [
    'session_state_manager',
    'agent_tools'
]