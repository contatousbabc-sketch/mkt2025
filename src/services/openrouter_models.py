#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço de Modelos OpenRouter
Lista de modelos disponíveis (mantém APIs externas nas análises)
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class OpenRouterModelsService:
    """Serviço para listar modelos OpenRouter disponíveis"""
    
    def __init__(self):
        """Inicializa o serviço de modelos"""
        logger.info("🤖 OpenRouter Models Service inicializado")
    
    def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retorna modelos OpenRouter disponíveis localmente"""
        logger.info("📋 Retornando modelos OpenRouter locais")
        return self._get_local_models()
    
    def _get_local_models(self) -> List[Dict[str, Any]]:
        """Retorna lista completa de modelos OpenRouter armazenados localmente"""
        return [
            # Anthropic Claude Models
            {
                'id': 'anthropic/claude-3-haiku:beta',
                'name': 'Claude 3 Haiku',
                'description': 'Modelo rápido e eficiente para análises',
                'context_length': 200000,
                'provider': 'anthropic',
                'pricing': {'prompt': '0.25', 'completion': '1.25'},
                'recommended': True
            },
            {
                'id': 'anthropic/claude-3-sonnet:beta',
                'name': 'Claude 3 Sonnet', 
                'description': 'Modelo balanceado para análises detalhadas',
                'context_length': 200000,
                'provider': 'anthropic',
                'pricing': {'prompt': '3', 'completion': '15'},
                'recommended': True
            },
            {
                'id': 'anthropic/claude-3.5-sonnet:beta',
                'name': 'Claude 3.5 Sonnet',
                'description': 'Modelo mais avançado para análises complexas',
                'context_length': 200000,
                'provider': 'anthropic',
                'pricing': {'prompt': '3', 'completion': '15'},
                'recommended': True
            },
            {
                'id': 'anthropic/claude-3-opus:beta',
                'name': 'Claude 3 Opus',
                'description': 'Modelo premium com máxima qualidade',
                'context_length': 200000,
                'provider': 'anthropic',
                'pricing': {'prompt': '15', 'completion': '75'}
            },
            
            # OpenAI Models
            {
                'id': 'openai/gpt-4o',
                'name': 'GPT-4o',
                'description': 'Modelo multimodal da OpenAI',
                'context_length': 128000,
                'provider': 'openai',
                'pricing': {'prompt': '5', 'completion': '15'},
                'recommended': True
            },
            {
                'id': 'openai/gpt-4o-mini',
                'name': 'GPT-4o Mini',
                'description': 'Versão mais rápida e econômica do GPT-4o',
                'context_length': 128000,
                'provider': 'openai',
                'pricing': {'prompt': '0.15', 'completion': '0.6'},
                'recommended': True
            },
            {
                'id': 'openai/gpt-4-turbo',
                'name': 'GPT-4 Turbo',
                'description': 'Modelo GPT-4 otimizado para velocidade',
                'context_length': 128000,
                'provider': 'openai',
                'pricing': {'prompt': '10', 'completion': '30'}
            },
            {
                'id': 'openai/gpt-3.5-turbo',
                'name': 'GPT-3.5 Turbo',
                'description': 'Modelo econômico para análises básicas',
                'context_length': 16385,
                'provider': 'openai',
                'pricing': {'prompt': '0.5', 'completion': '1.5'}
            },
            
            # Meta Llama Models
            {
                'id': 'meta-llama/llama-3.1-8b-instruct:free',
                'name': 'Llama 3.1 8B Instruct (Grátis)',
                'description': 'Modelo gratuito da Meta',
                'context_length': 131072,
                'provider': 'meta',
                'pricing': {'prompt': '0', 'completion': '0'},
                'recommended': True
            },
            {
                'id': 'meta-llama/llama-3.1-70b-instruct:nitro',
                'name': 'Llama 3.1 70B Instruct',
                'description': 'Modelo open source da Meta para análises',
                'context_length': 131072,
                'provider': 'meta',
                'pricing': {'prompt': '0.9', 'completion': '0.9'},
                'recommended': True
            },
            {
                'id': 'meta-llama/llama-3.1-405b-instruct:nitro',
                'name': 'Llama 3.1 405B Instruct',
                'description': 'Maior modelo da Meta com máxima capacidade',
                'context_length': 131072,
                'provider': 'meta',
                'pricing': {'prompt': '5', 'completion': '5'}
            },
            
            # Google Models
            {
                'id': 'google/gemini-pro-1.5',
                'name': 'Gemini Pro 1.5',
                'description': 'Modelo avançado do Google para análises',
                'context_length': 1000000,
                'provider': 'google',
                'pricing': {'prompt': '3.5', 'completion': '10.5'},
                'recommended': True
            },
            {
                'id': 'google/gemini-flash-1.5',
                'name': 'Gemini Flash 1.5',
                'description': 'Versão rápida do Gemini',
                'context_length': 1000000,
                'provider': 'google',
                'pricing': {'prompt': '0.075', 'completion': '0.3'},
                'recommended': True
            },
            
            # Mistral Models
            {
                'id': 'mistralai/mistral-7b-instruct:free',
                'name': 'Mistral 7B Instruct (Grátis)',
                'description': 'Modelo gratuito da Mistral AI',
                'context_length': 32768,
                'provider': 'mistral',
                'pricing': {'prompt': '0', 'completion': '0'},
                'recommended': True
            },
            {
                'id': 'mistralai/mixtral-8x7b-instruct:nitro',
                'name': 'Mixtral 8x7B Instruct',
                'description': 'Modelo mixture-of-experts da Mistral',
                'context_length': 32768,
                'provider': 'mistral',
                'pricing': {'prompt': '0.54', 'completion': '0.54'}
            },
            {
                'id': 'mistralai/mistral-large',
                'name': 'Mistral Large',
                'description': 'Modelo premium da Mistral AI',
                'context_length': 32768,
                'provider': 'mistral',
                'pricing': {'prompt': '8', 'completion': '24'}
            },
            
            # Other Notable Models
            {
                'id': 'perplexity/llama-3.1-sonar-large-128k-online',
                'name': 'Sonar Large 128K Online',
                'description': 'Modelo com acesso à internet da Perplexity',
                'context_length': 127072,
                'provider': 'perplexity',
                'pricing': {'prompt': '5', 'completion': '5'}
            },
            {
                'id': 'qwen/qwen-2-72b-instruct',
                'name': 'Qwen 2 72B Instruct',
                'description': 'Modelo multilíngue da Alibaba Cloud',
                'context_length': 131072,
                'provider': 'qwen',
                'pricing': {'prompt': '0.9', 'completion': '0.9'}
            }
        ]
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Busca informações de um modelo específico"""
        models = self.get_available_models()
        for model in models:
            if model['id'] == model_id:
                return model
        
        # Se não encontrar, retorna info básica
        return {
            'id': model_id,
            'name': model_id,
            'description': 'Modelo personalizado',
            'context_length': 4096,
            'provider': 'unknown',
            'pricing': {}
        }
    
    def validate_model(self, model_id: str) -> bool:
        """Valida se um modelo existe"""
        models = self.get_available_models()
        return any(model['id'] == model_id for model in models)

# Instância global
openrouter_models = OpenRouterModelsService()