#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARQV30 Enhanced v3.0 - Chat Routes
Sistema de chat integrado com agente UBIE
"""

import logging
import json
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from typing import Dict, Any, List, Optional

# Importações locais
try:
    from ubie.agent.session_state_manager import SessionStateManager as UBIESessionManager
    from ubie.agent.conversation_memory import ConversationMemory
    from ubie.agent.agent_tools import UBIEAgentTools
    from services.enhanced_ai_manager import enhanced_ai_manager
    from services.session_persistence import session_persistence
except ImportError as e:
    logging.warning(f"Importação falhou: {e}")
    UBIESessionManager = None
    ConversationMemory = None
    UBIEAgentTools = None
    enhanced_ai_manager = None
    session_persistence = None

logger = logging.getLogger(__name__)

# Debug das importações
logger.info(f"🔍 DEBUG - UBIESessionManager: {UBIESessionManager is not None}")
logger.info(f"🔍 DEBUG - ConversationMemory: {ConversationMemory is not None}")
logger.info(f"🔍 DEBUG - UBIEAgentTools: {UBIEAgentTools is not None}")
logger.info(f"🔍 DEBUG - enhanced_ai_manager: {enhanced_ai_manager is not None}")
logger.info(f"🔍 DEBUG - session_persistence: {session_persistence is not None}")

# Cria blueprint
chat_bp = Blueprint('chat', __name__)

# Sistema de chat global
chat_sessions = {}
chat_memory = {}

class ChatAgent:
    """Agente de chat integrado com UBIE"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Inicializa componentes UBIE
        if UBIESessionManager:
            self.session_manager = UBIESessionManager()  # Singleton, sem parâmetros
            self.conversation_memory = ConversationMemory()  # Usa DB padrão
            self.agent_tools = UBIEAgentTools()
        else:
            self.session_manager = None
            self.conversation_memory = None
            self.agent_tools = None
        
        # Histórico de conversas
        self.conversation_history = []
        
        logger.info(f"🤖 ChatAgent criado para sessão: {session_id}")
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Processa mensagem do usuário e gera resposta"""
        try:
            self.last_activity = datetime.now()
            
            # Adiciona mensagem do usuário ao histórico
            user_message = {
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'context': context or {}
            }
            self.conversation_history.append(user_message)
            
            # Salva na memória de conversação se disponível
            if self.conversation_memory:
                # ConversationMemory usa save_conversation, não add_message
                pass
            
            # Processa comandos de ferramentas se detectados
            tool_result = self._process_tool_commands(message)
            
            # Gera resposta usando IA (incluindo resultado das ferramentas se houver)
            response = self._generate_response(message, context, tool_result)
            
            # Adiciona resposta do agente ao histórico
            agent_message = {
                'role': 'assistant',
                'content': response['content'],
                'timestamp': datetime.now().isoformat(),
                'metadata': response.get('metadata', {})
            }
            self.conversation_history.append(agent_message)
            
            # Salva resposta na memória
            if self.conversation_memory:
                self.conversation_memory.save_conversation(
                    self.session_id,
                    message,
                    response['content'],
                    response.get('metadata', {})
                )
            
            return {
                'success': True,
                'response': response['content'],
                'metadata': response.get('metadata', {}),
                'session_id': self.session_id,
                'timestamp': agent_message['timestamp']
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                'session_id': self.session_id
            }
    
    def _process_tool_commands(self, message: str) -> Dict[str, Any]:
        """Processa comandos de ferramentas na mensagem do usuário"""
        tool_result = None
        
        if not self.agent_tools:
            return tool_result
            
        try:
            # Detecta comandos de análise
            if any(keyword in message.lower() for keyword in ['iniciar análise', 'começar análise', 'start analysis']):
                # Extrair dados básicos da mensagem se houver
                data = {'produto': 'costura', 'message': message}  # Produto padrão baseado no contexto
                tool_result = self.agent_tools.execute_tool('start_analysis', session_id=self.session_id, data=data)
            
            # Detecta comandos de pausa
            elif any(keyword in message.lower() for keyword in ['pausar', 'pause', 'parar', 'stop']):
                if 'análise' in message.lower() or 'workflow' in message.lower():
                    tool_result = self.agent_tools.execute_tool('pause_workflow', session_id=self.session_id, reason="Pausado via comando do usuário")
            
            # Detecta comandos de retomada
            elif any(keyword in message.lower() for keyword in ['retomar', 'resume', 'continuar', 'continue']):
                if 'análise' in message.lower() or 'workflow' in message.lower():
                    tool_result = self.agent_tools.execute_tool('resume_workflow', session_id=self.session_id)
            
            # Detecta comandos de status
            elif any(keyword in message.lower() for keyword in ['status', 'situação', 'estado']):
                tool_result = self.agent_tools.execute_tool('get_system_status', session_id=self.session_id)
            
            # Detecta comandos de busca
            elif any(keyword in message.lower() for keyword in ['buscar', 'pesquisar', 'search']):
                # Extrair query da mensagem
                query = message.replace('buscar', '').replace('pesquisar', '').replace('search', '').strip()
                if query:
                    tool_result = self.agent_tools.execute_tool('trigger_search', query=query, session_id=self.session_id)
            
            # Detecta comandos de relatório
            elif any(keyword in message.lower() for keyword in ['relatório', 'report', 'gerar relatório']):
                tool_result = self.agent_tools.execute_tool('generate_report', session_id=self.session_id)
            
            # Detecta comandos de módulo específico
            elif 'executar módulo' in message.lower() or 'execute module' in message.lower():
                # Tentar extrair nome do módulo
                modules = ['avatars', 'concorrencia', 'insights_mercado', 'palavras_chave', 'posicionamento']
                module_found = None
                for module in modules:
                    if module in message.lower():
                        module_found = module
                        break
                
                if module_found:
                    tool_result = self.agent_tools.execute_tool('execute_module', 
                                                               module_name=module_found, 
                                                               session_id=self.session_id,
                                                               data={'produto': 'costura'})
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar comando de ferramenta: {e}")
            tool_result = {
                'status': 'error',
                'message': f'Erro ao executar comando: {str(e)}'
            }
        
        return tool_result
    
    def _generate_response(self, message: str, context: Dict[str, Any] = None, tool_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gera resposta usando IA integrada com cliente Gemini direto"""
        try:
            # Contexto da conversa
            conversation_context = self._build_conversation_context()
            
            # Prompt para o agente
            system_prompt = """Você é UBIE, um assistente especializado em análise de mercado e marketing digital com CONTROLE TOTAL sobre o fluxo da aplicação.
            
Suas especialidades:
- Análise de mercado e concorrência
- Estratégias de marketing digital  
- Criação de campanhas publicitárias
- Análise de dados e métricas
- Geração de insights acionáveis
- CONTROLE TOTAL do fluxo da aplicação
- Gerenciamento completo de sessões e workflows
- Execução de análises completas sob demanda
- Acesso direto a todos os módulos do sistema

FERRAMENTAS DISPONÍVEIS (CONTROLE TOTAL):
- start_analysis(session_id, data): Inicia análise completa
- pause_workflow(session_id, reason): Pausa análises em execução
- resume_workflow(session_id): Retoma análises pausadas
- get_system_status(session_id): Verifica status completo do sistema
- execute_module(module_name, session_id, data): Executa módulo específico
- get_session_data(session_id): Obtém dados completos da sessão
- update_session(session_id, updates): Atualiza dados da sessão
- trigger_search(query, session_id, search_type): Executa busca real
- generate_report(session_id, report_type): Gera relatório completo
- search(query): Busca informações
- analyze(data): Analisa dados
- generate(prompt): Gera conteúdo
- save(data, filename): Salva dados

Responda de forma:
- Profissional mas acessível
- Baseada em dados quando possível
- Com sugestões práticas e acionáveis
- Focada em resultados de negócio
- Use as ferramentas quando necessário para controlar o fluxo

Histórico da conversa:
{conversation_context}

Contexto adicional: {context}

{tool_result_text}

Mensagem do usuário: {message}"""

            # Adiciona resultado das ferramentas se houver
            tool_result_text = ""
            if tool_result:
                tool_result_text = f"RESULTADO DA FERRAMENTA EXECUTADA:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)}\n"

            prompt = system_prompt.format(
                conversation_context=conversation_context,
                context=json.dumps(context or {}, ensure_ascii=False, indent=2),
                tool_result_text=tool_result_text,
                message=message
            )
            
            # Usa enhanced_ai_manager diretamente
            if enhanced_ai_manager:
                logger.info("🚀 Usando enhanced_ai_manager com API DIRETA do Gemini")
                try:
                    response = enhanced_ai_manager.generate_response(
                        prompt=prompt,
                        max_tokens=2000,
                        temperature=0.8
                    )
                    
                    if response and response.get('success'):
                        logger.info("✅ Resposta gerada com sucesso pelo enhanced_ai_manager")
                        return {
                            'content': response['content'],
                            'metadata': {
                                'model': response.get('model', 'gemini-direct'),
                                'tokens_used': response.get('tokens_used', 0),
                                'api_key_used': response.get('api_key_used', 'gemini_1'),
                                'source': 'enhanced_ai_manager'
                            }
                        }
                    else:
                        logger.warning(f"⚠️ enhanced_ai_manager falhou: {response}")
                except Exception as e:
                    logger.error(f"❌ Erro no enhanced_ai_manager: {e}")
            else:
                logger.warning("⚠️ enhanced_ai_manager não disponível")
            
            # Fallback para resposta padrão
            return self._generate_fallback_response(message, context)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resposta: {e}")
            return self._generate_fallback_response(message, context)
    
    def _build_conversation_context(self) -> str:
        """Constrói contexto da conversa para a IA"""
        if not self.conversation_history:
            return "Nenhuma conversa anterior."
        
        # Pega as últimas 10 mensagens
        recent_messages = self.conversation_history[-10:]
        
        context_lines = []
        for msg in recent_messages:
            role = "Usuário" if msg['role'] == 'user' else "UBIE"
            context_lines.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def _generate_fallback_response(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gera resposta de fallback quando IA não está disponível"""
        
        # Respostas baseadas em palavras-chave
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['análise', 'mercado', 'concorrência']):
            response = """Entendo que você está interessado em análise de mercado! 

Para uma análise completa, posso ajudar com:
- Análise da concorrência
- Identificação de oportunidades
- Estratégias de posicionamento
- Métricas e KPIs relevantes

Você poderia me dar mais detalhes sobre seu segmento ou produto específico?"""

        elif any(word in message_lower for word in ['marketing', 'campanha', 'publicidade']):
            response = """Ótimo! Marketing digital é uma das minhas especialidades.

Posso ajudar com:
- Estratégias de marketing digital
- Criação de campanhas
- Segmentação de público
- Canais de aquisição
- Otimização de conversão

Qual é seu objetivo principal com o marketing? Aumentar vendas, gerar leads, ou fortalecer a marca?"""

        elif any(word in message_lower for word in ['dados', 'métricas', 'analytics']):
            response = """Análise de dados é fundamental para o sucesso!

Posso ajudar com:
- Definição de KPIs
- Análise de métricas
- Interpretação de dados
- Relatórios de performance
- Insights acionáveis

Que tipo de dados você gostaria de analisar?"""

        else:
            response = f"""Olá! Sou o UBIE, seu assistente especializado em análise de mercado e marketing digital.

Posso ajudar com:
🔍 Análise de mercado e concorrência
📊 Estratégias de marketing digital
📈 Análise de dados e métricas
💡 Geração de insights acionáveis

Como posso ajudar você hoje?"""

        return {
            'content': response,
            'metadata': {
                'model': 'fallback',
                'type': 'keyword_based'
            }
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retorna histórico da conversa"""
        return self.conversation_history
    
    def clear_conversation(self):
        """Limpa histórico da conversa"""
        self.conversation_history = []
        if self.conversation_memory:
            self.conversation_memory.clear_session_memory(self.session_id)
        logger.info(f"🧹 Conversa limpa para sessão: {self.session_id}")

# ===== ROTAS DO CHAT =====

@chat_bp.route('/chat/send', methods=['POST'])
def send_message():
    """Envia mensagem para o agente de chat"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON obrigatórios'
            }), 400
        
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                'success': False,
                'error': 'Mensagem obrigatória'
            }), 400
        
        session_id = data.get('session_id')
        if not session_id:
            session_id = f"chat_{int(time.time())}_{hash(message) % 10000}"
        
        context = data.get('context', {})
        
        # Cria ou recupera agente de chat
        if session_id not in chat_sessions:
            chat_sessions[session_id] = ChatAgent(session_id)
        
        agent = chat_sessions[session_id]
        
        # Processa mensagem
        response = agent.process_message(message, context)
        
        logger.info(f"💬 Mensagem processada para sessão {session_id}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'message': str(e)
        }), 500

@chat_bp.route('/chat/history/<session_id>', methods=['GET'])
def get_chat_history(session_id: str):
    """Obtém histórico de chat de uma sessão"""
    try:
        if session_id not in chat_sessions:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada',
                'history': []
            }), 404
        
        agent = chat_sessions[session_id]
        history = agent.get_conversation_history()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'history': history,
            'total_messages': len(history),
            'created_at': agent.created_at.isoformat(),
            'last_activity': agent.last_activity.isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter histórico: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@chat_bp.route('/chat/sessions', methods=['GET'])
def list_chat_sessions():
    """Lista todas as sessões de chat ativas"""
    try:
        sessions_info = []
        
        for session_id, agent in chat_sessions.items():
            sessions_info.append({
                'session_id': session_id,
                'created_at': agent.created_at.isoformat(),
                'last_activity': agent.last_activity.isoformat(),
                'message_count': len(agent.conversation_history),
                'is_active': (datetime.now() - agent.last_activity).seconds < 3600  # 1 hora
            })
        
        # Ordena por última atividade
        sessions_info.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': sessions_info,
            'total_sessions': len(sessions_info),
            'active_sessions': len([s for s in sessions_info if s['is_active']])
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar sessões: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@chat_bp.route('/chat/clear/<session_id>', methods=['POST'])
def clear_chat_session(session_id: str):
    """Limpa uma sessão de chat específica"""
    try:
        if session_id not in chat_sessions:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
        
        agent = chat_sessions[session_id]
        agent.clear_conversation()
        
        return jsonify({
            'success': True,
            'message': f'Sessão {session_id} limpa com sucesso',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar sessão: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@chat_bp.route('/chat/delete/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id: str):
    """Deleta uma sessão de chat"""
    try:
        if session_id not in chat_sessions:
            return jsonify({
                'success': False,
                'error': 'Sessão não encontrada'
            }), 404
        
        del chat_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': f'Sessão {session_id} deletada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao deletar sessão: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@chat_bp.route('/chat/status', methods=['GET'])
def chat_status():
    """Status do sistema de chat"""
    try:
        return jsonify({
            'success': True,
            'status': 'online',
            'total_sessions': len(chat_sessions),
            'active_sessions': len([s for s in chat_sessions.values() 
                                 if (datetime.now() - s.last_activity).seconds < 3600]),
            'components': {
                'ubie_session_manager': UBIESessionManager is not None,
                'conversation_memory': ConversationMemory is not None,
                'agent_tools': UBIEAgentTools is not None,
                'enhanced_ai_manager': enhanced_ai_manager is not None
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter status: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500