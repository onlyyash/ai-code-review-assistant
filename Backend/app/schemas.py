import json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

ReviewMode = Literal["General", "Security", "Performance", "Code Style"]
Language = Literal["python", "javascript"]


def _normalize(value: str) -> str:
    return value.strip().lower()


class CodeSubmission(BaseModel):
    language: Language
    question_title: str
    code: str = Field(min_length=1, max_length=20_000)
    review_mode: ReviewMode = "General"

    @field_validator("language", "question_title", mode="before")
    @classmethod
    def normalize(cls, v):
        return _normalize(v) if isinstance(v, str) else v


class SimilarityDetails(BaseModel):
    token_similarity: float
    fingerprint_similarity: float


class CodeFeedback(BaseModel):
    pass_status: bool
    readability_score: Optional[int]
    efficiency_score: Optional[int]
    suggestions: Optional[list[str]]
    errors: Optional[list[str]]
    corrected_code: Optional[str]
    raw_ai_feedback: str
    review_mode: ReviewMode = "General"
    similarity_score: Optional[float] = None
    is_similar_to_sample: Optional[bool] = None
    similarity_details: Optional[SimilarityDetails] = None


class SampleAnswerCreate(BaseModel):
    question_title: str = Field(min_length=1)
    language: Language
    ideal_code: str = Field(min_length=1)

    @field_validator("language", "question_title", mode="before")
    @classmethod
    def normalize(cls, v):
        return _normalize(v) if isinstance(v, str) else v


class SubmissionRead(BaseModel):
    id: int
    language: str
    question_title: Optional[str] = None
    review_mode: Optional[str] = None
    code: str
    created_at: datetime
    pass_status: Optional[bool]
    readability_score: Optional[int]
    efficiency_score: Optional[int]
    suggestions: list[str] = []
    errors: list[str] = []
    corrected_code: Optional[str]
    raw_ai_feedback: Optional[str]
    similarity_score: Optional[float]
    is_similar_to_sample: Optional[bool]

    model_config = {
        "from_attributes": True
    }

    @field_validator("suggestions", "errors", mode="before")
    @classmethod
    def decode_list(cls, v):
        # Stored as a JSON list; rows from older versions are comma-separated.
        if not v:
            return []
        if isinstance(v, list):
            return v
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return [part.strip() for part in v.split(", ") if part.strip()]
