
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()


class GeminiServiceError(Exception):
    """Raised when Gemini configuration or API requests fail."""


def generate_ai_response(prompt: str) -> str:
    """
    Send a text prompt to Gemini and return the generated text.

    Args:
        prompt: The prompt to send to Gemini.

    Returns:
        Generated text from Gemini.

    Raises:
        GeminiServiceError: If configuration, request, or response fails.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if not api_key:
        raise GeminiServiceError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=model_name,
            contents=prompt.strip(),
        )

        generated_text = response.text

        if not generated_text or not generated_text.strip():
            raise GeminiServiceError(
                "Gemini returned an empty response."
            )

        return generated_text.strip()

    except GeminiServiceError:
        raise
    except Exception as exc:
        # Do not expose API keys or raw provider errors to the UI.
        raise GeminiServiceError(
            "Gemini API request failed. Check your API key, model name, "
            "internet connection, quota, and API configuration."
        ) from exc
