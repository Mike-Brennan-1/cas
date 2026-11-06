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