"""
MCP News Client - Cliente para obtención de noticias
====================================================

Este módulo implementa el cliente MCP de noticias que proporciona:

- fetch_general_news(): Noticias generales de actualidad
- fetch_topic_news(topic): Noticias sobre un tema específico

Utiliza NewsAPI como fuente principal con fallback a GNews y scraping.
"""

import os
import logging
from typing import Any
from datetime import datetime, timedelta
from urllib.parse import quote
from dateutil import parser as date_parser

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class NewsClient:
    """
    Cliente MCP para obtención de noticias.
    
    Fuentes de datos:
    1. NewsAPI (principal) - https://newsapi.org/
    2. GNews (fallback) - https://gnews.io/
    3. Scraping (último recurso) - Google News RSS
    """
    
    # URLs de las APIs
    NEWSAPI_BASE_URL = "https://newsapi.org/v2"
    GNEWS_BASE_URL = "https://gnews.io/api/v4"
    GOOGLE_NEWS_RSS = "https://news.google.com/rss"
    
    # Fuentes españolas para NewsAPI
    SPANISH_SOURCES = ["el-mundo", "el-pais", "marca", "abc-es"]
    
    def __init__(self):
        """Inicializa el cliente de noticias."""
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.gnews_key = os.getenv("GNEWS_KEY", "")
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        logger.info("[NewsClient] Cliente de noticias inicializado (España)")
    
    def _filter_today_articles(
        self, 
        articles: list[dict[str, Any]], 
        max_hours: int = 24,
        min_articles: int = 5
    ) -> list[dict[str, Any]]:
        """
        Filtra y ordena artículos priorizando los más recientes.
        
        IMPORTANTE: Siempre devuelve artículos, nunca una lista vacía.
        Si no hay suficientes noticias recientes, incluye las más antiguas.
        
        Args:
            articles: Lista de artículos
            max_hours: Preferencia de horas de antigüedad (default: 24)
            min_articles: Mínimo de artículos a devolver (default: 5)
            
        Returns:
            Lista ordenada por fecha, priorizando noticias recientes
        """
        if not articles:
            return []
        
        now = datetime.now()
        cutoff_time = now - timedelta(hours=max_hours)
        
        recent = []
        older = []
        
        for article in articles:
            published_str = article.get("publishedAt", "")
            if not published_str:
                # Si no tiene fecha, asumimos que es reciente
                article["_parsed_date"] = now
                recent.append(article)
                continue
            
            try:
                # Parsear fecha (soporta múltiples formatos)
                published_date = date_parser.parse(published_str)
                
                # Hacer naive si tiene timezone para comparar
                if published_date.tzinfo:
                    published_date = published_date.replace(tzinfo=None)
                
                article["_parsed_date"] = published_date
                
                if published_date >= cutoff_time:
                    recent.append(article)
                else:
                    older.append(article)
            except Exception as e:
                # Si no podemos parsear la fecha, asumimos reciente
                logger.debug(f"[NewsClient] No se pudo parsear fecha '{published_str}': {e}")
                article["_parsed_date"] = now
                recent.append(article)
        
        # Ordenar ambas listas por fecha más reciente primero
        recent.sort(key=lambda x: x.get("_parsed_date", datetime.min), reverse=True)
        older.sort(key=lambda x: x.get("_parsed_date", datetime.min), reverse=True)
        
        # Combinar: primero recientes, luego más antiguas si necesitamos más
        result = recent.copy()
        
        # Si no tenemos suficientes artículos recientes, agregar más antiguos
        if len(result) < min_articles and older:
            needed = min_articles - len(result)
            result.extend(older[:needed])
            logger.info(f"[NewsClient] Añadidos {min(needed, len(older))} artículos más antiguos para completar")
        
        # Limpiar campos temporales
        for article in result:
            article.pop("_parsed_date", None)
        
        logger.info(f"[NewsClient] Filtrado: {len(recent)} recientes + {len(result) - len(recent)} antiguos = {len(result)} total")
        return result
    
    def fetch_general_news(
        self,
        max_articles: int = 10,
        language: str = "es",
        country: str = "es"
    ) -> list[dict[str, Any]]:
        """
        Obtiene noticias generales de actualidad.
        
        Args:
            max_articles: Número máximo de artículos a obtener
            language: Código de idioma (es, en, etc.)
            country: Código de país (es, us, etc.)
            
        Returns:
            Lista de artículos con estructura:
            [{"title": str, "description": str, "content": str, 
              "source": str, "url": str, "publishedAt": str}, ...]
        """
        logger.info(f"[NewsClient] Obteniendo noticias generales ({country}, {language})")
        
        # Pedir más artículos para tener margen después de filtrar
        fetch_count = max_articles * 3
        all_articles = []
        
        # Intentar NewsAPI primero
        if self.newsapi_key:
            articles = self._fetch_from_newsapi_top_headlines(
                country=country,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
                logger.info(f"[NewsClient] NewsAPI aportó {len(articles)} artículos")
        
        # También probar GNews para tener más variedad
        if self.gnews_key and len(all_articles) < max_articles:
            articles = self._fetch_from_gnews_top(
                country=country,
                language=language,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
                logger.info(f"[NewsClient] GNews aportó {len(articles)} artículos")
        
        # Si aún no tenemos suficientes, usar Google News RSS
        if len(all_articles) < max_articles:
            articles = self._fetch_from_google_news_rss(
                topic=None,
                language=language,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
                logger.info(f"[NewsClient] Google RSS aportó {len(articles)} artículos")
        
        # Eliminar duplicados por título
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Filtrar y ordenar por fecha
        if unique_articles:
            filtered = self._filter_today_articles(unique_articles, max_hours=24, min_articles=max_articles)
            return filtered[:max_articles]
        
        # Si todo falló, devolver lo que tengamos sin filtrar
        logger.warning("[NewsClient] No se pudieron obtener noticias de ninguna fuente")
        return all_articles[:max_articles]
    
    def fetch_topic_news(
        self,
        topic: str,
        max_articles: int = 8,
        language: str = "es"
    ) -> list[dict[str, Any]]:
        """
        Obtiene noticias sobre un tema específico.
        
        Args:
            topic: Tema o palabras clave a buscar
            max_articles: Número máximo de artículos
            language: Código de idioma
            
        Returns:
            Lista de artículos relacionados con el tema
        """
        logger.info(f"[NewsClient] Buscando noticias sobre: '{topic}'")
        
        # Pedir más artículos para tener margen después de filtrar
        fetch_count = max_articles * 3
        all_articles = []
        
        # Intentar NewsAPI primero
        if self.newsapi_key:
            articles = self._fetch_from_newsapi_everything(
                query=topic,
                language=language,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
        
        # También probar GNews
        if self.gnews_key and len(all_articles) < max_articles:
            articles = self._fetch_from_gnews_search(
                query=topic,
                language=language,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
        
        # Google News RSS como fallback
        if len(all_articles) < max_articles:
            articles = self._fetch_from_google_news_rss(
                topic=topic,
                language=language,
                max_articles=fetch_count
            )
            if articles:
                all_articles.extend(articles)
        
        # Eliminar duplicados
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get("title", "").lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Filtrar y ordenar
        if unique_articles:
            filtered = self._filter_today_articles(unique_articles, max_hours=72, min_articles=max_articles)
            return filtered[:max_articles]
        
        return all_articles[:max_articles]
    
    def _fetch_from_newsapi_top_headlines(
        self,
        country: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """Obtiene titulares de NewsAPI priorizando fuentes españolas."""
        try:
            url = f"{self.NEWSAPI_BASE_URL}/top-headlines"
            
            # Si es España, usar fuentes específicas españolas
            if country == "es":
                params = {
                    "apiKey": self.newsapi_key,
                    "sources": ",".join(self.SPANISH_SOURCES),
                    "pageSize": max_articles,
                }
            else:
                params = {
                    "apiKey": self.newsapi_key,
                    "country": country,
                    "pageSize": max_articles,
                }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                logger.info(f"[NewsClient] NewsAPI retornó {len(articles)} artículos de España")
                return self._normalize_newsapi_articles(articles)
            else:
                logger.warning(f"[NewsClient] NewsAPI error: {data.get('message')}")
                # Si falla con sources, intentar con country
                return self._fetch_newsapi_by_country(country, max_articles)
                
        except Exception as e:
            logger.error(f"[NewsClient] Error en NewsAPI top-headlines: {e}")
            return []
    
    def _fetch_newsapi_by_country(
        self,
        country: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """Fallback: obtiene titulares por país."""
        try:
            url = f"{self.NEWSAPI_BASE_URL}/top-headlines"
            params = {
                "apiKey": self.newsapi_key,
                "country": country,
                "pageSize": max_articles,
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                logger.info(f"[NewsClient] NewsAPI (country) retornó {len(articles)} artículos")
                return self._normalize_newsapi_articles(articles)
            return []
        except Exception as e:
            logger.error(f"[NewsClient] Error en NewsAPI by country: {e}")
            return []
    
    def _fetch_from_newsapi_everything(
        self,
        query: str,
        language: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """Busca artículos en NewsAPI, priorizando noticias recientes."""
        try:
            url = f"{self.NEWSAPI_BASE_URL}/everything"
            
            # Buscar solo en las últimas 24-48 horas para noticias frescas
            from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
            
            params = {
                "apiKey": self.newsapi_key,
                "q": query,
                "language": language,
                "sortBy": "publishedAt",  # Ordenar por fecha de publicación
                "pageSize": max_articles,
                "from": from_date,
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                logger.info(f"[NewsClient] NewsAPI everything retornó {len(articles)} artículos")
                return self._normalize_newsapi_articles(articles)
            else:
                logger.warning(f"[NewsClient] NewsAPI error: {data.get('message')}")
                return []
                
        except Exception as e:
            logger.error(f"[NewsClient] Error en NewsAPI everything: {e}")
            return []
    
    def _fetch_from_gnews_top(
        self,
        country: str,
        language: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """Obtiene titulares de GNews."""
        try:
            url = f"{self.GNEWS_BASE_URL}/top-headlines"
            params = {
                "apikey": self.gnews_key,
                "country": country,
                "lang": language,
                "max": max_articles,
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            logger.info(f"[NewsClient] GNews retornó {len(articles)} artículos")
            return self._normalize_gnews_articles(articles)
            
        except Exception as e:
            logger.error(f"[NewsClient] Error en GNews top-headlines: {e}")
            return []
    
    def _fetch_from_gnews_search(
        self,
        query: str,
        language: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """Busca artículos en GNews."""
        try:
            url = f"{self.GNEWS_BASE_URL}/search"
            params = {
                "apikey": self.gnews_key,
                "q": query,
                "lang": language,
                "max": max_articles,
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get("articles", [])
            
            logger.info(f"[NewsClient] GNews search retornó {len(articles)} artículos")
            return self._normalize_gnews_articles(articles)
            
        except Exception as e:
            logger.error(f"[NewsClient] Error en GNews search: {e}")
            return []
    
    def _fetch_from_google_news_rss(
        self,
        topic: str | None,
        language: str,
        max_articles: int
    ) -> list[dict[str, Any]]:
        """
        Obtiene noticias del RSS de Google News.
        Fallback cuando las APIs no están disponibles.
        Usa Google News España para noticias locales.
        """
        try:
            # Usar dominio de Google News España
            base_url = "https://news.google.com/rss"
            
            # Parámetros para España
            geo_params = "hl=es-ES&gl=ES&ceid=ES:es"
            
            # Construir URL del RSS
            if topic:
                # Búsqueda por tema en España
                url = f"{base_url}/search?q={quote(topic)}&{geo_params}"
            else:
                # Noticias generales de España
                url = f"{base_url}?{geo_params}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parsear RSS con BeautifulSoup
            soup = BeautifulSoup(response.content, "lxml-xml")
            items = soup.find_all("item")[:max_articles]
            
            articles = []
            for item in items:
                article = {
                    "title": item.title.text if item.title else "",
                    "description": item.description.text if item.description else "",
                    "content": item.description.text if item.description else "",
                    "source": self._extract_source_from_title(item.title.text) if item.title else "Google News",
                    "url": item.link.text if item.link else "",
                    "publishedAt": item.pubDate.text if item.pubDate else "",
                }
                articles.append(article)
            
            logger.info(f"[NewsClient] Google News España RSS retornó {len(articles)} artículos")
            return articles
            
        except Exception as e:
            logger.error(f"[NewsClient] Error en Google News RSS: {e}")
            return []
    
    def _normalize_newsapi_articles(self, articles: list[dict]) -> list[dict[str, Any]]:
        """Normaliza artículos de NewsAPI al formato común."""
        normalized = []
        for article in articles:
            source = article.get("source", {})
            normalized.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", article.get("description", "")),
                "source": source.get("name", "Desconocida") if isinstance(source, dict) else str(source),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
            })
        return normalized
    
    def _normalize_gnews_articles(self, articles: list[dict]) -> list[dict[str, Any]]:
        """Normaliza artículos de GNews al formato común."""
        normalized = []
        for article in articles:
            source = article.get("source", {})
            normalized.append({
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", article.get("description", "")),
                "source": source.get("name", "Desconocida") if isinstance(source, dict) else str(source),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
            })
        return normalized
    
    def _extract_source_from_title(self, title: str) -> str:
        """
        Extrae el nombre de la fuente del título de Google News.
        El formato típico es: "Título - Fuente"
        """
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2:
                return parts[1].strip()
        return "Google News"
