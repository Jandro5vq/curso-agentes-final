"""
Fetch Extra Info Node - Búsqueda de información adicional
=========================================================

Este nodo se ejecuta cuando el evaluador de contexto determina
que la información disponible es insuficiente para responder
la pregunta del usuario.

Busca información adicional relacionada con la pregunta
usando el MCP de noticias.
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


def _extract_search_terms(user_input: str) -> str:
    """
    Extrae términos de búsqueda relevantes de la pregunta del usuario.
    
    Por simplicidad, usa la pregunta completa. En una implementación
    más avanzada, se podría usar NLP para extraer entidades.
    """
    # Eliminar palabras interrogativas comunes
    stop_words = {
        "qué", "que", "cuál", "cual", "cómo", "como", "dónde", "donde",
        "cuándo", "cuando", "por qué", "porque", "quién", "quien",
        "hay", "es", "son", "fue", "fueron", "ha", "han", "sobre",
        "del", "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
        "me", "puedes", "decir", "contar", "explicar", "saber", "noticias"
    }
    
    words = user_input.lower().replace("?", "").replace("¿", "").split()
    filtered = [w for w in words if w not in stop_words and len(w) > 2]
    
    # Si quedan muy pocas palabras, usar la entrada original
    if len(filtered) < 2:
        return user_input
    
    return " ".join(filtered)


def fetch_extra_info_node(state: NewsState) -> dict[str, Any]:
    """
    Nodo que busca información adicional para responder la pregunta.
    
    Se ejecuta cuando context_sufficient es False.
    Busca noticias relacionadas con la pregunta del usuario.
    
    Args:
        state: Estado actual del grafo
        
    Returns:
        Diccionario con artículos adicionales:
        {"external_articles": [{"title": str, "description": str, ...}, ...]}
    """
    user_input = state.get("user_input", "")
    
    if not user_input:
        logger.warning("[FetchExtraInfo] No hay pregunta para buscar información")
        return {"external_articles": []}
    
    # Extraer términos de búsqueda de la pregunta
    search_query = _extract_search_terms(user_input)
    
    logger.info(f"[FetchExtraInfo] Buscando información adicional: '{search_query}'")
    
    client = get_news_client()
    
    try:
        # Buscar noticias relacionadas con la pregunta
        articles = client.fetch_topic_news(
            topic=search_query,
            max_articles=5,
            language="es"
        )
        
        logger.info(f"[FetchExtraInfo] Obtenidos {len(articles)} artículos adicionales")
        
        # Validar y estructurar artículos
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
                "search_query": search_query,  # Marcar con la búsqueda realizada
            }
            validated_articles.append(validated)
        
        return {"external_articles": validated_articles}
        
    except Exception as e:
        logger.error(f"[FetchExtraInfo] Error buscando información adicional: {e}")
        return {"external_articles": []}
