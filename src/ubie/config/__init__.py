#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo Config - Configurações do Agente ARQ-Mestre
"""

import os
from pathlib import Path

# Configurações base
UBIE_BASE_DIR = Path(__file__).parent.parent
SYSTEM_PROMPT_FILE = UBIE_BASE_DIR / 'config' / 'system_prompt.txt'
ANALYSES_BASE_DIR = os.getenv('ANALYSES_BASE_DIR', 'analyses_data')

__all__ = [
    'UBIE_BASE_DIR',
    'SYSTEM_PROMPT_FILE', 
    'ANALYSES_BASE_DIR'
]