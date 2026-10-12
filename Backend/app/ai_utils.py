import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

# An alias that Google keeps pointing at the current Flash-Lite model (works on the free tier), so the app
# doesn't break when a specific version is retired.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

MODE_INSTRUCTIONS = {
    "General": "Review the code for correctness, bugs, readability, and efficiency.",
    "Security": "Focus on security issues (input validation, injection risks, secrets, unsafe functions) and recommend fixes.",
    "Performance": "Focus on performance bottlenecks, algorithmic complexity, memory usage, and suggest optimizations.",
    "Code Style": "Focus on code style, maintainability, naming, structure, and best practices for the given language.",
}


class ReviewResult(BaseModel):
    """The shape Gemini is asked to return. Passing this as the response
    schema makes the model reply with JSON, so there is nothing to scrape
    out of Markdown."""
    bugs: list[str] = Field(default_factory=list, description="Concrete bugs or errors, one per item.")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions, one per item.")
    readability_score: int = Field(description="Readability from 1 (poor) to 10 (excellent).")
    efficiency_score: int = Field(description="Efficiency from 1 (poor) to 10 (excellent).")
    improved_code: str | None = Field(default=None, description="Full improved version of the code, or null if no change is needed.")


class AIReviewError(RuntimeError):
    pass


@lru_cache
def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise AIReviewError("GEMINI_API_KEY is not set")
    # Retry rate limits and temporary overloads with exponential backoff.
    retry = types.HttpRetryOptions(attempts=4, initial_delay=2, http_status_codes=[429, 500, 503, 504])
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(retry_options=retry))


def build_prompt(language: str, code: str, review_mode: str) -> str:
    instruction = MODE_INSTRUCTIONS.get(review_mode, MODE_INSTRUCTIONS["General"])
    return (
        "You are a senior software engineer reviewing a submission.\n"
        f"{instruction}\n"
        "Score readability and efficiency from 1 to 10. Only list bugs that are "
        "actually present; return an empty list if there are none.\n\n"
        f"Language: {language}\n"
        f"Code:\n```{language}\n{code}\n```"
    )


def _clamp(score: int) -> int:
    return max(1, min(10, score))


def get_review(language: str, code: str, review_mode: str = "General") -> tuple[ReviewResult, str]:
    """Ask Gemini for a structured review. Returns the parsed result and the
    raw JSON text (kept for the history view)."""
    try:
        response = _client().models.generate_content(
            model=GEMINI_MODEL,
            contents=build_prompt(language, code, review_mode),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReviewResult,
                temperature=0.2,
            ),
        )
    except errors.APIError as e:
        # Invalid key, retired model, quota exceeded, Gemini outage...
        raise AIReviewError(f"Gemini API error {e.code}: {e.message}") from e
    raw = response.text or ""
    result = response.parsed
    if not isinstance(result, ReviewResult):
        try:
            result = ReviewResult.model_validate_json(raw)
        except ValidationError as e:
            raise AIReviewError(f"Model returned an invalid review: {e}") from e

    result.readability_score = _clamp(result.readability_score)
    result.efficiency_score = _clamp(result.efficiency_score)
    return result, raw
