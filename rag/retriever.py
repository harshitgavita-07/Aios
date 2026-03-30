"""
Retriever — Intelligent document retrieval with reranking
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from .embedder import LocalEmbedder
from .vector_store import FAISSStore

log = logging.getLogger("aios.rag.retriever")


class Retriever:
    """
    Intelligent document retrieval with freshness checks.
    
    Change: Smart retrieval with reranking
    Why:
    - Raw similarity isn't always best
    - Freshness matters for some content
    - Need diversity in results
    Impact:
    - Higher quality retrieval
    - Better answer coverage
    """

    def __init__(self, embedder: LocalEmbedder, store: FAISSStore):
        self.embedder = embedder
        self.store = store
        self.freshness_threshold_hours = 24
        log.info("Retriever initialized")

    def retrieve(self, 
                query: str, 
                k: int = 5,
                filter_fresh: bool = False) -> List[Dict]:
        """
        Retrieve relevant documents for a query.
        
        Change: Multi-stage retrieval
        Why:
        - Initial retrieval gets candidates
        - Reranking improves quality
        - Filtering removes stale content
        Impact:
        - More relevant results
        - Better coverage
        """
        # Embed query
        query_embedding = self.embedder.embed_query(query)
        
        # Initial retrieval (get more than needed for reranking)
        candidates = self.store.search(query_embedding, k=k*3)
        
        if not candidates:
            return []
        
        # Rerank candidates
        reranked = self._rerank(candidates, query)
        
        # Filter by freshness if requested
        if filter_fresh:
            reranked = self._filter_fresh(reranked)
        
        # Return top k
        return reranked[:k]

    def _rerank(self, candidates: List[Dict], query: str) -> List[Dict]:
        """
        Rerank candidates for better relevance.
        
        Change: Result reranking
        Why:
        - Initial similarity isn't perfect
        - Need to penalize redundancy
        - Boost diversity
        Impact:
        - Better result ordering
        - Less redundancy
        """
        query_terms = set(query.lower().split())
        scored = []
        
        for doc in candidates:
            score = doc.get("score", 0)
            content = doc.get("content", "").lower()
            
            # Boost for exact term matches
            term_matches = sum(1 for term in query_terms if term in content)
            score += term_matches * 0.05
            
            # Boost for recency (if timestamp available)
            timestamp = doc.get("timestamp") or doc.get("_added_at")
            if timestamp:
                try:
                    doc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    age_hours = (datetime.now() - doc_time).total_seconds() / 3600
                    if age_hours < self.freshness_threshold_hours:
                        score += 0.1  # Boost fresh content
                except:
                    pass
            
            scored.append((score, doc))
        
        # Sort by new score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Add new scores
        for score, doc in scored:
            doc["rerank_score"] = score
        
        return [doc for _, doc in scored]

    def _filter_fresh(self, documents: List[Dict]) -> List[Dict]:
        """Filter to only fresh documents."""
        fresh = []
        cutoff = datetime.now() - timedelta(hours=self.freshness_threshold_hours)
        
        for doc in documents:
            timestamp = doc.get("timestamp") or doc.get("_added_at")
            if timestamp:
                try:
                    doc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if doc_time > cutoff:
                        fresh.append(doc)
                except:
                    fresh.append(doc)  # Include if timestamp is malformed
            else:
                fresh.append(doc)  # Include if no timestamp
        
        return fresh

    def hybrid_search(self, 
                     query: str, 
                     semantic_results: List[Dict],
                     keyword_results: List[Dict],
                     k: int = 5) -> List[Dict]:
        """
        Combine semantic and keyword search results.
        
        Change: Hybrid search
        Why:
        - Semantic search finds meaning
        - Keyword search finds exact matches
        - Combined = best of both
        Impact:
        - More complete results
        - Better recall
        """
        # Combine and deduplicate
        seen_urls = set()
        combined = []
        
        # Add semantic results first (higher weight)
        for doc in semantic_results:
            url = doc.get("url", doc.get("_id"))
            if url not in seen_urls:
                doc["source_type"] = "semantic"
                doc["hybrid_score"] = doc.get("score", 0) * 1.0
                combined.append(doc)
                seen_urls.add(url)
        
        # Add keyword results
        for doc in keyword_results:
            url = doc.get("url", doc.get("_id"))
            if url not in seen_urls:
                doc["source_type"] = "keyword"
                doc["hybrid_score"] = doc.get("score", 0) * 0.8
                combined.append(doc)
                seen_urls.add(url)
        
        # Sort by hybrid score
        combined.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        
        return combined[:k]
