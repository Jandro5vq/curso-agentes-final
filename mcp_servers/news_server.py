"""
MCP News Server - Servidor MCP Real de Noticias
================================================

Este es un servidor MCP REAL usando FastMCP que expone herramientas
para obtener noticias. Puede ser usado por:
- Claude Desktop
- Cualquier cliente MCP
- LangChain via langchain-mcp-adapters

Ejecutar como servidor:
    python -m mcp_servers.news_server

O con uvicorn:
    uvicorn mcp_servers.news_server:mcp --host 0.0.0.0 --port 8000
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Añadir el directorio padre al path para importar mcps
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear servidor MCP
mcp = FastMCP("news-service")


# =============================================================================
# HERRAMIENTAS MCP
# =============================================================================

@mcp.tool()
def fetch_general_news(
    max_articles: int = 10,
    country: str = "es",
    language: str = "es"
) -> str:
    """
    Obtiene las noticias generales más importantes del día.
    
    Busca en múltiples fuentes (NewsAPI, GNews, Google News RSS)
    y prioriza noticias de España.
    
    Args:
        max_articles: Número máximo de artículos a obtener (1-20)
        country: Código del país para filtrar noticias (es=España, us=USA, etc)
        language: Idioma de las noticias (es=español, en=inglés)
    
    Returns:
        Texto formateado con las noticias incluyendo título, fuente y descripción
    """
    from mcps import NewsClient
    
    # Validar parámetros
    max_articles = min(max(1, max_articles), 20)
    
    client = NewsClient()
    articles = client.fetch_general_news(
        max_articles=max_articles,
        language=language,
        country=country
    )
    
    if not articles:
        return "No se encontraron noticias disponibles en este momento."
    
    # Formatear resultado
    result_parts = [f"📰 {len(articles)} noticias encontradas:\n"]
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Sin título")
        source = article.get("source", "Fuente desconocida")
        if isinstance(source, dict):
            source = source.get("name", "Fuente desconocida")
        published = article.get("publishedAt", article.get("published_at", ""))
        description = article.get("description", "")[:300]
        url = article.get("url", "")
        
        result_parts.append(
            f"\n{i}. **{title}**\n"
            f"   📍 Fuente: {source}\n"
            f"   🕐 Fecha: {published}\n"
            f"   📝 {description}\n"
            f"   🔗 {url}"
        )
    
    return "\n".join(result_parts)


@mcp.tool()
def fetch_topic_news(
    topic: str,
    max_articles: int = 5,
    language: str = "es"
) -> str:
    """
    Busca noticias sobre un tema específico.
    
    Útil para encontrar información sobre deportes, tecnología,
    política, economía, o cualquier otro tema de interés.
    
    Args:
        topic: El tema o palabras clave para buscar (ej: "fútbol", "inteligencia artificial", "economía")
        max_articles: Número máximo de artículos a obtener (1-10)
        language: Idioma de las noticias (es=español, en=inglés)
    
    Returns:
        Texto formateado con las noticias encontradas sobre el tema
    """
    from mcps import NewsClient
    
    if not topic or not topic.strip():
        return "Error: Debes especificar un tema para buscar."
    
    # Validar parámetros
    max_articles = min(max(1, max_articles), 10)
    
    client = NewsClient()
    articles = client.fetch_topic_news(
        topic=topic.strip(),
        max_articles=max_articles
    )
    
    if not articles:
        return f"No se encontraron noticias sobre '{topic}'."
    
    result_parts = [f"🔍 {len(articles)} noticias sobre '{topic}':\n"]
    
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Sin título")
        source = article.get("source", "Fuente desconocida")
        if isinstance(source, dict):
            source = source.get("name", "Fuente desconocida")
        published = article.get("publishedAt", article.get("published_at", ""))
        description = article.get("description", "")[:300]
        
        result_parts.append(
            f"\n{i}. **{title}**\n"
            f"   📍 Fuente: {source}\n"
            f"   🕐 Fecha: {published}\n"
            f"   📝 {description}"
        )
    
    return "\n".join(result_parts)


@mcp.tool()
def get_news_sources() -> str:
    """
    Lista las fuentes de noticias disponibles.
    
    Returns:
        Lista de fuentes españolas e internacionales soportadas
    """
    sources = """
📰 **Fuentes de Noticias Disponibles**

🇪🇸 **Fuentes Españolas (Prioridad):**
• El País
• El Mundo
• ABC
• Marca
• La Vanguardia
• 20 Minutos

🌐 **Agregadores:**
• NewsAPI (principal)
• GNews (respaldo)
• Google News España RSS (fallback)

ℹ️ Las noticias se filtran automáticamente para mostrar 
   las más recientes y relevantes.
"""
    return sources


# =============================================================================
# RECURSOS MCP (Opcional - para contexto)
# =============================================================================

@mcp.resource("news://today")
def get_today_summary() -> str:
    """Resumen de las noticias de hoy."""
    from mcps import NewsClient
    
    client = NewsClient()
    articles = client.fetch_general_news(max_articles=5)
    
    if not articles:
        return "No hay noticias disponibles."
    
    summary = f"📅 Resumen del {datetime.now().strftime('%d/%m/%Y')}:\n\n"
    for article in articles[:5]:
        summary += f"• {article.get('title', 'Sin título')}\n"
    
    return summary


# =============================================================================
# PROMPTS MCP (Plantillas útiles)
# =============================================================================

@mcp.prompt()
def news_analyst_prompt(topic: str = "general") -> str:
    """
    Plantilla para analizar noticias como un experto.
    
    Args:
        topic: Tema a analizar (general, economía, deportes, tecnología)
    """
    return f"""Eres un analista de noticias experto especializado en {topic}.

Tu tarea es:
1. Obtener las últimas noticias usando las herramientas disponibles
2. Analizar las noticias más relevantes
3. Identificar tendencias y patrones
4. Proporcionar un análisis conciso y profesional

Usa la herramienta fetch_general_news o fetch_topic_news según necesites.
Responde siempre en español con un tono profesional pero accesible."""


@mcp.prompt()
def podcast_script_prompt() -> str:
    """Plantilla para generar guiones de podcast de noticias."""
    return """Eres un guionista de podcasts de noticias profesional.

Tu tarea es crear un guion de podcast basándote en las noticias que obtengas.

Estructura del guion:
1. INTRO: Saludo breve y presentación (~15 segundos)
2. TITULARES: Menciona las 2-3 noticias más importantes (~30 segundos)
3. DESARROLLO: Cada noticia en detalle con transiciones (~2 minutos)
4. CIERRE: Despedida y llamada a acción (~15 segundos)

Reglas:
- Escribe para ser ESCUCHADO, no leído
- Sin asteriscos ni formato markdown
- Frases cortas y claras
- Transiciones naturales entre noticias

Primero usa fetch_general_news para obtener las noticias, luego genera el guion."""


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    print("🚀 Iniciando servidor MCP de Noticias...")
    print("=" * 50)
    print("Herramientas disponibles:")
    print("  • fetch_general_news - Noticias generales")
    print("  • fetch_topic_news - Noticias por tema")
    print("  • get_news_sources - Lista de fuentes")
    print("=" * 50)
    
    # Ejecutar servidor MCP
    mcp.run()
