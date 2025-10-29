
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente Gemini Direto com Rotação de APIs
Para uso exclusivo do UBIE com acesso total ao fluxo
"""

import os
import logging
import json
import time
import threading
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class DirectGeminiClient:
    """Cliente Gemini direto com rotação automática de 3 chaves API"""
    
    def __init__(self):
        """Inicializa cliente com rotação de chaves Gemini"""
        self.api_keys = []
        self.current_key_index = 0
        self.lock = threading.Lock()
        
        # Carregar chaves do .env
        self._load_gemini_keys()
        
        # Configurações otimizadas
        self.generation_config = {
            'temperature': 0.8,
            'top_p': 0.95,
            'top_k': 64,
            'max_output_tokens': 8192,
            'candidate_count': 1
        }
        
        # Configurações de segurança mínimas
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        self.available = len(self.api_keys) > 0
        logger.info(f"✅ DirectGeminiClient inicializado com {len(self.api_keys)} chaves")
    
    def _load_gemini_keys(self):
        """Carrega as 3 chaves Gemini do .env"""
        gemini_keys = [
            os.getenv('GEMINI_API_KEY'),
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2')
        ]
        
        for i, key in enumerate(gemini_keys, 1):
            if key and key.strip():
                self.api_keys.append(key.strip())
                logger.info(f"✅ Chave Gemini {i} carregada")
        
        if not self.api_keys:
            logger.error("❌ Nenhuma chave Gemini encontrada no .env")
    
    def _get_next_key(self) -> Optional[str]:
        """Obtém próxima chave na rotação"""
        if not self.api_keys:
            return None
            
        with self.lock:
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"🔄 Rotacionando para chave Gemini {self.current_key_index + 1}/{len(self.api_keys)}")
            return key
    
    def generate_content(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Gera conteúdo usando API Gemini direta com rotação"""
        if not self.available:
            raise Exception("❌ Nenhuma chave Gemini disponível")
        
        # Configurar parâmetros customizados
        config = self.generation_config.copy()
        if max_tokens:
            config['max_output_tokens'] = max_tokens
        if temperature is not None:
            config['temperature'] = temperature
        
        # Construir prompt final
        final_prompt = prompt
        if system_prompt:
            final_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Tentar com todas as chaves até conseguir
        last_error = None
        for attempt in range(len(self.api_keys)):
            api_key = self._get_next_key()
            if not api_key:
                break
                
            try:
                logger.info(f"🤖 Tentativa {attempt + 1} com chave Gemini")
                
                # Configurar API
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.0-flash-exp")
                
                # Gerar conteúdo
                start_time = time.time()
                response = model.generate_content(
                    final_prompt,
                    generation_config=config,
                    safety_settings=self.safety_settings
                )
                processing_time = time.time() - start_time
                
                if response.text:
                    logger.info(f"✅ Sucesso com chave Gemini {attempt + 1}")
                    return {
                        'success': True,
                        'content': response.text,
                        'model': 'gemini-2.0-flash-exp',
                        'processing_time': processing_time,
                        'key_used': attempt + 1
                    }
                else:
                    logger.warning(f"⚠️ Resposta vazia da chave {attempt + 1}")
                    last_error = "Resposta vazia"
                    
            except Exception as e:
                logger.error(f"❌ Erro com chave Gemini {attempt + 1}: {e}")
                last_error = str(e)
                time.sleep(0.5)  # Breve pausa antes da próxima tentativa
                continue
        
        # Se chegou aqui, todas as tentativas falharam
        raise Exception(f"❌ Todas as chaves Gemini falharam. Último erro: {last_error}")
    
    def test_connection(self) -> bool:
        """Testa conexão com todas as chaves"""
        if not self.available:
            return False
            
        working_keys = 0
        for i, api_key in enumerate(self.api_keys, 1):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.0-flash-exp")
                
                response = model.generate_content(
                    "Responda apenas: GEMINI_OK",
                    generation_config={'max_output_tokens': 10},
                    safety_settings=self.safety_settings
                )
                
                if response.text and "GEMINI_OK" in response.text:
                    logger.info(f"✅ Chave Gemini {i} funcionando")
                    working_keys += 1
                else:
                    logger.warning(f"⚠️ Chave Gemini {i} com problema")
                    
            except Exception as e:
                logger.error(f"❌ Chave Gemini {i} falhou: {e}")
        
        logger.info(f"📊 {working_keys}/{len(self.api_keys)} chaves Gemini funcionando")
        return working_keys > 0
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do cliente"""
        return {
            'available': self.available,
            'total_keys': len(self.api_keys),
            'current_key_index': self.current_key_index,
            'model': 'gemini-2.0-flash-exp',
            'timestamp': datetime.now().isoformat()
        }

# Instância global
direct_gemini_client = DirectGeminiClient()
