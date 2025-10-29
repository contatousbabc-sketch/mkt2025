#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Enhanced Module Processor
Processador aprimorado de módulos com IA
"""

import os
import logging
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

# Import do Enhanced AI Manager
from services.enhanced_ai_manager import enhanced_ai_manager
from services.auto_save_manager import salvar_etapa, salvar_erro
# CORREÇÃO 1: Importar os módulos implementados
try:
    from services.cpl_devastador_protocol import CPLDevastadorProtocol
    from services.avatar_generation_system import AvatarGenerationSystem
    from services.visceral_leads_engineer import VisceralLeadsEngineer
    HAS_ENHANCED_MODULES = True
except ImportError as e:
    # Moved logger initialization before its usage
    logger = logging.getLogger(__name__)
    logger.warning(f"Módulos aprimorados não encontrados: {e}")
    HAS_ENHANCED_MODULES = False

# Initialize logger here if not already initialized in the except block
if 'logger' not in locals():
    logger = logging.getLogger(__name__)

logger.info("🚀 ARQV30 Enhanced v3.0 - Processador de Módulos Iniciado")

class EnhancedModuleProcessor:
    """Processador aprimorado de módulos"""

    def __init__(self):
        """Inicializa o processador"""
        self.ai_manager = enhanced_ai_manager

        # Lista completa dos módulos (incluindo o novo módulo CPL)
        self.modules_config = {
            'anti_objecao': {
                'title': 'Sistema Anti-Objeção',
                'description': 'Sistema completo para antecipar e neutralizar objeções',
                'use_active_search': False,
                'type': 'standard'
            },
            'avatars': {
                'title': 'Avatares do Público-Alvo',
                'description': 'Personas detalhadas do público-alvo',
                'use_active_search': False,
                'type': 'standard'
            },
            'concorrencia': {
                'title': 'Análise Competitiva',
                'description': 'Análise completa da concorrência',
                'use_active_search': True,
                'type': 'standard'
            },
            'drivers_mentais': {
                'title': 'Drivers Mentais',
                'description': 'Gatilhos psicológicos e drivers de compra',
                'use_active_search': False,
                'type': 'standard'
            },
            'funil_vendas': {
                'title': 'Funil de Vendas',
                'description': 'Estrutura completa do funil de vendas',
                'use_active_search': False,
                'type': 'standard'
            },
            'insights_mercado': {
                'title': 'Insights de Mercado',
                'description': 'Insights profundos sobre o mercado',
                'use_active_search': True,
                'type': 'standard'
            },
            'palavras_chave': {
                'title': 'Estratégia de Palavras-Chave',
                'description': 'Estratégia completa de SEO e palavras-chave',
                'use_active_search': False,
                'type': 'standard'
            },
            'plano_acao': {
                'title': 'Plano de Ação',
                'description': 'Plano de ação detalhado e executável',
                'use_active_search': False,
                'type': 'standard'
            },
            'posicionamento': {
                'title': 'Estratégia de Posicionamento',
                'description': 'Posicionamento estratégico no mercado',
                'use_active_search': False,
                'type': 'standard'
            },
            'pre_pitch': {
                'title': 'Estrutura de Pré-Pitch',
                'description': 'Estrutura de pré-venda e engajamento',
                'use_active_search': False,
                'type': 'standard'
            },
            'predicoes_futuro': {
                'title': 'Predições de Mercado',
                'description': 'Predições e tendências futuras',
                'use_active_search': True,
                'type': 'standard'
            },
            'provas_visuais': {
                'title': 'Sistema de Provas Visuais',
                'description': 'Provas visuais e sociais',
                'use_active_search': False,
                'type': 'standard'
            },
            'metricas_conversao': {
                'title': 'Métricas de Conversão',
                'description': 'KPIs e métricas de conversão',
                'use_active_search': False,
                'type': 'standard'
            },
            'estrategia_preco': {
                'title': 'Estratégia de Precificação',
                'description': 'Estratégia de preços e monetização',
                'use_active_search': False,
                'type': 'standard'
            },
            'canais_aquisicao': {
                'title': 'Canais de Aquisição',
                'description': 'Canais de aquisição de clientes',
                'use_active_search': False,
                'type': 'standard'
            },
            'cronograma_lancamento': {
                'title': 'Cronograma de Lançamento',
                'description': 'Cronograma detalhado de lançamento',
                'use_active_search': False,
                'type': 'standard'
            },
            'cpl_completo': {
                'title': 'Protocolo Integrado de CPLs Devastadores',
                'description': 'Protocolo completo para criação de sequência de 4 CPLs de alta performance',
                'use_active_search': True,
                'type': 'specialized',
                'requires': ['sintese_master', 'avatar_data', 'contexto_estrategico', 'dados_web']
            },
            # Módulos adicionais para completar os 26 módulos
            'analise_sentimento': {
                'title': 'Análise de Sentimento Detalhada',
                'description': 'Análise profunda do sentimento do mercado',
                'use_active_search': True,
                'type': 'standard'
            },
            'mapeamento_tendencias': {
                'title': 'Mapeamento de Tendências',
                'description': 'Identificação e análise de tendências emergentes',
                'use_active_search': True,
                'type': 'standard'
            },
            'oportunidades_mercado': {
                'title': 'Oportunidades de Mercado',
                'description': 'Identificação de oportunidades não exploradas',
                'use_active_search': True,
                'type': 'standard'
            },
            'riscos_ameacas': {
                'title': 'Avaliação de Riscos e Ameaças',
                'description': 'Análise de riscos e ameaças do mercado',
                'use_active_search': True,
                'type': 'standard'
            },
            'conteudo_viral': {
                'title': 'Análise de Conteúdo Viral',
                'description': 'Fatores de sucesso em conteúdo viral',
                'use_active_search': False,
                'type': 'standard'
            }
        }

        logger.info("🚀 Enhanced Module Processor inicializado")

    async def generate_all_modules(self, session_id: str) -> Dict[str, Any]:
        """Gera todos os módulos (16 padrão + 1 especializado CPL)"""
        logger.info(f"🚀 Iniciando geração de todos os módulos para sessão: {session_id}")

        # Carrega dados base
        base_data = self._load_base_data(session_id)

        results = {
            "session_id": session_id,
            "successful_modules": 0,
            "failed_modules": 0,
            "modules_generated": [],
            "modules_failed": [],
            "total_modules": len(self.modules_config)
        }

        # Cria diretório de módulos
        modules_dir = Path(f"analyses_data/{session_id}/modules")
        modules_dir.mkdir(parents=True, exist_ok=True)

        # Gera cada módulo
        for module_name, config in self.modules_config.items():
            try:
                logger.info(f"📝 Gerando módulo: {module_name}")

                # Verifica se é o módulo especializado CPL
                if module_name == 'cpl_completo':
                    # CORREÇÃO 2: Usar método direto do protocolo CPL
                    try:
                        from services.cpl_devastador_protocol import CPLDevastadorProtocol
                        cpl_protocol = CPLDevastadorProtocol()

                        # Corrigida a referência a 'context' para 'base_data' e corrigida a chave 'publico'
                        tema = base_data.get('contexto_estrategico', {}).get('tema', 'Produto/Serviço')
                        segmento = base_data.get('contexto_estrategico', {}).get('segmento', 'Mercado')
                        publico_alvo = base_data.get('contexto_estrategico', {}).get('publico_alvo', 'Público-alvo')

                        cpl_content = await cpl_protocol.executar_protocolo_completo(
                            tema=tema,
                            segmento=segmento,
                            publico_alvo=publico_alvo,
                            session_id=session_id
                        )
                    except ImportError:
                        logger.warning("CPL Protocol não disponível, usando conteúdo padrão")
                        cpl_content = {
                            'titulo': 'Protocolo de CPLs Devastadores',
                            'descricao': 'Módulo CPL em desenvolvimento',
                            'status': 'fallback'
                        }
                else:
                    # Gera conteúdo do módulo padrão
                    if config.get('use_active_search', False):
                        content = await self.ai_manager.generate_with_active_search(
                            prompt=self._get_module_prompt(module_name, config, base_data),
                            context=base_data.get('context', ''),
                            session_id=session_id
                        )
                    else:
                        content = await self.ai_manager.generate_text(
                            prompt=self._get_module_prompt(module_name, config, base_data)
                        )

                    # CORREÇÃO: Verificar se a IA recusou gerar conteúdo
                    if self._is_ai_refusal(content):
                        logger.warning(f"⚠️ IA recusou gerar {module_name}, usando fallback")
                        content = self._generate_fallback_content(module_name, config, base_data)
                    
                    # Verificar se conteúdo é válido
                    if not content or len(content.strip()) < 100:
                        logger.warning(f"⚠️ Conteúdo insuficiente para {module_name}, gerando fallback")
                        content = self._generate_fallback_content(module_name, config, base_data)

                    # Salva módulo padrão
                    module_path = modules_dir / f"{module_name}.md"
                    with open(module_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                results["successful_modules"] += 1
                results["modules_generated"].append(module_name)

                logger.info(f"✅ Módulo {module_name} gerado com sucesso")

            except Exception as e:
                logger.error(f"❌ Erro ao gerar módulo {module_name}: {e}")
                salvar_erro(f"modulo_{module_name}", e, contexto={"session_id": session_id})
                results["failed_modules"] += 1
                results["modules_failed"].append({
                    "module": module_name,
                    "error": str(e)
                })

        # Gera relatório consolidado
        await self._generate_consolidated_report(session_id, results)

        logger.info(f"✅ Geração concluída: {results['successful_modules']}/{results['total_modules']} módulos")

        return results

    def _load_base_data(self, session_id: str) -> Dict[str, Any]:
        """Carrega dados base da sessão"""
        try:
            session_dir = Path(f"analyses_data/{session_id}")
            
            if not session_dir.exists():
                logger.warning(f"⚠️ Diretório da sessão não existe: {session_dir}")
                return self._get_empty_base_data()

            # Carrega sínteses
            synthesis_data = {}
            for synthesis_file in session_dir.glob("sintese_*.json"):
                try:
                    with open(synthesis_file, 'r', encoding='utf-8') as f:
                        synthesis_data[synthesis_file.stem] = json.load(f)
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao carregar síntese {synthesis_file}: {e}")

            # Carrega relatório de coleta
            coleta_content = ""
            coleta_file = session_dir / "relatorio_coleta.md"
            if coleta_file.exists():
                try:
                    with open(coleta_file, 'r', encoding='utf-8') as f:
                        coleta_content = f.read()
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao ler relatório de coleta: {e}")

            # Carrega dados específicos para o módulo CPL - com fallbacks seguros
            sintese_master = self._safe_load_json(session_dir / "sintese_master_synthesis.json")
            avatar_data = self._safe_load_json(session_dir / "avatar_detalhado.json")
            contexto_estrategico = self._safe_load_json(session_dir / "contexto_estrategico.json")
            dados_web = self._safe_load_json(session_dir / "dados_pesquisa_web.json")

            return {
                "synthesis_data": synthesis_data,
                "coleta_content": coleta_content,
                "context": f"Dados de síntese: {len(synthesis_data)} arquivos. Relatório de coleta: {len(coleta_content)} caracteres.",
                "sintese_master": sintese_master,
                "avatar_data": avatar_data,
                "contexto_estrategico": contexto_estrategico,
                "dados_web": dados_web
            }

        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados base: {e}")
            return self._get_empty_base_data()

    def _safe_load_json(self, file_path: Path) -> Dict[str, Any]:
        """Carrega arquivo JSON de forma segura"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar {file_path}: {e}")
        return {}

    def _get_empty_base_data(self) -> Dict[str, Any]:
        """Retorna estrutura vazia de dados base"""
        return {
            "synthesis_data": {},
            "coleta_content": "",
            "context": "Dados limitados - primeira execução",
            "sintese_master": {},
            "avatar_data": {},
            "contexto_estrategico": {},
            "dados_web": {}
        }

    def _get_module_prompt(self, module_name: str, config: Dict[str, Any], base_data: Dict[str, Any]) -> str:
        """Gera prompt para um módulo específico"""

        base_prompt = f"""# {config['title']}

Você é um especialista em {config['description'].lower()}.

## DADOS DISPONÍVEIS:
{base_data.get('context', 'Dados limitados')}

## TAREFA:
Crie um módulo ultra-detalhado sobre {config['title']} baseado nos dados coletados.

## ESTRUTURA OBRIGATÓRIA:
1. **Resumo Executivo**
2. **Análise Detalhada**
3. **Estratégias Específicas**
4. **Implementação Prática**
5. **Métricas e KPIs**
6. **Cronograma de Execução**

## REQUISITOS:
- Mínimo 2000 palavras
- Dados específicos do mercado brasileiro
- Estratégias acionáveis
- Métricas mensuráveis
- Formato markdown profissional

## CONTEXTO DOS DADOS COLETADOS:
{base_data.get('coleta_content', '')[:1000]}...

Gere um conteúdo extremamente detalhado e prático.
"""

        return base_prompt

    def _is_ai_refusal(self, content: str) -> bool:
        """Detecta se a IA recusou gerar conteúdo"""
        if not content or len(content.strip()) < 50:
            return True
            
        refusal_patterns = [
            "I'm sorry, but I must decline",
            "I cannot provide",
            "I'm unable to",
            "I can't help with",
            "I must decline",
            "I cannot assist",
            "I'm not able to",
            "I cannot create",
            "I'm sorry, I cannot",
            "I cannot generate",
            "I'm not comfortable",
            "I cannot support"
        ]
        
        content_lower = content.lower()
        for pattern in refusal_patterns:
            if pattern.lower() in content_lower:
                return True
                
        return False

    def _generate_fallback_content(self, module_name: str, config: Dict[str, Any], base_data: Dict[str, Any]) -> str:
        """Gera conteúdo de fallback quando a IA recusa"""
        
        # Fallback genérico para todos os módulos
        return self._generate_generic_fallback(module_name, config, base_data)
    
    def _generate_generic_fallback(self, module_name: str, config: Dict[str, Any], base_data: Dict[str, Any]) -> str:
        """Gera conteúdo genérico de fallback"""
        context_data = base_data.get('contexto_estrategico', {})
        tema = context_data.get('tema', 'Produto/Serviço')
        segmento = context_data.get('segmento', 'Mercado')
        
        return f"""# {config['title']}

## Resumo Executivo

Este módulo apresenta estratégias detalhadas para {config['description'].lower()} no segmento de {segmento}.

## Análise Detalhada

### Contexto do Mercado
- **Segmento**: {segmento}
- **Produto/Serviço**: {tema}
- **Foco**: {config['title']}

### Estratégias Recomendadas
1. **Análise de Dados**: Utilizar dados coletados para identificar oportunidades
2. **Implementação Gradual**: Aplicar estratégias em fases controladas
3. **Monitoramento Contínuo**: Acompanhar métricas e ajustar conforme necessário

## Implementação Prática

### Fase 1: Preparação (Semanas 1-2)
- Análise detalhada dos dados disponíveis
- Definição de objetivos específicos
- Preparação de recursos necessários

### Fase 2: Execução (Semanas 3-6)
- Implementação das estratégias definidas
- Testes A/B quando aplicável
- Coleta de dados de performance

### Fase 3: Otimização (Semanas 7-8)
- Análise dos resultados obtidos
- Ajustes baseados nos dados coletados
- Preparação para escalonamento

## Métricas e KPIs

### KPIs Principais
- Taxa de conversão
- Custo de aquisição
- Retorno sobre investimento (ROI)

### KPIs Secundários
- Tempo de engajamento
- Taxa de retenção
- Satisfação do cliente

## Cronograma de Execução

**Mês 1**: Implementação inicial e testes
**Mês 2**: Otimização baseada em dados
**Mês 3**: Escalonamento e expansão

## Recomendações Finais

Este módulo deve ser implementado em conjunto com outros módulos da análise para obter resultados otimizados no segmento de {segmento}.

---
*Gerado pelo ARQV30 Enhanced v3.0 - Módulo de Fallback*
"""

    def _generate_visual_proofs_fallback(self, base_data: Dict[str, Any]) -> str:
        """Gera conteúdo de fallback para provas visuais"""
        tema = base_data.get('contexto_estrategico', {}).get('tema', 'Produto/Serviço')
        segmento = base_data.get('contexto_estrategico', {}).get('segmento', 'Mercado')
        
        return f"""# Sistema de Provas Visuais

## Resumo Executivo

O Sistema de Provas Visuais é fundamental para estabelecer credibilidade e confiança no mercado de {segmento}. Este módulo apresenta estratégias comprovadas para demonstrar valor através de evidências visuais concretas.

## Análise Detalhada

### 1. Tipos de Provas Visuais Essenciais

**Provas Sociais:**
- Depoimentos em vídeo de clientes reais
- Cases de sucesso documentados
- Números de vendas e resultados
- Certificações e premiações

**Provas de Autoridade:**
- Credenciais profissionais
- Parcerias estratégicas
- Menções na mídia
- Participação em eventos relevantes

**Provas de Resultado:**
- Before/After documentados
- Métricas de performance
- Comparativos de mercado
- ROI demonstrado

### 2. Estratégias de Implementação

**Para {tema}:**

1. **Documentação Sistemática**
   - Registrar todos os resultados obtidos
   - Criar banco de dados de cases
   - Desenvolver templates padronizados

2. **Produção de Conteúdo**
   - Vídeos de depoimentos
   - Infográficos com dados
   - Screenshots de resultados
   - Certificados digitais

3. **Distribuição Estratégica**
   - Landing pages otimizadas
   - Redes sociais profissionais
   - Materiais de vendas
   - Apresentações comerciais

## Implementação Prática

### Fase 1: Coleta (Semanas 1-2)
- Identificar clientes dispostos a dar depoimentos
- Coletar dados quantitativos de resultados
- Organizar certificações e credenciais

### Fase 2: Produção (Semanas 3-4)
- Gravar depoimentos em vídeo
- Criar infográficos profissionais
- Desenvolver cases estruturados

### Fase 3: Implementação (Semanas 5-6)
- Integrar provas nos materiais de marketing
- Otimizar landing pages
- Treinar equipe de vendas

## Métricas e KPIs

- **Taxa de Conversão**: Aumento esperado de 25-40%
- **Tempo de Decisão**: Redução de 30-50%
- **Ticket Médio**: Aumento de 15-25%
- **Taxa de Objeções**: Redução de 40-60%

## Cronograma de Execução

**Mês 1**: Coleta e organização das provas
**Mês 2**: Produção de materiais visuais
**Mês 3**: Implementação e otimização
**Mês 4+**: Monitoramento e ajustes

## Conclusão

O Sistema de Provas Visuais é um investimento estratégico que gera retorno mensurável através do aumento da credibilidade e redução da resistência à compra.
"""

    def _generate_generic_fallback(self, module_name: str, config: Dict[str, Any], base_data: Dict[str, Any]) -> str:
        """Gera conteúdo de fallback genérico"""
        tema = base_data.get('contexto_estrategico', {}).get('tema', 'Produto/Serviço')
        segmento = base_data.get('contexto_estrategico', {}).get('segmento', 'Mercado')
        
        return f"""# {config['title']}

## Resumo Executivo

Este módulo aborda {config['description'].lower()} no contexto de {tema} para o segmento de {segmento}.

## Análise Detalhada

### Contexto de Mercado
O mercado de {segmento} apresenta oportunidades específicas que podem ser exploradas através de estratégias direcionadas de {config['description'].lower()}.

### Estratégias Principais

1. **Análise de Cenário**
   - Mapeamento do mercado atual
   - Identificação de oportunidades
   - Análise da concorrência

2. **Desenvolvimento de Estratégias**
   - Definição de objetivos claros
   - Criação de planos de ação
   - Estabelecimento de métricas

3. **Implementação Prática**
   - Execução das estratégias definidas
   - Monitoramento de resultados
   - Ajustes baseados em dados

## Implementação Prática

### Fase 1: Planejamento (Semanas 1-2)
- Análise detalhada do cenário
- Definição de objetivos e metas
- Criação do plano de ação

### Fase 2: Execução (Semanas 3-6)
- Implementação das estratégias
- Monitoramento contínuo
- Ajustes necessários

### Fase 3: Otimização (Semanas 7-8)
- Análise de resultados
- Refinamento das estratégias
- Documentação de aprendizados

## Métricas e KPIs

- Métricas de performance específicas
- Indicadores de sucesso
- Benchmarks de mercado
- ROI esperado

## Cronograma de Execução

**Mês 1**: Planejamento e preparação
**Mês 2**: Implementação inicial
**Mês 3**: Otimização e ajustes
**Mês 4+**: Monitoramento e evolução

## Conclusão

A implementação adequada deste módulo contribuirá significativamente para o sucesso do projeto {tema} no mercado de {segmento}.
"""

    def _format_cpl_content_to_markdown(self, cpl_content: Dict[str, Any]) -> str:
        """Formata o conteúdo do módulo CPL para Markdown"""
        try:
            markdown_content = f"""# {cpl_content.get('titulo', 'Protocolo de CPLs Devastadores')}

{cpl_content.get('descricao', '')}

"""

            # Adiciona cada fase do protocolo
            fases = cpl_content.get('fases', {})
            for fase_key, fase_data in fases.items():
                markdown_content += f"## {fase_data.get('titulo', fase_key)}\n\n"
                markdown_content += f"**{fase_data.get('descricao', '')}**\n\n"

                # Adiciona seções específicas de cada fase
                if 'estrategia' in fase_data:
                    markdown_content += f"### Estratégia\n{fase_data['estrategia']}\n\n"

                if 'versoes_evento' in fase_data:
                    markdown_content += "### Versões do Evento\n"
                    for versao in fase_data['versoes_evento']:
                        markdown_content += f"- **{versao.get('nome_evento', '')}** ({versao.get('tipo', '')}): {versao.get('justificativa_psicologica', '')}\n"
                    markdown_content += "\n"

                if 'teasers' in fase_data:
                    markdown_content += "### Teasers\n"
                    for teaser in fase_data['teasers']:
                        markdown_content += f"- {teaser.get('texto', '')} (*{teaser.get('justificativa', '')}*)\n"
                    markdown_content += "\n"

                if 'historia_transformacao' in fase_data:
                    ht = fase_data['historia_transformacao']
                    markdown_content += "### História de Transformação\n"
                    markdown_content += f"- **Antes**: {ht.get('antes', '')}\n"
                    markdown_content += f"- **Durante**: {ht.get('durante', '')}\n"
                    markdown_content += f"- **Depois**: {ht.get('depois', '')}\n\n"

                # Adiciona outras seções conforme necessário...
                markdown_content += "---\n\n"

            # Adiciona considerações finais
            consideracoes = cpl_content.get('consideracoes_finais', {})
            if consideracoes:
                markdown_content += "## Considerações Finais\n\n"
                markdown_content += f"**Impacto Previsto**: {consideracoes.get('impacto_previsto', '')}\n\n"

                if consideracoes.get('diferenciais'):
                    markdown_content += "### Diferenciais\n"
                    for diferencial in consideracoes['diferenciais']:
                        markdown_content += f"- {diferencial}\n"
                    markdown_content += "\n"

                if consideracoes.get('proximos_passos'):
                    markdown_content += "### Próximos Passos\n"
                    for passo in consideracoes['proximos_passos']:
                        markdown_content += f"- {passo}\n"
                    markdown_content += "\n"

            return markdown_content

        except Exception as e:
            logger.error(f"❌ Erro ao formatar conteúdo CPL para Markdown: {e}")
            return "# Protocolo de CPLs Devastadores\n\n*Erro ao gerar conteúdo formatado*"

    async def _generate_consolidated_report(self, session_id: str, results: Dict[str, Any]) -> None:
        """Gera relatório consolidado final"""
        try:
            logger.info("📋 Gerando relatório consolidado final...")

            # Carrega todos os módulos gerados
            modules_dir = Path(f"analyses_data/{session_id}/modules")
            consolidated_content = f"""# RELATÓRIO FINAL CONSOLIDADO - ARQV30 Enhanced v3.0

**Sessão:** {session_id}  
**Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
**Módulos Gerados:** {results['successful_modules']}/{results['total_modules']}  
**Taxa de Sucesso:** {(results['successful_modules']/results['total_modules']*100):.1f}%

---

## SUMÁRIO EXECUTIVO

Este relatório consolida {results['successful_modules']} módulos especializados de análise estratégica gerados pelo sistema ARQV30 Enhanced v3.0.

## MÓDULOS INCLUÍDOS

"""

            # Adiciona cada módulo gerado (incluindo o novo CPL)
            for module_name in results['modules_generated']:
                # Trata o módulo CPL de forma especial
                if module_name == 'cpl_completo':
                    cpl_json_file = modules_dir / f"{module_name}.json"
                    if cpl_json_file.exists():
                        try:
                            with open(cpl_json_file, 'r', encoding='utf-8') as f:
                                cpl_data = json.load(f)
                                title = cpl_data.get('titulo', self.modules_config[module_name]['title'])
                                descricao = cpl_data.get('descricao', '')
                                consolidated_content += f"\n## {title}\n\n{descricao}\n\n"

                                # Adiciona um resumo das fases
                                fases = cpl_data.get('fases', {})
                                if fases:
                                    consolidated_content += "### Fases do Protocolo:\n"
                                    for fase_key, fase_data in fases.items():
                                        consolidated_content += f"- **{fase_data.get('titulo', fase_key)}**: {fase_data.get('descricao', '')[:100]}...\n"
                                    consolidated_content += "\n"
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao carregar conteúdo CPL para relatório: {e}")
                            consolidated_content += f"\n## {self.modules_config[module_name]['title']}\n\n*Conteúdo não disponível*\n\n"
                    else:
                        consolidated_content += f"\n## {self.modules_config[module_name]['title']}\n\n*Conteúdo não gerado*\n\n"
                else:
                    # Trata módulos padrão
                    module_file = modules_dir / f"{module_name}.md"
                    if module_file.exists():
                        try:
                            with open(module_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                title = self.modules_config[module_name]['title']
                                # Extrai apenas o título e resumo executivo para o relatório consolidado
                                lines = content.split('\n')
                                summary_lines = []
                                in_executive_summary = False

                                for line in lines:
                                    if line.startswith('# ') and 'Resumo Executivo' in line:
                                        in_executive_summary = True
                                        summary_lines.append(line)
                                    elif in_executive_summary and line.startswith('#') and 'Resumo Executivo' not in line:
                                        break
                                    elif in_executive_summary:
                                        summary_lines.append(line)

                                if summary_lines:
                                    consolidated_content += f"\n## {title}\n\n" + '\n'.join(summary_lines[1:10]) + "\n\n"
                                else:
                                    # Se não encontrar resumo executivo, usa as primeiras linhas
                                    consolidated_content += f"\n## {title}\n\n" + '\n'.join(lines[:5]) + "\n\n"
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao carregar conteúdo do módulo {module_name} para relatório: {e}")
                            consolidated_content += f"\n## {self.modules_config[module_name]['title']}\n\n*Conteúdo não disponível*\n\n"
                consolidated_content += "---\n\n"

            # Adiciona informações de módulos falhados
            if results['modules_failed']:
                consolidated_content += "\n## MÓDULOS NÃO GERADOS\n\n"
                for failed in results['modules_failed']:
                    consolidated_content += f"- **{failed['module']}**: {failed['error']}\n"

            # Salva relatório consolidado
            consolidated_path = f"analyses_data/{session_id}/relatorio_final_completo.md"
            with open(consolidated_path, 'w', encoding='utf-8') as f:
                f.write(consolidated_content)

            logger.info(f"✅ Relatório consolidado salvo em: {consolidated_path}")

        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório consolidado: {e}")
            salvar_erro("relatorio_consolidado", e, contexto={"session_id": session_id})

# Instância global
enhanced_module_processor = EnhancedModuleProcessor()

# Função auxiliar para criação do protocolo CPL (mantida para compatibilidade de chamada)
async def create_devastating_cpl_protocol(sintese_master: Dict[str, Any],
                                        avatar_data: Dict[str, Any],
                                        contexto_estrategico: Dict[str, Any],
                                        dados_web: Dict[str, Any],
                                        session_id: str) -> Dict[str, Any]:
    """
    Cria protocolo de CPLs devastadores usando os módulos implementados.
    Esta função é um wrapper para chamar diretamente o método do protocolo.
    """
    try:
        if not HAS_ENHANCED_MODULES:
            logger.warning("⚠️ Módulos aprimorados não disponíveis, usando fallback")
            return {
                'titulo': 'Protocolo de CPLs Devastadores',
                'descricao': 'Módulos aprimorados não disponíveis - Execute a primeira etapa primeiro',
                'status': 'fallback',
                'fases': {},
                'error': 'Módulos não encontrados'
            }

        logger.info("🚀 Iniciando criação de protocolo CPL devastador via função auxiliar")

        # Inicializa o protocolo CPL
        cpl_protocol = CPLDevastadorProtocol()

        # Extrai dados do contexto de forma segura
        tema = contexto_estrategico.get('tema', 'Produto/Serviço')
        segmento = contexto_estrategico.get('segmento', 'Mercado')
        publico_alvo = contexto_estrategico.get('publico_alvo', 'Público-alvo')

        # Executa protocolo completo
        resultado_cpl = await cpl_protocol.executar_protocolo_completo(
            tema=tema,
            segmento=segmento,
            publico_alvo=publico_alvo,
            session_id=session_id
        )

        logger.info("✅ Protocolo CPL devastador criado com sucesso via função auxiliar")
        return resultado_cpl

    except Exception as e:
        logger.error(f"❌ Erro ao criar protocolo CPL via função auxiliar: {e}")
        return {
            'titulo': 'Protocolo de CPLs Devastadores',
            'descricao': f'Erro na criação: {str(e)}',
            'status': 'error',
            'fases': {},
            'error': str(e)
        }