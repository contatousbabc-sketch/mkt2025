
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Cliente Direto Google Gemini
Integração direta com API Gemini usando as 3 chaves com rotação automática
"""

import os
import logging
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiDirectClient:
    """Cliente direto para API Gemini com rotação de chaves"""
    
    def __init__(self):
        """Inicializa cliente Gemini direto com 3 chaves"""
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.model_name = "gemini-2.0-flash-exp"
        
        # Estatísticas
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "key_rotations": 0,
            "last_used_key": None
        }
        
        logger.info("🤖 Gemini Direct Client inicializado")
        logger.info(f"🔑 {len(self.api_keys)} chaves Gemini carregadas")
        logger.info(f"🎯 Modelo: {self.model_name}")
    
    def _load_api_keys(self) -> List[str]:
        """Carrega as 3 chaves Gemini do .env"""
        keys = []
        
        # Chave principal
        main_key = os.getenv('GEMINI_API_KEY')
        if main_key and main_key.strip():
            keys.append(main_key.strip())
            logger.info("✅ Gemini API principal carregada")
        
        # Chaves numeradas
        for i in range(1, 3):  # GEMINI_API_KEY_1 e GEMINI_API_KEY_2
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key and key.strip():
                keys.append(key.strip())
                logger.info(f"✅ Gemini API {i} carregada")
        
        if not keys:
            logger.error("❌ NENHUMA CHAVE GEMINI ENCONTRADA!")
            raise ValueError("Gemini API keys são obrigatórias")
        
        return keys
    
    def _get_current_api_key(self) -> str:
        """Obtém chave atual com rotação"""
        if not self.api_keys:
            raise ValueError("Nenhuma chave Gemini disponível")
        
        key = self.api_keys[self.current_key_index]
        self.stats["last_used_key"] = f"gemini_{self.current_key_index + 1}"
        return key
    
    def _rotate_key(self):
        """Rotaciona para próxima chave"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.stats["key_rotations"] += 1
        logger.info(f"🔄 Rotação para chave Gemini {self.current_key_index + 1}")
    
    async def generate_content(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Gera conteúdo usando API direta do Gemini
        
        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt do sistema (opcional)
            max_tokens: Máximo de tokens
            temperature: Temperatura
            
        Returns:
            Dict com resposta e metadados
        """
        self.stats["total_requests"] += 1
        
        # Preparar mensagens
        contents = []
        
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"INSTRUÇÕES DO SISTEMA: {system_prompt}\n\nUSUÁRIO: {prompt}"}]
            })
        else:
            contents.append({
                "role": "user", 
                "parts": [{"text": prompt}]
            })
        
        # Configuração da requisição
        request_data = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "topK": 64,
                "topP": 0.95,
                "maxOutputTokens": max_tokens,
                "candidateCount": 1
            },
            "safetySettings": [
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
        }
        
        # Tentar com cada chave disponível
        for attempt in range(len(self.api_keys)):
            try:
                api_key = self._get_current_api_key()
                url = f"{self.base_url}/models/{self.model_name}:generateContent"
                
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
                
                logger.info(f"🤖 Tentativa {attempt + 1} com chave Gemini {self.current_key_index + 1}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=headers,
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            
                            # Extrair texto da resposta
                            if "candidates" in result and len(result["candidates"]) > 0:
                                candidate = result["candidates"][0]
                                if "content" in candidate and "parts" in candidate["content"]:
                                    text_content = candidate["content"]["parts"][0]["text"]
                                    
                                    self.stats["successful_requests"] += 1
                                    
                                    logger.info(f"✅ Sucesso com chave Gemini {self.current_key_index + 1}")
                                    
                                    return {
                                        "content": text_content,
                                        "model_used": self.model_name,
                                        "provider": "gemini_direct",
                                        "api_key_used": f"gemini_{self.current_key_index + 1}",
                                        "tokens_used": result.get("usageMetadata", {}).get("totalTokenCount", 0),
                                        "success": True,
                                        "timestamp": datetime.now().isoformat()
                                    }
                            
                            raise Exception("Resposta vazia ou malformada do Gemini")
                        
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Erro HTTP {response.status} com chave {self.current_key_index + 1}: {error_text}")
                            
                            # Se for erro 429 ou quota, rotacionar chave
                            if response.status == 429 or "quota" in error_text.lower():
                                logger.warning(f"⚠️ Quota/rate limit na chave {self.current_key_index + 1}, rotacionando...")
                                self._rotate_key()
                                continue
                            
                            # Para outros erros, tentar próxima chave também
                            self._rotate_key()
                            continue
            
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout com chave Gemini {self.current_key_index + 1}")
                self._rotate_key()
                continue
                
            except Exception as e:
                logger.error(f"❌ Erro com chave Gemini {self.current_key_index + 1}: {str(e)}")
                self._rotate_key()
                continue
        
        # Se chegou aqui, todas as chaves falharam
        self.stats["failed_requests"] += 1
        raise Exception("Todas as chaves Gemini falharam")
    
    def generate_content_sync(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Versão síncrona da geração de conteúdo"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.generate_content(prompt, system_prompt, max_tokens, temperature)
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do cliente"""
        return {
            "model": self.model_name,
            "available_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }

# Instância global
gemini_direct_client = GeminiDirectClient()

# Funções de conveniência
async def generate_with_gemini_direct(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> str:
    """Função de conveniência para geração assíncrona"""
    result = await gemini_direct_client.generate_content(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    return result["content"]

def generate_with_gemini_direct_sync(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4000,
    temperature: float = 0.7
) -> str:
    """Função de conveniência para geração síncrona"""
    result = gemini_direct_client.generate_content_sync(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    return result["content"]

if __name__ == "__main__":
    # Teste rápido
    async def test():
        try:
            response = await generate_with_gemini_direct("Olá, como você está?")
            print(f"Resposta: {response}")
        except Exception as e:
            print(f"Erro no teste: {e}")
    
    asyncio.run(test())
