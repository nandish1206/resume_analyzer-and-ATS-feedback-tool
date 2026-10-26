
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

for model in client.models.list():
    name = getattr(model, "name", "") or ""
    methods = getattr(model, "supported_actions", None) or []

    if "generateContent" in methods:
        print(name)
