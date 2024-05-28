import types
import pytest
from httpx import ConnectError
from ollama import ResponseError
from openai import AuthenticationError as OAIAuthError, NotFoundError as OAINotFoundError
from anthropic import AuthenticationError as CAuthError, NotFoundError as CNotFoundError
from google.generativeai import AuthenticationError as GAuthError, NotFoundError as GNotFoundError
from mistral import AuthenticationError as MAuthError, NotFoundError as MNotFoundError
from app.core.config import settings
from app.services.llm.groq import GroqClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.openai import OpenAIClient
from app.services.llm.anthropic import ClaudeClient
from app.services.llm.gemini import GeminiClient
from app.services.llm.mistral import MistralClient, MistralModel


# Tests for OllamaClient
@pytest.mark.parametrize(
    ("endpoint", "model", "error"),
    [
        ("mydomain", settings.OLLAMA_MODEL, ConnectError),
        ("https://quackai.com", settings.OLLAMA_MODEL, ResponseError),
        (settings.OLLAMA_ENDPOINT, "quack", ResponseError),
        (settings.OLLAMA_ENDPOINT, settings.OLLAMA_MODEL, None),
    ],
)
def test_ollamaclient_constructor(endpoint, model, error):
    if error is None:
        OllamaClient(endpoint, model)
    else:
        with pytest.raises(error):
            OllamaClient(endpoint, model)


def test_ollamaclient_chat():
    llm_client = OllamaClient(settings.OLLAMA_ENDPOINT, settings.OLLAMA_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)


# Tests for GroqClient
def test_groqclient_constructor():
    with pytest.raises(GAuthError):
        GroqClient("api_key", settings.GROQ_MODEL)
    if isinstance(settings.GROQ_API_KEY, str):
        with pytest.raises(GNotFoundError):
            GroqClient(settings.GROQ_API_KEY, "quack")
        GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL)


@pytest.mark.skipif(settings.GROQ_API_KEY is None, reason="GROQ_API_KEY is None")
def test_groqclient_chat():
    llm_client = GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)


# Tests for OpenAIClient
def test_openaiclient_constructor():
    with pytest.raises(OAIAuthError):
        OpenAIClient("api_key", settings.OPENAI_MODEL)
    if isinstance(settings.OPENAI_API_KEY, str):
        with pytest.raises(OAINotFoundError):
            OpenAIClient(settings.OPENAI_API_KEY, "quack")
        OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)


@pytest.mark.skipif(settings.OPENAI_API_KEY is None, reason="OPENAI_API_KEY is None")
def test_openaiclient_chat():
    llm_client = OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)


# Tests for ClaudeClient
@pytest.mark.parametrize(
    ("endpoint", "model", "error"),
    [
        ("mydomain", settings.ANTHROPIC_MODEL, ConnectError),
        ("https://invalidendpoint.com", settings.ANTHROPIC_MODEL, ResponseError),
        (settings.ANTHROPIC_ENDPOINT, "invalid_model", ResponseError),
        (settings.ANTHROPIC_ENDPOINT, settings.ANTHROPIC_MODEL, None),
    ],
)
def test_anthropic_client_constructor(endpoint, model, error):
    if error is None:
        ClaudeClient(endpoint, model)
    else:
        with pytest.raises(error):
            ClaudeClient(endpoint, model)


def test_anthropic_client_constructor_with_invalid_api_key():
    with pytest.raises(CAuthError):
        ClaudeClient("invalid_api_key", settings.ANTHROPIC_MODEL)
    if isinstance(settings.ANTHROPIC_API_KEY, str):
        with pytest.raises(CNotFoundError):
            ClaudeClient(settings.ANTHROPIC_API_KEY, "invalid_model")
        ClaudeClient(settings.ANTHROPIC_API_KEY, settings.ANTHROPIC_MODEL)


@pytest.mark.skipif(settings.ANTHROPIC_API_KEY is None, reason="ANTHROPIC_API_KEY is None")
def test_anthropic_client_chat():
    llm_client = ClaudeClient(settings.ANTHROPIC_API_KEY, settings.ANTHROPIC_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)


# Tests for GeminiClient
@pytest.mark.parametrize(
    ("endpoint", "model", "error"),
    [
        ("mydomain", settings.GEMINI_MODEL, ConnectError),
        ("https://invalidendpoint.com", settings.GEMINI_MODEL, ResponseError),
        (settings.GEMINI_ENDPOINT, "invalid_model", ResponseError),
        (settings.GEMINI_ENDPOINT, settings.GEMINI_MODEL, None),
    ],
)
def test_gemini_client_constructor(endpoint, model, error):
    if error is None:
        GeminiClient(endpoint, model)
    else:
        with pytest.raises(error):
            GeminiClient(endpoint, model)


def test_gemini_client_constructor_with_invalid_api_key():
    with pytest.raises(GAuthError):
        GeminiClient("invalid_api_key", settings.GEMINI_MODEL)
    if isinstance(settings.GEMINI_API_KEY, str):
        with pytest.raises(GNotFoundError):
            GeminiClient(settings.GEMINI_API_KEY, "invalid_model")
        GeminiClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)


@pytest.mark.skipif(settings.GEMINI_API_KEY is None, reason="GEMINI_API_KEY is None")
def test_gemini_client_chat():
    llm_client = GeminiClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)


# Tests for MistralClient
def test_mistralclient_constructor():
    with pytest.raises(MAuthError):
        MistralClient("invalid_api_key", MistralModel.Mistral_7B)
    if isinstance(settings.MISTRAL_API_KEY, str):
        with pytest.raises(MNotFoundError):
            MistralClient(settings.MISTRAL_API_KEY, "invalid_model")
        MistralClient(settings.MISTRAL_API_KEY, MistralModel.Mistral_7B)


@pytest.mark.skipif(settings.MISTRAL_API_KEY is None, reason="MISTRAL_API_KEY is None")
def test_mistralclient_chat():
    llm_client = MistralClient(settings.MISTRAL_API_KEY, MistralModel.Mistral_7B)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)
