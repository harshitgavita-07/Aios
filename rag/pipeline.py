"""
RAG Pipeline — End-to-end retrieval and generation
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path 

from .web_search import WebSearch, WebFetcher
from .processor import ContentProcessor
from .embedder import LocalEmbedder
from .vector_store import FAISSStore
from .retriever import Retriever

log = logging.getLogger("aios.rag.pipeline")


class RAGPipeline:
    """
    Complete RAG pipeline: web search → fetch → process → embed → store → retrieve.
    
    Change: End-to-end RAG pipeline
    Why:
    - Need coordinated workflow
    - Web data needs full processing
    - Results need caching
    Impact:
    - Complete RAG capability
    - Reusable web knowledge
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        
        # Initialize components
        self.web_search = WebSearch()
        self.web_fetcher = WebFetcher()
        self.processor = ContentProcessor()
        self.embedder = LocalEmbedder()
        self.store = FAISSStore(index_path=self.data_dir / "faiss_index")
        self.retriever = Retriever(self.embedder, self.store)
        
        # Knowledge cache for freshness tracking
        self._knowledge_cache: Dict[str, datetime] = {}
        self._cache_duration = timedelta(hours=24)
        
        log.info("RAGPipeline initialized")

    def research(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Research a topic using web search and RAG.
        
        Change: Dynamic knowledge acquisition
        Why:
        - Static knowledge gets stale
        - Web provides latest info
        - Need processed, searchable content
        Impact:
        - Up-to-date responses
        - Research capability
        """
        log.info(f"Researching: {query}")
        
        # Step 1: Search web
        search_results = self.web_search.search(query, num_results=max_results)
        
        if not search_results:
            log.warning("No search results found")
            return []
        
        # Step 2: Fetch content
        urls = [r["url"] for r in search_results]
        fetched = self.web_fetcher.fetch_multiple(urls)
        
        # Step 3: Process and store
        documents = []
        for result, content_data in zip(search_results, fetched):
            if content_data:
                # Clean and chunk
                clean_text = self.processor.clean_html(content_data["content"])
                chunks = self.processor.chunk_text(clean_text)
                
                for chunk in chunks:
                    doc = {
                        "content": chunk,
                        "source": "web",
                        "url": result["url"],
                        "title": result["title"],
                        "snippet": result.get("snippet", ""),
                        "timestamp": content_data["timestamp"],
                        "query": query,
                    }
                    documents.append(doc)
        
        if not documents:
            log.warning("No content extracted from search results")
            return []
        
        # Step 4: Embed and store
        embeddings = self.embedder.embed([d["content"] for d in documents])
        self.store.add_batch(embeddings, documents)
        
        # Update cache
        for doc in documents:
            self._knowledge_cache[doc["url"]] = datetime.now()
        
        log.info(f"Stored {len(documents)} chunks from {len(search_results)} web pages")
        
        # Step 5: Retrieve relevant chunks
        relevant = self.retriever.retrieve(query, k=10)
        
        return relevant

    def query(self, query: str, use_web: bool = False) -> List[Dict]:
        """
        Query the knowledge base.
        
        Change: Unified query interface
        Why:
        - Simpler API for callers
        - Optional web augmentation
        - Consistent response format
        Impact:
        - Easy integration
        - Flexible querying
        """
        if use_web:
            return self.research(query)
        else:
            return self.retriever.retrieve(query, k=5)

    def is_fresh(self, url: str) -> bool:
        """Check if cached knowledge is still fresh."""
        if url not in self._knowledge_cache:
            return False
        
        cached_time = self._knowledge_cache[url]
        return datetime.now() - cached_time < self._cache_duration

    def get_stats(self) -> Dict:
        """Get pipeline statistics."""
        return {
            "vector_store_size": self.store.count(),
            "knowledge_cache_entries": len(self._knowledge_cache),
            "cache_duration_hours": self._cache_duration.total_seconds() / 3600,
        }
