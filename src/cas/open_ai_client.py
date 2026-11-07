from openai import OpenAI, APIError
from cas.config import OPEN_AI_API_KEY, INSTRUCTIONS, MODEL


class OpenAiClient:

    def __init__(self):
        self.client = OpenAI(api_key=OPEN_AI_API_KEY)
        self.instructions = INSTRUCTIONS
        self.previous_response_id: str | None = None
        self.model = MODEL

    def process_prompt(self,
                       prompt: str,
                       language: str | None = None,
                       text_format: dict | None = None,
                       ) -> str:
        """Send a prompt and return the reply text.

        text_format is an optional Responses API format, such as a JSON schema,
        for when the reply needs a fixed structure.
        """

        if language:
            instructions = f"{self.instructions}\nWrite your entire response in {language}"
        else:
            instructions = self.instructions

        options = {"text": {"format": text_format}} if text_format else {}

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
                input=prompt,
                previous_response_id=self.previous_response_id,
                **options,
            )
            self.previous_response_id = response.id
            return response.output_text
        
        except APIError as e:
            raise RuntimeError(
                f"Open AI API failed: {e}"
            ) from e

    def reset_conversation(self):
        self.previous_response_id = None
