"""
News Tools - Herramientas MCP para obtención de noticias
=========================================================

Herramientas que encapsulan NewsClient para ser usadas
por agentes con tool calling.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from mcps import NewsClient

logger = logging.getLogger(__name__)

# Cliente singleton
_news_client: Optional[NewsClient] = None


def _get_client() -> NewsClient:
    """Obtiene el cliente de noticias singleton."""
    global _news_client
    if _news_client is None:
        _news_client = NewsClient()
    return _news_client


@tool
def fetch_general_news_tool(
    max_articles: int = 10,
    country: str = "es"
) -> str:
    """
    Obtiene las noticias generales más importantes del día.
    
    Usa esta herramienta cuando necesites obtener un resumen de las
    noticias más relevantes del día en España o el país especificado.
    
    Args:
        max_articles: Número máximo de artículos a obtener (default: 10)
        country: Código del país para filtrar noticias (default: "es" España)
    
    Returns:
        Texto formateado con las noticias obtenidas incluyendo título,
        fuente, fecha y descripción de cada artículo.
    """
    logger.info(f"[Tool] fetch_general_news llamado: max={max_articles}, country={country}")
    
    try:
        client = _get_client()
        articles = client.fetch_general_news(
            max_articles=max_articles,
            language="es",
            country=country
        )
        
        if not articles:
            return "No se encontraron noticias disponibles en este momento."
        
        # Formatear artículos como texto
        result_parts = [f"📰 Se encontraron {len(articles)} noticias:\n"]
        
        for i, article in enumerate(articles, 1):
            title = article.get("title", "Sin título")
            source = article.get("source", "Fuente desconocida")
            if isinstance(source, dict):
                source = source.get("name", "Fuente desconocida")
            published = article.get("publishedAt", article.get("published_at", ""))
            description = article.get("description", "")[:200]
            
            result_parts.append(
                f"\n{i}. **{title}**\n"
                f"   Fuente: {source} | Fecha: {published}\n"
                f"   {description}"
            )
        
        return "\n".join(result_parts)
        
    except Exception as e:
        logger.error(f"[Tool] Error en fetch_general_news: {e}")
        return f"Error al obtener noticias: {str(e)}"


@tool
def fetch_topic_news_tool(
    topic: str,
    max_articles: int = 5
) -> str:
    """
    Busca noticias sobre un tema específico.
    
    Usa esta herramienta cuando necesites encontrar noticias sobre
    un tema concreto como deportes, tecnología, política, etc.
    
    Args:
        topic: El tema o palabras clave para buscar (ej: "fútbol", "inteligencia artificial")
        max_articles: Número máximo de artículos a obtener (default: 5)
    
    Returns:
        Texto formateado con las noticias encontradas sobre el tema
        incluyendo título, fuente, fecha y descripción.
    """
    logger.info(f"[Tool] fetch_topic_news llamado: topic={topic}, max={max_articles}")
    
    try:
        client = _get_client()
        articles = client.fetch_topic_news(
            topic=topic,
            max_articles=max_articles
        )
        
        if not articles:
            return f"No se encontraron noticias sobre '{topic}'."
        
        result_parts = [f"🔍 Se encontraron {len(articles)} noticias sobre '{topic}':\n"]
        
        for i, article in enumerate(articles, 1):
            title = article.get("title", "Sin título")
            source = article.get("source", "Fuente desconocida")
            if isinstance(source, dict):
                source = source.get("name", "Fuente desconocida")
            published = article.get("publishedAt", article.get("published_at", ""))
            description = article.get("description", "")[:200]
            
            result_parts.append(
                f"\n{i}. **{title}**\n"
                f"   Fuente: {source} | Fecha: {published}\n"
                f"   {description}"
            )
        
        return "\n".join(result_parts)
        
    except Exception as e:
        logger.error(f"[Tool] Error en fetch_topic_news: {e}")
        return f"Error al buscar noticias sobre '{topic}': {str(e)}"


def get_news_tools() -> list:
    """Retorna todas las herramientas de noticias."""
    return [fetch_general_news_tool, fetch_topic_news_tool]
