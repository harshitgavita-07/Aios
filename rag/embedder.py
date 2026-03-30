"""
Local Embedder — Generate embeddings without external APIs
Uses sentence-transformers or local fallback.
"""

import logging
import hashlib
from typing import List, Optional
from pathlib import Path
import json

log = logging.getLogger("aios.rag.embedder")


class LocalEmbedder:
    """
    Generate embeddings locally.
    
    Change: Local embedding generation
    Why:
    - External embedding APIs cost money
    - Local embeddings preserve privacy
    - sentence-transformers is efficient
    Impact:
    - Free embedding generation
    - Privacy-preserving
    - Fast local computation
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.embedding_dim = 384  # MiniLM-L6 output dimension
        
        # Cache for embeddings
        self._embedding_cache: dict = {}
        self._cache_dir = Path(__file__).parent.parent / "data" / "embeddings"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_model()

    def _load_model(self):
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            log.info(f"Loaded embedding model: {self.model_name}")
        except ImportError:
            log.warning("sentence_transformers not installed, using fallback")
            self._model = None

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Change: Batch embedding with caching
        Why:
        - Embedding is expensive
        - Repeated content should use cache
        - Batch processing is faster
        Impact:
        - Faster repeated queries
        - Lower CPU usage
        """
        if not texts:
            return []
        
        # Check cache first
        results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                results.append((i, self._embedding_cache[cache_key]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                results.append((i, None))
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            if self._model:
                embeddings = self._model.encode(uncached_texts, show_progress_bar=False)
            else:
                # Fallback: simple hash-based embedding (not semantically meaningful,
                # but allows the system to work without sentence-transformers)
                embeddings = self._fallback_embed(uncached_texts)
            
            for idx, emb in zip(uncached_indices, embeddings):
                cache_key = self._get_cache_key(texts[idx])
                self._embedding_cache[cache_key] = emb.tolist() if hasattr(emb, 'tolist') else emb
                results[idx] = (idx, self._embedding_cache[cache_key])
        
        return [r[1] for r in sorted(results, key=lambda x: x[0])]

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.embed([text])[0]

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def _fallback_embed(self, texts: List[str]) -> List[List[float]]:
        """
        Fallback embedding using hashing.
        Not semantically meaningful, but deterministic.
        """
        import numpy as np
        embeddings = []
        for text in texts:
            # Create deterministic pseudo-embedding
            hash_val = hashlib.md5(text.encode()).digest()
            # Expand to embedding_dim
            vec = np.array([b / 255.0 for b in hash_val])
            # Pad or truncate to embedding_dim
            if len(vec) < self.embedding_dim:
                vec = np.pad(vec, (0, self.embedding_dim - len(vec)))
            else:
                vec = vec[:self.embedding_dim]
            embeddings.append(vec.tolist())
        return embeddings

    def save_cache(self):
        """Save embedding cache to disk."""
        cache_file = self._cache_dir / "embedding_cache.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(self._embedding_cache, f)
        except Exception as e:
            log.warning(f"Failed to save embedding cache: {e}")

    def load_cache(self):
        """Load embedding cache from disk."""
        cache_file = self._cache_dir / "embedding_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    self._embedding_cache = json.load(f)
            except Exception as e:
                log.warning(f"Failed to load embedding cache: {e}")
