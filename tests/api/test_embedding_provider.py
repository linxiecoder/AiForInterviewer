import pytest

from app.application.embeddings.ports import EmbeddingProviderError
from app.infrastructure.embeddings.openai_compatible import (
    OpenAICompatibleEmbeddingProvider,
    OpenAICompatibleEmbeddingSettings,
)


class _FakeEmbeddingResponse:
    def __init__(self, body=None, *, json_error: Exception | None = None) -> None:
        self._body = body
        self._json_error = json_error

    def raise_for_status(self) -> None:
        return None

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._body


class _FakeEmbeddingClient:
    def __init__(self, response: _FakeEmbeddingResponse) -> None:
        self.response = response

    def post(self, *_args, **_kwargs) -> _FakeEmbeddingResponse:
        return self.response


def test_embedding_settings_fail_closed_without_model_or_dimension() -> None:
    with pytest.raises(EmbeddingProviderError, match="EMBEDDING_DIMENSION"):
        OpenAICompatibleEmbeddingSettings.from_env({"EMBEDDING_MODEL": "text-embedding-3-small"})

    with pytest.raises(EmbeddingProviderError, match="EMBEDDING_MODEL"):
        OpenAICompatibleEmbeddingSettings.from_env({"EMBEDDING_DIMENSION": "1536"})


def test_embedding_provider_maps_malformed_json_to_provider_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        OpenAICompatibleEmbeddingSettings(
            api_key="test-key",
            model="text-embedding-3-small",
            dimension=3,
        ),
        client=_FakeEmbeddingClient(
            _FakeEmbeddingResponse(json_error=ValueError("not json"))
        ),
    )

    with pytest.raises(EmbeddingProviderError, match="invalid JSON"):
        provider.embed_texts(("hello",))


def test_embedding_provider_maps_invalid_vector_values_to_provider_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        OpenAICompatibleEmbeddingSettings(
            api_key="test-key",
            model="text-embedding-3-small",
            dimension=3,
        ),
        client=_FakeEmbeddingClient(
            _FakeEmbeddingResponse(
                {
                    "model": "text-embedding-3-small",
                    "data": [{"index": 0, "embedding": [0.1, "not-a-number", 0.3]}],
                }
            )
        ),
    )

    with pytest.raises(EmbeddingProviderError, match="non-numeric"):
        provider.embed_texts(("hello",))
