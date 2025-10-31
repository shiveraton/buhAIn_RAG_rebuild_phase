"""
Semantic retrieval service for RAG-powered trivia generation.

This module provides semantic search functionality to retrieve relevant facts
from the vector database based on query similarity.
"""

import json
import os
from typing import List, Tuple
import numpy as np
from game_seg_trivia.models import TriviaSourceFact

# Global model instance (loaded once and reused)
_embedding_model = None
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "monsoon-nlp/monsoon-paraphrase-filipino")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

def get_embedding_model():
    """
    Get or initialize the sentence transformer model.
    Lazy-imports sentence_transformers to avoid import-time crashes when heavy deps (Pillow/regex) are broken.
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            # local import to avoid top-level import errors when dependencies are missing
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            raise RuntimeError(
                "sentence-transformers (and/or its dependencies) failed to import. "
                "Install required packages in the project venv:\n"
                "  python -m pip install --upgrade --force-reinstall --only-binary :all: Pillow regex sentence-transformers\n"
                f"Underlying import error: {e}"
            )
        try:
            _embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
        except Exception as e:
            fallback = 'all-MiniLM-L6-v2'
            print(f"[retrieval_service] Failed to load '{EMBEDDING_MODEL}': {e}. Falling back to '{fallback}'.")
            _embedding_model = SentenceTransformer(fallback, device=EMBEDDING_DEVICE)
    return _embedding_model


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
        
    Returns:
        Cosine similarity score (0 to 1, higher = more similar)
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    
    return float(dot_product / (norm_v1 * norm_v2))


def retrieve_relevant_facts(
    query: str,
    top_k: int = 5,
    min_similarity: float = 0.3
) -> List[Tuple[TriviaSourceFact, float]]:
    """
    Retrieve the most relevant facts for a given query using semantic search.
    
    This function:
    1. Embeds the query using the same model used during ingestion
    2. Computes cosine similarity between query and all stored facts
    3. Returns top K most similar facts above the minimum similarity threshold
    
    Args:
        query: The search query (e.g., topic, question, or concept)
        top_k: Number of top results to return (default: 5)
        min_similarity: Minimum similarity threshold (0-1, default: 0.3)
        
    Returns:
        List of tuples (TriviaSourceFact, similarity_score), sorted by similarity descending
        
    Example:
        >>> facts = retrieve_relevant_facts("Baybayin vowels", top_k=3)
        >>> for fact, score in facts:
        ...     print(f"Score: {score:.3f}, Page: {fact.metadata.get('page')}")
        ...     print(f"Content: {fact.content[:100]}...")
    """
    # Generate query embedding
    model = get_embedding_model()
    query_embedding = model.encode([query])[0].tolist()
    
    # Retrieve all facts from database
    all_facts = TriviaSourceFact.objects.all()
    
    # Compute similarities
    results = []
    for fact in all_facts:
        similarity = cosine_similarity(query_embedding, fact.embedding)
        if similarity >= min_similarity:
            results.append((fact, similarity))
    
    # Sort by similarity (descending) and take top K
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def format_facts_for_llm(facts: List[Tuple[TriviaSourceFact, float]]) -> str:
    """
    Format retrieved facts into a context string for LLM prompts.
    
    Args:
        facts: List of (TriviaSourceFact, similarity_score) tuples
        
    Returns:
        Formatted string with fact content, page numbers, and relevance scores
        
    Example output:
        '''
        [Fact 1, Page 12, Relevance: 0.85]
        Baybayin vowels are represented by three basic characters...
        
        [Fact 2, Page 15, Relevance: 0.78]
        The kudlit diacritic modifies the vowel sound...
        '''
    """
    if not facts:
        return "No relevant context found."
    
    formatted_parts = []
    for i, (fact, score) in enumerate(facts, 1):
        # Parse metadata (stored as JSON string in Django JSONField)
        metadata = fact.metadata if isinstance(fact.metadata, dict) else json.loads(fact.metadata)
        page = metadata.get('page', 'Unknown')
        formatted_parts.append(
            f"[Fact {i}, Page {page}, Relevance: {score:.2f}]\n{fact.content.strip()}\n"
        )
    
    return "\n".join(formatted_parts)
