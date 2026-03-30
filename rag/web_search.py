"""
Web Search + Fetch — Dynamic knowledge acquisition
Lightweight web search and content fetching.
"""

import logging
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Optional
from datetime import datetime

log = logging.getLogger("aios.rag.web")


class WebSearch:
    """
    Web search integration for dynamic knowledge.
    
    Change: Web search capability
    Why:
    - Local models have stale knowledge
    - Need current information for research queries
    Impact:
    - Up-to-date responses
    - Research capability
    """

    def __init__(self):
        # Using Searx instances (privacy-friendly, no API key needed)
        self.searx_instances = [
            "https://search.sapti.app",  # Public Searx instance
        ]
        self.timeout = 10
        log.info("WebSearch initialized")

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search the web for relevant results.
        
        Change: Web search without API keys
        Why:
        - Keep it local-first (no external APIs)
        - Searx provides private search
        Impact:
        - Free web search
        - Privacy-preserving
        """
        results = []
        
        for instance in self.searx_instances:
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "language": "en",
                    "safesearch": 1,
                    "categories": "general",
                }
                url = f"{instance}/search?{urllib.parse.urlencode(params)}"
                
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "AIOS/2.0 (Local AI Assistant)",
                        "Accept": "application/json",
                    }
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    
                    for item in data.get("results", [])[:num_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "snippet": item.get("content", ""),
                            "source": instance,
                            "timestamp": datetime.now().isoformat(),
                        })
                
                if results:
                    break  # Success, no need to try other instances
                    
            except Exception as e:
                log.warning(f"Search failed for {instance}: {e}")
                continue
        
        log.info(f"Web search returned {len(results)} results for: {query}")
        return results


class WebFetcher:
    """
    Fetch and extract content from web pages.
    """

    def __init__(self):
        self.timeout = 15
        self.max_content_length = 50000  # 50KB limit

    def fetch(self, url: str) -> Optional[Dict]:
        """
        Fetch content from a URL.
        
        Change: Web page fetching
        Why:
        - Search results need content extraction
        - Provides full context for RAG
        Impact:
        - Rich web knowledge
        - Complete information
        """
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml",
                }
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read()[:self.max_content_length]
                
                # Try to detect encoding
                encoding = response.headers.get_content_charset() or "utf-8"
                try:
                    text = content.decode(encoding, errors="replace")
                except:
                    text = content.decode("utf-8", errors="replace")
                
                return {
                    "url": url,
                    "content": text,
                    "content_type": response.headers.get("Content-Type", ""),
                    "timestamp": datetime.now().isoformat(),
                }
                
        except Exception as e:
            log.warning(f"Failed to fetch {url}: {e}")
            return None

    def fetch_multiple(self, urls: List[str]) -> List[Dict]:
        """Fetch multiple URLs."""
        results = []
        for url in urls:
            result = self.fetch(url)
            if result:
                results.append(result)
        return results
