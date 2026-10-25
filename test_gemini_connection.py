
from app.utils.gemini_service import (
    generate_ai_response,
    GeminiServiceError,
)

try:
    result = generate_ai_response(
        "Reply with exactly this text: Gemini connection successful."
    )
    print("Gemini connection successful!")
    print("Response:", result)

except (GeminiServiceError, ValueError) as exc:
    print("Gemini test failed:", exc)
