from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.schemas import CodeSubmission, CodeFeedback, SampleAnswerCreate, SubmissionRead
from app.database import init_db, SessionLocal
from app.models import Submission, SampleAnswer
from app.ai_utils import get_gemini_feedback, parse_ai_feedback
from typing import List
import difflib
import os

# Load environment variables
load_dotenv()

app = FastAPI()
init_db()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/submit-code", response_model=CodeFeedback)
async def submit_code(data: CodeSubmission):
    try:
        # NEW: read review_mode safely (default = General)
        review_mode = getattr(data, "review_mode", "General")

        # Step 1: Get raw AI feedback WITH review mode
        ai_reply = get_gemini_feedback(
            data.language,
            data.code,
            review_mode
        )

        # Step 2: Parse feedback into structured fields
        parsed = parse_ai_feedback(ai_reply)

        # Step 3: Determine pass/fail status
        readability = parsed["readability_score"] or 0
        efficiency = parsed["efficiency_score"] or 0
        pass_status = readability >= 5 and efficiency >= 5

        # Step 4: Compare with sample answer
        db: Session = SessionLocal()
        sample = db.query(SampleAnswer).filter_by(
            language=data.language,
            question_title=data.question_title.strip().lower()
        ).first()

        similarity_score = None
        is_similar_to_sample = None

        if sample:
            matcher = difflib.SequenceMatcher(
                None,
                sample.ideal_code.strip(),
                data.code.strip()
            )
            similarity_score = round(matcher.ratio() * 100, 2)
            is_similar_to_sample = similarity_score >= 70

        # Step 5: Package final response
        feedback = CodeFeedback(
            pass_status=pass_status,
            readability_score=parsed["readability_score"],
            efficiency_score=parsed["efficiency_score"],
            suggestions=parsed["suggestions"],
            errors=parsed["errors"],
            corrected_code=parsed["corrected_code"],
            raw_ai_feedback=ai_reply,
            similarity_score=similarity_score,
            is_similar_to_sample=is_similar_to_sample
        )

        # Step 6: Save to DB
        db_submission = Submission(
            language=data.language,
            code=data.code,
            pass_status=feedback.pass_status,
            readability_score=feedback.readability_score,
            efficiency_score=feedback.efficiency_score,
            suggestions=", ".join(feedback.suggestions or []),
            errors=", ".join(feedback.errors or []),
            corrected_code=feedback.corrected_code,
            raw_ai_feedback=ai_reply,
            similarity_score=similarity_score,
            is_similar_to_sample=is_similar_to_sample
        )

        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        db.close()

        return feedback

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: Seed route for a sample answer
@app.post("/add-sample-answer")
def add_sample_answer(data: SampleAnswerCreate):
    db = SessionLocal()

    existing = db.query(SampleAnswer).filter_by(
        question_title=data.question_title.strip().lower(),
        language=data.language.strip().lower()
    ).first()

    if existing:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Sample answer already exists for this question and language."
        )

    sample = SampleAnswer(
        question_title=data.question_title.strip().lower(),
        language=data.language.strip().lower(),
        ideal_code=data.ideal_code.strip()
    )

    db.add(sample)
    db.commit()
    db.close()

    return {"message": "Sample answer added successfully."}


@app.get("/sample-questions")
def get_sample_questions():
    db = SessionLocal()
    samples = db.query(SampleAnswer).all()
    db.close()
    return [
        {
            "id": s.id,
            "question_title": s.question_title,
            "language": s.language,
            "ideal_code": s.ideal_code
        }
        for s in samples
    ]


@app.get("/submission-history", response_model=List[SubmissionRead])
def get_history():
    db = SessionLocal()
    records = db.query(Submission).all()
    db.close()
    return records
