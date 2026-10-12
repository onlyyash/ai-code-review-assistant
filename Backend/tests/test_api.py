import json

from app import main
from app.ai_utils import AIReviewError, ReviewResult, build_prompt


def add_sample(client, title="Two Sum", language="python", code="def f(a, b):\n    return a + b"):
    return client.post("/add-sample-answer", json={
        "question_title": title, "language": language, "ideal_code": code,
    })


def test_submit_returns_structured_feedback(client):
    r = client.post("/submit-code", json={
        "language": "python", "question_title": "anything", "code": "print(1)",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["pass_status"] is True
    assert body["errors"] == ["Off-by-one in loop"]
    assert body["corrected_code"] == "print('fixed')"
    assert body["similarity_score"] is None  # no sample for this question


def test_review_mode_is_passed_to_the_model(client):
    client.post("/submit-code", json={
        "language": "python", "question_title": "q", "code": "x = 1", "review_mode": "Security",
    })
    assert client.review_calls[-1]["review_mode"] == "Security"


def test_unknown_review_mode_is_rejected(client):
    r = client.post("/submit-code", json={
        "language": "python", "question_title": "q", "code": "x = 1", "review_mode": "Vibes",
    })
    assert r.status_code == 422


def test_sample_lookup_ignores_case_and_whitespace(client):
    assert add_sample(client, title="Two Sum").status_code == 201
    r = client.post("/submit-code", json={
        "language": "Python", "question_title": "  TWO SUM ",
        "code": "def g(x, y):\n    return x + y",
    })
    body = r.json()
    assert body["similarity_score"] == 100
    assert body["is_similar_to_sample"] is True
    assert set(body["similarity_details"]) == {"token_similarity", "fingerprint_similarity"}


def test_duplicate_sample_is_rejected(client):
    add_sample(client)
    assert add_sample(client, title="two sum ").status_code == 400


def test_suggestions_with_commas_survive_the_round_trip(client):
    client.post("/submit-code", json={"language": "python", "question_title": "q", "code": "x = 1"})
    history = client.get("/submission-history").json()
    # Stored as JSON, so "Add type hints, e.g. list[int]" is not split in two.
    assert history[0]["suggestions"] == ["Use a list comprehension", "Add type hints, e.g. list[int]"]


def test_history_is_newest_first_and_paginated(client):
    for i in range(3):
        client.post("/submit-code", json={"language": "python", "question_title": f"q{i}", "code": f"x = {i}"})
    history = client.get("/submission-history?limit=2").json()
    assert [h["question_title"] for h in history] == ["q2", "q1"]


def test_legacy_comma_separated_rows_still_load(client):
    from app.database import SessionLocal
    from app.models import Submission
    db = SessionLocal()
    db.add(Submission(language="python", code="x", suggestions="one, two", errors=""))
    db.commit()
    db.close()
    assert client.get("/submission-history").json()[0]["suggestions"] == ["one", "two"]


def test_model_failure_returns_502(client, monkeypatch):
    def broken(*args, **kwargs):
        raise AIReviewError("Model returned an invalid review")
    monkeypatch.setattr(main, "get_review", broken)
    r = client.post("/submit-code", json={"language": "python", "question_title": "q", "code": "x = 1"})
    assert r.status_code == 502


def test_prompt_includes_mode_instruction():
    assert "security issues" in build_prompt("python", "x = 1", "Security")


def test_review_schema_round_trips():
    data = {"bugs": [], "suggestions": ["a"], "readability_score": 8, "efficiency_score": 9, "improved_code": None}
    assert ReviewResult.model_validate_json(json.dumps(data)).suggestions == ["a"]
