"""
Writer Node - Generación de guiones para podcast
================================================

Este nodo genera guiones de texto pensados para locución usando OpenAI.
Controla la duración del guion según el modo:

- daily: ~3 minutos (~450 palabras a 150 palabras/minuto)
- mini_podcast: ~1 minuto (~150 palabras a 150 palabras/minuto)

El guion generado está listo para ser sintetizado por TTS.
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


def _format_articles_for_prompt(articles: list[dict]) -> str:
    """Formatea los artículos como contexto para el prompt."""
    if not articles:
        return "No hay artículos disponibles."
    
    formatted = []
    for i, article in enumerate(articles, 1):
        formatted.append(
            f"[{i}] {article.get('title', 'Sin título')}\n"
            f"    Fuente: {article.get('source', 'Desconocida')}\n"
            f"    Descripción: {article.get('description', 'Sin descripción')}\n"
            f"    Contenido: {article.get('content', '')[:500]}..."
        )
    
    return "\n\n".join(formatted)


def writer_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que genera el guion del podcast.
    
    Usa OpenAI para generar texto pensado para locución,
    controlando la duración según el modo de operación.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con el guion generado:
        {"script": str}
    """
    mode = state["mode"]
    articles = state.get("articles", [])
    user_input = state.get("user_input", "")
    
    if not articles:
        logger.warning("[Writer] No hay artículos para generar guion")
        return {"script": "No se encontraron noticias para reportar hoy."}
    
    # Determinar duración objetivo
    if mode == "daily":
        target_words = 450  # ~3 minutos
        duration_desc = "aproximadamente 3 minutos"
        intro = "el noticiario diario"
    else:  # mini_podcast
        target_words = 150  # ~1 minuto
        duration_desc = "aproximadamente 1 minuto"
        intro = f"un breve resumen sobre {user_input}"
    
    logger.info(f"[Writer] Generando guion para {mode} ({target_words} palabras objetivo)")
    
    # Construir el prompt
    system_prompt = f"""Eres un locutor profesional de noticias en español.
Tu tarea es escribir un guion de podcast informativo que dure {duration_desc}.

REGLAS IMPORTANTES:
1. El guion debe tener aproximadamente {target_words} palabras
2. Usa un tono profesional pero accesible
3. Incluye transiciones naturales entre noticias
4. Comienza con un saludo breve y termina con una despedida
5. NO uses marcadores como "[Pausa]" o "[Música]" - solo texto para leer
6. Escribe en español de España
7. Resume las noticias de forma clara y concisa
8. Menciona las fuentes cuando sea relevante

ESTRUCTURA SUGERIDA:
- Saludo e introducción breve
- Desarrollo de las noticias principales
- Despedida

El guion es para {intro}."""

    articles_context = _format_articles_for_prompt(articles)
    
    human_prompt = f"""Genera el guion del podcast basándote en estas noticias:

{articles_context}

Recuerda: aproximadamente {target_words} palabras, listo para ser leído en voz alta."""

    try:
        llm = _get_llm()
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ])
        
        script = response.content.strip()
        word_count = len(script.split())
        
        logger.info(f"[Writer] Guion generado: {word_count} palabras")
        
        return {"script": script}
        
    except Exception as e:
        logger.error(f"[Writer] Error generando guion: {e}")
        # Generar un guion de fallback básico
        fallback_script = _generate_fallback_script(articles, mode)
        return {"script": fallback_script}


def _generate_fallback_script(articles: list[dict], mode: str) -> str:
    """Genera un guion básico en caso de error con el LLM."""
    if mode == "daily":
        intro = "Buenos días, estas son las noticias más destacadas de hoy."
    else:
        intro = "Aquí tienes un breve resumen de las noticias."
    
    news_items = []
    for article in articles[:5]:  # Limitar a 5 noticias
        title = article.get("title", "")
        description = article.get("description", "")
        if title:
            news_items.append(f"{title}. {description}")
    
    body = " A continuación, ".join(news_items) if news_items else "No hay noticias disponibles."
    
    outro = "Esto ha sido todo por hoy. Hasta pronto."
    
    return f"{intro} {body} {outro}"
