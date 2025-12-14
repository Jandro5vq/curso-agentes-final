# Navegación Web y Extracción de Contenido
# =======================================

import os
import logging
import asyncio
from typing import Any, Optional
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class WebScraper:
    """Cliente para navegación web y extracción de contenido."""
    
    def __init__(self):
        """Inicializa el web scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.timeout = 10
        
    def extract_article_content(self, url: str) -> dict[str, Any]:
        """
        Extrae el contenido completo de un artículo web.
        
        Args:
            url: URL del artículo a extraer
            
        Returns:
            Diccionario con el contenido extraído
        """
        try:
            logger.info(f"[WebScraper] Extrayendo contenido de: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer metadatos
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            image_url = self._extract_main_image(soup, url)
            
            # Extraer contenido principal
            content = self._extract_main_content(soup)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'author': author,
                'publish_date': publish_date,
                'image_url': image_url,
                'content': content,
                'word_count': len(content.split()) if content else 0,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"[WebScraper] Error extrayendo {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'success': False
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrae el título del artículo."""
        # Prioridad: og:title, title tag, h1
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'title',
            'h1'
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    title = elem.get('content', '').strip()
                else:
                    title = elem.get_text().strip()
                if title:
                    return title
        
        return "Sin título"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrae la descripción del artículo."""
        desc_selectors = [
            'meta[property="og:description"]',
            'meta[name="description"]',
            'meta[name="twitter:description"]'
        ]
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                desc = elem.get('content', '').strip()
                if desc:
                    return desc
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extrae el autor del artículo."""
        author_selectors = [
            'meta[name="author"]',
            '[rel="author"]',
            '.author',
            '.byline',
            '[class*="author"]'
        ]
        
        for selector in author_selectors:
            elem = soup.select_one(selector)
            if elem:
                author = elem.get('content') or elem.get_text()
                if author:
                    return author.strip()
        
        return ""
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """Extrae la fecha de publicación."""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'time[datetime]',
            '.date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            elem = soup.select_one(selector)
            if elem:
                date = elem.get('content') or elem.get('datetime') or elem.get_text()
                if date:
                    return date.strip()
        
        return ""
    
    def _extract_main_image(self, soup: BeautifulSoup, base_url: str) -> str:
        """Extrae la imagen principal del artículo."""
        img_selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            'article img',
            '.main-image img',
            '.featured-image img'
        ]
        
        for selector in img_selectors:
            elem = soup.select_one(selector)
            if elem:
                img_url = elem.get('content') or elem.get('src')
                if img_url:
                    # Convertir URL relativa a absoluta
                    if not img_url.startswith('http'):
                        img_url = urljoin(base_url, img_url)
                    return img_url
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extrae el contenido principal del artículo."""
        # Remover elementos no deseados
        for elem in soup(['script', 'style', 'nav', 'header', 'footer', 
                         'aside', '.advertisement', '.sidebar']):
            elem.decompose()
        
        # Selectores de contenido principal (orden de prioridad)
        content_selectors = [
            'article',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="body"]',
            'main',
            '.post',
            '#content'
        ]
        
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                # Extraer solo párrafos de texto
                paragraphs = elem.find_all(['p', 'h1', 'h2', 'h3', 'h4'])
                content_parts = []
                
                for p in paragraphs:
                    text = p.get_text().strip()
                    if len(text) > 20:  # Filtrar párrafos muy cortos
                        content_parts.append(text)
                
                if content_parts:
                    content = '\n\n'.join(content_parts)
                    # Limitar a 5000 caracteres para evitar contenido excesivo
                    if len(content) > 5000:
                        content = content[:5000] + "..."
                    return content
        
        # Fallback: extraer todo el texto
        return soup.get_text()[:5000]


# Singleton instance
_scraper = None

def get_web_scraper() -> WebScraper:
    """Obtiene la instancia singleton del web scraper."""
    global _scraper
    if _scraper is None:
        _scraper = WebScraper()
    return _scraper