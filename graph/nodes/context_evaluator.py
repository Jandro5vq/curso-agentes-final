"""
Context Evaluator Node - Evaluación de suficiencia del contexto
===============================================================

Este nodo evalúa si el contexto disponible (artículos del día +
historial de conversación) es suficiente para responder a la
pregunta del usuario.

SOLO responde YES o NO. No llama a MCPs ni genera contenido.
"""

from typing import Any
import logging
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import NewsState


logger = logging.getLogger(__name__)


def _get_llm() -> ChatOpenAI:
    """Obtiene la instancia del LLM configurada."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.0,  # Determinístico para evaluación
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def _format_context(articles: list[dict], conversation: list[dict]) -> str:
    """Formatea el contexto disponible para el prompt."""
    context_parts = []
    
    # Artículos del día
    if articles:
        articles_text = "\n".join([
            f"- {a.get('title', 'Sin título')}: {a.get('description', '')}"
            for a in articles
        ])
        context_parts.append(f"NOTICIAS DEL DÍA:\n{articles_text}")
    else:
        context_parts.append("NOTICIAS DEL DÍA: No hay noticias cargadas")
    
    # Historial de conversación
    if conversation:
        conv_text = "\n".join([
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in conversation[-10:]  # Últimos 10 mensajes
        ])
        context_parts.append(f"CONVERSACIÓN PREVIA:\n{conv_text}")
    
    return "\n\n".join(context_parts)


def context_evaluator_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que evalúa si el contexto es suficiente para responder.
    
    Analiza los artículos del día y el historial de conversación
    para determinar si pueden responder la pregunta del usuario.
    
    SOLO modifica el campo context_sufficient con True o False.
    NO llama a MCPs ni genera contenido.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la evaluación:
        {"context_sufficient": bool}
    """
    user_question = state.get("user_input", "")
    articles = state.get("articles", [])
    conversation = state.get("conversation", [])
    
    if not user_question:
        logger.warning("[ContextEvaluator] No hay pregunta del usuario")
        return {"context_sufficient": False}
    
    # Si no hay artículos, el contexto definitivamente es insuficiente
    if not articles:
        logger.info("[ContextEvaluator] No hay artículos - contexto insuficiente")
        return {"context_sufficient": False}
    
    logger.info(f"[ContextEvaluator] Evaluando contexto para: '{user_question}'")
    
    context = _format_context(articles, conversation)
    
    system_prompt = """Eres un evaluador de contexto. Tu tarea es determinar si la información disponible es SUFICIENTE para responder a la pregunta del usuario.

REGLAS:
1. Responde ÚNICAMENTE con "YES" o "NO"
2. Responde "YES" si el contexto contiene información relevante para responder la pregunta
3. Responde "NO" si la pregunta requiere información que no está en el contexto
4. Sé conservador: si tienes dudas, responde "NO"

NO añadas explicaciones. Solo "YES" o "NO"."""

    human_prompt = f"""CONTEXTO DISPONIBLE:
{context}

PREGUNTA DEL USUARIO:
{user_question}

¿Es el contexto SUFICIENTE para responder esta pregunta?"""

    try:
        llm = _get_llm()
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        
        answer = response.content.strip().upper()
        is_sufficient = answer.startswith("YES") or answer == "SÍ" or answer == "SI"
        
        logger.info(f"[ContextEvaluator] Respuesta: {answer} -> context_sufficient={is_sufficient}")
        
        return {"context_sufficient": is_sufficient}
        
    except Exception as e:
        logger.error(f"[ContextEvaluator] Error evaluando contexto: {e}")
        # En caso de error, asumir que el contexto es insuficiente
        # para forzar búsqueda de información adicional
        return {"context_sufficient": False}
