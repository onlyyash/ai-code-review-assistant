import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

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
    return genai.Client(api_key=api_key)


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
    response = _client().models.generate_content(
        model=GEMINI_MODEL,
        contents=build_prompt(language, code, review_mode),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReviewResult,
            temperature=0.2,
        ),
    )
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
