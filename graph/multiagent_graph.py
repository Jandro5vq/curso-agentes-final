"""
MultiAgent Graph - Grafo LangGraph con sistema multi-agente real
================================================================

Este módulo implementa el grafo de estados con:
- Agentes especializados con tool calling
- Orquestación inteligente por un agente maestro
- Herramientas MCP reales invocadas por LLMs

Arquitectura:
                         ┌─────────────────┐
                         │   START         │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   ORCHESTRATOR  │ ◄── Agente Maestro (LLM)
                         │   (Coordinator) │     Decide qué agente invocar
                         └────────┬────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │    REPORTER     │   │     WRITER      │   │    PRODUCER     │
   │   (Sub-agent)   │   │   (Sub-agent)   │   │   (Sub-agent)   │
   │                 │   │                 │   │                 │
   │ Tools:          │   │ (LLM directo)   │   │ Tools:          │
   │ - fetch_news    │   │                 │   │ - synthesize    │
   │ - fetch_topic   │   │                 │   │ - send_audio    │
   └────────┬────────┘   └────────┬────────┘   │ - send_message  │
            │                     │            └────────┬────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │      END        │
                         └─────────────────┘
"""

import logging
from typing import Literal, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .multiagent_state import MultiAgentState, create_initial_multiagent_state
from agents import (
    OrchestratorAgent,
    ReporterAgent,
    WriterAgent, 
    ProducerAgent,
)

# Guardrails para validación de entrada
from guardrails import InputGuardrail, ContentValidator

logger = logging.getLogger(__name__)

# Instancias singleton de agentes
_orchestrator: OrchestratorAgent | None = None
_reporter: ReporterAgent | None = None
_writer: WriterAgent | None = None
_producer: ProducerAgent | None = None

# Instancia singleton del guardrail de entrada
_input_guardrail: InputGuardrail | None = None


def _get_input_guardrail() -> InputGuardrail:
    """Obtiene la instancia singleton del guardrail de entrada."""
    global _input_guardrail
    if _input_guardrail is None:
        _input_guardrail = InputGuardrail()
    return _input_guardrail


def _get_agents():
    """Obtiene las instancias singleton de los agentes."""
    global _orchestrator, _reporter, _writer, _producer
    
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
        _reporter = _orchestrator.reporter
        _writer = _orchestrator.writer
        _producer = _orchestrator.producer
    
    return _orchestrator, _reporter, _writer, _producer


# =============================================================================
# NODOS DEL GRAFO
# =============================================================================

async def router_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo inicial que prepara el estado para el flujo.
    Incluye validación de entrada con guardrails.
    """
    logger.info(f"[Router] Mode: {state['mode']}, Chat: {state['chat_id']}")
    
    # Validar entrada del usuario con guardrail
    user_input = state.get("user_input")
    guardrail = _get_input_guardrail()
    
    validation_info = None
    if user_input:
        input_type = "question" if state["mode"] == "question" else "topic"
        validation_result = guardrail.validate(user_input, input_type=input_type)
        
        if not validation_result.is_valid:
            logger.warning(f"[Router] Input guardrail falló: {validation_result.message}")
            return {
                "current_agent": "router",
                "error": f"Entrada no válida: {validation_result.message}",
                "success": False,
                "agent_history": state.get("agent_history", []) + [{
                    "agent": "router",
                    "status": "failed",
                    "input": f"mode={state['mode']}, user_input={user_input[:50]}...",
                    "output": f"Guardrail: {validation_result.message}",
                    "tools_used": ["input_guardrail"],
                    "error": validation_result.message,
                }],
            }
        
        validation_info = {
            "guardrail_status": validation_result.status.value,
            "guardrail_message": validation_result.message,
        }
        logger.info(f"[Router] Input guardrail pasó: {validation_result.status.value}")
    
    return {
        "current_agent": "router",
        "agent_history": state.get("agent_history", []) + [{
            "agent": "router",
            "status": "completed",
            "input": f"mode={state['mode']}",
            "output": "Routing initiated" + (f" - Guardrail: {validation_info['guardrail_status']}" if validation_info else ""),
            "tools_used": ["input_guardrail"] if user_input else [],
            "error": None,
        }],
        "metadata": {**state.get("metadata", {}), "input_validation": validation_info} if validation_info else state.get("metadata", {}),
    }


async def reporter_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo del agente Reporter que obtiene noticias usando tools.
    """
    logger.info(f"[ReporterNode] Ejecutando con mode={state['mode']}")
    
    _, reporter, _, _ = _get_agents()
    
    # Determinar la tarea según el modo
    mode = state["mode"]
    user_input = state.get("user_input")
    
    if mode == "daily":
        # DAILY: Noticias mixtas y variadas
        task = """Esto es para el DAILY de "La IA Dice".
Obtén las 10 noticias más importantes con VARIEDAD de temas.
Incluye: tecnología, IA, ciencia, startups, política, economía, deportes, entretenimiento, etc.
El objetivo es dar un resumen completo y diverso de la actualidad."""
    elif mode == "mini_podcast":
        # PÍLDORA: Mini-podcast temático sobre un tema específico
        if user_input:
            task = f"""Esto es para una PÍLDORA de "La IA Dice" sobre: {user_input}
Busca las 5 noticias más relevantes SOLO sobre este tema específico.
Es un mini-podcast enfocado, profundiza en este tema concreto."""
        else:
            task = """Esto es para una PÍLDORA de "La IA Dice".
Obtén las 5 noticias más importantes del tema de actualidad más relevante.
Enfócate en un área temática coherente."""
    elif mode == "question":
        task = f"Busca noticias relacionadas con: {user_input}"
    else:
        task = "Obtén noticias generales del día."
    
    # Ejecutar agente con tool calling
    result = await reporter.invoke(task)
    
    step = {
        "agent": "reporter",
        "status": "completed" if result["success"] else "failed",
        "input": task,
        "output": result.get("response", ""),
        "tools_used": result.get("tools_used", []),
        "error": result.get("error"),
    }
    
    return {
        "news_content": result.get("response", ""),
        "current_agent": "reporter",
        "agent_history": state.get("agent_history", []) + [step],
        "error": result.get("error") if not result["success"] else None,
    }


async def writer_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo del agente Writer que genera guiones de podcast.
    """
    logger.info(f"[WriterNode] Generando guion para mode={state['mode']}")
    
    _, _, writer, _ = _get_agents()
    
    news_content = state.get("news_content", "")
    mode = state["mode"]
    user_input = state.get("user_input", "")
    
    # Determinar tipo de guion: daily (noticias mixtas) o pildora (temático)
    if mode == "daily":
        script_type = "daily"
        topic = None
    else:
        script_type = "pildora"
        topic = user_input if user_input else "tecnología"
    
    # Ejecutar agente
    result = await writer.invoke(
        news_content=news_content,
        script_type=script_type,
        topic=topic,
    )
    
    step = {
        "agent": "writer",
        "status": "completed" if result["success"] else "failed",
        "input": f"script_type={script_type}, news_length={len(news_content)}",
        "output": f"Script: {result.get('word_count', 0)} words",
        "tools_used": [],  # Writer no usa tools externos
        "error": result.get("error"),
    }
    
    return {
        "script": result.get("script", ""),
        "current_agent": "writer",
        "agent_history": state.get("agent_history", []) + [step],
        "error": result.get("error") if not result["success"] else None,
    }


async def producer_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo del agente Producer que genera audio y lo envía.
    """
    logger.info(f"[ProducerNode] Produciendo para chat_id={state['chat_id']}")
    
    _, _, _, producer = _get_agents()
    
    script = state.get("script", "")
    chat_id = state["chat_id"]
    mode = state["mode"]
    user_input = state.get("user_input", "")
    
    # Determinar tipo y topic
    if mode == "daily":
        podcast_type = "daily"
        topic = None
    else:
        podcast_type = "pildora"
        topic = user_input if user_input else None
    
    # Ejecutar agente con tool calling (TTS + Telegram)
    result = await producer.invoke(
        script=script,
        chat_id=chat_id,
        podcast_type=podcast_type,
        topic=topic,
    )
    
    step = {
        "agent": "producer",
        "status": "completed" if result["success"] else "failed",
        "input": f"script_length={len(script)}, chat_id={chat_id}",
        "output": result.get("response", ""),
        "tools_used": result.get("tools_used", []),
        "error": result.get("error"),
    }
    
    return {
        "audio_path": result.get("audio_path"),
        "current_agent": "producer",
        "agent_history": state.get("agent_history", []) + [step],
        "success": result["success"],
        "error": result.get("error") if not result["success"] else None,
    }


async def answer_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo que genera y envía respuesta textual (modo question).
    """
    logger.info(f"[AnswerNode] Respondiendo pregunta para chat_id={state['chat_id']}")
    
    orchestrator, _, _, producer = _get_agents()
    
    news_content = state.get("news_content", "")
    question = state.get("user_input", "")
    chat_id = state["chat_id"]
    
    # Generar respuesta usando el LLM del orchestrator
    from langchain_core.messages import SystemMessage, HumanMessage
    
    prompt = f"""
Basándote en estas noticias, responde a la pregunta del usuario de forma clara y concisa.

PREGUNTA: {question}

NOTICIAS ENCONTRADAS:
{news_content}

Genera una respuesta informativa y útil.
"""
    
    try:
        response = await orchestrator.llm.ainvoke([
            SystemMessage(content="Eres un asistente de noticias. Responde de forma clara y concisa."),
            HumanMessage(content=prompt)
        ])
        answer = response.content
    except Exception as e:
        answer = f"Error al generar respuesta: {e}"
    
    # Enviar respuesta por Telegram
    send_result = await producer.send_text_only(chat_id, answer)
    
    step = {
        "agent": "answer",
        "status": "completed" if send_result.get("success") else "failed",
        "input": question,
        "output": answer[:200] + "..." if len(answer) > 200 else answer,
        "tools_used": ["send_telegram_message_tool"],
        "error": send_result.get("error"),
    }
    
    return {
        "answer": answer,
        "current_agent": "answer",
        "agent_history": state.get("agent_history", []) + [step],
        "success": send_result.get("success", False),
    }


async def finalize_node(state: MultiAgentState) -> dict[str, Any]:
    """
    Nodo final que marca el estado como completado.
    """
    logger.info(f"[FinalizeNode] Finalizando. Success: {state.get('success')}")
    
    return {
        "current_agent": "finalize",
        "success": state.get("success", False),
    }


# =============================================================================
# FUNCIONES DE ROUTING
# =============================================================================

def route_by_mode(state: MultiAgentState) -> Literal["reporter"]:
    """
    Después del router, siempre vamos primero al reporter.
    """
    return "reporter"


def route_after_reporter(state: MultiAgentState) -> Literal["writer", "answer"]:
    """
    Después del reporter, decidimos si generar guion o responder.
    """
    mode = state["mode"]
    
    if mode == "question":
        return "answer"
    else:
        return "writer"


def route_after_writer(state: MultiAgentState) -> Literal["producer"]:
    """
    Después del writer, siempre vamos al producer.
    """
    return "producer"


def route_after_answer(state: MultiAgentState) -> Literal["finalize"]:
    """
    Después de responder, finalizamos.
    """
    return "finalize"


def route_after_producer(state: MultiAgentState) -> Literal["finalize"]:
    """
    Después del producer, finalizamos.
    """
    return "finalize"


# =============================================================================
# CREACIÓN DEL GRAFO
# =============================================================================

def create_multiagent_graph() -> StateGraph:
    """
    Crea el grafo multi-agente con tool calling real.
    
    Flujos:
    - daily/mini_podcast: router → reporter → writer → producer → finalize
    - question: router → reporter → answer → finalize
    
    Returns:
        Grafo compilado listo para ejecutar
    """
    logger.info("[MultiAgentGraph] Creando grafo multi-agente")
    
    # Crear builder
    builder = StateGraph(MultiAgentState)
    
    # Agregar nodos
    builder.add_node("router", router_node)
    builder.add_node("reporter", reporter_node)
    builder.add_node("writer", writer_node)
    builder.add_node("producer", producer_node)
    builder.add_node("answer", answer_node)
    builder.add_node("finalize", finalize_node)
    
    # Entry point
    builder.add_edge(START, "router")
    
    # Router → Reporter (siempre)
    builder.add_edge("router", "reporter")
    
    # Reporter → Writer o Answer (según mode)
    builder.add_conditional_edges(
        "reporter",
        route_after_reporter,
        {
            "writer": "writer",
            "answer": "answer",
        }
    )
    
    # Writer → Producer
    builder.add_edge("writer", "producer")
    
    # Producer → Finalize
    builder.add_edge("producer", "finalize")
    
    # Answer → Finalize
    builder.add_edge("answer", "finalize")
    
    # Finalize → END
    builder.add_edge("finalize", END)
    
    # Compilar
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    logger.info("[MultiAgentGraph] Grafo compilado exitosamente")
    
    return graph


# Singleton del grafo
_multiagent_graph = None


def get_multiagent_graph() -> StateGraph:
    """Obtiene el grafo multi-agente singleton."""
    global _multiagent_graph
    
    if _multiagent_graph is None:
        _multiagent_graph = create_multiagent_graph()
    
    return _multiagent_graph


# =============================================================================
# UTILIDADES PARA VISUALIZACIÓN
# =============================================================================

def get_graph_mermaid() -> str:
    """
    Genera el diagrama Mermaid del grafo.
    
    Returns:
        String con el código Mermaid del grafo
    """
    graph = get_multiagent_graph()
    return graph.get_graph().draw_mermaid()


def print_graph_ascii():
    """Imprime una representación ASCII del grafo."""
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║           MULTIAGENT NEWS SERVICE - LANGGRAPH                     ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║                                                                   ║
    ║                         ┌─────────┐                               ║
    ║                         │  START  │                               ║
    ║                         └────┬────┘                               ║
    ║                              │                                    ║
    ║                              ▼                                    ║
    ║                    ┌─────────────────┐                            ║
    ║                    │     ROUTER      │                            ║
    ║                    │  (Entry Point)  │                            ║
    ║                    └────────┬────────┘                            ║
    ║                              │                                    ║
    ║                              ▼                                    ║
    ║    ┌────────────────────────────────────────────────────┐         ║
    ║    │                    REPORTER                        │         ║
    ║    │              🤖 Sub-Agent with Tools               │         ║
    ║    │    ┌─────────────────────────────────────────┐     │         ║
    ║    │    │ Tools:                                  │     │         ║
    ║    │    │  • fetch_general_news_tool              │     │         ║
    ║    │    │  • fetch_topic_news_tool                │     │         ║
    ║    │    └─────────────────────────────────────────┘     │         ║
    ║    └────────────────────────┬───────────────────────────┘         ║
    ║                              │                                    ║
    ║              ┌───────────────┴───────────────┐                    ║
    ║              │                               │                    ║
    ║      [daily/mini_podcast]              [question]                 ║
    ║              │                               │                    ║
    ║              ▼                               ▼                    ║
    ║    ┌─────────────────┐             ┌─────────────────┐            ║
    ║    │     WRITER      │             │     ANSWER      │            ║
    ║    │  🤖 Sub-Agent   │             │   🤖 LLM +      │            ║
    ║    │  (LLM directo)  │             │   Telegram Tool │            ║
    ║    └────────┬────────┘             └────────┬────────┘            ║
    ║              │                               │                    ║
    ║              ▼                               │                    ║
    ║    ┌────────────────────────────────┐       │                    ║
    ║    │           PRODUCER             │       │                    ║
    ║    │      🤖 Sub-Agent with Tools   │       │                    ║
    ║    │  ┌──────────────────────────┐  │       │                    ║
    ║    │  │ Tools:                   │  │       │                    ║
    ║    │  │  • synthesize_speech     │  │       │                    ║
    ║    │  │  • send_telegram_audio   │  │       │                    ║
    ║    │  │  • send_telegram_message │  │       │                    ║
    ║    │  └──────────────────────────┘  │       │                    ║
    ║    └────────────────┬───────────────┘       │                    ║
    ║                      │                       │                    ║
    ║                      └───────────┬───────────┘                    ║
    ║                                  │                                ║
    ║                                  ▼                                ║
    ║                         ┌─────────────────┐                       ║
    ║                         │    FINALIZE     │                       ║
    ║                         └────────┬────────┘                       ║
    ║                                  │                                ║
    ║                                  ▼                                ║
    ║                            ┌─────────┐                            ║
    ║                            │   END   │                            ║
    ║                            └─────────┘                            ║
    ║                                                                   ║
    ╠═══════════════════════════════════════════════════════════════════╣
    ║  TOOLS (MCP):                                                     ║
    ║  ├── News Tools (invocadas por Reporter LLM)                      ║
    ║  │   ├── fetch_general_news_tool                                  ║
    ║  │   └── fetch_topic_news_tool                                    ║
    ║  ├── TTS Tools (invocadas por Producer LLM)                       ║
    ║  │   └── synthesize_speech_tool                                   ║
    ║  └── Telegram Tools (invocadas por Producer LLM)                  ║
    ║      ├── send_telegram_message_tool                               ║
    ║      └── send_telegram_audio_tool                                 ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
