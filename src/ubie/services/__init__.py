#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo Services - Serviços de infraestrutura do UBIE
"""

from .internal_proxy import (
    get_requests_session,
    get_aiohttp_session, 
    get_playwright_proxy_config
)

__all__ = [
    'get_requests_session',
    'get_aiohttp_session',
    'get_playwright_proxy_config'
]