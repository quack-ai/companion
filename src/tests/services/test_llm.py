import types

import pytest
from groq import AuthenticationError, NotFoundError
from httpx import ConnectError
from ollama import ResponseError

from app.core.config import settings
from app.services.llm.groq import GroqClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.openai import OpenAIClient


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


def test_groqclient_constructor():
    with pytest.raises(AuthenticationError):
        GroqClient("api_key", settings.GROQ_MODEL)
    if isinstance(settings.GROQ_API_KEY, str):
        with pytest.raises(NotFoundError):
            GroqClient(settings.GROQ_API_KEY, "quack")
        GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL)


@pytest.mark.skipif("settings.GROQ_API_KEY is None")
def test_groqclient_chat():
    llm_client = GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)


def test_openaiclient_constructor():
    with pytest.raises(AuthenticationError):
        OpenAIClient("api_key", settings.OPENAI_MODEL)
    if isinstance(settings.OPENAI_API_KEY, str):
        with pytest.raises(NotFoundError):
            OpenAIClient(settings.OPENAI_API_KEY, "quack")
        OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)


@pytest.mark.skipif("settings.OPENAI_API_KEY is None")
def test_openaiclient_chat():
    llm_client = OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
    stream = llm_client.chat([{"role": "user", "content": "hello"}])
    assert isinstance(stream, types.GeneratorType)
    for chunk in stream:
        assert isinstance(chunk, str)
