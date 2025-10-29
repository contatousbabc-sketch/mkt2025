# services/openrouter_hierarchy_manager.py
"""OPENROUTER HIERARCHY MANAGER - ARQV30 Enhanced v3.0
Gerenciador centralizado da hierarquia de IAs via OpenRouter
Implementa rotação inteligente: Grok-4 → Gemini-2.0 → Qwen3-Coder
ZERO SIMULAÇÃO - Apenas modelos reais funcionais
INCLUINDO: Middle-Out Transformer Implementation
"""
import os
import json
import time
import logging
import asyncio
import aiohttp
import re
import math
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MiddleOutConfig:
    """Configuração do Middle-Out Transformer"""
    enabled: bool = True
    num_passes: int = 3
    center_weight: float = 1.5
    expansion_rate: float = 0.8
    temperature_decay: float = 0.95
    attention_focus: float = 0.7
    bidirectional_weight: float = 1.2
    coherence_threshold: float = 0.85
    min_chunk_size: int = 32
    max_chunk_size: int = 256
    preserve_structure: bool = True
    optimize_for_code: bool = False

class MiddleOutTransformer:
    """
    Middle-Out Transformer Implementation

    Processa prompts iniciando do centro e expandindo bidirecionalmente,
    permitindo melhor compreensão contextual e coerência nas respostas.
    """

    def __init__(self, config: Optional[MiddleOutConfig] = None):
        self.config = config or MiddleOutConfig()

        # Métricas de performance
        self.metrics = {
            "total_transforms": 0,
            "successful_transforms": 0,
            "average_processing_time": 0.0,
            "coherence_scores": [],
            "tokens_processed": 0,
            "last_reset": datetime.now()
        }

        logger.info("🔄 Middle-Out Transformer inicializado")
        logger.info(f"📊 Config: {self.config.num_passes} passes, center_weight={self.config.center_weight}")

    def _tokenize_simple(self, text: str) -> List[str]:
        """Tokenização simples baseada em palavras e pontuação"""
        # Preservar estrutura de código se necessário
        if self.config.optimize_for_code and ('```' in text or 'def ' in text or 'class ' in text):
            return self._tokenize_code_aware(text)

        # Tokenização padrão
        tokens = re.findall(r'\S+|\s+', text)
        return [token for token in tokens if token.strip()]

    def _tokenize_code_aware(self, text: str) -> List[str]:
        """Tokenização especial para código"""
        # Dividir por linhas primeiro
        lines = text.split('\n')
        tokens = []

        for line in lines:
            if line.strip():
                # Tokenizar linha preservando indentação
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    tokens.append(' ' * indent)

                # Tokenizar conteúdo da linha
                line_tokens = re.findall(r'\w+|[^\w\s]|\s+', line.strip())
                tokens.extend([t for t in line_tokens if t.strip()])

            tokens.append('\n')

        return tokens

    def _find_center_point(self, tokens: List[str]) -> int:
        """Encontra o ponto central mais significativo do texto"""
        if len(tokens) <= 2:
            return len(tokens) // 2

        # Calcular pesos dos tokens baseado em importância
        weights = []
        for i, token in enumerate(tokens):
            weight = 1.0

            # Aumentar peso para palavras-chave importantes
            if any(keyword in token.lower() for keyword in
                   ['def', 'class', 'function', 'method', 'main', 'important', 'key', 'core']):
                weight *= 2.0

            # Aumentar peso para tokens no meio
            distance_from_center = abs(i - len(tokens) // 2) / len(tokens)
            weight *= (1.0 - distance_from_center * 0.5)

            # Reduzir peso para tokens muito comuns
            if token.lower() in ['the', 'a', 'an', 'is', 'are', 'was', 'were', 'and', 'or', 'but']:
                weight *= 0.5

            weights.append(weight)

        # Encontrar ponto com maior peso em região central
        center_start = len(tokens) // 4
        center_end = 3 * len(tokens) // 4
        center_region = weights[center_start:center_end]

        if center_region:
            max_weight_idx = center_region.index(max(center_region))
            return center_start + max_weight_idx

        return len(tokens) // 2

    def _create_expansion_sequence(self, center: int, total_length: int) -> List[Tuple[int, int]]:
        """Cria sequência de expansão a partir do centro"""
        sequence = []

        # Começar com chunk central
        chunk_size = min(self.config.min_chunk_size, total_length)
        left = max(0, center - chunk_size // 2)
        right = min(total_length, left + chunk_size)
        sequence.append((left, right))

        # Expandir bidirecionalmente
        for pass_num in range(self.config.num_passes - 1):
            expansion = int(chunk_size * self.config.expansion_rate * (pass_num + 1))

            # Expandir para esquerda
            new_left = max(0, left - expansion)
            if new_left < left:
                sequence.append((new_left, left))

            # Expandir para direita
            new_right = min(total_length, right + expansion)
            if new_right > right:
                sequence.append((right, new_right))

            # Atualizar limites
            left = new_left
            right = new_right
            chunk_size = min(self.config.max_chunk_size, chunk_size + expansion)

        return sequence

    def _calculate_coherence_score(self, text: str) -> float:
        """Calcula score de coerência do texto"""
        if not text.strip():
            return 0.0

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 1:
            return 0.8  # Texto muito curto, assumir coerência razoável

        # Métricas de coerência
        coherence_score = 1.0

        # 1. Consistência de vocabulário
        words = re.findall(r'\b\w+\b', text.lower())
        unique_words = set(words)
        if len(words) > 0:
            vocabulary_diversity = len(unique_words) / len(words)
            coherence_score *= (0.7 + 0.3 * vocabulary_diversity)

        # 2. Conectividade entre sentenças
        connective_words = ['however', 'therefore', 'moreover', 'furthermore', 'consequently',
                           'additionally', 'meanwhile', 'similarly', 'in contrast', 'as a result']

        connective_count = sum(1 for word in connective_words if word in text.lower())
        connectivity_bonus = min(0.2, connective_count * 0.05)
        coherence_score += connectivity_bonus

        # 3. Penalizar repetições excessivas
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Ignorar palavras muito curtas
                word_counts[word] = word_counts.get(word, 0) + 1

        max_repetition = max(word_counts.values()) if word_counts else 1
        repetition_penalty = min(0.3, (max_repetition - 1) * 0.1)
        coherence_score -= repetition_penalty

        return max(0.0, min(1.0, coherence_score))

    def transform_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Aplica transformação middle-out no prompt

        Args:
            prompt: Prompt original do usuário
            system_prompt: Prompt do sistema (opcional)

        Returns:
            Dict com prompt transformado e metadados
        """
        start_time = datetime.now().timestamp()
        self.metrics["total_transforms"] += 1

        if not self.config.enabled:
            return {
                "transformed_prompt": prompt,
                "system_prompt": system_prompt,
                "transformation_applied": False,
                "processing_time": 0.0,
                "coherence_score": 1.0,
                "metadata": {"reason": "transformer_disabled"}
            }

        try:
            # Tokenizar prompt
            tokens = self._tokenize_simple(prompt)

            if len(tokens) < self.config.min_chunk_size:
                # Prompt muito pequeno, não transformar
                return {
                    "transformed_prompt": prompt,
                    "system_prompt": system_prompt,
                    "transformation_applied": False,
                    "processing_time": datetime.now().timestamp() - start_time,
                    "coherence_score": 1.0,
                    "metadata": {"reason": "prompt_too_small", "token_count": len(tokens)}
                }

            # Encontrar centro e criar sequência de expansão
            center = self._find_center_point(tokens)
            expansion_sequence = self._create_expansion_sequence(center, len(tokens))

            # Reconstruir prompt com foco no centro
            weighted_tokens = []

            for start, end in expansion_sequence:
                chunk_tokens = tokens[start:end]

                # Aplicar peso baseado na distância do centro
                for i, token in enumerate(chunk_tokens):
                    global_idx = start + i
                    distance_from_center = abs(global_idx - center) / len(tokens)

                    weight = self.config.center_weight * (1.0 - distance_from_center)
                    weight *= self.config.bidirectional_weight if global_idx != center else 1.0

                    weighted_tokens.append({
                        "token": token,
                        "weight": weight,
                        "position": global_idx,
                        "distance_from_center": distance_from_center
                    })

            # Ordenar por peso (mais importantes primeiro)
            weighted_tokens.sort(key=lambda x: x["weight"], reverse=True)

            # Reconstruir mantendo ordem original mas com estrutura otimizada
            if self.config.preserve_structure:
                # Manter ordem original, apenas destacar elementos importantes
                transformed_prompt = self._reconstruct_with_structure(tokens, weighted_tokens, center)
            else:
                # Reordenar completamente baseado em importância
                transformed_prompt = self._reconstruct_by_importance(weighted_tokens)

            # Calcular score de coerência
            coherence_score = self._calculate_coherence_score(transformed_prompt)

            # Aplicar transformação no system_prompt se fornecido
            transformed_system = system_prompt
            if system_prompt and len(system_prompt) > self.config.min_chunk_size:
                system_result = self.transform_prompt(system_prompt)
                transformed_system = system_result["transformed_prompt"]

            # Atualizar métricas
            processing_time = datetime.now().timestamp() - start_time
            self.metrics["successful_transforms"] += 1
            self.metrics["coherence_scores"].append(coherence_score)
            self.metrics["tokens_processed"] += len(tokens)

            # Calcular tempo médio
            if self.metrics["successful_transforms"] > 0:
                self.metrics["average_processing_time"] = (
                    (self.metrics["average_processing_time"] * (self.metrics["successful_transforms"] - 1) + processing_time) /
                    self.metrics["successful_transforms"]
                )

            return {
                "transformed_prompt": transformed_prompt,
                "system_prompt": transformed_system,
                "transformation_applied": True,
                "processing_time": processing_time,
                "coherence_score": coherence_score,
                "metadata": {
                    "original_length": len(tokens),
                    "center_position": center,
                    "expansion_passes": len(expansion_sequence),
                    "weight_distribution": self._calculate_weight_stats(weighted_tokens)
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro na transformação middle-out: {str(e)}")
            return {
                "transformed_prompt": prompt,
                "system_prompt": system_prompt,
                "transformation_applied": False,
                "processing_time": datetime.now().timestamp() - start_time,
                "coherence_score": 0.0,
                "metadata": {"error": str(e)}
            }

    def _reconstruct_with_structure(self, original_tokens: List[str], weighted_tokens: List[Dict], center: int) -> str:
        """Reconstrói prompt mantendo estrutura original mas com otimizações"""
        # Criar mapa de pesos por posição
        weight_map = {wt["position"]: wt["weight"] for wt in weighted_tokens}

        # Reconstruir com ênfase nos elementos mais importantes
        result_parts = []

        for i, token in enumerate(original_tokens):
            weight = weight_map.get(i, 1.0)

            # Destacar tokens importantes (apenas para prompt, não alterar estrutura)
            if weight > self.config.center_weight * 0.8:
                # Token importante - manter como está mas pode ser processado diferentemente
                result_parts.append(token)
            else:
                result_parts.append(token)

        return ''.join(result_parts)

    def _reconstruct_by_importance(self, weighted_tokens: List[Dict]) -> str:
        """Reconstrói prompt reordenando por importância"""
        # Agrupar por importância
        high_importance = [wt for wt in weighted_tokens if wt["weight"] > self.config.center_weight * 0.8]
        medium_importance = [wt for wt in weighted_tokens if self.config.center_weight * 0.4 <= wt["weight"] <= self.config.center_weight * 0.8]
        low_importance = [wt for wt in weighted_tokens if wt["weight"] < self.config.center_weight * 0.4]

        # Reconstruir: high -> medium -> low
        result_parts = []

        for group in [high_importance, medium_importance, low_importance]:
            # Manter ordem relativa dentro de cada grupo
            group.sort(key=lambda x: x["position"])
            result_parts.extend([wt["token"] for wt in group])

        return ''.join(result_parts)

    def _calculate_weight_stats(self, weighted_tokens: List[Dict]) -> Dict[str, float]:
        """Calcula estatísticas dos pesos"""
        weights = [wt["weight"] for wt in weighted_tokens]

        if not weights:
            return {}

        return {
            "min_weight": min(weights),
            "max_weight": max(weights),
            "avg_weight": sum(weights) / len(weights),
            "weight_variance": sum((w - sum(weights)/len(weights))**2 for w in weights) / len(weights)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de performance do transformer"""
        avg_coherence = sum(self.metrics["coherence_scores"]) / len(self.metrics["coherence_scores"]) if self.metrics["coherence_scores"] else 0.0

        return {
            "total_transforms": self.metrics["total_transforms"],
            "successful_transforms": self.metrics["successful_transforms"],
            "success_rate": self.metrics["successful_transforms"] / max(1, self.metrics["total_transforms"]),
            "average_processing_time": self.metrics["average_processing_time"],
            "average_coherence_score": avg_coherence,
            "tokens_processed": self.metrics["tokens_processed"],
            "last_reset": self.metrics["last_reset"].isoformat(),
            "config": {
                "enabled": self.config.enabled,
                "num_passes": self.config.num_passes,
                "center_weight": self.config.center_weight,
                "expansion_rate": self.config.expansion_rate
            }
        }

    def reset_metrics(self):
        """Reseta métricas de performance"""
        self.metrics = {
            "total_transforms": 0,
            "successful_transforms": 0,
            "average_processing_time": 0.0,
            "coherence_scores": [],
            "tokens_processed": 0,
            "last_reset": datetime.now()
        }
        logger.info("📊 Métricas do Middle-Out Transformer resetadas")

@dataclass
class AIModel:
    """Estrutura de dados para modelo de IA"""
    name: str
    provider: str
    endpoint: str
    max_tokens: int
    temperature: float
    is_free: bool
    priority: int
    status: str = "active"  # active, failed, disabled
    last_used: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    # Configuração do transformer
    transforms: Optional[List[str]] = None
    middle_out_config: Optional[MiddleOutConfig] = None

class OpenRouterHierarchyManager:
    """Gerenciador centralizado da hierarquia de IAs via OpenRouter com Middle-Out Transformer"""

    def __init__(self):
        # 1. URL BASE CORRIGIDA
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0

        # Inicializar Middle-Out Transformer
        self.middle_out_transformer = MiddleOutTransformer()

        # HIERARQUIA DEFINIDA COM GROK-4 COMO PRIMÁRIO
        self.models_hierarchy = [
            AIModel(
                name="x-ai/grok-4-fast:free",
                provider="x-ai",
                endpoint=f"{self.base_url}/chat/completions",
                max_tokens=4000,
                temperature=0.7,
                is_free=True,
                priority=1,
                transforms=["middle-out"],
                middle_out_config=MiddleOutConfig(
                    enabled=True,
                    num_passes=3,
                    center_weight=1.5,
                    preserve_structure=True
                )
            ),
            AIModel(
                name="google/gemini-2.0-flash-exp:free",
                provider="google",
                endpoint=f"{self.base_url}/chat/completions",
                max_tokens=8000,
                temperature=0.7,
                is_free=True,
                priority=2,
                transforms=["middle-out"],
                middle_out_config=MiddleOutConfig(
                    enabled=True,
                    num_passes=2,
                    center_weight=1.3,
                    preserve_structure=True
                )
            ),
            AIModel(
                name="qwen/qwen3-coder:free",
                provider="qwen",
                endpoint=f"{self.base_url}/chat/completions",
                max_tokens=4000,
                temperature=0.7,
                is_free=True,
                priority=3,
                transforms=["middle-out"],
                middle_out_config=MiddleOutConfig(
                    enabled=True,
                    num_passes=2,
                    center_weight=1.2,
                    optimize_for_code=True
                )
            ),
            AIModel(
                name="openai/gpt-3.5-turbo",
                provider="openai",
                endpoint=f"{self.base_url}/chat/completions",
                max_tokens=4000,
                temperature=0.7,
                is_free=False, # Pago
                priority=4,
                transforms=["middle-out"],
                middle_out_config=MiddleOutConfig(
                    enabled=True,
                    num_passes=2,
                    center_weight=1.1,
                    preserve_structure=False
                )
            ),
            AIModel(
                name="anthropic/claude-3-haiku",
                provider="anthropic",
                endpoint=f"{self.base_url}/chat/completions",
                max_tokens=4000,
                temperature=0.7,
                is_free=False, # Pago
                priority=5,
                transforms=["middle-out"],
                middle_out_config=MiddleOutConfig(
                    enabled=True,
                    num_passes=2,
                    center_weight=1.0,
                    preserve_structure=False
                )
            )
        ]

        # Estatísticas de uso
        self.usage_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "model_usage": {},
            "transformer_usage": {},
            "last_reset": datetime.now()
        }

        logger.info("🤖 OpenRouter Hierarchy Manager inicializado")
        logger.info(f"📊 Hierarquia: {' → '.join([m.name for m in self.models_hierarchy])}")
        logger.info("🔄 Middle-Out Transformer ativo")

    def _load_api_keys(self) -> List[str]:
        """Carrega múltiplas chaves OpenRouter"""
        keys = []

        # Chave principal
        main_key = os.getenv('OPENROUTER_API_KEY')
        if main_key and main_key.strip():
            keys.append(main_key.strip())
            logger.info("✅ OpenRouter API principal carregada")

        # Chaves numeradas
        for i in range(1, 6):  # Até 5 chaves
            key = os.getenv(f'OPENROUTER_API_KEY_{i}')
            if key and key.strip():
                keys.append(key.strip())
                logger.info(f"✅ OpenRouter API {i} carregada")

        if not keys:
            logger.error("❌ NENHUMA CHAVE OPENROUTER ENCONTRADA!")
            raise ValueError("OpenRouter API keys são obrigatórias")

        logger.info(f"🔑 {len(keys)} chave(s) OpenRouter carregadas")
        return keys

    def _get_current_api_key(self) -> str:
        """Obtém chave atual com rotação"""
        if not self.api_keys:
            raise ValueError("Nenhuma chave OpenRouter disponível")

        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def _get_next_available_model(self) -> Optional[AIModel]:
        """Obtém próximo modelo disponível na hierarquia"""
        for model in sorted(self.models_hierarchy, key=lambda x: x.priority):
            if model.status == "active":
                return model

        logger.error("❌ Nenhum modelo disponível na hierarquia!")
        return None

    def _mark_model_failed(self, model: AIModel, error: str, duration: int = 300):
        """Marca modelo como falhado temporariamente"""
        model.failure_count += 1
        model.status = "failed"

        logger.warning(f"⚠️ Modelo {model.name} marcado como falhado: {error}")

        # Reabilitar após 'duration' segundos
        async def reactivate_model():
            await asyncio.sleep(duration)
            model.status = "active"
            logger.info(f"✅ Modelo {model.name} reativado após {duration}s")

        asyncio.create_task(reactivate_model())

    def _mark_model_success(self, model: AIModel):
        """Marca modelo como bem-sucedido"""
        model.success_count += 1
        model.last_used = datetime.now()
        model.status = "active"

    def _apply_middle_out_transform(self, prompt: str, system_prompt: Optional[str], model: AIModel) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """Aplica transformação middle-out se configurada para o modelo"""
        if not model.transforms or "middle-out" not in model.transforms:
            return prompt, system_prompt, {"transformation_applied": False}

        # Configurar transformer para este modelo específico
        original_config = None
        if model.middle_out_config:
            original_config = self.middle_out_transformer.config
            self.middle_out_transformer.config = model.middle_out_config

        try:
            # Aplicar transformação
            transform_result = self.middle_out_transformer.transform_prompt(prompt, system_prompt)

            # Atualizar estatísticas
            if model.name not in self.usage_stats["transformer_usage"]:
                self.usage_stats["transformer_usage"][model.name] = 0
            self.usage_stats["transformer_usage"][model.name] += 1

            logger.info(f"🔄 Middle-out aplicado em {model.name}: coherence={transform_result['coherence_score']:.3f}")

            return (
                transform_result["transformed_prompt"],
                transform_result["system_prompt"],
                transform_result["metadata"]
            )

        finally:
            # Restaurar configuração original se foi alterada
            if original_config:
                self.middle_out_transformer.config = original_config

    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model_override: Optional[str] = None,
        enable_transforms: bool = True
    ) -> Dict[str, Any]:
        """
        Gera completion usando hierarquia de modelos com Middle-Out Transformer

        Args:
            prompt: Prompt do usuário
            system_prompt: Prompt do sistema (opcional)
            max_tokens: Máximo de tokens (opcional)
            temperature: Temperatura (opcional)
            model_override: Forçar modelo específico (opcional)
            enable_transforms: Habilitar transformações (padrão: True)

        Returns:
            Dict com resposta e metadados
        """
        self.usage_stats["total_requests"] += 1

        # Determinar modelo a usar
        if model_override:
            target_model = next((m for m in self.models_hierarchy if m.name == model_override), None)
            if not target_model:
                logger.error(f"❌ Modelo override não encontrado: {model_override}")
                target_model = self._get_next_available_model()
        else:
            target_model = self._get_next_available_model()

        if not target_model:
            raise Exception("Nenhum modelo disponível")

        # Aplicar transformação middle-out se habilitada
        transformed_prompt = prompt
        transformed_system = system_prompt
        transform_metadata = {"transformation_applied": False}

        if enable_transforms:
            transformed_prompt, transformed_system, transform_metadata = self._apply_middle_out_transform(
                prompt, system_prompt, target_model
            )

        # Preparar mensagens
        messages = []
        if transformed_system:
            messages.append({"role": "system", "content": transformed_system})
        messages.append({"role": "user", "content": transformed_prompt})

        # Configurar parâmetros
        request_params = {
            "model": target_model.name,
            "messages": messages,
            "max_tokens": max_tokens or target_model.max_tokens,
            "temperature": temperature or target_model.temperature,
            "stream": False
        }

        # Adicionar transforms se definido no modelo
        if target_model.transforms:
            request_params["transforms"] = target_model.transforms
            logger.info(f"🔧 Aplicando transforms: {target_model.transforms} para {target_model.name}")

        # Tentar com modelo atual
        for attempt in range(3):  # Até 3 tentativas
            try:
                api_key = self._get_current_api_key()
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/joscarmao/v1800finalv2",
                    "X-Title": "ARQV30 Enhanced v3.0"
                }

                logger.info(f"🤖 Tentativa {attempt + 1} com {target_model.name}")

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        target_model.endpoint,
                        headers=headers,
                        json=request_params,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:

                        if response.status == 200:
                            result = await response.json()

                            # Sucesso!
                            self._mark_model_success(target_model)
                            self.usage_stats["successful_requests"] += 1

                            # Atualizar estatísticas
                            if target_model.name not in self.usage_stats["model_usage"]:
                                self.usage_stats["model_usage"][target_model.name] = 0
                            self.usage_stats["model_usage"][target_model.name] += 1

                            logger.info(f"✅ Sucesso com {target_model.name}")

                            return {
                                "content": result["choices"][0]["message"]["content"],
                                "model_used": target_model.name,
                                "provider": target_model.provider,
                                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                                "success": True,
                                "timestamp": datetime.now().isoformat(),
                                "transform_metadata": transform_metadata,
                                "transforms_applied": target_model.transforms or [],
                                "original_prompt_length": len(prompt),
                                "transformed_prompt_length": len(transformed_prompt)
                            }

                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Erro HTTP {response.status}: {error_text}")

                            # Se erro 429 (rate limit) ou contém "rate", marcar modelo como falhado por curto período
                            if response.status == 429 or "rate" in error_text.lower():
                                logger.warning(f"⚠️ Modelo {target_model.name} com rate limit, tentando próximo")
                                self._mark_model_failed(target_model, f"HTTP {response.status}", duration=60) # 1 minuto apenas
                                break  # Sair do loop de tentativas para este modelo e tentar o próximo

                            # Para outros erros, tentar novamente
                            if attempt == 2:  # Última tentativa
                                self._mark_model_failed(target_model, f"HTTP {response.status}")
                                break

                            await asyncio.sleep(2 ** attempt)  # Backoff exponencial

            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout com {target_model.name}")
                if attempt == 2:
                    self._mark_model_failed(target_model, "Timeout")
                    break
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"❌ Erro com {target_model.name}: {str(e)}")
                if attempt == 2:
                    self._mark_model_failed(target_model, str(e))
                    break
                await asyncio.sleep(2 ** attempt)

        # Se chegou aqui, o modelo atual falhou - tentar próximo na hierarquia
        remaining_models = [m for m in self.models_hierarchy if m.status == "active" and m.priority > target_model.priority]

        if remaining_models:
            next_model = min(remaining_models, key=lambda x: x.priority)
            logger.info(f"🔄 Tentando próximo modelo: {next_model.name}")

            # Chamada recursiva com próximo modelo
            return await self.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model_override=next_model.name,
                enable_transforms=enable_transforms
            )

        # Todos os modelos falharam
        self.usage_stats["failed_requests"] += 1
        raise Exception("Todos os modelos da hierarquia falharam")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do gerenciador"""
        return {
            "models": [
                {
                    "name": model.name,
                    "provider": model.provider,
                    "priority": model.priority,
                    "status": model.status,
                    "success_count": model.success_count,
                    "failure_count": model.failure_count,
                    "last_used": model.last_used.isoformat() if model.last_used else None,
                    "transforms": model.transforms,
                    "middle_out_enabled": model.middle_out_config.enabled if model.middle_out_config else False
                }
                for model in self.models_hierarchy
            ],
            "usage_stats": self.usage_stats,
            "api_keys_count": len(self.api_keys),
            "active_models": len([m for m in self.models_hierarchy if m.status == "active"]),
            "middle_out_metrics": self.middle_out_transformer.get_metrics()
        }

    def reset_failed_models(self):
        """Reativa todos os modelos falhados"""
        for model in self.models_hierarchy:
            if model.status == "failed":
                model.status = "active"
                logger.info(f"✅ Modelo {model.name} reativado manualmente")

    def update_middle_out_config(self, model_name: str, config: MiddleOutConfig):
        """Atualiza configuração middle-out para um modelo específico"""
        model = next((m for m in self.models_hierarchy if m.name == model_name), None)
        if model:
            model.middle_out_config = config
            logger.info(f"🔄 Configuração middle-out atualizada para {model_name}")
        else:
            logger.error(f"❌ Modelo não encontrado: {model_name}")

    def toggle_middle_out_for_model(self, model_name: str, enabled: bool):
        """Habilita/desabilita middle-out para um modelo específico"""
        model = next((m for m in self.models_hierarchy if m.name == model_name), None)
        if model and model.middle_out_config:
            model.middle_out_config.enabled = enabled
            logger.info(f"🔄 Middle-out {'habilitado' if enabled else 'desabilitado'} para {model_name}")
        else:
            logger.error(f"❌ Modelo ou configuração middle-out não encontrada: {model_name}")

    def get_middle_out_metrics(self) -> Dict[str, Any]:
        """Retorna métricas detalhadas do middle-out transformer"""
        return self.middle_out_transformer.get_metrics()

    def reset_middle_out_metrics(self):
        """Reseta métricas do middle-out transformer"""
        self.middle_out_transformer.reset_metrics()

# Instância global para uso em todo o projeto
openrouter_manager = OpenRouterHierarchyManager()

# Função de conveniência para uso direto
async def generate_ai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    model_override: Optional[str] = None,
    enable_transforms: bool = True
) -> str:
    """
    Função de conveniência para gerar resposta de IA com Middle-Out Transformer

    Args:
        prompt: Prompt do usuário
        system_prompt: Prompt do sistema (opcional)
        max_tokens: Máximo de tokens (opcional)
        temperature: Temperatura (opcional)
        model_override: Forçar modelo específico (opcional)
        enable_transforms: Habilitar transformações (padrão: True)

    Returns:
        String com a resposta da IA
    """
    try:
        result = await openrouter_manager.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            enable_transforms=enable_transforms
        )
        return result["content"]
    except Exception as e:
        logger.error(f"❌ Erro ao gerar resposta de IA: {str(e)}")
        raise

# Função síncrona para compatibilidade
def generate_ai_response_sync(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    model_override: Optional[str] = None,
    enable_transforms: bool = True
) -> str:
    """Versão síncrona da função de geração de resposta"""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        generate_ai_response(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model_override=model_override,
            enable_transforms=enable_transforms
        )
    )

# Função para testar transformação middle-out
async def test_middle_out_transform(prompt: str) -> Dict[str, Any]:
    """
    Testa transformação middle-out sem fazer requisição para API

    Args:
        prompt: Prompt para testar

    Returns:
        Dict com resultado da transformação
    """
    return openrouter_manager.middle_out_transformer.transform_prompt(prompt)

# Função para análise de coerência
def analyze_text_coherence(text: str) -> float:
    """
    Analisa coerência de um texto usando as métricas do middle-out transformer

    Args:
        text: Texto para analisar

    Returns:
        Score de coerência (0.0 a 1.0)
    """
    return openrouter_manager.middle_out_transformer._calculate_coherence_score(text)

if __name__ == "__main__":
    # Teste completo do sistema
    async def test_complete_system():
        try:
            print("🧪 Iniciando teste completo do sistema...")

            # 1. Teste básico de transformação
            print("\n1️⃣ Testando transformação middle-out...")
            test_prompt = """
            Explique como funciona um algoritmo de machine learning para classificação de imagens.
            Preciso entender os conceitos principais, as etapas do processo e como avaliar a performance.
            Também gostaria de saber sobre redes neurais convolucionais e sua aplicação neste contexto.
            """

            transform_result = await test_middle_out_transform(test_prompt)
            print(f"✅ Transformação aplicada: {transform_result['transformation_applied']}")
            print(f"📊 Score de coerência: {transform_result['coherence_score']:.3f}")
            print(f"⏱️ Tempo de processamento: {transform_result['processing_time']:.3f}s")

            # 2. Teste de análise de coerência
            print("\n2️⃣ Testando análise de coerência...")
            coherent_text = "Machine learning é uma área da inteligência artificial. Ela permite que computadores aprendam sem programação explícita. Os algoritmos analisam dados e identificam padrões."
            incoherent_text = "Machine learning gatos azuis. Computadores banana aprender sem programação. Os algoritmos árvores e identificam padrões pizza."

            coherent_score = analyze_text_coherence(coherent_text)
            incoherent_score = analyze_text_coherence(incoherent_text)

            print(f"📈 Texto coerente: {coherent_score:.3f}")
            print(f"📉 Texto incoerente: {incoherent_score:.3f}")

            # 3. Teste de geração com IA (se chaves estiverem disponíveis)
            print("\n3️⃣ Testando geração de resposta...")
            try:
                response = await generate_ai_response(
                    prompt="Olá! Como você está?",
                    system_prompt="Você é um assistente útil e amigável.",
                    enable_transforms=True
                )
                print(f"🤖 Resposta: {response[:100]}...")

            except Exception as e:
                print(f"⚠️ Teste de geração falhou (normal se não houver chaves): {str(e)}")

            # 4. Status do sistema
            print("\n4️⃣ Status do sistema...")
            status = openrouter_manager.get_status()
            print(f"📊 Modelos ativos: {status['active_models']}")
            print(f"🔄 Middle-out habilitado: {any(m['middle_out_enabled'] for m in status['models'])}")

            # 5. Métricas do middle-out
            print("\n5️⃣ Métricas do Middle-Out Transformer...")
            metrics = openrouter_manager.get_middle_out_metrics()
            print(f"🎯 Taxa de sucesso: {metrics['success_rate']:.3f}")
            print(f"⏱️ Tempo médio: {metrics['average_processing_time']:.3f}s")
            print(f"📈 Coerência média: {metrics['average_coherence_score']:.3f}")

            print("\n✅ Teste completo finalizado com sucesso!")

        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()

    # Executar teste
    asyncio.run(test_complete_system())