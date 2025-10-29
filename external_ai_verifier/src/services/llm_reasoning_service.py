#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - External LLM Reasoning Service
Serviço de raciocínio com LLMs para análise aprofundada
"""

import logging
import os
from typing import Dict, Any, Optional

# Try to import LLM clients, fallback gracefully
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExternalLLMReasoningService:
    """Serviço de raciocínio com LLMs externo independente"""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicializa o serviço de LLM"""
        self.config = config.get('llm_reasoning', {})
        self.enabled = self.config.get('enabled', True)
        self.provider = self.config.get('provider', 'gemini').lower()
        self.model = self.config.get('model', 'gemini-1.5-flash')
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.temperature = self.config.get('temperature', 0.3)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        
        self.client = None
        self._initialize_llm_client()
        
        logger.info(f"✅ External LLM Reasoning Service inicializado (Provider: {self.provider}, Available: {self.client is not None})")
    
    def _initialize_llm_client(self):
        """Inicializa o cliente LLM baseado no provider configurado"""
        try:
            if self.provider == 'gemini' and GEMINI_AVAILABLE:
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.client = genai.GenerativeModel(self.model)
                    logger.info(f"✅ Gemini client inicializado: {self.model}")
                else:
                    logger.warning("⚠️ GEMINI_API_KEY não configurada")
                    
            elif self.provider == 'openai' and OPENAI_AVAILABLE:
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    openai.api_key = api_key
                    self.client = openai
                    logger.info(f"✅ OpenAI client inicializado: {self.model}")
                else:
                    logger.warning("⚠️ OPENAI_API_KEY não configurada")
            else:
                logger.warning(f"⚠️ Provider '{self.provider}' não disponível ou não configurado")
                
        except Exception as e:
            logger.error(f"Erro ao inicializar LLM client: {e}")
            self.client = None
    
    def analyze_with_llm(self, text: str, context: str = "") -> Dict[str, Any]:
        """
        Analisa o texto com LLM para raciocínio aprofundado
        
        Args:
            text (str): Texto para análise
            context (str): Contexto adicional
            
        Returns:
            Dict[str, Any]: Resultados da análise LLM
        """
        if not self.enabled or not self.client or not text or not text.strip():
            return self._get_default_result()
        
        try:
            # Prepare prompt for analysis
            prompt = self._create_analysis_prompt(text, context)
            
            # Get LLM response
            if self.provider == 'gemini':
                response = self._analyze_with_gemini(prompt)
            elif self.provider == 'openai':
                response = self._analyze_with_openai(prompt)
            else:
                return self._get_default_result()
            
            # Parse and structure response
            analysis_result = self._parse_llm_response(response, text)
            
            logger.debug(f"LLM analysis completed: confidence={analysis_result.get('llm_confidence', 0):.3f}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise LLM: {e}")
            return self._get_default_result()
    
    def _create_analysis_prompt(self, text: str, context: str = "") -> str:
        """Cria o prompt para análise LLM"""
        base_prompt = f"""Analise o seguinte texto de forma crítica e objetiva:

TEXTO PARA ANÁLISE:
\"{text}\"

{f'CONTEXTO ADICIONAL: {context}' if context else ''}

Por favor, forneça uma análise estruturada considerando:

1. QUALIDADE DO CONTEÚDO (0-10):
   - Clareza e coerência
   - Fundamentação das afirmações
   - Presença de evidências

2. CONFIABILIDADE (0-10):
   - Presença de fontes ou referências
   - Linguagem objetiva vs. subjetiva
   - Sinais de credibilidade

3. VIÉS/PARCIALIDADE (0-10, onde 0=neutro, 10=muito tendencioso):
   - Linguagem emotiva ou manipulativa
   - Apresentação unilateral de fatos
   - Generalizações ou estereótipos

4. RISCO DE DESINFORMAÇÃO (0-10):
   - Afirmações sem evidências
   - Padrões típicos de desinformação
   - Inconsistências factuais

Forneça sua resposta no seguinte formato:
QUALIDADE: [pontuação]/10 - [breve justificativa]
CONFIABILIDADE: [pontuação]/10 - [breve justificativa]  
VIÉS: [pontuação]/10 - [breve justificativa]
DESINFORMAÇÃO: [pontuação]/10 - [breve justificativa]
RECOMENDAÇÃO: [APROVAR/REJEITAR/REVISÃO_MANUAL] - [razão principal]
CONFIANÇA_ANÁLISE: [0-100]% - [justificativa da confiança]"""

        return base_prompt
    
    def _analyze_with_gemini(self, prompt: str) -> str:
        """Análise com Gemini"""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Erro no Gemini: {e}")
            raise
    
    def _analyze_with_openai(self, prompt: str) -> str:
        """Análise com OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro no OpenAI: {e}")
            raise
    
    def _parse_llm_response(self, response: str, original_text: str) -> Dict[str, Any]:
        """Parse da resposta LLM para formato estruturado"""
        try:
            import re
            
            # Initialize result structure
            result = {
                'llm_response': response,
                'quality_score': 5.0,
                'reliability_score': 5.0,
                'bias_score': 5.0,
                'disinformation_score': 5.0,
                'llm_recommendation': 'REVISÃO_MANUAL',
                'llm_confidence': 0.5,
                'analysis_reasoning': '',
                'provider': self.provider,
                'model': self.model
            }
            
            # Extract scores using regex
            patterns = {
                'quality_score': r'QUALIDADE:\s*([0-9]+(?:\.[0-9]+)?)',
                'reliability_score': r'CONFIABILIDADE:\s*([0-9]+(?:\.[0-9]+)?)',
                'bias_score': r'VIÉS:\s*([0-9]+(?:\.[0-9]+)?)',
                'disinformation_score': r'DESINFORMAÇÃO:\s*([0-9]+(?:\.[0-9]+)?)',
                'llm_recommendation': r'RECOMENDAÇÃO:\s*(APROVAR|REJEITAR|REVISÃO_MANUAL)',
                'llm_confidence': r'CONFIANÇA_ANÁLISE:\s*([0-9]+)%?'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    if key == 'llm_confidence':
                        result[key] = min(float(match.group(1)) / 100.0, 1.0)
                    elif key == 'llm_recommendation':
                        result[key] = match.group(1).upper()
                    else:
                        # Convert 0-10 scores to 0-1 range
                        score = min(float(match.group(1)) / 10.0, 1.0)
                        result[key] = score
            
            # Extract reasoning from response
            reasoning_parts = []
            for line in response.split('\\n'):
                if ' - ' in line and any(keyword in line.upper() for keyword in ['QUALIDADE', 'CONFIABILIDADE', 'VIÉS', 'DESINFORMAÇÃO']):
                    reasoning_parts.append(line.split(' - ', 1)[-1])
            
            result['analysis_reasoning'] = ' | '.join(reasoning_parts)
            
            # Validate and adjust confidence based on consistency
            result['llm_confidence'] = self._validate_llm_confidence(result)
            
            return result
            
        except Exception as e:
            logger.warning(f"Erro no parsing da resposta LLM: {e}")
            # Return response as-is with default scores
            return {
                'llm_response': response,
                'quality_score': 0.5,
                'reliability_score': 0.5,
                'bias_score': 0.5,
                'disinformation_score': 0.5,
                'llm_recommendation': 'REVISÃO_MANUAL',
                'llm_confidence': 0.3,
                'analysis_reasoning': 'Erro no parsing da resposta',
                'provider': self.provider,
                'model': self.model
            }
    
    def _validate_llm_confidence(self, result: Dict[str, Any]) -> float:
        """Valida e ajusta a confiança baseada na consistência da análise"""
        try:
            # Check consistency between recommendation and scores
            quality = result.get('quality_score', 0.5)
            reliability = result.get('reliability_score', 0.5) 
            bias = result.get('bias_score', 0.5)
            disinformation = result.get('disinformation_score', 0.5)
            recommendation = result.get('llm_recommendation', 'REVISÃO_MANUAL')
            base_confidence = result.get('llm_confidence', 0.5)
            
            # Calculate expected recommendation based on scores
            avg_positive_scores = (quality + reliability) / 2.0
            avg_negative_scores = (bias + disinformation) / 2.0
            
            expected_approval = avg_positive_scores > 0.7 and avg_negative_scores < 0.4
            expected_rejection = avg_positive_scores < 0.4 or avg_negative_scores > 0.6
            
            # Check consistency
            consistency_bonus = 0.0
            if recommendation == 'APROVAR' and expected_approval:
                consistency_bonus = 0.1
            elif recommendation == 'REJEITAR' and expected_rejection:
                consistency_bonus = 0.1
            elif recommendation == 'REVISÃO_MANUAL':
                consistency_bonus = 0.05  # Neutral is always somewhat consistent
            
            # Adjust confidence
            adjusted_confidence = min(base_confidence + consistency_bonus, 1.0)
            adjusted_confidence = max(adjusted_confidence, 0.1)
            
            return adjusted_confidence
            
        except Exception as e:
            logger.warning(f"Erro na validação de confiança: {e}")
            return 0.5
    
    def _get_default_result(self) -> Dict[str, Any]:
        """Retorna resultado padrão quando LLM não está disponível"""
        return {
            'llm_response': 'LLM não disponível ou configurado',
            'quality_score': 0.5,
            'reliability_score': 0.5,
            'bias_score': 0.5,
            'disinformation_score': 0.5,
            'llm_recommendation': 'REVISÃO_MANUAL',
            'llm_confidence': 0.1,
            'analysis_reasoning': 'Análise LLM não disponível',
            'provider': self.provider,
            'model': self.model
        }