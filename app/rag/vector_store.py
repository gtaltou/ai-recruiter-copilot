import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.rag.embeddings import LiteLLMEmbeddingFunction
import logging
import os

logger = logging.getLogger(__name__)

class VectorStore:
    """Store vectoriel ChromaDB pour les CVs."""

    def __init__(self):
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.embedding_function = LiteLLMEmbeddingFunction()
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=self.embedding_function,
            )
        except ValueError:
            return self.client.create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=self.embedding_function,
            )

    def add_cv(self, cv_id: str, text: str, metadata: dict = None) -> None:
        """Ajoute un CV à la base vectorielle."""
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[cv_id],
        )
        logger.info(f"CV {cv_id} indexé avec succès.")

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Recherche sémantique de CVs."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        return [
            {
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "score": results["distances"][0][i] if results.get("distances") else 0.0,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            }
            for i in range(len(results["ids"][0]))
        ]

    def count(self) -> int:
        return self.collection.count()

vector_store = VectorStore()
