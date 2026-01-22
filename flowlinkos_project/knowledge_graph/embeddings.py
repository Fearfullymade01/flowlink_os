"""
Embedding service for generating semantic vectors for text using sentence-transformers.
Handles vector generation, similarity computation, and caching.
"""

import logging
from typing import List, Optional, Dict, Tuple
import numpy as np
import hashlib
import json

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding service with a specific model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
                       'all-MiniLM-L6-v2' is a good balance of speed/quality
                       'all-mpnet-base-v2' is more accurate but slower
        """
        self.model = None
        self.model_name = model_name
        self.embedding_dim = 384  # sensible default for MiniLM
        try:
            # Lazy import to avoid import errors during migrations/startup if deps mismatch
            from sentence_transformers import SentenceTransformer  # type: ignore
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Initialized embedding service with model: {model_name}")
        except Exception as e:
            logger.warning(
                "sentence-transformers unavailable or failed to load (%s). "
                "Falling back to lightweight hash-based embeddings.",
                e,
            )
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding, or None if error
        """
        if not text or not isinstance(text, str):
            return None
        
        try:
            text = text.strip()[:1000]  # Limit to 1000 chars
            if self.model is not None:
                embedding = self.model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
            # Fallback: deterministic hash-based embedding
            h = hashlib.sha256(text.encode("utf-8")).digest()
            # Expand to embedding_dim with simple repetition and normalization
            arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
            reps = int(np.ceil(self.embedding_dim / arr.size))
            vec = np.tile(arr, reps)[: self.embedding_dim]
            norm = np.linalg.norm(vec)
            if norm == 0:
                return vec.tolist()
            return (vec / norm).tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return None
    
    def embed_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (or None for failed texts)
        """
        if not texts:
            return []
        
        try:
            # Clean and limit texts
            cleaned_texts = [t.strip()[:1000] for t in texts if t and isinstance(t, str)]
            if not cleaned_texts:
                return [None] * len(texts)

            if self.model is not None:
                embeddings = self.model.encode(cleaned_texts, convert_to_tensor=False)
                # Map back to original list, handling failed texts
                result = []
                embedding_idx = 0
                for text in texts:
                    if text and isinstance(text, str) and text.strip():
                        result.append(embeddings[embedding_idx].tolist())
                        embedding_idx += 1
                    else:
                        result.append(None)
                return result

            # Fallback per-text using hash-based embedding
            results: List[Optional[List[float]]] = []
            for text in texts:
                if text and isinstance(text, str) and text.strip():
                    results.append(self.embed_text(text))
                else:
                    results.append(None)
            return results
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return [None] * len(texts)
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            embed1 = np.array(embedding1)
            embed2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(embed1, embed2) / (
                np.linalg.norm(embed1) * np.linalg.norm(embed2)
            )
            
            # Normalize to 0-1 range (cosine similarity is -1 to 1)
            return float((similarity + 1) / 2)
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def find_similar(
        self,
        query_embedding: List[float],
        candidates: List[List[float]],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings from candidates.
        
        Args:
            query_embedding: Query embedding vector
            candidates: List of candidate embeddings
            top_k: Number of top results to return
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        try:
            if not query_embedding or not candidates:
                return []
            
            query = np.array(query_embedding)
            similarities = []
            
            for idx, candidate in enumerate(candidates):
                if candidate is None:
                    continue
                
                score = self.compute_similarity(query_embedding, candidate)
                if score >= threshold:
                    similarities.append((idx, score))
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
        except Exception as e:
            logger.error(f"Error finding similar: {e}")
            return []
    
    def batch_similarity(
        self,
        query_embeddings: List[List[float]],
        candidates: List[List[float]]
    ) -> np.ndarray:
        """
        Compute similarity matrix between queries and candidates (batched).
        
        Args:
            query_embeddings: List of query embedding vectors
            candidates: List of candidate embedding vectors
            
        Returns:
            Numpy matrix of shape (len(queries), len(candidates))
        """
        try:
            if not query_embeddings or not candidates:
                return np.array([])
            
            queries = np.array([e for e in query_embeddings if e is not None])
            cands = np.array([e for e in candidates if e is not None])
            
            if queries.size == 0 or cands.size == 0:
                return np.array([])
            
            # Normalize vectors
            queries = queries / np.linalg.norm(queries, axis=1, keepdims=True)
            cands = cands / np.linalg.norm(cands, axis=1, keepdims=True)
            
            # Compute similarity matrix
            similarity_matrix = np.dot(queries, cands.T)
            
            # Normalize to 0-1 range
            similarity_matrix = (similarity_matrix + 1) / 2
            
            return similarity_matrix
        except Exception as e:
            logger.error(f"Error in batch similarity: {e}")
            return np.array([])


# Initialize default embedding service
_default_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create default embedding service (singleton)."""
    global _default_service
    if _default_service is None:
        _default_service = EmbeddingService()
    return _default_service


def embed(text: str) -> Optional[List[float]]:
    """Convenience function to embed text using default service."""
    return get_embedding_service().embed_text(text)


def embed_batch(texts: List[str]) -> List[Optional[List[float]]]:
    """Convenience function to embed multiple texts using default service."""
    return get_embedding_service().embed_texts(texts)


def similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Convenience function to compute similarity using default service."""
    return get_embedding_service().compute_similarity(embedding1, embedding2)
