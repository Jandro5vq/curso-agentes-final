# Tavily Web Search Client
# =======================

import os
import logging
from typing import Any, Dict, List
import requests

logger = logging.getLogger(__name__)


class TavilyClient:
    """Cliente para búsqueda web y extracción de contenido usando Tavily API."""
    
    def __init__(self):
        """Inicializa el cliente Tavily."""
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        self.base_url = "https://api.tavily.com"
        
        if not self.api_key:
            logger.warning("[TavilyClient] TAVILY_API_KEY no configurado")
        else:
            logger.info("[TavilyClient] Cliente Tavily inicializado")
    
    def search_news(
        self, 
        query: str, 
        max_results: int = 5,
        include_content: bool = True,
        include_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Busca noticias y contenido web usando Tavily.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados
            include_content: Si incluir el contenido extraído
            include_images: Si incluir imágenes
            
        Returns:
            Lista de resultados con contenido extraído
        """
        if not self.api_key:
            logger.error("[TavilyClient] API key no disponible")
            return []
        
        try:
            url = f"{self.base_url}/search"
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": False,
                "include_images": include_images,
                "include_raw_content": include_content,
                "max_results": max_results,
                "include_domains": [
                    "elpais.com",
                    "elmundo.es", 
                    "abc.es",
                    "marca.com",
                    "lavanguardia.com",
                    "eleconomista.es",
                    "rtve.es"
                ]
            }
            
            logger.info(f"[TavilyClient] Buscando: '{query}'")
            
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Procesar y normalizar resultados
            processed_results = []
            for result in results:
                processed = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "description": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", ""),
                    "source": self._extract_domain(result.get("url", "")),
                    "publishedAt": "",  # Tavily no siempre proporciona fecha
                    "content": result.get("raw_content", "")[:2000] if include_content else "",
                    "score": result.get("score", 0)
                }
                processed_results.append(processed)
            
            logger.info(f"[TavilyClient] Encontrados {len(processed_results)} resultados")
            return processed_results
            
        except Exception as e:
            logger.error(f"[TavilyClient] Error en búsqueda: {e}")
            return []
    
    def get_article_content(self, url: str) -> Dict[str, Any]:
        """
        Extrae contenido completo de una URL específica.
        
        Args:
            url: URL del artículo
            
        Returns:
            Diccionario con el contenido extraído
        """
        if not self.api_key:
            logger.error("[TavilyClient] API key no disponible")
            return {"success": False, "error": "API key no configurado"}
        
        try:
            api_url = f"{self.base_url}/extract"
            
            payload = {
                "api_key": self.api_key,
                "urls": [url]
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if results:
                result = results[0]
                return {
                    "success": True,
                    "url": url,
                    "title": result.get("title", ""),
                    "content": result.get("raw_content", ""),
                    "word_count": len(result.get("raw_content", "").split())
                }
            else:
                return {"success": False, "error": "No se pudo extraer contenido"}
                
        except Exception as e:
            logger.error(f"[TavilyClient] Error extrayendo {url}: {e}")
            return {"success": False, "error": str(e)}
    
    def _extract_domain(self, url: str) -> str:
        """Extrae el dominio de una URL."""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remover 'www.' si está presente
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "Fuente desconocida"


# Singleton instance
_tavily_client = None

def get_tavily_client() -> TavilyClient:
    """Obtiene la instancia singleton del cliente Tavily."""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client