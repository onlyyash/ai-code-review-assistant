from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CodeSubmission(BaseModel):
    language: str
    question_title: str
    code: str
    review_mode: str = "General"


class CodeFeedback(BaseModel):
    pass_status: bool
    readability_score: Optional[int]
    efficiency_score: Optional[int]
    suggestions: Optional[list[str]]
    errors: Optional[list[str]]
    corrected_code: Optional[str]
    raw_ai_feedback: str
    similarity_score: Optional[float] = None
    is_similar_to_sample: Optional[bool] = None


class SampleAnswerCreate(BaseModel):
    question_title: str
    language: str
    ideal_code: str


class SubmissionRead(BaseModel):
    id: int
    language: str
    code: str
    created_at: datetime
    pass_status: Optional[bool]
    readability_score: Optional[int]
    efficiency_score: Optional[int]
    suggestions: Optional[str]
    errors: Optional[str]
    corrected_code: Optional[str]
    raw_ai_feedback: Optional[str]
    similarity_score: Optional[float]
    is_similar_to_sample: Optional[bool]

    model_config = {
        "from_attributes": True
    }
