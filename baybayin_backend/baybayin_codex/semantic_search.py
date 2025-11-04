"""
Baybayin Codex Semantic Search
Provides a simple interface for semantic search and RAG using the vector store
"""

from .vector_store import BaybayinVectorStore

class SemanticSearch:
    def __init__(self, model_name='all-MiniLM-L6-v2', index_path='vector_index.faiss', meta_path='vector_meta.pkl'):
        self.vector_store = BaybayinVectorStore(model_name, index_path, meta_path)

    def search(self, query, top_k=5):
        """
        Perform semantic search for a query string
        Returns: List of dicts with score and metadata
        """
        return self.vector_store.search(query, top_k)

    def add_documents(self, texts, meta_list):
        """
        Add new documents to the vector store
        texts: List[str]
        meta_list: List[dict]
        """
        self.vector_store.add_content(texts, meta_list)

    def clear_index(self):
        """
        Clear the vector store index
        """
        self.vector_store.clear()
