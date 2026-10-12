import os
import tempfile

import pytest

# Point the app at a throwaway database before it is imported.
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from app.ai_utils import ReviewResult  # noqa: E402
from app.database import engine  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    """A test client with an empty database and a fake Gemini call."""
    Base.metadata.drop_all(bind=engine)

    calls = []

    def fake_review(language, code, review_mode="General"):
        calls.append({"language": language, "code": code, "review_mode": review_mode})
        result = ReviewResult(
            bugs=["Off-by-one in loop"],
            suggestions=["Use a list comprehension", "Add type hints, e.g. list[int]"],
            readability_score=7,
            efficiency_score=6,
            improved_code="print('fixed')",
        )
        return result, result.model_dump_json()

    monkeypatch.setattr(main, "get_review", fake_review)
    with TestClient(main.app) as c:
        c.review_calls = calls
        yield c
