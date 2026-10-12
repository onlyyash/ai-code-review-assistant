import json
import os
from contextlib import asynccontextmanager
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.ai_utils import AIReviewError, get_review
from app.database import get_db, init_db
from app.models import SampleAnswer, Submission
from app.schemas import (
    CodeFeedback,
    CodeSubmission,
    SampleAnswerCreate,
    SimilarityDetails,
    SubmissionRead,
)
from app.similarity import compare

load_dotenv()

PASS_THRESHOLD = 5
SIMILARITY_THRESHOLD = 70


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Code Reviewer", lifespan=lifespan)

# Comma-separated list of allowed frontend origins, e.g. "https://my-app.vercel.app"
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# A plain `def` (not `async def`): the Gemini call blocks, and FastAPI runs
# sync endpoints in a thread pool so other requests are not held up.
@app.post("/submit-code", response_model=CodeFeedback)
def submit_code(data: CodeSubmission, db: Session = Depends(get_db)):
    try:
        review, raw = get_review(data.language, data.code, data.review_mode)
    except AIReviewError as e:
        raise HTTPException(status_code=502, detail=str(e))

    pass_status = (
        review.readability_score >= PASS_THRESHOLD
        and review.efficiency_score >= PASS_THRESHOLD
    )

    sample = db.query(SampleAnswer).filter_by(
        language=data.language,
        question_title=data.question_title,
    ).first()

    similarity_score = None
    is_similar_to_sample = None
    similarity_details = None
    if sample:
        result = compare(sample.ideal_code, data.code, data.language)
        similarity_score = result["score"]
        is_similar_to_sample = similarity_score >= SIMILARITY_THRESHOLD
        similarity_details = SimilarityDetails(
            token_similarity=result["token_similarity"],
            fingerprint_similarity=result["fingerprint_similarity"],
        )

    feedback = CodeFeedback(
        pass_status=pass_status,
        readability_score=review.readability_score,
        efficiency_score=review.efficiency_score,
        suggestions=review.suggestions,
        errors=review.bugs,
        corrected_code=review.improved_code,
        raw_ai_feedback=raw,
        review_mode=data.review_mode,
        similarity_score=similarity_score,
        is_similar_to_sample=is_similar_to_sample,
        similarity_details=similarity_details,
    )

    db.add(Submission(
        language=data.language,
        question_title=data.question_title,
        review_mode=data.review_mode,
        code=data.code,
        pass_status=feedback.pass_status,
        readability_score=feedback.readability_score,
        efficiency_score=feedback.efficiency_score,
        suggestions=json.dumps(feedback.suggestions),
        errors=json.dumps(feedback.errors),
        corrected_code=feedback.corrected_code,
        raw_ai_feedback=raw,
        similarity_score=similarity_score,
        is_similar_to_sample=is_similar_to_sample,
    ))
    db.commit()

    return feedback


@app.post("/add-sample-answer", status_code=201)
def add_sample_answer(data: SampleAnswerCreate, db: Session = Depends(get_db)):
    existing = db.query(SampleAnswer).filter_by(
        question_title=data.question_title,
        language=data.language,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Sample answer already exists for this question and language."
        )

    db.add(SampleAnswer(
        question_title=data.question_title,
        language=data.language,
        ideal_code=data.ideal_code.strip(),
    ))
    db.commit()
    return {"message": "Sample answer added successfully."}


@app.get("/sample-questions")
def get_sample_questions(db: Session = Depends(get_db)):
    return [
        {
            "id": s.id,
            "question_title": s.question_title,
            "language": s.language,
            "ideal_code": s.ideal_code,
        }
        for s in db.query(SampleAnswer).order_by(SampleAnswer.question_title).all()
    ]


@app.get("/submission-history", response_model=List[SubmissionRead])
def get_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(Submission)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
