from cas.ai import write_backstory
from cas.config import INSTRUCTIONS


def test_returns_the_model_output(fake_openai):
    assert write_backstory("{}", language=None) == "A backstory"


def test_prompt_contains_the_sim_details(fake_openai):
    write_backstory('{"first_name": "Terry"}', language=None)

    assert '{"first_name": "Terry"}' in fake_openai.call_args.kwargs["input"]


def test_language_reaches_the_api(fake_openai):
    write_backstory("{}", language="Russian")

    assert "Russian" in fake_openai.call_args.kwargs["instructions"]


def test_no_language_leaves_the_instructions_unchanged(fake_openai):
    write_backstory("{}", language=None)

    assert fake_openai.call_args.kwargs["instructions"] == INSTRUCTIONS


def test_each_backstory_starts_a_new_conversation(fake_openai):
    write_backstory("first sim", language=None)
    write_backstory("second sim", language=None)

    assert [call.kwargs["previous_response_id"] for call in fake_openai.call_args_list] == [None, None]
