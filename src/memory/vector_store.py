import math
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.logger import logger


class LocalVectorStore:
    """
    In-memory fallback vector store implementation using TF-IDF term overlap
    for offline development, testing, or environments without Pinecone API keys.
    """

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}

    def upsert(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata,
            "tokens": set(text.lower().split())
        }

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = set(query_text.lower().split())
        if not query_tokens:
            return []

        scored_docs = []
        for doc_id, doc in self.documents.items():
            doc_tokens = doc["tokens"]
            if not doc_tokens:
                continue
            # Simple Jaccard similarity score
            intersection = query_tokens.intersection(doc_tokens)
            union = query_tokens.union(doc_tokens)
            score = len(intersection) / float(len(union)) if union else 0.0

            scored_docs.append({
                "id": doc_id,
                "score": score,
                "text": doc["text"],
                "metadata": doc["metadata"]
            })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]


class VectorStoreManager:
    """
    Unified Manager for Pinecone & Fallback Local Vector DB.
    """

    def __init__(self):
        self.use_local = settings.USE_LOCAL_VECTOR_STORE or not settings.PINECONE_API_KEY
        self.local_store = LocalVectorStore()
        self.pinecone_index = None

        if not self.use_local and settings.PINECONE_API_KEY:
            try:
                import pinecone
                pinecone.init(
                    api_key=settings.PINECONE_API_KEY,
                    environment=settings.PINECONE_ENVIRONMENT
                )
                self.pinecone_index = pinecone.Index(settings.PINECONE_INDEX_NAME)
                logger.info("[VectorStoreManager] Connected to Pinecone index.")
            except Exception as e:
                logger.warning(f"[VectorStoreManager] Failed to init Pinecone, using local store: {e}")
                self.use_local = True

    def store_memory(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        if self.use_local or not self.pinecone_index:
            self.local_store.upsert(doc_id, text, metadata)
        else:
            try:
                # In real Pinecone usage, text would be embedded via OpenAI Embeddings API first
                self.pinecone_index.upsert([(doc_id, [0.1] * 1536, metadata)])
            except Exception as e:
                logger.error(f"Error storing vector in Pinecone: {e}")
                self.local_store.upsert(doc_id, text, metadata)

    def search_similar_repairs(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.use_local or not self.pinecone_index:
            return self.local_store.query(query_text, top_k=top_k)
        else:
            try:
                # Query Pinecone with vector
                res = self.pinecone_index.query(vector=[0.1] * 1536, top_k=top_k, include_metadata=True)
                return [{"id": m.id, "score": m.score, "metadata": m.metadata} for m in res.matches]
            except Exception as e:
                logger.error(f"Error searching Pinecone: {e}")
                return self.local_store.query(query_text, top_k=top_k)


vector_store = VectorStoreManager()
