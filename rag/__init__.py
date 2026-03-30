"""
AIOS RAG — Retrieval-Augmented Generation Module

Provides local knowledge retrieval and dynamic web research capabilities.
"""

__version__ = "2.0.0"

from .pipeline import RAGPipeline
from .web_search import WebSearch, WebFetcher
from .embedder import LocalEmbedder
from .vector_store import FAISSStore
from .retriever import Retriever
from .processor import ContentProcessor

__all__ = [
    "RAGPipeline",
    "WebSearch",
    "WebFetcher",
    "LocalEmbedder",
    "FAISSStore",
    "Retriever",
    "ContentProcessor",
]
