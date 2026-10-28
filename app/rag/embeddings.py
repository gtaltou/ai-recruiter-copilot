from chromadb import EmbeddingFunction
from litellm import embedding
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LiteLLMEmbeddingFunction(EmbeddingFunction):
    """Fonction d'embedding utilisant LiteLLM."""

    def __init__(self, model: str = settings.EMBEDDING_MODEL):
        self.model = model

    def __call__(self, texts: list[str]) -> list[list[float]]:
        try:
            response = embedding(model=self.model, input=texts)
            return [item["embedding"] for item in response.data]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
