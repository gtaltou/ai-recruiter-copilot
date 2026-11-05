from litellm import completion
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """Client LLM unifié via LiteLLM."""

    def __init__(self):
        self.model = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Génère une réponse depuis le LLM."""
        try:
            response = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type,
        temperature: float = 0.1,
    ) -> object:
        """Génère une réponse structurée (JSON mode)."""
        try:
            response = await completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )
            import json
            return response_model(**json.loads(response.choices[0].message.content))
        except Exception as e:
            logger.error(f"Structured LLM call failed: {e}")
            raise

_llm_client = None

def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

# Accès rétrocompatible : from app.core.llm import llm_client fonctionne toujours
def __getattr__(name):
    if name == "llm_client":
        return get_llm_client()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

