"""CLI entry point and reusable wrapper for SISTec Course Recommendation."""

from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import pandas as pd

from recommender import CourseRecommender, load_courses

OUTPUT_COLS = ["programme", "level", "department", "campus", "match_score", "recommendation_reason"]


@lru_cache(maxsize=1)
def get_recommender() -> CourseRecommender:
    return CourseRecommender(load_courses())


def recommend_courses(
    student_stream: str,
    student_subjects: Sequence[str] | str | None,
    student_interests: Sequence[str] | str,
    student_skills: Sequence[str] | str,
    top_n: int = 5,
) -> pd.DataFrame:
    """Return top-N eligible SISTec course recommendations with scores and reasons."""
    recs, _ = get_recommender().recommend(student_stream, student_subjects, student_interests, student_skills, top_n)
    return recs[OUTPUT_COLS].copy() if not recs.empty else pd.DataFrame(columns=OUTPUT_COLS)


if __name__ == "__main__":
    engine = get_recommender()
    print(f"ML Model Ready | Courses: {len(engine.df)} | TF-IDF Matrix: {engine.feature_matrix.shape}")

    samples = {
        "PCM": (["Physics", "Chemistry", "Mathematics"], "Artificial Intelligence, Data Science", "Python, Statistics"),
        "PCB": (["Physics", "Chemistry", "Biology"], "Healthcare, Medicines, Pharmacy", "Laboratory Skills, Research"),
        "PCMB": (["Physics", "Chemistry", "Mathematics", "Biology"], "Robotics, Automation, Healthcare", "Python, Problem Solving"),
        "Commerce": (["Accountancy", "Business Studies", "Economics"], "Business, Marketing, Finance", "Communication, Leadership"),
        "Arts": (["History", "Political Science", "Sociology"], "Entrepreneurship, Management", "Communication, Decision Making"),
    }
    for stream, (subjects, interests, skills) in samples.items():
        print(f"\n=== {stream} ===")
        print(recommend_courses(stream, subjects, interests, skills, top_n=5).to_string(index=False))
