import subprocess

import pytest
import requests

from hermeshub.agent import (
    AgentUnavailableError,
    HermesAgentClient,
    _prompt_with_system,
    _reply_from_response,
    is_backend_error,
)


def test_reply_from_common_shapes():
    assert _reply_from_response({"reply": "hello"}) == "hello"
    assert _reply_from_response({"response": "hello"}) == "hello"
    assert _reply_from_response({"text": "hello"}) == "hello"
    assert _reply_from_response({"message": "hello"}) == "hello"
    assert _reply_from_response({"content": "hello"}) == "hello"


def test_reply_from_openai_shape():
    data = {"choices": [{"message": {"content": "hello"}}]}
    assert _reply_from_response(data) == "hello"


def test_reply_from_empty_shape():
    assert _reply_from_response({}) == ""


def test_prompt_with_system_keeps_user_text_and_short_reply_instruction():
    prompt = _prompt_with_system("tell me about mars", "Keep replies short.")

    assert "System instructions:" in prompt
    assert "Keep replies short." in prompt
    assert "User said:\ntell me about mars" in prompt
    assert prompt.endswith("Answer:")


def test_http_connection_error_is_actionable(monkeypatch):
    class Config:
        command = None
        agent_url = "http://127.0.0.1:8000"
        system_prompt = "Keep replies short."
        request_timeout_seconds = 1

    def post(*_args, **_kwargs):
        raise requests.exceptions.ConnectionError("refused")

    monkeypatch.setattr("hermeshub.agent.requests.post", post)

    with pytest.raises(AgentUnavailableError, match="Start the agent HTTP server"):
        HermesAgentClient(Config()).ask("hello")


def test_command_error_includes_stderr(monkeypatch):
    class Config:
        command = "hermes chat --quiet -q {prompt}"
        system_prompt = "Keep replies short."
        request_timeout_seconds = 1

    def run(*_args, **_kwargs):
        raise subprocess.CalledProcessError(1, "hermes", stderr="run hermes model")

    monkeypatch.setattr("hermeshub.agent.subprocess.run", run)

    with pytest.raises(AgentUnavailableError, match="run hermes model"):
        HermesAgentClient(Config()).ask("hello")


def test_backend_error_detection():
    assert is_backend_error("Failed to execute: Error invoking Gemini: 429 quota")
    assert is_backend_error("You exceeded your current quota")
    assert not is_backend_error("I am doing well.")
