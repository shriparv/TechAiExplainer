from __future__ import annotations

import logging
import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # Fallback will use simple regex stripping
from duckduckgo_search import DDGS

class SearchClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        # Use a generic user agent to prevent 403s on some sites
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    def _fetch_url_content(self, url: str) -> str:
        try:
            self.logger.info("Fetching content from: %s", url)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            if BeautifulSoup:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Extract text from paragraphs and headers to get the main content
                elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'li'])
                text = " ".join([elem.get_text(strip=True) for elem in elements])
            else:
                # Simple fallback: strip HTML tags via regex
                import re
                text = re.sub(r'<[^>]+>', ' ', response.text)
                text = re.sub(r'\s+', ' ', text).strip()
            # Truncate to a reasonable size to avoid blowing up LLM context
            return text[:4000]
        except Exception as e:
            self.logger.warning("Failed to fetch %s: %s", url, e)
            return ""

    def search_topic(self, topic: str, max_results: int = 3) -> str:
        self.logger.info("Searching internet for topic: %s", topic)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(topic, max_results=max_results))
                self.logger.info("Found %d search results", len(results))
                
                context_parts = []
                for i, res in enumerate(results):
                    url = res.get('href')
                    snippet = res.get('body')
                    title = res.get('title')
                    
                    # Fetch actual page content
                    page_content = self._fetch_url_content(url) if url else ""
                    
                    # If page content is too short or failed, fall back to snippet
                    content_to_use = page_content if len(page_content) > 100 else snippet
                    
                    context_parts.append(f"--- Source {i+1}: {title} ---\n{content_to_use}")
                
                final_context = "\n\n".join(context_parts)
                self.logger.info("Generated raw context size: %d chars", len(final_context))
                return final_context
        except Exception as e:
            self.logger.error("Failed to perform web search: %s", e)
            return "Web search failed. Rely on internal knowledge."

    def search_news(self, topic: str, max_results: int = 3) -> str:
        self.logger.info("Searching news for topic: %s", topic)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(topic, max_results=max_results))
                
                context_parts = []
                for i, res in enumerate(results):
                    context_parts.append(f"News {i+1} ({res.get('date')}): {res.get('title')} - {res.get('body')}")
                
                return "\n\n".join(context_parts)
        except Exception as e:
            self.logger.error("Failed to perform news search: %s", e)
            return ""
