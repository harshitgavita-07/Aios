"""
Content Processor — Clean and chunk content for embedding
"""

import re
import logging
from typing import List

log = logging.getLogger("aios.rag.processor")


class ContentProcessor:
    """
    Process raw content into clean, embeddable chunks.
    
    Change: Content cleaning and chunking
    Why:
    - Raw HTML needs cleaning
    - Long documents need chunking
    - Quality affects retrieval accuracy
    Impact:
    - Better embedding quality
    - More accurate retrieval
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        log.info(f"ContentProcessor initialized (chunk_size={chunk_size})")

    def clean_html(self, html: str) -> str:
        """
        Remove HTML tags and clean text.
        
        Change: HTML cleaning
        Why:
        - Raw HTML hurts embedding quality
        - Scripts/styles need removal
        Impact:
        - Clean text for embedding
        - Better semantic similarity
        """
        # Remove script and style sections
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        
        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        
        return text.strip()

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Change: Smart chunking
        Why:
        - Long documents exceed context window
        - Overlapping preserves context
        - Sentence boundaries matter
        Impact:
        - Optimal chunk sizes
        - Preserved context
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences + [sentence]
                current_length = overlap_length + sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def extract_title(self, html: str) -> str:
        """Extract title from HTML."""
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE)
        if match:
            return self.clean_html(match.group(1))
        return ""
