"""Print the Gemini models available to the key in .env (set GEMINI_MODEL to one of them)."""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Available models for this key:")
for model in client.models.list():
    print(f"- {model.name} | {model.supported_actions}")
