from cas.open_ai_client import OpenAiClient
client = OpenAiClient()

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