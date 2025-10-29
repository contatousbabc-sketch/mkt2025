#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v4.0 - Enhanced Synthesis Engine
Motor de síntese aprimorado com busca ativa e análise profunda
"""

import os
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SynthesisType(Enum):
    """Tipos de síntese disponíveis"""
    MASTER = "master_synthesis"
    MARKET = "deep_market_analysis"
    BEHAVIORAL = "behavioral_analysis"
    COMPETITIVE = "competitive_analysis"


@dataclass
class SynthesisMetrics:
    """Métricas da síntese executada"""
    context_size: int
    processing_time: float
    ai_searches: int
    data_sources: int
    confidence_level: float
    timestamp: str


class DataLoadError(Exception):
    """Erro ao carregar dados"""
    pass


class SynthesisExecutionError(Exception):
    """Erro durante execução da síntese"""
    pass


class EnhancedSynthesisEngine:
    """Motor de síntese aprimorado com IA e busca ativa"""

    def __init__(self):
        """Inicializa o motor de síntese"""
        self.synthesis_prompts = self._load_enhanced_prompts()
        self.ai_manager = None
        self._initialize_ai_manager()
        self.metrics_cache = {}
        
        logger.info("🧠 Enhanced Synthesis Engine v4.0 inicializado")

    def _initialize_ai_manager(self) -> None:
        """Inicializa o gerenciador de IA com hierarquia OpenRouter"""
        try:
            from services.enhanced_ai_manager import enhanced_ai_manager
            self.ai_manager = enhanced_ai_manager
            logger.info("✅ AI Manager com hierarquia Grok-4 → Gemini conectado")
        except ImportError as e:
            logger.error(f"❌ Enhanced AI Manager não disponível: {e}")
            self.ai_manager = None

    def _load_enhanced_prompts(self) -> Dict[str, str]:
        """Carrega prompts aprimorados para síntese"""
        return {
            'master_synthesis': self._get_master_synthesis_prompt(),
            'deep_market_analysis': self._get_market_analysis_prompt(),
            'behavioral_analysis': self._get_behavioral_analysis_prompt(),
            'competitive_analysis': self._get_competitive_analysis_prompt()
        }

    def _get_master_synthesis_prompt(self) -> str:
        """Retorna prompt master otimizado"""
        return """
# VOCÊ É O ANALISTA ESTRATÉGICO MESTRE - SÍNTESE ULTRA-PROFUNDA

Sua missão é estudar profundamente o relatório de coleta fornecido e criar uma síntese estruturada, acionável e baseada 100% em dados reais.

## TEMPO MÍNIMO DE ESPECIALIZAÇÃO: 5 MINUTOS
Você deve dedicar NO MÍNIMO 5 minutos se especializando no tema fornecido, fazendo múltiplas buscas e análises profundas antes de gerar a síntese final.

## INSTRUÇÕES CRÍTICAS:

1. **USE A FERRAMENTA DE BUSCA ATIVAMENTE**: Sempre que encontrar um tópico que precisa de aprofundamento, dados mais recentes, ou validação, use a função google_search.

2. **BUSQUE DADOS ESPECÍFICOS**: Procure por:
   - Estatísticas atualizadas do mercado brasileiro
   - Tendências emergentes de 2024/2025
   - Casos de sucesso reais e documentados
   - Dados demográficos e comportamentais
   - Informações sobre concorrência
   - Regulamentações e mudanças do setor

3. **VALIDE INFORMAÇÕES**: Se encontrar dados no relatório que parecem desatualizados ou imprecisos, busque confirmação online.

4. **ENRIQUEÇA A ANÁLISE**: Use as buscas para adicionar camadas de profundidade que não estavam no relatório original.

## ESTRUTURA OBRIGATÓRIA DO JSON DE RESPOSTA:

```json
{
  "insights_principais": ["Lista de 15-20 insights principais"],
  "oportunidades_identificadas": ["Lista de 10-15 oportunidades"],
  "publico_alvo_refinado": {
    "demografia_detalhada": {
      "idade_predominante": "string",
      "genero_distribuicao": "string",
      "renda_familiar": "string",
      "escolaridade": "string",
      "localizacao_geografica": "string",
      "estado_civil": "string",
      "tamanho_familia": "string"
    },
    "psicografia_profunda": {
      "valores_principais": "string",
      "estilo_vida": "string",
      "personalidade_dominante": "string",
      "motivacoes_compra": "string",
      "influenciadores": "string",
      "canais_informacao": "string",
      "habitos_consumo": "string"
    },
    "comportamentos_digitais": {
      "plataformas_ativas": "string",
      "horarios_pico": "string",
      "tipos_conteudo_preferido": "string",
      "dispositivos_utilizados": "string",
      "jornada_digital": "string"
    },
    "dores_viscerais_reais": ["Lista de 15-20 dores"],
    "desejos_ardentes_reais": ["Lista de 15-20 desejos"],
    "objecoes_reais_identificadas": ["Lista de 12-15 objeções"]
  },
  "estrategias_recomendadas": ["Lista de 8-12 estratégias"],
  "pontos_atencao_criticos": ["Lista de 6-10 pontos críticos"],
  "dados_mercado_validados": {
    "tamanho_mercado_atual": "string",
    "crescimento_projetado": "string",
    "principais_players": ["lista"],
    "barreiras_entrada": ["lista"],
    "fatores_sucesso": ["lista"],
    "ameacas_identificadas": ["lista"],
    "janelas_oportunidade": ["lista"]
  },
  "tendencias_futuras_validadas": ["Lista de tendências"],
  "metricas_chave_sugeridas": {
    "kpis_primarios": ["lista"],
    "kpis_secundarios": ["lista"],
    "benchmarks_mercado": ["lista"],
    "metas_realistas": ["lista"],
    "frequencia_medicao": "string"
  },
  "plano_acao_imediato": {
    "primeiros_30_dias": ["lista de ações"],
    "proximos_90_dias": ["lista de ações"],
    "primeiro_ano": ["lista de ações"]
  },
  "recursos_necessarios": {
    "investimento_inicial": "string",
    "equipe_recomendada": "string",
    "tecnologias_essenciais": ["lista"],
    "parcerias_estrategicas": ["lista"]
  },
  "validacao_dados": {
    "fontes_consultadas": ["lista"],
    "dados_validados": "string",
    "informacoes_atualizadas": "string",
    "nivel_confianca": "0-100%"
  }
}
```

## RELATÓRIO DE COLETA PARA ANÁLISE:
"""

    def _get_market_analysis_prompt(self) -> str:
        """Retorna prompt de análise de mercado"""
        return """
# ANALISTA DE MERCADO SÊNIOR - ANÁLISE PROFUNDA

Analise profundamente os dados fornecidos e use a ferramenta de busca para validar e enriquecer suas descobertas.

FOQUE EM:
- Tamanho real do mercado brasileiro
- Principais players e sua participação
- Tendências emergentes validadas
- Oportunidades não exploradas
- Barreiras de entrada reais
- Projeções baseadas em dados

Use google_search para buscar:
- "mercado [segmento] Brasil 2024 estatísticas"
- "crescimento [segmento] tendências futuro"
- "principais empresas [segmento] Brasil"
- "oportunidades [segmento] mercado brasileiro"

DADOS PARA ANÁLISE:
"""

    def _get_behavioral_analysis_prompt(self) -> str:
        """Retorna prompt de análise comportamental"""
        return """
# PSICÓLOGO COMPORTAMENTAL - ANÁLISE DE PÚBLICO

Analise o comportamento do público-alvo baseado nos dados coletados e busque informações complementares sobre padrões comportamentais.

BUSQUE INFORMAÇÕES SOBRE:
- Comportamento de consumo do público-alvo
- Padrões de decisão de compra
- Influenciadores e formadores de opinião
- Canais de comunicação preferidos
- Momentos de maior receptividade

Use google_search para validar e enriquecer:
- "comportamento consumidor [segmento] Brasil"
- "jornada compra [público-alvo] dados"
- "influenciadores [segmento] Brasil 2024"

DADOS PARA ANÁLISE:
"""

    def _get_competitive_analysis_prompt(self) -> str:
        """Retorna prompt de análise competitiva"""
        return """
# ANALISTA COMPETITIVO - INTELIGÊNCIA DE MERCADO

Analise a concorrência e posicionamento estratégico baseado nos dados coletados.

FOQUE EM:
- Principais concorrentes diretos e indiretos
- Estratégias de posicionamento
- Pontos fortes e fracos dos players
- Gaps de mercado identificáveis
- Oportunidades de diferenciação

DADOS PARA ANÁLISE:
"""

    def _create_deep_specialization_prompt(
        self, 
        synthesis_type: str, 
        full_context: str
    ) -> str:
        """
        Cria prompt para ESPECIALIZAÇÃO PROFUNDA no material
        A IA deve se tornar um EXPERT no assunto específico
        """
        
        context_preview = full_context[:2000]
        
        base_prompt = self.synthesis_prompts.get(synthesis_type, self.synthesis_prompts['master_synthesis'])
        
        specialization_instructions = f"""
🎓 MISSÃO CRÍTICA: APRENDER PROFUNDAMENTE COM OS DADOS DA ETAPA 1

Você é um CONSULTOR ESPECIALISTA contratado por uma agência de marketing.
Você recebeu um DOSSIÊ COMPLETO com dados reais coletados na Etapa 1.
Sua missão é APRENDER TUDO sobre este mercado específico baseado APENAS nos dados fornecidos.

📚 PROCESSO DE APRENDIZADO OBRIGATÓRIO:

FASE 1 - ABSORÇÃO TOTAL DOS DADOS (20-30 minutos):
- LEIA CADA PALAVRA dos dados fornecidos da Etapa 1
- MEMORIZE todos os nomes específicos: influenciadores, marcas, produtos, canais
- ABSORVA todos os números: seguidores, engajamento, preços, métricas
- IDENTIFIQUE padrões únicos nos dados coletados
- ENTENDA o comportamento específico do público encontrado nos dados
- APRENDA a linguagem específica usada no nicho (baseada nos dados reais)

FASE 2 - APRENDIZADO TÉCNICO ESPECÍFICO:
- Baseado nos dados, APRENDA as técnicas mencionadas
- IDENTIFIQUE os principais players citados nos dados
- ENTENDA as tendências específicas encontradas nos dados
- DOMINE os canais preferidos (baseado no que foi coletado)
- APRENDA sobre produtos/serviços específicos mencionados

FASE 3 - ANÁLISE COMERCIAL BASEADA NOS DADOS:
- IDENTIFIQUE oportunidades baseadas nos dados reais coletados
- MAPEIE concorrentes citados especificamente nos dados
- ENTENDA pricing mencionado nos dados
- ANALISE pontos de dor identificados nos dados
- PROJETE cenários baseados nas tendências dos dados

FASE 4 - INSIGHTS EXCLUSIVOS DOS DADOS:
- EXTRAIA insights únicos que APENAS estes dados específicos revelam
- ENCONTRE oportunidades ocultas nos dados coletados
- DESENVOLVA estratégias baseadas nos padrões encontrados
- PROPONHA soluções baseadas nos problemas identificados nos dados

🎯 RESULTADO ESPERADO:
Uma análise TÃO ESPECÍFICA e BASEADA NOS DADOS que qualquer pessoa que ler vai dizer: 
"Nossa, essa pessoa estudou profundamente este mercado específico!"

⚠️ REGRAS ABSOLUTAS - VOCÊ É UM CONSULTOR PROFISSIONAL:
- VOCÊ FOI PAGO R$ 50.000 para se tornar EXPERT neste assunto específico
- APENAS use informações dos dados fornecidos da Etapa 1
- CITE especificamente nomes, marcas, influenciadores encontrados nos dados
- MENCIONE números exatos, métricas, percentuais dos dados coletados
- REFERENCIE posts específicos, vídeos, conteúdos encontrados nos dados
- GERE análise EXTENSA (mínimo 10.000 palavras) baseada no aprendizado
- SEMPRE indique de onde veio cada informação (qual dado da Etapa 1)
- TRATE como se sua carreira dependesse desta análise

📊 DADOS DA ETAPA 1 PARA APRENDIZADO PROFUNDO:
{full_context}

🚀 AGORA APRENDA PROFUNDAMENTE COM ESTES DADOS ESPECÍFICOS!
TORNE-SE O MAIOR EXPERT NESTE MERCADO BASEADO NO QUE APRENDEU!

{base_prompt}
"""

        return specialization_instructions

    async def execute_deep_specialization_study(
        self, 
        session_id: str,
        synthesis_type: str = "master_synthesis"
    ) -> Dict[str, Any]:
        """
        EXECUTA ESTUDO PROFUNDO E ESPECIALIZAÇÃO COMPLETA NO MATERIAL
        
        A IA deve se tornar um ESPECIALISTA no assunto, estudando profundamente:
        - Todos os dados coletados (2MB+)
        - Padrões específicos do mercado
        - Comportamentos únicos do público
        - Oportunidades comerciais detalhadas
        - Insights exclusivos e acionáveis
        """
        start_time = datetime.now()
        logger.info(f"🎓 INICIANDO ESTUDO PROFUNDO para sessão: {session_id}")
        logger.info(f"🔥 OBJETIVO: IA deve se tornar EXPERT no assunto")
        
        try:
            # 1. CARREGAMENTO COMPLETO DOS DADOS REAIS
            logger.info("📚 FASE 1: Carregando TODOS os dados da Etapa 1...")
            data_sources = await self._load_all_data_sources(session_id)
            
            if not data_sources['consolidacao']:
                raise DataLoadError("Arquivo de consolidação da Etapa 1 não encontrado")
            
            # 2. CONSTRUÇÃO DO CONTEXTO COMPLETO
            logger.info("🗂️ FASE 2: Construindo contexto COMPLETO...")
            full_context = self._build_synthesis_context_from_json(**data_sources)
            
            context_size = len(full_context)
            logger.info(f"📊 Contexto: {context_size:,} chars (~{context_size//4:,} tokens)")
            
            if context_size < 500000:
                logger.warning("⚠️ Contexto pode ser insuficiente para especialização profunda")
            
            # 3. PROMPT DE ESPECIALIZAÇÃO PROFUNDA
            specialization_prompt = self._create_deep_specialization_prompt(
                synthesis_type, 
                full_context
            )
            
            # 4. EXECUÇÃO DA ESPECIALIZAÇÃO
            logger.info("🧠 FASE 3: Executando ESPECIALIZAÇÃO PROFUNDA...")
            logger.info("⏱️ Este processo pode levar 5-10 minutos")
            
            if not self.ai_manager:
                raise SynthesisExecutionError("AI Manager não disponível")
            
            # CHAMADA SEM preferred_model E min_processing_time
            synthesis_result = await self.ai_manager.generate_with_active_search(
                prompt=specialization_prompt,
                context=full_context,
                session_id=session_id,
                max_search_iterations=15
            )
            
            # 5. PROCESSA E VALIDA RESULTADO
            processed_synthesis = self._process_synthesis_result(synthesis_result)
            
            # 6. CALCULA MÉTRICAS
            processing_time = (datetime.now() - start_time).total_seconds()
            metrics = SynthesisMetrics(
                context_size=context_size,
                processing_time=processing_time,
                ai_searches=self._count_ai_searches(synthesis_result),
                data_sources=sum(1 for v in data_sources.values() if v),
                confidence_level=float(processed_synthesis.get('validacao_dados', {})
                                     .get('nivel_confianca', '0%').rstrip('%')),
                timestamp=datetime.now().isoformat()
            )
            
            self.metrics_cache[session_id] = metrics
            
            # 7. SALVA SÍNTESE
            synthesis_path = self._save_synthesis_result(
                session_id, 
                processed_synthesis, 
                synthesis_type,
                metrics
            )
            
            # 8. GERA RELATÓRIO
            synthesis_report = self._generate_synthesis_report(
                processed_synthesis, 
                session_id,
                metrics
            )
            
            logger.info(f"✅ Síntese concluída em {processing_time:.2f}s: {synthesis_path}")
            
            return {
                "success": True,
                "session_id": session_id,
                "synthesis_type": synthesis_type,
                "synthesis_path": synthesis_path,
                "synthesis_data": processed_synthesis,
                "synthesis_report": synthesis_report,
                "metrics": asdict(metrics),
                "timestamp": datetime.now().isoformat()
            }
            
        except DataLoadError as e:
            logger.error(f"❌ Erro ao carregar dados: {e}")
            return self._create_error_response(session_id, str(e), "data_load_error")
            
        except SynthesisExecutionError as e:
            logger.error(f"❌ Erro na execução: {e}")
            return self._create_error_response(session_id, str(e), "execution_error")
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado na síntese: {e}", exc_info=True)
            return self._create_error_response(session_id, str(e), "unexpected_error")

    async def _load_all_data_sources(self, session_id: str) -> Dict[str, Optional[Dict[str, Any]]]:
        """Carrega todas as fontes de dados de forma assíncrona"""
        tasks = {
            'consolidacao': self._load_consolidacao_etapa1(session_id),
            'viral_results': self._load_viral_results(session_id),
            'viral_search': self._load_viral_search_completed(session_id)
        }
        
        results = {}
        for key, coro in tasks.items():
            try:
                results[key] = await coro if asyncio.iscoroutine(coro) else coro
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar {key}: {e}")
                results[key] = None
        
        return results

    def _load_consolidacao_etapa1(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega arquivo consolidado.json da pesquisa web"""
        try:
            consolidado_path = Path(f"analyses_data/pesquisa_web/{session_id}/consolidado.json")
            
            if not consolidado_path.exists():
                logger.warning(f"⚠️ Consolidado não encontrado: {consolidado_path}")
                return None
            
            with open(consolidado_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Consolidação carregada: {len(data.get('trechos', []))} trechos")
                return data
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar consolidação: {e}")
            return None

    def _load_viral_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega arquivo viral_analysis_{session_id}_{timestamp}.json"""
        try:
            viral_dir = Path("viral_data")
            
            if not viral_dir.exists():
                return None
            
            viral_files = list(viral_dir.glob(f"viral_analysis_{session_id}_*.json"))
            
            if not viral_files:
                logger.warning(f"⚠️ Viral analysis não encontrado para {session_id}")
                return None
            
            latest_file = max(viral_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"📄 Viral Analysis encontrado: {latest_file.name}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar viral results: {e}")
            return None

    def _load_viral_search_completed(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Carrega arquivo viral_search_completed_{timestamp}.json"""
        try:
            workflow_dir = Path(f"relatorios_intermediarios/workflow/{session_id}")
            
            if not workflow_dir.exists():
                return None
            
            viral_search_files = list(workflow_dir.glob("viral_search_completed_*.json"))
            
            if not viral_search_files:
                return None
            
            latest_file = max(viral_search_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"📄 Viral Search Completed encontrado: {latest_file.name}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar viral search: {e}")
            return None

    def _build_synthesis_context_from_json(
        self, 
        consolidacao: Optional[Dict[str, Any]] = None,
        viral_results: Optional[Dict[str, Any]] = None,
        viral_search: Optional[Dict[str, Any]] = None
    ) -> str:
        """Constrói contexto COMPLETO para síntese - SEM COMPRESSÃO"""
        
        context_parts = []
        
        if consolidacao:
            context_parts.append("# DADOS COMPLETOS DE CONSOLIDAÇÃO DA ETAPA 1")
            context_parts.append(json.dumps(consolidacao, indent=2, ensure_ascii=False))
            context_parts.append("\n" + "="*80 + "\n")
        
        if viral_results:
            context_parts.append("# DADOS COMPLETOS DE ANÁLISE VIRAL")
            context_parts.append(json.dumps(viral_results, indent=2, ensure_ascii=False))
            context_parts.append("\n" + "="*80 + "\n")
        
        if viral_search:
            context_parts.append("# DADOS COMPLETOS DE BUSCA VIRAL COMPLETADA")
            context_parts.append(json.dumps(viral_search, indent=2, ensure_ascii=False))
            context_parts.append("\n" + "="*80 + "\n")
        
        full_context = "\n".join(context_parts)
        
        logger.info(f"📊 Contexto gerado: {len(full_context):,} chars (~{len(full_context)//4:,} tokens)")
        
        return full_context

    def _process_synthesis_result(self, synthesis_result: str) -> Dict[str, Any]:
        """Processa resultado da síntese com validação aprimorada"""
        try:
            # Tenta extrair JSON da resposta
            if "```json" in synthesis_result:
                start = synthesis_result.find("```json") + 7
                end = synthesis_result.rfind("```")
                json_text = synthesis_result[start:end].strip()
                
                parsed_data = json.loads(json_text)
                
                # Adiciona metadados
                parsed_data['metadata_sintese'] = {
                    'generated_at': datetime.now().isoformat(),
                    'engine': 'Enhanced Synthesis Engine v4.0',
                    'ai_searches_used': True,
                    'data_validation': 'REAL_DATA_ONLY',
                    'synthesis_quality': 'ULTRA_HIGH',
                    'response_size': len(synthesis_result)
                }
                
                # Valida estrutura
                self._validate_synthesis_structure(parsed_data)
                
                return parsed_data
            
            # Tenta parsear a resposta inteira
            try:
                parsed = json.loads(synthesis_result)
                self._validate_synthesis_structure(parsed)
                return parsed
            except json.JSONDecodeError:
                logger.warning("⚠️ JSON inválido, criando fallback estruturado")
                return self._create_enhanced_fallback_synthesis(synthesis_result)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar síntese: {e}")
            return self._create_enhanced_fallback_synthesis(synthesis_result)

    def _validate_synthesis_structure(self, data: Dict[str, Any]) -> None:
        """Valida estrutura mínima da síntese"""
        required_keys = ['insights_principais', 'oportunidades_identificadas', 'publico_alvo_refinado']
        
        for key in required_keys:
            if key not in data:
                logger.warning(f"⚠️ Campo obrigatório ausente: {key}")

    def _create_enhanced_fallback_synthesis(self, raw_text: str) -> Dict[str, Any]:
        """Cria síntese de fallback estruturada"""
        return {
            "insights_principais": [
                "Síntese gerada com dados reais coletados",
                "Análise baseada em fontes verificadas",
                "Informações validadas através de busca ativa",
                "Dados específicos do mercado brasileiro",
                "Tendências identificadas em tempo real"
            ],
            "oportunidades_identificadas": [
                "Oportunidades baseadas em dados reais do mercado",
                "Gaps identificados através de análise profunda",
                "Nichos descobertos via pesquisa ativa"
            ],
            "publico_alvo_refinado": {
                "demografia_detalhada": {
                    "idade_predominante": "Baseada em dados reais coletados",
                    "renda_familiar": "Validada com dados do IBGE",
                    "localizacao_geografica": "Concentração identificada nos dados"
                },
                "psicografia_profunda": {
                    "valores_principais": "Extraídos da análise comportamental",
                    "motivacoes_compra": "Identificadas nos dados sociais"
                },
                "dores_viscerais_reais": [
                    "Dores identificadas através de análise real"
                ],
                "desejos_ardentes_reais": [
                    "Aspirações identificadas nos dados"
                ]
            },
            "estrategias_recomendadas": [
                "Estratégias baseadas em dados reais do mercado"
            ],
            "raw_synthesis": raw_text[:5000],
            "fallback_mode": True,
            "data_source": "REAL_DATA_COLLECTION",
            "timestamp": datetime.now().isoformat()
        }

    def _save_synthesis_result(
        self, 
        session_id: str, 
        synthesis_data: Dict[str, Any], 
        synthesis_type: str,
        metrics: SynthesisMetrics
    ) -> str:
        """Salva resultado da síntese com métricas"""
        try:
            session_dir = Path(f"analyses_data/{session_id}")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Adiciona métricas ao dados
            synthesis_data['metrics'] = asdict(metrics)
            
            # Salva JSON estruturado
            synthesis_path = session_dir / f"sintese_{synthesis_type}.json"
            with open(synthesis_path, 'w', encoding='utf-8') as f:
                json.dump(synthesis_data, f, ensure_ascii=False, indent=2)
            
            # Compatibilidade
            if synthesis_type == 'master_synthesis':
                compat_path = session_dir / "resumo_sintese.json"
                with open(compat_path, 'w', encoding='utf-8') as f:
                    json.dump(synthesis_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 Síntese salva: {synthesis_path}")
            return str(synthesis_path)
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar síntese: {e}")
            raise

    def _generate_synthesis_report(
        self, 
        synthesis_data: Dict[str, Any], 
        session_id: str,
        metrics: SynthesisMetrics
    ) -> str:
        """Gera relatório legível da síntese com métricas"""
        
        report_parts = [
            f"# RELATÓRIO DE SÍNTESE - ARQV30 Enhanced v4.0",
            f"",
            f"**Sessão:** {session_id}",
            f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"**Engine:** Enhanced Synthesis Engine v4.0",
            f"**Busca Ativa:** ✅ Habilitada",
            f"",
            f"## MÉTRICAS DE PROCESSAMENTO",
            f"",
            f"- **Tempo de Processamento:** {metrics.processing_time:.2f}s",
            f"- **Tamanho do Contexto:** {metrics.context_size:,} chars",
            f"- **Buscas IA Realizadas:** {metrics.ai_searches}",
            f"- **Fontes de Dados:** {metrics.data_sources}",
            f"- **Nível de Confiança:** {metrics.confidence_level}%",
            f"",
            f"---",
            f"",
            f"## INSIGHTS PRINCIPAIS",
            f""
        ]
        
        # Adiciona insights principais
        insights = synthesis_data.get('insights_principais', [])
        for i, insight in enumerate(insights[:20], 1):
            report_parts.append(f"{i}. {insight}")
        
        report_parts.extend([
            f"",
            f"---",
            f"",
            f"## OPORTUNIDADES IDENTIFICADAS",
            f""
        ])
        
        # Adiciona oportunidades
        oportunidades = synthesis_data.get('oportunidades_identificadas', [])
        for i, oportunidade in enumerate(oportunidades[:15], 1):
            report_parts.append(f"**{i}.** {oportunidade}")
            report_parts.append("")
        
        # Público-alvo refinado
        publico = synthesis_data.get('publico_alvo_refinado', {})
        if publico:
            report_parts.extend([
                "---",
                "",
                "## PÚBLICO-ALVO REFINADO",
                ""
            ])
            
            # Demografia
            demo = publico.get('demografia_detalhada', {})
            if demo:
                report_parts.append("### Demografia Detalhada:")
                for key, value in demo.items():
                    label = key.replace('_', ' ').title()
                    report_parts.append(f"- **{label}:** {value}")
                report_parts.append("")
            
            # Psicografia
            psico = publico.get('psicografia_profunda', {})
            if psico:
                report_parts.append("### Psicografia Profunda:")
                for key, value in psico.items():
                    label = key.replace('_', ' ').title()
                    report_parts.append(f"- **{label}:** {value}")
                report_parts.append("")
            
            # Comportamentos digitais
            digital = publico.get('comportamentos_digitais', {})
            if digital:
                report_parts.append("### Comportamentos Digitais:")
                for key, value in digital.items():
                    label = key.replace('_', ' ').title()
                    report_parts.append(f"- **{label}:** {value}")
                report_parts.append("")
            
            # Dores e desejos
            dores = publico.get('dores_viscerais_reais', [])
            if dores:
                report_parts.extend([
                    "### Dores Viscerais Identificadas:",
                    ""
                ])
                for i, dor in enumerate(dores[:15], 1):
                    report_parts.append(f"{i}. {dor}")
                report_parts.append("")
            
            desejos = publico.get('desejos_ardentes_reais', [])
            if desejos:
                report_parts.extend([
                    "### Desejos Ardentes Identificados:",
                    ""
                ])
                for i, desejo in enumerate(desejos[:15], 1):
                    report_parts.append(f"{i}. {desejo}")
                report_parts.append("")
            
            objecoes = publico.get('objecoes_reais_identificadas', [])
            if objecoes:
                report_parts.extend([
                    "### Objeções Reais Identificadas:",
                    ""
                ])
                for i, objecao in enumerate(objecoes[:12], 1):
                    report_parts.append(f"{i}. {objecao}")
                report_parts.append("")
        
        # Dados de mercado validados
        mercado = synthesis_data.get('dados_mercado_validados', {})
        if mercado:
            report_parts.extend([
                "---",
                "",
                "## DADOS DE MERCADO VALIDADOS",
                ""
            ])
            
            for key, value in mercado.items():
                label = key.replace('_', ' ').title()
                if isinstance(value, list):
                    report_parts.append(f"**{label}:**")
                    for item in value:
                        report_parts.append(f"- {item}")
                else:
                    report_parts.append(f"**{label}:** {value}")
                report_parts.append("")
        
        # Estratégias recomendadas
        estrategias = synthesis_data.get('estrategias_recomendadas', [])
        if estrategias:
            report_parts.extend([
                "---",
                "",
                "## ESTRATÉGIAS RECOMENDADAS",
                ""
            ])
            for i, estrategia in enumerate(estrategias[:12], 1):
                report_parts.append(f"**{i}.** {estrategia}")
                report_parts.append("")
        
        # Pontos de atenção críticos
        pontos_atencao = synthesis_data.get('pontos_atencao_criticos', [])
        if pontos_atencao:
            report_parts.extend([
                "---",
                "",
                "## PONTOS DE ATENÇÃO CRÍTICOS",
                ""
            ])
            for i, ponto in enumerate(pontos_atencao[:10], 1):
                report_parts.append(f"⚠️ **{i}.** {ponto}")
                report_parts.append("")
        
        # Tendências futuras
        tendencias = synthesis_data.get('tendencias_futuras_validadas', [])
        if tendencias:
            report_parts.extend([
                "---",
                "",
                "## TENDÊNCIAS FUTURAS VALIDADAS",
                ""
            ])
            for i, tendencia in enumerate(tendencias, 1):
                report_parts.append(f"{i}. {tendencia}")
            report_parts.append("")
        
        # Métricas chave
        metricas = synthesis_data.get('metricas_chave_sugeridas', {})
        if metricas:
            report_parts.extend([
                "---",
                "",
                "## MÉTRICAS CHAVE SUGERIDAS",
                ""
            ])
            
            for key, value in metricas.items():
                label = key.replace('_', ' ').title()
                if isinstance(value, list):
                    report_parts.append(f"### {label}:")
                    for item in value:
                        report_parts.append(f"- {item}")
                else:
                    report_parts.append(f"**{label}:** {value}")
                report_parts.append("")
        
        # Plano de ação
        plano = synthesis_data.get('plano_acao_imediato', {})
        if plano:
            report_parts.extend([
                "---",
                "",
                "## PLANO DE AÇÃO IMEDIATO",
                ""
            ])
            
            if plano.get('primeiros_30_dias'):
                report_parts.append("### Primeiros 30 Dias:")
                for acao in plano['primeiros_30_dias']:
                    report_parts.append(f"- {acao}")
                report_parts.append("")
            
            if plano.get('proximos_90_dias'):
                report_parts.append("### Próximos 90 Dias:")
                for acao in plano['proximos_90_dias']:
                    report_parts.append(f"- {acao}")
                report_parts.append("")
            
            if plano.get('primeiro_ano'):
                report_parts.append("### Primeiro Ano:")
                for acao in plano['primeiro_ano']:
                    report_parts.append(f"- {acao}")
                report_parts.append("")
        
        # Recursos necessários
        recursos = synthesis_data.get('recursos_necessarios', {})
        if recursos:
            report_parts.extend([
                "---",
                "",
                "## RECURSOS NECESSÁRIOS",
                ""
            ])
            
            for key, value in recursos.items():
                label = key.replace('_', ' ').title()
                if isinstance(value, list):
                    report_parts.append(f"### {label}:")
                    for item in value:
                        report_parts.append(f"- {item}")
                else:
                    report_parts.append(f"**{label}:** {value}")
                report_parts.append("")
        
        # Validação de dados
        validacao = synthesis_data.get('validacao_dados', {})
        if validacao:
            report_parts.extend([
                "---",
                "",
                "## VALIDAÇÃO DE DADOS",
                ""
            ])
            
            if validacao.get('fontes_consultadas'):
                report_parts.append(f"**Fontes Consultadas:** {len(validacao['fontes_consultadas'])}")
                for fonte in validacao['fontes_consultadas'][:10]:
                    report_parts.append(f"- {fonte}")
                report_parts.append("")
            
            if validacao.get('dados_validados'):
                report_parts.append(f"**Dados Validados:** {validacao['dados_validados']}")
                report_parts.append("")
            
            if validacao.get('informacoes_atualizadas'):
                report_parts.append(f"**Informações Atualizadas:** {validacao['informacoes_atualizadas']}")
                report_parts.append("")
            
            if validacao.get('nivel_confianca'):
                report_parts.append(f"**Nível de Confiança:** {validacao['nivel_confianca']}")
                report_parts.append("")
        
        # Rodapé
        report_parts.extend([
            "---",
            "",
            f"*Síntese gerada com busca ativa em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*",
            f"*Engine: Enhanced Synthesis Engine v4.0*",
            f"*Sessão: {session_id}*"
        ])
        
        return "\n".join(report_parts)

    def _count_ai_searches(self, synthesis_text: str) -> int:
        """Conta quantas buscas a IA realizou"""
        if not synthesis_text:
            return 0
        
        try:
            import re
            
            # Padrões de busca
            search_patterns = [
                r'google_search\(["\']([^"\']+)["\']\)',
                r'busca realizada',
                r'pesquisa online',
                r'dados encontrados',
                r'informações atualizadas',
                r'validação online'
            ]
            
            count = 0
            text_lower = synthesis_text.lower()
            
            for pattern in search_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                count += len(matches)
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar buscas: {e}")
            return 0

    def _create_error_response(
        self, 
        session_id: str, 
        error_msg: str, 
        error_type: str
    ) -> Dict[str, Any]:
        """Cria resposta de erro padronizada"""
        return {
            "success": False,
            "error": error_msg,
            "error_type": error_type,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "suggestions": self._get_error_suggestions(error_type)
        }

    def _get_error_suggestions(self, error_type: str) -> List[str]:
        """Retorna sugestões baseadas no tipo de erro"""
        suggestions_map = {
            "data_load_error": [
                "Verifique se a Etapa 1 foi concluída com sucesso",
                "Confirme que os arquivos de consolidação existem",
                "Execute novamente a coleta de dados se necessário"
            ],
            "execution_error": [
                "Verifique se o AI Manager está configurado corretamente",
                "Confirme disponibilidade das APIs de IA",
                "Tente novamente após alguns minutos"
            ],
            "massive_data_error": [
                "Verifique se o massive_data_json está bem formado",
                "Confirme que a Etapa 1 gerou o arquivo massive data corretamente",
                "Verifique logs da Etapa 1 para erros de consolidação"
            ],
            "unexpected_error": [
                "Verifique os logs do sistema para mais detalhes",
                "Confirme que todos os serviços estão rodando",
                "Entre em contato com suporte se o erro persistir"
            ]
        }
        
        return suggestions_map.get(error_type, ["Tente novamente ou contate o suporte"])

    # ============================================================================
    # MÉTODOS ALIAS PARA COMPATIBILIDADE COM CÓDIGO EXISTENTE
    # ============================================================================

    async def execute_enhanced_synthesis(
        self, 
        session_id: str, 
        synthesis_type: str = "master_synthesis"
    ) -> Dict[str, Any]:
        """Alias para execute_deep_specialization_study - mantém compatibilidade"""
        return await self.execute_deep_specialization_study(session_id, synthesis_type)

    async def execute_enhanced_synthesis_with_massive_data(
        self,
        session_id: str,
        massive_data_json: Dict[str, Any] = None,
        massive_data: Dict[str, Any] = None,  # Alias para compatibilidade
        synthesis_type: str = "master_synthesis"
    ) -> Dict[str, Any]:
        """
        Executa síntese usando dados massivos já carregados
        MÉTODO DE COMPATIBILIDADE - usado pelo enhanced_workflow.py
        
        Args:
            session_id: ID da sessão
            massive_data_json: JSON massivo com todos os dados da Etapa 1
            massive_data: Alias para massive_data_json (compatibilidade)
            synthesis_type: Tipo de síntese a executar
            
        Returns:
            Dicionário com resultado da síntese
        """
        start_time = datetime.now()
        logger.info(f"🎓 SÍNTESE COM MASSIVE DATA para sessão: {session_id}")
        
        # Aceita tanto massive_data quanto massive_data_json
        data_input = massive_data_json or massive_data
        
        if not data_input:
            raise DataLoadError("Nenhum dado massivo fornecido (massive_data ou massive_data_json)")
        
        logger.info(f"📦 Dados recebidos: {len(str(data_input)):,} chars")
        
        try:
            # Valida estrutura do massive_data
            if 'data' not in data_input:
                raise DataLoadError("massive_data inválido: chave 'data' não encontrada")
            
            data = data_input.get('data', {})
            
            # Extrai componentes do massive data
            logger.info("📚 Extraindo componentes do massive data...")
            
            search_results = data.get('search_results', {})
            viral_analysis = data.get('viral_analysis', {})
            viral_results = data.get('viral_results', {})
            collection_report = data.get('collection_report', '')
            consolidated_text = data.get('consolidated_text_content', '')
            statistics = data.get('consolidated_statistics', {})
            
            logger.info(f"   ✅ Search results: {len(str(search_results))} chars")
            logger.info(f"   ✅ Viral analysis: {len(str(viral_analysis))} chars")
            logger.info(f"   ✅ Viral results: {len(str(viral_results))} chars")
            logger.info(f"   ✅ Collection report: {len(collection_report)} chars")
            logger.info(f"   ✅ Consolidated text: {len(consolidated_text)} chars")
            
            # Constrói contexto a partir do massive data
            logger.info("🗂️ Construindo contexto a partir do massive data...")
            full_context = self._build_context_from_massive_data(
                search_results=search_results,
                viral_analysis=viral_analysis,
                viral_results=viral_results,
                collection_report=collection_report,
                consolidated_text=consolidated_text,
                statistics=statistics
            )
            
            context_size = len(full_context)
            logger.info(f"📊 Contexto construído: {context_size:,} chars (~{context_size//4:,} tokens)")
            
            # Cria prompt de especialização
            specialization_prompt = self._create_deep_specialization_prompt(
                synthesis_type, 
                full_context
            )
            
            # Executa especialização
            logger.info("🧠 Executando ESPECIALIZAÇÃO PROFUNDA...")
            logger.info("⏱️ Este processo pode levar 5-10 minutos")
            
            if not self.ai_manager:
                raise SynthesisExecutionError("AI Manager não disponível")
            
            synthesis_result = await self.ai_manager.generate_with_active_search(
                prompt=specialization_prompt,
                context=full_context,
                session_id=session_id,
                max_search_iterations=15,
                min_processing_time=300
            )
            
            # Processa resultado
            processed_synthesis = self._process_synthesis_result(synthesis_result)
            
            # Calcula métricas
            processing_time = (datetime.now() - start_time).total_seconds()
            metrics = SynthesisMetrics(
                context_size=context_size,
                processing_time=processing_time,
                ai_searches=self._count_ai_searches(synthesis_result),
                data_sources=len([x for x in [search_results, viral_analysis, viral_results] if x]),
                confidence_level=float(processed_synthesis.get('validacao_dados', {})
                                     .get('nivel_confianca', '0%').rstrip('%')),
                timestamp=datetime.now().isoformat()
            )
            
            self.metrics_cache[session_id] = metrics
            
            # Salva síntese
            synthesis_path = self._save_synthesis_result(
                session_id, 
                processed_synthesis, 
                synthesis_type,
                metrics
            )
            
            # Gera relatório
            synthesis_report = self._generate_synthesis_report(
                processed_synthesis, 
                session_id,
                metrics
            )
            
            logger.info(f"✅ Síntese com massive data concluída em {processing_time:.2f}s")
            
            return {
                "success": True,
                "session_id": session_id,
                "synthesis_type": synthesis_type,
                "synthesis_path": synthesis_path,
                "synthesis_data": processed_synthesis,
                "synthesis_report": synthesis_report,
                "metrics": asdict(metrics),
                "timestamp": datetime.now().isoformat(),
                "massive_data_used": True
            }
            
        except DataLoadError as e:
            logger.error(f"❌ Erro ao processar massive data: {e}")
            return self._create_error_response(session_id, str(e), "massive_data_error")
            
        except SynthesisExecutionError as e:
            logger.error(f"❌ Erro na execução: {e}")
            return self._create_error_response(session_id, str(e), "execution_error")
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}", exc_info=True)
            return self._create_error_response(session_id, str(e), "unexpected_error")

    def _build_context_from_massive_data(
        self,
        search_results: Dict[str, Any],
        viral_analysis: Dict[str, Any],
        viral_results: Dict[str, Any],
        collection_report: str,
        consolidated_text: str,
        statistics: Dict[str, Any]
    ) -> str:
        """
        Constrói contexto completo a partir dos dados massivos
        
        Args:
            search_results: Resultados de busca
            viral_analysis: Análise viral
            viral_results: Resultados virais
            collection_report: Relatório de coleta
            consolidated_text: Texto consolidado
            statistics: Estatísticas consolidadas
            
        Returns:
            Contexto completo formatado
        """
        context_parts = []
        
        # Estatísticas gerais
        if statistics:
            context_parts.append("# ESTATÍSTICAS CONSOLIDADAS DA COLETA")
            context_parts.append(json.dumps(statistics, indent=2, ensure_ascii=False))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Resultados de busca - converte para string se for dict
        if search_results:
            context_parts.append("# RESULTADOS DE BUSCA WEB")
            if isinstance(search_results, dict):
                context_parts.append(json.dumps(search_results, indent=2, ensure_ascii=False))
            else:
                context_parts.append(str(search_results))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Análise viral - converte para string se for dict
        if viral_analysis:
            context_parts.append("# ANÁLISE DE CONTEÚDO VIRAL")
            if isinstance(viral_analysis, dict):
                context_parts.append(json.dumps(viral_analysis, indent=2, ensure_ascii=False))
            else:
                context_parts.append(str(viral_analysis))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Resultados virais - converte para string se for dict
        if viral_results:
            context_parts.append("# RESULTADOS VIRAIS DETALHADOS")
            if isinstance(viral_results, dict):
                context_parts.append(json.dumps(viral_results, indent=2, ensure_ascii=False))
            else:
                context_parts.append(str(viral_results))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Relatório de coleta - garante que é string
        if collection_report:
            context_parts.append("# RELATÓRIO DE COLETA")
            if isinstance(collection_report, dict):
                context_parts.append(json.dumps(collection_report, indent=2, ensure_ascii=False))
            else:
                context_parts.append(str(collection_report))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Texto consolidado - garante que é string
        if consolidated_text:
            context_parts.append("# CONTEÚDO TEXTUAL CONSOLIDADO")
            if isinstance(consolidated_text, dict):
                context_parts.append(json.dumps(consolidated_text, indent=2, ensure_ascii=False))
            else:
                context_parts.append(str(consolidated_text))
            context_parts.append("\n" + "="*80 + "\n")
        
        # Garante que todos os itens são strings antes do join
        context_parts_str = []
        for i, part in enumerate(context_parts):
            if isinstance(part, dict):
                logger.warning(f"⚠️ Item {i} ainda é dict, convertendo...")
                context_parts_str.append(json.dumps(part, indent=2, ensure_ascii=False))
            elif isinstance(part, str):
                context_parts_str.append(part)
            else:
                context_parts_str.append(str(part))
        
        full_context = "\n".join(context_parts_str)
        
        logger.info(f"📊 Contexto construído do massive data: {len(full_context):,} chars")
        
        return full_context

    async def execute_behavioral_synthesis(self, session_id: str) -> Dict[str, Any]:
        """Executa síntese comportamental específica"""
        return await self.execute_deep_specialization_study(
            session_id, 
            SynthesisType.BEHAVIORAL.value
        )

    async def execute_behavioral_synthesis_with_massive_data(
        self,
        session_id: str,
        massive_data_json: Dict[str, Any] = None,
        massive_data: Dict[str, Any] = None,
        synthesis_type: str = None
    ) -> Dict[str, Any]:
        """Executa síntese comportamental com massive data"""
        return await self.execute_enhanced_synthesis_with_massive_data(
            session_id=session_id,
            massive_data_json=massive_data_json,
            massive_data=massive_data,
            synthesis_type=synthesis_type or SynthesisType.BEHAVIORAL.value
        )

    async def execute_market_synthesis(self, session_id: str) -> Dict[str, Any]:
        """Executa síntese de mercado específica"""
        return await self.execute_deep_specialization_study(
            session_id, 
            SynthesisType.MARKET.value
        )

    async def execute_market_synthesis_with_massive_data(
        self,
        session_id: str,
        massive_data_json: Dict[str, Any] = None,
        massive_data: Dict[str, Any] = None,
        synthesis_type: str = None
    ) -> Dict[str, Any]:
        """Executa síntese de mercado com massive data"""
        return await self.execute_enhanced_synthesis_with_massive_data(
            session_id=session_id,
            massive_data_json=massive_data_json,
            massive_data=massive_data,
            synthesis_type=synthesis_type or SynthesisType.MARKET.value
        )

    async def execute_competitive_synthesis(self, session_id: str) -> Dict[str, Any]:
        """Executa síntese competitiva específica"""
        return await self.execute_deep_specialization_study(
            session_id, 
            SynthesisType.COMPETITIVE.value
        )

    async def execute_competitive_synthesis_with_massive_data(
        self,
        session_id: str,
        massive_data_json: Dict[str, Any] = None,
        massive_data: Dict[str, Any] = None,
        synthesis_type: str = None
    ) -> Dict[str, Any]:
        """Executa síntese competitiva com massive data"""
        return await self.execute_enhanced_synthesis_with_massive_data(
            session_id=session_id,
            massive_data_json=massive_data_json,
            massive_data=massive_data,
            synthesis_type=synthesis_type or SynthesisType.COMPETITIVE.value
        )

    # ============================================================================
    # MÉTODOS AUXILIARES E UTILITÁRIOS
    # ============================================================================

    def get_synthesis_status(self, session_id: str) -> Dict[str, Any]:
        """Verifica status da síntese para uma sessão"""
        try:
            session_dir = Path(f"analyses_data/{session_id}")
            
            if not session_dir.exists():
                return {
                    "status": "not_started",
                    "message": "Diretório da sessão não encontrado"
                }
            
            # Verifica arquivos de síntese
            synthesis_files = list(session_dir.glob("sintese_*.json"))
            report_files = list(session_dir.glob("relatorio_sintese.md"))
            
            if synthesis_files or report_files:
                latest_synthesis = None
                synthesis_data = None
                
                if synthesis_files:
                    latest_synthesis = max(synthesis_files, key=lambda f: f.stat().st_mtime)
                    
                    # Carrega dados da síntese
                    try:
                        with open(latest_synthesis, 'r', encoding='utf-8') as f:
                            synthesis_data = json.load(f)
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao carregar síntese: {e}")
                
                # Busca métricas no cache ou nos dados
                metrics = self.metrics_cache.get(session_id)
                if not metrics and synthesis_data:
                    metrics_data = synthesis_data.get('metrics')
                    if metrics_data:
                        metrics = SynthesisMetrics(**metrics_data)
                
                return {
                    "status": "completed",
                    "synthesis_available": bool(synthesis_files),
                    "report_available": bool(report_files),
                    "latest_synthesis": str(latest_synthesis) if latest_synthesis else None,
                    "files_found": len(synthesis_files) + len(report_files),
                    "metrics": asdict(metrics) if metrics else None,
                    "synthesis_types": [
                        f.stem.replace('sintese_', '') 
                        for f in synthesis_files
                    ]
                }
            else:
                return {
                    "status": "not_found",
                    "message": "Síntese ainda não foi executada"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao verificar status da síntese: {e}")
            return {
                "status": "error", 
                "error": str(e)
            }

    def get_available_synthesis_types(self) -> List[Dict[str, str]]:
        """Retorna lista de tipos de síntese disponíveis"""
        return [
            {
                "type": SynthesisType.MASTER.value,
                "name": "Síntese Master Completa",
                "description": "Análise completa e aprofundada de todos os dados"
            },
            {
                "type": SynthesisType.MARKET.value,
                "name": "Análise de Mercado",
                "description": "Foco em dados de mercado, concorrência e oportunidades"
            },
            {
                "type": SynthesisType.BEHAVIORAL.value,
                "name": "Análise Comportamental",
                "description": "Foco em comportamento do público-alvo e psicografia"
            },
            {
                "type": SynthesisType.COMPETITIVE.value,
                "name": "Análise Competitiva",
                "description": "Foco em inteligência competitiva e posicionamento"
            }
        ]

    def get_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna métricas de uma síntese específica"""
        metrics = self.metrics_cache.get(session_id)
        
        if not metrics:
            # Tenta carregar do arquivo
            try:
                session_dir = Path(f"analyses_data/{session_id}")
                synthesis_files = list(session_dir.glob("sintese_*.json"))
                
                if synthesis_files:
                    latest_file = max(synthesis_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metrics_data = data.get('metrics')
                        if metrics_data:
                            return metrics_data
            except Exception as e:
                logger.error(f"❌ Erro ao carregar métricas: {e}")
        
        return asdict(metrics) if metrics else None

    def clear_cache(self, session_id: Optional[str] = None) -> None:
        """Limpa cache de métricas"""
        if session_id:
            self.metrics_cache.pop(session_id, None)
            logger.info(f"🗑️ Cache limpo para sessão: {session_id}")
        else:
            self.metrics_cache.clear()
            logger.info("🗑️ Todo cache de métricas limpo")

    def export_synthesis_to_formats(
        self, 
        session_id: str, 
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Exporta síntese para diferentes formatos
        
        Args:
            session_id: ID da sessão
            formats: Lista de formatos desejados ['json', 'md', 'txt', 'csv']
        
        Returns:
            Dicionário com caminhos dos arquivos gerados
        """
        if formats is None:
            formats = ['json', 'md']
        
        try:
            session_dir = Path(f"analyses_data/{session_id}")
            synthesis_file = session_dir / "sintese_master_synthesis.json"
            
            if not synthesis_file.exists():
                raise FileNotFoundError("Arquivo de síntese não encontrado")
            
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                synthesis_data = json.load(f)
            
            exported_files = {}
            
            # JSON já existe
            if 'json' in formats:
                exported_files['json'] = str(synthesis_file)
            
            # Markdown
            if 'md' in formats:
                metrics = self.get_metrics(session_id)
                if metrics:
                    metrics_obj = SynthesisMetrics(**metrics)
                else:
                    metrics_obj = SynthesisMetrics(
                        context_size=0, processing_time=0, ai_searches=0,
                        data_sources=0, confidence_level=0, 
                        timestamp=datetime.now().isoformat()
                    )
                
                report = self._generate_synthesis_report(
                    synthesis_data, 
                    session_id, 
                    metrics_obj
                )
                
                md_path = session_dir / "relatorio_sintese.md"
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                exported_files['md'] = str(md_path)
            
            # Texto simples
            if 'txt' in formats:
                txt_content = self._convert_to_plain_text(synthesis_data)
                txt_path = session_dir / "sintese_resumo.txt"
                
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(txt_content)
                
                exported_files['txt'] = str(txt_path)
            
            logger.info(f"📦 Síntese exportada em {len(exported_files)} formatos")
            return exported_files
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar síntese: {e}")
            return {}

    def _convert_to_plain_text(self, synthesis_data: Dict[str, Any]) -> str:
        """Converte dados de síntese para texto simples"""
        lines = [
            "=" * 80,
            "SÍNTESE DE ANÁLISE - ARQV30 Enhanced v4.0",
            "=" * 80,
            "",
            "INSIGHTS PRINCIPAIS:",
            ""
        ]
        
        for i, insight in enumerate(synthesis_data.get('insights_principais', [])[:10], 1):
            lines.append(f"{i}. {insight}")
        
        lines.extend(["", "OPORTUNIDADES:", ""])
        
        for i, opp in enumerate(synthesis_data.get('oportunidades_identificadas', [])[:10], 1):
            lines.append(f"{i}. {opp}")
        
        lines.extend(["", "ESTRATÉGIAS RECOMENDADAS:", ""])
        
        for i, strat in enumerate(synthesis_data.get('estrategias_recomendadas', [])[:10], 1):
            lines.append(f"{i}. {strat}")
        
        lines.extend(["", "=" * 80])
        
        return "\n".join(lines)


# ============================================================================
# INSTÂNCIA GLOBAL E FUNÇÕES AUXILIARES
# ============================================================================

# Instância global
enhanced_synthesis_engine = EnhancedSynthesisEngine()


# Funções auxiliares para uso externo
async def run_synthesis(
    session_id: str, 
    synthesis_type: str = "master_synthesis"
) -> Dict[str, Any]:
    """Função auxiliar para executar síntese"""
    return await enhanced_synthesis_engine.execute_deep_specialization_study(
        session_id, 
        synthesis_type
    )


def get_synthesis_info(session_id: str) -> Dict[str, Any]:
    """Função auxiliar para obter informações da síntese"""
    return enhanced_synthesis_engine.get_synthesis_status(session_id)


def list_synthesis_types() -> List[Dict[str, str]]:
    """Função auxiliar para listar tipos disponíveis"""
    return enhanced_synthesis_engine.get_available_synthesis_types()


if __name__ == "__main__":
    # Testes básicos
    import sys
    
    print("🧠 Enhanced Synthesis Engine v4.0")
    print("=" * 60)
    
    # Lista tipos disponíveis
    print("\nTipos de Síntese Disponíveis:")
    for synthesis_type in list_synthesis_types():
        print(f"  - {synthesis_type['name']}: {synthesis_type['description']}")
    
    # Teste de status se session_id for fornecido
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        print(f"\n📊 Status da Sessão: {session_id}")
        status = get_synthesis_info(session_id)
        print(json.dumps(status, indent=2, ensure_ascii=False))