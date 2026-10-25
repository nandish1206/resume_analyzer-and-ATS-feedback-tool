
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiServiceError(Exception):
    """Raised when Gemini configuration or API requests fail."""


def generate_ai_response(prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt must be a non-empty string.")

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL")

    if not api_key:
        raise GeminiServiceError(
            "GEMINI_API_KEY is missing from the .env file."
        )

    if not model_name:
        raise GeminiServiceError(
            "GEMINI_MODEL is missing from the .env file."
        )

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=60000),
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt.strip(),
            config=types.GenerateContentConfig(
                max_output_tokens=1024,
                response_mime_type="application/json",
            ),
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
        logger.exception(
            "Gemini request failed for configured model %s",
            model_name,
        )
        raise GeminiServiceError(
            "Gemini request failed. Check the terminal logs for details."
        ) from exc
