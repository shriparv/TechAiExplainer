from __future__ import annotations

import logging
from duckduckgo_search import DDGS

class SearchClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def search_topic(self, topic: str, max_results: int = 5) -> str:
        self.logger.info("Searching internet for topic: %s", topic)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(topic, max_results=max_results))
                self.logger.info("Found %d search results", len(results))
                
                context_parts = []
                for i, res in enumerate(results):
                    context_parts.append(f"Source {i+1} (Title: {res.get('title')}): {res.get('body')}")
                
                final_context = "\n\n".join(context_parts)
                self.logger.info("Generated context size: %d chars", len(final_context))
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
