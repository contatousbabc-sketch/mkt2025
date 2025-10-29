#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - CPL Completo
Módulo integrado para geração completa de CPLs devastadores
Implementa protocolo completo de 5 fases progressivas
ZERO SIMULAÇÃO - Apenas CPLs reais e funcionais
"""

import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from .enhanced_ai_manager import enhanced_ai_manager
from .cpl_generator_service import cpl_generator_service
from .cpl_protocol_1 import cpl_protocol_1
from .auto_save_manager import salvar_etapa, salvar_erro

logger = logging.getLogger(__name__)

class CPLCompleto:
    """
    Módulo completo para geração de CPLs devastadores
    Integra todos os protocolos e fases do sistema
    """
    
    def __init__(self):
        """Inicializa o módulo CPL Completo"""
        self.nome_modulo = "CPL Completo - Sistema Devastador"
        self.versao = "3.0 Enhanced"
        self.protocolos_disponiveis = [
            'cpl_protocol_1', 'cpl_protocol_2', 'cpl_protocol_3', 
            'cpl_protocol_4', 'cpl_protocol_5', 'cpl_completo'
        ]
        
        logger.info("🎯 CPL Completo inicializado - Sistema Devastador v3.0")
    
    async def gerar_cpl_devastador(
        self,
        session_id: str,
        dados_sessao: Dict[str, Any],
        tipo_cpl: str = "completo",
        configuracoes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera CPL devastador completo ou específico
        
        Args:
            session_id: ID da sessão
            dados_sessao: Dados completos da sessão
            tipo_cpl: Tipo de CPL (completo, protocol_1, protocol_2, etc.)
            configuracoes: Configurações específicas
        """
        logger.info(f"🚀 Iniciando geração de CPL {tipo_cpl} para sessão {session_id}")
        
        try:
            # Extrair dados necessários
            nicho = dados_sessao.get('nicho', 'Não especificado')
            avatar_data = dados_sessao.get('avatar_data', {})
            dados_coletados = dados_sessao.get('dados_coletados', {})
            
            # Configurações padrão
            config = configuracoes or {}
            tipo_evento = config.get('tipo_evento', 'auto')
            
            if tipo_cpl == "completo":
                # Gerar CPL completo (5 fases)
                resultado = await self._gerar_cpl_completo_5_fases(
                    session_id, nicho, avatar_data, dados_coletados, tipo_evento
                )
            elif tipo_cpl == "protocol_1":
                # Gerar apenas Protocol 1
                resultado = await self._gerar_protocol_1(
                    session_id, nicho, avatar_data, dados_coletados, tipo_evento
                )
            else:
                # Outros protocolos específicos
                resultado = await self._gerar_protocol_especifico(
                    session_id, tipo_cpl, nicho, avatar_data, dados_coletados, config
                )
            
            # Salvar resultado
            await self._salvar_resultado_cpl(session_id, tipo_cpl, resultado)
            
            logger.info(f"✅ CPL {tipo_cpl} gerado com sucesso para sessão {session_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'tipo_cpl': tipo_cpl,
                'resultado': resultado,
                'timestamp': datetime.now().isoformat(),
                'arquivos_gerados': await self._listar_arquivos_gerados(session_id, tipo_cpl)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na geração de CPL {tipo_cpl}: {e}")
            salvar_erro("cpl_completo_error", e, contexto={
                'session_id': session_id,
                'tipo_cpl': tipo_cpl
            })
            raise
    
    async def _gerar_cpl_completo_5_fases(
        self,
        session_id: str,
        nicho: str,
        avatar_data: Dict[str, Any],
        dados_coletados: Dict[str, Any],
        tipo_evento: str
    ) -> Dict[str, Any]:
        """Gera CPL completo seguindo protocolo de 5 fases"""
        
        logger.info("📐 Iniciando geração de CPL completo - 5 fases")
        
        # Usar o serviço principal de geração
        resultado_completo = await cpl_generator_service.gerar_cpl_completo(
            session_id=session_id,
            nicho=nicho,
            avatar_data=avatar_data,
            dados_coletados=dados_coletados,
            tipo_evento=tipo_evento
        )
        
        return resultado_completo
    
    async def _gerar_protocol_1(
        self,
        session_id: str,
        nicho: str,
        avatar_data: Dict[str, Any],
        dados_coletados: Dict[str, Any],
        tipo_evento: str
    ) -> Dict[str, Any]:
        """Gera apenas Protocol 1: Arquitetura do Evento Magnético"""
        
        logger.info("📐 Gerando CPL Protocol 1 - Arquitetura do Evento Magnético")
        
        resultado_protocol_1 = await cpl_protocol_1.executar_protocolo(
            session_id=session_id,
            nicho=nicho,
            avatar_data=avatar_data,
            dados_coletados=dados_coletados,
            tipo_evento=tipo_evento
        )
        
        return resultado_protocol_1
    
    async def _gerar_protocol_especifico(
        self,
        session_id: str,
        tipo_cpl: str,
        nicho: str,
        avatar_data: Dict[str, Any],
        dados_coletados: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera protocolo específico (2, 3, 4 ou 5)"""
        
        logger.info(f"📐 Gerando {tipo_cpl}")
        
        # Mapeamento de protocolos
        protocolos_map = {
            'protocol_2': 'CPL1 - A Oportunidade Paralisante',
            'protocol_3': 'CPL2 - A Transformação Impossível',
            'protocol_4': 'CPL3 - O Caminho Revolucionário',
            'protocol_5': 'CPL4 - A Decisão Inevitável'
        }
        
        nome_protocolo = protocolos_map.get(tipo_cpl, tipo_cpl)
        
        # Gerar usando IA com prompt específico
        prompt_especifico = await self._criar_prompt_protocolo_especifico(
            tipo_cpl, nome_protocolo, nicho, avatar_data, dados_coletados, config
        )
        
        resultado = await enhanced_ai_manager.generate_text(
            prompt=prompt_especifico,
            system_prompt=f"Você é o maior especialista em {nome_protocolo}. Crie conteúdo devastador e específico.",
            max_tokens=12000,
            temperature=0.8
        )
        
        return {
            'protocolo': nome_protocolo,
            'tipo_cpl': tipo_cpl,
            'conteudo': resultado,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _criar_prompt_protocolo_especifico(
        self,
        tipo_cpl: str,
        nome_protocolo: str,
        nicho: str,
        avatar_data: Dict[str, Any],
        dados_coletados: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        """Cria prompt específico para cada protocolo"""
        
        prompts_base = {
            'protocol_2': f"""
            PROTOCOLO CPL2 - A OPORTUNIDADE PARALISANTE
            
            CONTEXTO:
            - Nicho: {nicho}
            - Avatar: {json.dumps(avatar_data, ensure_ascii=False, indent=2)}
            - Dados: {json.dumps(dados_coletados, ensure_ascii=False, indent=2)}
            
            OBJETIVO CIRÚRGICO:
            Criar CPL1 que faça o avatar questionar TUDO que acreditava ser verdade 
            e gere obsessão imediata pela nova oportunidade.
            
            ESTRUTURA OBRIGATÓRIA:
            [ ] Teaser (30 segundos que valem 1 milhão)
            [ ] Apresentação (Quem é você e por que importa)
            [ ] Promessa (O que vão descobrir hoje)
            [ ] Prova/Objeção (Destruir ceticismo inicial)
            [ ] História (Jornada do herói completa)
            [ ] A Grande Oportunidade (15-20 minutos de valor puro)
            [ ] Gatilhos Psicológicos (CURIOSITY GAP, SOCIAL PROOF, AUTHORITY)
            [ ] Destruição de Objeções (10 principais)
            [ ] Antecipação (Criar loop para CPL2)
            [ ] CTA (Ação específica e urgente)
            
            ENTREGUE: Script completo de 12+ páginas com conteúdo devastador.
            """,
            
            'protocol_3': f"""
            PROTOCOLO CPL3 - A TRANSFORMAÇÃO IMPOSSÍVEL
            
            CONTEXTO:
            - Nicho: {nicho}
            - Avatar: {json.dumps(avatar_data, ensure_ascii=False, indent=2)}
            
            OBJETIVO CIRÚRGICO:
            Provar além de qualquer dúvida que pessoas comuns conseguiram 
            resultados extraordinários, criando crença inabalável.
            
            ESTRUTURA OBRIGATÓRIA:
            [ ] Teaser (Ainda mais impactante)
            [ ] 5 Cases Devastadores (Cético, Relâmpago, Pior Caso, Astronômico, Igual ao Avatar)
            [ ] Revelação Parcial do Método (20-30%)
            [ ] Construção de Esperança Sistemática
            [ ] Transição Magistral para CPL3
            
            ENTREGUE: Script completo de 12+ páginas com cases e método parcial.
            """,
            
            'protocol_4': f"""
            PROTOCOLO CPL4 - O CAMINHO REVOLUCIONÁRIO
            
            CONTEXTO:
            - Nicho: {nicho}
            - Avatar: {json.dumps(avatar_data, ensure_ascii=False, indent=2)}
            
            OBJETIVO CIRÚRGICO:
            Revelar método completo criando sensação de "FINALMENTE O MAPA!" 
            enquanto constrói urgência extrema.
            
            ESTRUTURA OBRIGATÓRIA:
            [ ] Revelação do Método Completo
            [ ] Demonstração ao Vivo
            [ ] FAQ Estratégico (20 perguntas)
            [ ] Criação de Escassez Genuína
            [ ] Setup Perfeito para Oferta
            
            ENTREGUE: Script de 12+ páginas com método completo e urgência.
            """,
            
            'protocol_5': f"""
            PROTOCOLO CPL5 - A DECISÃO INEVITÁVEL
            
            CONTEXTO:
            - Nicho: {nicho}
            - Avatar: {json.dumps(avatar_data, ensure_ascii=False, indent=2)}
            
            OBJETIVO CIRÚRGICO:
            Criar oferta tão irresistível que o "NÃO" se torne 
            logicamente impossível e emocionalmente doloroso.
            
            ESTRUTURA OBRIGATÓRIA:
            [ ] Oferta Principal (Detalhamento obsessivo)
            [ ] Stack de 5 Bônus (Velocidade, Facilidade, Segurança, Status, Surpresa)
            [ ] Precificação Psicológica
            [ ] Garantia Tripla
            [ ] Urgência Multicamada
            [ ] Fechamento Inevitável
            
            ENTREGUE: Script de 15+ páginas com oferta irrecusável.
            """
        }
        
        return prompts_base.get(tipo_cpl, f"Gere conteúdo para {nome_protocolo}")
    
    async def _salvar_resultado_cpl(
        self,
        session_id: str,
        tipo_cpl: str,
        resultado: Dict[str, Any]
    ):
        """Salva resultado do CPL em arquivos organizados"""
        
        try:
            # Criar diretório da sessão
            session_dir = Path(f"sessions/{session_id}/cpls")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Salvar JSON principal
            json_path = session_dir / f"{tipo_cpl}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, ensure_ascii=False, indent=2)
            
            # Salvar Markdown para leitura
            md_path = session_dir / f"{tipo_cpl}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {tipo_cpl.upper()}\n\n")
                f.write(f"**Sessão:** {session_id}\n")
                f.write(f"**Timestamp:** {resultado.get('timestamp', 'N/A')}\n\n")
                
                if 'resultado' in resultado:
                    f.write("## RESULTADO\n\n")
                    if isinstance(resultado['resultado'], dict):
                        for key, value in resultado['resultado'].items():
                            f.write(f"### {key.upper()}\n\n")
                            if isinstance(value, dict) and 'conteudo' in value:
                                f.write(f"{value['conteudo']}\n\n")
                            else:
                                f.write(f"{value}\n\n")
                    else:
                        f.write(f"{resultado['resultado']}\n\n")
                
                if 'conteudo' in resultado:
                    f.write("## CONTEÚDO\n\n")
                    f.write(f"{resultado['conteudo']}\n\n")
            
            logger.info(f"✅ Resultado CPL salvo em {session_dir}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar resultado CPL: {e}")
            raise
    
    async def _listar_arquivos_gerados(
        self,
        session_id: str,
        tipo_cpl: str
    ) -> List[str]:
        """Lista arquivos gerados para o CPL"""
        
        try:
            session_dir = Path(f"sessions/{session_id}/cpls")
            arquivos = []
            
            if session_dir.exists():
                for arquivo in session_dir.glob(f"{tipo_cpl}.*"):
                    arquivos.append(str(arquivo))
                
                # Adicionar arquivos relacionados se for completo
                if tipo_cpl == "completo":
                    for arquivo in session_dir.glob("*.md"):
                        if str(arquivo) not in arquivos:
                            arquivos.append(str(arquivo))
            
            return arquivos
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar arquivos: {e}")
            return []
    
    def get_protocolos_disponiveis(self) -> List[str]:
        """Retorna lista de protocolos disponíveis"""
        return self.protocolos_disponiveis
    
    def get_info_modulo(self) -> Dict[str, Any]:
        """Retorna informações do módulo"""
        return {
            'nome': self.nome_modulo,
            'versao': self.versao,
            'protocolos_disponiveis': self.protocolos_disponiveis,
            'descricao': 'Módulo completo para geração de CPLs devastadores',
            'funcionalidades': [
                'Geração de CPL completo (5 fases)',
                'Protocolos específicos individuais',
                'Arquitetura de evento magnético',
                'Scripts de CPLs devastadores',
                'Validação automática',
                'Arquivos de entrega organizados'
            ]
        }

# Instância global do módulo
cpl_completo = CPLCompleto()