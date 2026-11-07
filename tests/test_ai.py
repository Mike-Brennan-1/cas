import json
from types import SimpleNamespace

import pytest

from cas.ai import pick_traits_and_aspiration, write_backstory
from cas.config import INSTRUCTIONS

TRAITS = {"Creative": "Loves making things.", "Genius": "Very clever.", "Gloomy": "Often sad.", "Goofball": "Silly."}
ASPIRATIONS = {"Bestselling Author": "Write a hit novel.", "Renaissance Sim": "Master many skills."}


def model_picks(fake_openai, **picks):
    fake_openai.return_value = SimpleNamespace(id="resp_1", output_text=json.dumps(picks))


def pick(backstory="Terry wrote poems in the dark."):
    return pick_traits_and_aspiration(backstory, traits=TRAITS, aspirations=ASPIRATIONS)


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


def test_picks_are_returned(fake_openai):
    model_picks(fake_openai, traits=["Creative", "Gloomy"], aspiration="Bestselling Author", reasoning="Poems.")

    assert pick() == {"traits": ["Creative", "Gloomy"], "aspiration": "Bestselling Author", "reasoning": "Poems."}


def test_pick_prompt_contains_the_backstory_and_descriptions(fake_openai):
    model_picks(fake_openai, traits=["Creative"], aspiration="Bestselling Author", reasoning="")

    pick("Terry wrote poems in the dark.")

    prompt = fake_openai.call_args.kwargs["input"]
    assert "Terry wrote poems in the dark." in prompt
    assert "Loves making things." in prompt
    assert "Write a hit novel." in prompt


def test_pick_schema_only_allows_known_names(fake_openai):
    model_picks(fake_openai, traits=["Creative"], aspiration="Bestselling Author", reasoning="")

    pick()

    text_format = fake_openai.call_args.kwargs["text"]["format"]
    properties = text_format["schema"]["properties"]
    assert text_format["strict"] is True
    assert properties["traits"]["items"]["enum"] == list(TRAITS)
    assert properties["traits"]["maxItems"] == 3
    assert properties["aspiration"]["enum"] == list(ASPIRATIONS)


def test_unknown_and_repeated_names_are_dropped(fake_openai):
    model_picks(
        fake_openai,
        traits=["Creative", "Creative", "Made Up", "Genius", "Gloomy", "Goofball"],
        aspiration="Made Up",
        reasoning="",
    )

    picks = pick()

    assert picks["traits"] == ["Creative", "Genius", "Gloomy"]
    assert picks["aspiration"] is None


def test_invalid_json_raises_a_runtime_error(fake_openai):
    fake_openai.return_value = SimpleNamespace(id="resp_1", output_text="not json")

    with pytest.raises(RuntimeError, match="valid JSON"):
        pick()


def test_each_pick_starts_a_new_conversation(fake_openai):
    model_picks(fake_openai, traits=["Creative"], aspiration="Bestselling Author", reasoning="")

    pick()
    pick()

    assert [call.kwargs["previous_response_id"] for call in fake_openai.call_args_list] == [None, None]
