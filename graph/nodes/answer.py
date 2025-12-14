"""
Answer Node - Generación de respuestas textuales
================================================

Este módulo contiene dos nodos de respuesta:

- answer_from_memory_node: Genera respuesta usando solo el contexto existente
- answer_with_augmentation_node: Genera respuesta usando contexto + info adicional

Ambos actualizan el historial de conversación.
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
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def _format_articles(articles: list[dict]) -> str:
    """Formatea artículos como contexto."""
    if not articles:
        return "No hay artículos disponibles."
    
    formatted = []
    for article in articles:
        formatted.append(
            f"- {article.get('title', 'Sin título')}\n"
            f"  Fuente: {article.get('source', 'Desconocida')}\n"
            f"  {article.get('description', '')}\n"
            f"  {article.get('content', '')[:300]}"
        )
    
    return "\n\n".join(formatted)


def _format_conversation(conversation: list[dict]) -> str:
    """Formatea el historial de conversación."""
    if not conversation:
        return ""
    
    formatted = []
    for msg in conversation[-6:]:  # Últimos 6 mensajes
        role = "Usuario" if msg.get("role") == "user" else "Asistente"
        formatted.append(f"{role}: {msg.get('content', '')}")
    
    return "\n".join(formatted)


def answer_from_memory_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que genera respuesta usando solo el contexto existente.
    
    Se ejecuta cuando context_sufficient es True.
    Usa los artículos del día y el historial de conversación
    para generar una respuesta informativa.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la respuesta y conversación actualizada:
        {"answer": str, "conversation": list[dict]}
    """
    user_question = state.get("user_input", "")
    articles = state.get("articles", [])
    conversation = state.get("conversation", [])
    
    logger.info(f"[Answer] Generando respuesta desde memoria para: '{user_question}'")
    
    # Preparar contexto
    articles_context = _format_articles(articles)
    conv_context = _format_conversation(conversation)
    
    system_prompt = """Eres un asistente de noticias amable y profesional.
Tu tarea es responder preguntas del usuario sobre las noticias del día.

REGLAS:
1. Responde de forma clara y concisa
2. Basa tu respuesta SOLO en la información proporcionada
3. Si no tienes información suficiente, indícalo claramente
4. Cita las fuentes cuando sea relevante
5. Mantén un tono informativo pero accesible
6. Responde en español"""

    # Construir contexto de conversación si existe
    conv_section = ""
    if conv_context:
        conv_section = f"CONVERSACIÓN PREVIA:\n{conv_context}\n\n"
    
    human_prompt = f"""NOTICIAS DEL DÍA:
{articles_context}

{conv_section}PREGUNTA DEL USUARIO:
{user_question}

Responde a la pregunta basándote en las noticias disponibles."""

    try:
        llm = _get_llm()
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        
        answer = response.content.strip()
        
        # Actualizar conversación
        updated_conversation = list(conversation)
        updated_conversation.append({"role": "user", "content": user_question})
        updated_conversation.append({"role": "assistant", "content": answer})
        
        logger.info(f"[Answer] Respuesta generada ({len(answer)} caracteres)")
        
        return {
            "answer": answer,
            "conversation": updated_conversation,
        }
        
    except Exception as e:
        logger.error(f"[Answer] Error generando respuesta: {e}")
        fallback = "Lo siento, ha ocurrido un error al procesar tu pregunta. Por favor, inténtalo de nuevo."
        
        updated_conversation = list(conversation)
        updated_conversation.append({"role": "user", "content": user_question})
        updated_conversation.append({"role": "assistant", "content": fallback})
        
        return {
            "answer": fallback,
            "conversation": updated_conversation,
        }


def answer_with_augmentation_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que genera respuesta usando contexto + información adicional.
    
    Se ejecuta cuando context_sufficient es False y tras fetch_extra_info.
    Combina los artículos del día con los artículos externos para
    generar una respuesta más completa.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la respuesta y conversación actualizada:
        {"answer": str, "conversation": list[dict]}
    """
    user_question = state.get("user_input", "")
    articles = state.get("articles", [])
    external_articles = state.get("external_articles", [])
    conversation = state.get("conversation", [])
    
    logger.info(f"[Answer] Generando respuesta con augmentación para: '{user_question}'")
    
    # Preparar contexto combinado
    daily_context = _format_articles(articles) if articles else "No hay noticias del día."
    extra_context = _format_articles(external_articles) if external_articles else ""
    conv_context = _format_conversation(conversation)
    
    system_prompt = """Eres un asistente de noticias amable y profesional.
Tu tarea es responder preguntas del usuario usando la información disponible.

REGLAS:
1. Responde de forma clara y concisa
2. Prioriza la información de las NOTICIAS DEL DÍA
3. Complementa con la INFORMACIÓN ADICIONAL si es necesario
4. Cita las fuentes cuando sea relevante
5. Si la información es limitada, indica lo que sabes y lo que no
6. Mantén un tono informativo pero accesible
7. Responde en español"""

    # Construir contexto de conversación si existe
    conv_section = ""
    if conv_context:
        conv_section = f"CONVERSACIÓN PREVIA:\n{conv_context}\n\n"
    
    human_prompt = f"""NOTICIAS DEL DÍA:
{daily_context}

INFORMACIÓN ADICIONAL ENCONTRADA:
{extra_context if extra_context else "No se encontró información adicional relevante."}

{conv_section}PREGUNTA DEL USUARIO:
{user_question}

Responde a la pregunta combinando toda la información disponible."""

    try:
        llm = _get_llm()
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        
        answer = response.content.strip()
        
        # Actualizar conversación
        updated_conversation = list(conversation)
        updated_conversation.append({"role": "user", "content": user_question})
        updated_conversation.append({"role": "assistant", "content": answer})
        
        logger.info(f"[Answer] Respuesta con augmentación generada ({len(answer)} caracteres)")
        
        return {
            "answer": answer,
            "conversation": updated_conversation,
        }
        
    except Exception as e:
        logger.error(f"[Answer] Error generando respuesta con augmentación: {e}")
        fallback = "Lo siento, no he podido encontrar información relevante sobre tu pregunta. ¿Podrías reformularla?"
        
        updated_conversation = list(conversation)
        updated_conversation.append({"role": "user", "content": user_question})
        updated_conversation.append({"role": "assistant", "content": fallback})
        
        return {
            "answer": fallback,
            "conversation": updated_conversation,
        }
