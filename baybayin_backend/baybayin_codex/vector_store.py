"""
Baybayin Codex Vector Store
Embeds content using Sentence Transformers and stores/retrieves vectors with FAISS
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

class BaybayinVectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2', index_path='vector_index.faiss', meta_path='vector_meta.pkl'):
        self.model = SentenceTransformer(model_name)
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
            self.metadata = []

    def save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)

    def add_content(self, texts, meta_list):
        """
        Embed and add a list of texts with metadata
        texts: List[str]
        meta_list: List[dict] (same length as texts)
        """
        embeddings = self.model.encode(texts, show_progress_bar=True)
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        self.index.add(np.array(embeddings, dtype='float32'))
        self.metadata.extend(meta_list)
        self.save_index()

    def search(self, query, top_k=5):
        """
        Semantic search for top_k most similar items
        Returns: List of (score, metadata)
        """
        query_emb = self.model.encode([query])
        D, I = self.index.search(np.array(query_emb, dtype='float32'), top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < len(self.metadata):
                results.append({'score': float(score), 'meta': self.metadata[idx]})
        return results

    def clear(self):
        self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
        self.metadata = []
        self.save_index()
