from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(20))
    question_title = Column(String)
    review_mode = Column(String(20))
    code = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    pass_status = Column(Boolean)
    readability_score = Column(Integer)
    efficiency_score = Column(Integer)
    suggestions = Column(Text)         # JSON list (older rows: comma-separated)
    errors = Column(Text)              # Same
    corrected_code = Column(Text)
    raw_ai_feedback = Column(Text)
    similarity_score = Column(Float)
    is_similar_to_sample = Column(Boolean)


class SampleAnswer(Base):
    __tablename__ = "sample_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_title = Column(String, nullable=False)
    language = Column(String, nullable=False)
    ideal_code = Column(Text, nullable=False)
