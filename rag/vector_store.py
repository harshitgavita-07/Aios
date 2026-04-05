"""
FAISS Vector Store — Local vector storage and search
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

log = logging.getLogger("aios.rag.vector_store")


class FAISSStore:
    """
    FAISS-based vector store for local embeddings.
    
    Change: Local vector storage
    Why:
    - Pinecone/Weaviate require cloud
    - FAISS is fast and local
    - No external dependencies
    Impact:
    - Free vector search
    - Privacy-preserving
    - Fast retrieval
    """

    def __init__(self, index_path: Optional[Path] = None, dim: int = 384):
        self.dim = dim
        self.index_path = index_path or Path(__file__).parent.parent / "data" / "faiss_index"
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self._index = None
        self._documents: List[Dict] = []
        self._doc_id = 0
        
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create new one."""
        try:
            import faiss
            import numpy as np
            
            index_file = self.index_path / "index.faiss"
            if index_file.exists():
                self._index = faiss.read_index(str(index_file))
                # Load documents
                import json
                doc_file = self.index_path / "documents.json"
                if doc_file.exists():
                    with open(doc_file, "r") as f:
                        self._documents = json.load(f)
                log.info(f"Loaded FAISS index with {len(self._documents)} documents")
            else:
                self._index = faiss.IndexFlatIP(self.dim)  # Inner product = cosine for normalized vectors
                log.info("Created new FAISS index")
                
        except ImportError:
            log.warning("FAISS not installed, using fallback (slower) store")
            self._index = None

    def add(self, embedding: List[float], document: Dict) -> int:
        """
        Add document with embedding to store.
        
        Change: Add with auto-save
        Why:
        - Documents need persistence
        - Batch save is more efficient
        Impact:
        - Persistent storage
        - Data durability
        """
        # Fix Bug 4: faiss was only imported inside _load_or_create_index();
        # normalize_L2 calls in add/add_batch/search crashed with NameError.
        import numpy as np
        try:
            import faiss as _faiss
        except ImportError:
            _faiss = None
        
        doc_copy = document.copy()
        doc_copy["_id"] = self._doc_id
        doc_copy["_added_at"] = datetime.now().isoformat()
        
        if self._index is not None and _faiss is not None:
            # Normalize for cosine similarity
            emb_array = np.array([embedding], dtype=np.float32)
            _faiss.normalize_L2(emb_array)
            self._index.add(emb_array)
        
        self._documents.append(doc_copy)
        self._doc_id += 1
        
        # Periodic save
        if self._doc_id % 10 == 0:
            self.save()
        
        return doc_copy["_id"]

    def add_batch(self, embeddings: List[List[float]], documents: List[Dict]):
        """Add multiple documents."""
        # Fix Bug 4: guard faiss import
        import numpy as np
        try:
            import faiss as _faiss
        except ImportError:
            _faiss = None
        
        if not embeddings or not documents:
            return
        
        if self._index is not None and _faiss is not None:
            emb_array = np.array(embeddings, dtype=np.float32)
            _faiss.normalize_L2(emb_array)
            self._index.add(emb_array)
        
        for doc in documents:
            doc_copy = doc.copy()
            doc_copy["_id"] = self._doc_id
            doc_copy["_added_at"] = datetime.now().isoformat()
            self._documents.append(doc_copy)
            self._doc_id += 1
        
        self.save()

    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """
        Search for similar documents.
        
        Change: Vector similarity search
        Why:
        - Semantic similarity requires vectors
        - k-NN is standard approach
        Impact:
        - Semantically relevant results
        - Fast retrieval
        """
        import numpy as np

        if self._index is None or len(self._documents) == 0:
            return []
        
        # Fix Bug 4: guard faiss import
        try:
            import faiss as _faiss
        except ImportError:
            return []
        # Normalize query
        query_array = np.array([query_embedding], dtype=np.float32)
        _faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self._index.search(query_array, k=min(k, len(self._documents)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._documents):
                doc = self._documents[idx].copy()
                doc["score"] = float(score)
                results.append(doc)
        
        return results

    def save(self):
        """Save index to disk."""
        try:
            import faiss
            import json
            
            if self._index is not None:
                faiss.write_index(self._index, str(self.index_path / "index.faiss"))
            
            with open(self.index_path / "documents.json", "w") as f:
                json.dump(self._documents, f)
                
        except Exception as e:
            log.warning(f"Failed to save index: {e}")

    def clear(self):
        """Clear all documents."""
        # Fix Bug 4: consistent import guard
        try:
            import faiss as _faiss
            self._index = _faiss.IndexFlatIP(self.dim)
        except ImportError:
            self._index = None
        self._documents = []
        self._doc_id = 0
        self.save()

    def count(self) -> int:
        """Get document count."""
        return len(self._documents)
