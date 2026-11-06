from dotenv import load_dotenv
import os

load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

INSTRUCTIONS = """
You are a fun web application designed to help users create Sims in the Sims 4.
"""

MODEL = "gpt-5.5"