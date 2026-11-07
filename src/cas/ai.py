import json

from cas.open_ai_client import OpenAiClient
client = OpenAiClient()

MAX_TRAITS = 3

def write_backstory(sim: str,
                    language: str | None                    
                    ) -> str:

    client.reset_conversation() #Every backstory starts fresh

    res = client.process_prompt(
        language=language,
        prompt = f"""
Write a creative backstory for this sim. The user has configured the sim with the following details. 
Your output will be displayed unedited to the user.

{sim}
"""
    )

    return res

def refine_backstory(
        sim: str,
        backstory: str,
        language: str | None,
        prompt: str
) -> str:

    client.reset_conversation() #The prompt carries all the context, so loaded sims refine correctly

    res = client.process_prompt(
        language=language,
        prompt= f"""
The user has requested that the Sim's backstory be refined in the following way.
Your output will be displayed unedited to the user.

Sim details: {sim}

Current backstory:
{backstory}

User input: {prompt}"""
    )

    return res


def _picks_format(traits: list[str], aspirations: list[str]) -> dict:
    """A strict JSON schema, so the model can only answer with names from the game data."""
    return {
        "type": "json_schema",
        "name": "sim_picks",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "traits": {
                    "type": "array",
                    "items": {"type": "string", "enum": traits},
                    "minItems": 1,
                    "maxItems": MAX_TRAITS,
                },
                "aspiration": {"type": "string", "enum": aspirations},
                "reasoning": {"type": "string"},
            },
            "required": ["traits", "aspiration", "reasoning"],
            "additionalProperties": False,
        },
    }


def pick_traits_and_aspiration(
        backstory: str,
        traits: dict[str, str],
        aspirations: dict[str, str],
) -> dict:
    """Choose traits and an aspiration that fit a backstory the user wrote.

    traits and aspirations map each name to its description. Returns a dict with
    "traits" (up to three names), "aspiration" (one name) and "reasoning".
    """

    client.reset_conversation() #Every pick starts fresh

    res = client.process_prompt(
        text_format=_picks_format(list(traits), list(aspirations)),
        prompt=f"""
The user has written a backstory for their sim. Choose the traits and the aspiration that fit it best.
Choose up to {MAX_TRAITS} different traits, usually {MAX_TRAITS}, and exactly one aspiration.
In "reasoning", explain your choices in two or three sentences, written in the same language as the backstory.
Your reasoning will be displayed unedited to the user.

Traits:
{json.dumps(traits, ensure_ascii=False)}

Aspirations:
{json.dumps(aspirations, ensure_ascii=False)}

Backstory:
{backstory}
"""
    )

    try:
        picks = json.loads(res)
    except json.JSONDecodeError as e:
        raise RuntimeError("Open AI API returned picks that weren't valid JSON") from e

    # The schema should guarantee valid names, but check anyway, since bad names would break the form.
    picked_traits = [trait for trait in dict.fromkeys(picks.get("traits", [])) if trait in traits]
    aspiration = picks.get("aspiration")

    return {
        "traits": picked_traits[:MAX_TRAITS],
        "aspiration": aspiration if aspiration in aspirations else None,
        "reasoning": picks.get("reasoning", ""),
    }