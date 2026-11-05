"""Tests unitaires pour le module app/core/llm.py."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.fixture(autouse=True)
def reset_llm_client():
    """Réinitialise le singleton LLMClient avant chaque test."""
    import app.core.llm
    app.core.llm._llm_client = None
    yield
    app.core.llm._llm_client = None


@pytest.fixture
def mock_settings():
    """Fixture qui patche settings avec LLM_PROVIDER et LLM_MODEL."""
    with patch("app.core.llm.settings") as mock:
        mock.LLM_PROVIDER = "openai"
        mock.LLM_MODEL = "gpt-4o-mini"
        yield mock


class TestLLMClientInitialization:
    """Tests d'initialisation du client LLM."""

    def test_client_creation(self, mock_settings):
        """Teste la création d'un LLMClient avec des paramètres valides."""
        from app.core.llm import LLMClient
        client = LLMClient()
        assert client.model == "openai/gpt-4o-mini"

    def test_client_custom_model(self, mock_settings):
        """Teste l'utilisation d'un modèle personnalisé."""
        mock_settings.LLM_MODEL = "gpt-4"
        from app.core.llm import LLMClient
        client = LLMClient()
        assert client.model == "openai/gpt-4"


class TestSingletonPattern:
    """Tests du pattern singleton lazy."""

    def test_get_llm_client(self, mock_settings):
        """Teste que get_llm_client retourne bien une instance."""
        from app.core.llm import LLMClient, get_llm_client
        assert isinstance(get_llm_client(), LLMClient)

    def test_singleton_is_cached(self, mock_settings):
        """Teste que get_llm_client retourne la même instance."""
        from app.core.llm import get_llm_client
        assert get_llm_client() is get_llm_client()

    def test_module_attribute_access(self, mock_settings):
        """Teste que l'accès à llm_client via le module fonctionne."""
        import app.core.llm
        client = app.core.llm.llm_client
        from app.core.llm import LLMClient
        assert isinstance(client, LLMClient)

    def test_module_attribute_is_singleton(self, mock_settings):
        """Teste que l'attribut module llm_client est un singleton."""
        import app.core.llm
        assert app.core.llm.llm_client is app.core.llm.llm_client


class TestLLMClientGenerate:
    """Tests de la méthode generate du client LLM."""

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_settings):
        """Teste une génération réussie avec réponse complète."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Réponse test"))
        ]

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate(
                system_prompt="Sois utile.",
                user_prompt="Test prompt"
            )

            mock_completion.assert_called_once()
            args, kwargs = mock_completion.call_args
            assert kwargs["model"] == "openai/gpt-4o-mini"
            assert kwargs["messages"] == [
                {"role": "system", "content": "Sois utile."},
                {"role": "user", "content": "Test prompt"}
            ]
            assert result == "Réponse test"

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self, mock_settings):
        """Teste la génération avec une température personnalisée."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Réponse"))]

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate(
                system_prompt="Sois utile.",
                user_prompt="Test prompt",
                temperature=0.5
            )

            args, kwargs = mock_completion.call_args
            assert kwargs["temperature"] == 0.5
            assert result == "Réponse"

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens(self, mock_settings):
        """Teste la génération avec un nombre max de tokens."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Réponse"))]

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate(
                system_prompt="Sois utile.",
                user_prompt="Test prompt",
                max_tokens=100
            )

            args, kwargs = mock_completion.call_args
            assert kwargs["max_tokens"] == 100
            assert result == "Réponse"

    @pytest.mark.asyncio
    async def test_generate_api_error(self, mock_settings):
        """Teste la gestion d'une erreur API."""
        from app.core.llm import LLMClient
        client = LLMClient()

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.side_effect = Exception("API Error")
            with pytest.raises(Exception, match="API Error"):
                await client.generate(
                    system_prompt="Sois utile.",
                    user_prompt="Test prompt"
                )

    @pytest.mark.asyncio
    async def test_generate_empty_response(self, mock_settings):
        """Teste la gestion d'une réponse vide (content=None)."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate(
                system_prompt="Sois utile.",
                user_prompt="Test prompt"
            )
            assert result is None


class TestLLMClientGenerateStructured:
    """Tests de la méthode generate_structured du client LLM."""

    @pytest.mark.asyncio
    async def test_generate_structured_success(self, mock_settings):
        """Teste une génération structurée réussie."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"name": "John", "age": 30}'))
        ]

        class DummyModel:
            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate_structured(
                system_prompt="Extract info.",
                user_prompt="John is 30.",
                response_model=DummyModel
            )

            assert result.name == "John"
            assert result.age == 30

            args, kwargs = mock_completion.call_args
            assert kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_structured_api_error(self, mock_settings):
        """Teste la gestion d'une erreur API sur generate_structured."""
        from app.core.llm import LLMClient
        client = LLMClient()

        class DummyModel:
            def __init__(self):
                pass

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.side_effect = Exception("API Error")
            with pytest.raises(Exception, match="API Error"):
                await client.generate_structured(
                    system_prompt="Extract info.",
                    user_prompt="John is 30.",
                    response_model=DummyModel
                )

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(self, mock_settings):
        """Teste la gestion d'un JSON invalide dans la réponse."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="not json"))
        ]

        class DummyModel:
            def __init__(self):
                pass

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            with pytest.raises(Exception):
                await client.generate_structured(
                    system_prompt="Extract info.",
                    user_prompt="John is 30.",
                    response_model=DummyModel
                )


class TestLLMClientEdgeCases:
    """Tests des cas limites."""

    def test_client_repr(self, mock_settings):
        """Teste la représentation string du client."""
        from app.core.llm import LLMClient
        client = LLMClient()
        repr_str = repr(client)
        assert "LLMClient" in repr_str

    @pytest.mark.asyncio
    async def test_generate_custom_system_prompt(self, mock_settings):
        """Teste generate avec un system_prompt personnalisé."""
        from app.core.llm import LLMClient
        client = LLMClient()

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Réponse"))]

        with patch("app.core.llm.completion", new_callable=AsyncMock) as mock_completion:
            mock_completion.return_value = mock_response
            result = await client.generate(
                system_prompt="Tu es un assistant expert en Python.",
                user_prompt="Explique les decorateurs."
            )

            args, kwargs = mock_completion.call_args
            assert kwargs["messages"][0]["content"] == "Tu es un assistant expert en Python."
            assert kwargs["messages"][1]["content"] == "Explique les decorateurs."
            assert result == "Réponse"
