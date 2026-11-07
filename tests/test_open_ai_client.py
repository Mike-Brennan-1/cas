from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from openai import APIError

from cas.config import INSTRUCTIONS, MODEL
from cas.open_ai_client import OpenAiClient


@pytest.fixture
def client():
    client = OpenAiClient()
    client.client = MagicMock()
    client.client.responses.create.return_value = SimpleNamespace(id="resp_1", output_text="Hello")
    return client


def sent_to_api(client):
    return client.client.responses.create.call_args.kwargs


def test_returns_the_response_text(client):
    assert client.process_prompt("Hi", language=None) == "Hello"


def test_sends_the_prompt_model_and_instructions(client):
    client.process_prompt("Hi", language=None)

    assert sent_to_api(client) == {
        "model": MODEL,
        "instructions": INSTRUCTIONS,
        "input": "Hi",
        "previous_response_id": None,
    }


def test_text_format_is_sent_when_given(client):
    text_format = {"type": "json_schema", "name": "x", "schema": {}}

    client.process_prompt("Hi", text_format=text_format)

    assert sent_to_api(client)["text"] == {"format": text_format}


def test_language_is_added_to_the_instructions(client):
    client.process_prompt("Hi", language="Russian")

    instructions = sent_to_api(client)["instructions"]

    assert instructions.startswith(INSTRUCTIONS)
    assert instructions.endswith("Write your entire response in Russian")


def test_language_does_not_stick_to_later_prompts(client):
    client.process_prompt("Hi", language="Russian")
    client.process_prompt("Hi", language=None)

    assert sent_to_api(client)["instructions"] == INSTRUCTIONS


def test_second_prompt_continues_the_conversation(client):
    client.process_prompt("First", language=None)
    client.process_prompt("Second", language=None)

    assert sent_to_api(client)["previous_response_id"] == "resp_1"


def test_reset_starts_a_new_conversation(client):
    client.process_prompt("First", language=None)
    client.reset_conversation()
    client.process_prompt("Second", language=None)

    assert sent_to_api(client)["previous_response_id"] is None


def test_api_errors_are_wrapped(client):
    error = APIError("Service down", request=MagicMock(), body=None)
    client.client.responses.create.side_effect = error

    with pytest.raises(RuntimeError, match="Open AI API failed: Service down") as raised:
        client.process_prompt("Hi", language=None)

    assert raised.value.__cause__ is error


def test_failed_call_keeps_the_previous_response_id(client):
    client.process_prompt("First", language=None)
    client.client.responses.create.side_effect = APIError("Service down", request=MagicMock(), body=None)

    with pytest.raises(RuntimeError):
        client.process_prompt("Second", language=None)

    assert client.previous_response_id == "resp_1"
