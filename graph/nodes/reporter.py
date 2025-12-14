"""
Reporter Node - Nodos de obtención de noticias
==============================================

Este módulo contiene los nodos que obtienen noticias:

- fetch_general_news_node: Obtiene noticias generales del día (modo daily)
- fetch_specific_news_node: Obtiene noticias sobre un tema específico (modo mini_podcast)

Ambos nodos usan el MCP de noticias (NewsClient) y devuelven
datos estructurados, no texto narrativo.
"""

from typing import Any
import logging

from ..state import NewsState
from mcps import NewsClient


logger = logging.getLogger(__name__)

# Cliente de noticias (singleton)
_news_client: NewsClient | None = None


def get_news_client() -> NewsClient:
    """Obtiene la instancia del cliente de noticias."""
    global _news_client
    if _news_client is None:
        _news_client = NewsClient()
    return _news_client


def fetch_general_news_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que obtiene noticias generales del día.
    
    Usado en el flujo 'daily' para generar el podcast diario.
    Busca las noticias más relevantes del día sin filtro de tema.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la lista de artículos obtenidos:
        {"articles": [{"title": str, "description": str, "content": str, "source": str, "url": str}, ...]}
    """
    logger.info(f"[Reporter] Obteniendo noticias generales para chat_id={state['chat_id']}")
    
    client = get_news_client()
    
    try:
        # Obtener noticias generales del día
        articles = client.fetch_general_news(
            max_articles=10,
            language="es",
            country="es"
        )
        
        logger.info(f"[Reporter] Obtenidos {len(articles)} artículos generales")
        
        # Validar estructura de artículos
        validated_articles = []
        for article in articles:
            validated = {
                "title": article.get("title", "Sin título"),
                "description": article.get("description", ""),
                "content": article.get("content", article.get("description", "")),
                "source": article.get("source", {}).get("name", "Fuente desconocida") 
                         if isinstance(article.get("source"), dict) 
                         else article.get("source", "Fuente desconocida"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", article.get("published_at", "")),
            }
            validated_articles.append(validated)
        
        return {"articles": validated_articles}
        
    except Exception as e:
        logger.error(f"[Reporter] Error obteniendo noticias generales: {e}")
        # Retornar lista vacía en caso de error
        return {"articles": []}


def fetch_specific_news_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que obtiene noticias sobre un tema específico.
    
    Usado en el flujo 'mini_podcast' para generar un podcast
    corto sobre el tema solicitado por el usuario.
    
    SIEMPRE busca noticias específicas, independientemente del contexto existente.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con la lista de artículos obtenidos:
        {"articles": [{"title": str, "description": str, "content": str, "source": str, "url": str}, ...]}
    """
    topic = state.get("user_input", "")
    
    if not topic:
        logger.warning("[Reporter] No se proporcionó tema para búsqueda específica")
        return {"articles": []}
    
    logger.info(f"[Reporter] Buscando noticias sobre: '{topic}' para chat_id={state['chat_id']}")
    
    client = get_news_client()
    
    try:
        # Obtener noticias específicas sobre el tema
        articles = client.fetch_topic_news(
            topic=topic,
            max_articles=8,
            language="es"
        )
        
        logger.info(f"[Reporter] Obtenidos {len(articles)} artículos sobre '{topic}'")
        
        # Validar estructura de artículos
        validated_articles = []
        for article in articles:
            validated = {
                "title": article.get("title", "Sin título"),
                "description": article.get("description", ""),
                "content": article.get("content", article.get("description", "")),
                "source": article.get("source", {}).get("name", "Fuente desconocida")
                         if isinstance(article.get("source"), dict)
                         else article.get("source", "Fuente desconocida"),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt", article.get("published_at", "")),
                "topic": topic,  # Marcar con el tema buscado
            }
            validated_articles.append(validated)
        
        return {"articles": validated_articles}
        
    except Exception as e:
        logger.error(f"[Reporter] Error buscando noticias sobre '{topic}': {e}")
        return {"articles": []}
