"""Modular data loading, eligibility filtering, and TF-IDF recommender for SISTec."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATASET_PATH = Path(__file__).resolve().parent / "courses.csv"
VALID_STREAMS = ("PCM", "PCB", "PCMB", "Commerce", "Arts")
STREAM_SUBJECTS = {
    "PCM": ["Physics", "Chemistry", "Mathematics"],
    "PCB": ["Physics", "Chemistry", "Biology"],
    "PCMB": ["Physics", "Chemistry", "Mathematics", "Biology"],
    "Commerce": ["Accountancy", "Business Studies", "Economics"],
    "Arts": ["History", "Political Science", "Sociology", "Economics"],
}
ALL_SUBJECTS = list(dict.fromkeys(
    [s for lst in STREAM_SUBJECTS.values() for s in lst]
    + ["Computer Science", "Information Practices", "Biotechnology", "Psychology", "English"]
))
OFFICIAL_NOTE = (
    "App filtering uses simplified stream/subject columns in courses.csv. "
    "Official admission eligibility (marks, relaxations, branch rules, Math/Bio/Biotech options) "
    "follows current SISTec, DTE MP, RGPV, and PCI norms."
)
REQUIRED_COLS = ("programme", "level", "department", "eligible_streams", "required_subjects")
TEXT_COLS = REQUIRED_COLS + ("campus", "interests", "skills", "subjects", "eligibility_criteria", "career_paths", "eligibility_source")
SEMICOLON_COLS = ("interests", "skills", "subjects", "eligible_streams", "required_subjects", "career_paths")


def split_items(value: object, pattern: str = ";") -> list[str]:
    """Split a delimited string into unique, trimmed items preserving order."""
    if value is None or pd.isna(value):
        return []
    seen, items = set(), []
    for raw in re.split(pattern, str(value)):
        cleaned = " ".join(raw.split()).strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            items.append(cleaned)
    return items


def load_courses(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Load, clean, and validate courses.csv while handling missing values."""
    path = Path(csv_path) if csv_path else DATASET_PATH
    if not path.exists():
        raise FileNotFoundError(f"Course dataset not found: {path}")

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(missing)}")

    for col in TEXT_COLS:
        df[col] = df[col].fillna("").astype(str).map(lambda x: " ".join(x.split())) if col in df.columns else ""
    df = df[df["programme"] != ""].reset_index(drop=True)
    for col in SEMICOLON_COLS:
        df[col] = df[col].map(lambda v: ";".join(split_items(v)))
    if df.empty:
        raise ValueError("Course dataset contains no valid rows.")
    return df


def normalize_stream(stream: str | None) -> str:
    if not isinstance(stream, str) or not stream.strip():
        raise ValueError(f"Stream is required ({', '.join(VALID_STREAMS)}).")
    for valid in VALID_STREAMS:
        if valid.lower() == stream.strip().lower():
            return valid
    raise ValueError(f"Unsupported stream '{stream}'. Choose from: {', '.join(VALID_STREAMS)}")


def normalize_subjects(subjects: Sequence[str] | str | None) -> list[str]:
    if subjects is None:
        return []
    if isinstance(subjects, str):
        return split_items(subjects, r"[,;]+")
    return split_items(";".join(str(s) for s in subjects))


def check_eligibility(row: pd.Series, stream: str, subject_set: set[str]) -> tuple[bool, str]:
    """Check whether a course passes the dataset's stream and subject pre-filter."""
    allowed = split_items(row["eligible_streams"])
    if not allowed or stream.lower() not in {s.lower() for s in allowed}:
        return False, f"Requires stream {', '.join(allowed) or 'N/A'} (selected: {stream})."

    req = str(row["required_subjects"]).strip()
    if not req:
        return False, "Required subjects missing in courses.csv; verify official guidelines."
    if req.lower() == "10+2 pass":
        return True, f"Eligible via {stream} (Class 12 pass from any recognized stream)."

    # Split only on standalone 'or' so words like 'Information' or 'History' stay intact.
    groups = [split_items(g) for g in re.split(r"\s+or\s+", req, flags=re.IGNORECASE) if g.strip()]
    for group in groups:
        if group and all(item.lower() in subject_set for item in group):
            return True, f"Matches {stream} and required subjects ({', '.join(group)})."

    missing = min(([item for item in g if item.lower() not in subject_set] for g in groups if g), key=len, default=[])
    return False, f"Missing required subject(s): {', '.join(missing)}."


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"(?u)\b\w+\b", text.lower()) if w not in ENGLISH_STOP_WORDS and (len(w) > 1 or w == "c")}


def _matched_tags(course_val: str, user_phrases: list[str], user_words: set[str]) -> list[str]:
    hits = []
    for item in split_items(course_val):
        low = item.lower()
        if any(p == low or (len(p) >= 3 and (p in low or low in p)) for p in user_phrases) or (_words(item) & user_words):
            hits.append(item)
    return hits


class CourseRecommender:
    """TF-IDF + Cosine Similarity recommender scoped to eligible SISTec courses."""

    def __init__(self, courses_df: pd.DataFrame) -> None:
        self.df = courses_df.reset_index(drop=True).copy()
        text = self.df[["programme", "department", "interests", "skills", "subjects", "career_paths"]].agg(" ".join, axis=1).str.replace(";", " ", regex=False)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b", stop_words="english")
        self.feature_matrix = self.vectorizer.fit_transform(text)
        self.terms = self.vectorizer.get_feature_names_out()
        self.similarity_matrix = cosine_similarity(self.feature_matrix)

    def _reason(self, row: pd.Series, idx: int, score: float, student_vec, phrases: list[str], words: set[str]) -> str:
        interests = _matched_tags(row["interests"], phrases, words)
        skills = _matched_tags(row["skills"], phrases, words)
        subjects = _matched_tags(row["subjects"], phrases, words)
        parts = []
        if interests:
            parts.append(f"Aligns with your interests ({', '.join(interests[:3])})")
        if skills:
            parts.append(f"matches your skills ({', '.join(skills[:3])})")
        if subjects:
            parts.append(f"covers {', '.join(subjects[:2])}")
        if parts:
            text = "; ".join(parts) + "."
            return text[0].upper() + text[1:]
        if score > 0:
            overlap = student_vec.multiply(self.feature_matrix[idx])
            top_terms = [str(self.terms[i]) for i, _ in sorted(zip(overlap.indices, overlap.data), key=lambda p: p[1], reverse=True)[:4]]
            if top_terms:
                return f"Matches profile keywords ({', '.join(top_terms)}) in {row['department']}."
        return "Eligible by stream and subjects; add matching interests/skills for personalized ranking."

    def recommend(self, student_stream: str, student_subjects: Sequence[str] | str | None, student_interests: Sequence[str] | str = "", student_skills: Sequence[str] | str = "", top_n: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
        stream = normalize_stream(student_stream)
        subjects = normalize_subjects(student_subjects)
        subject_set = {s.lower() for s in subjects}

        notes = [check_eligibility(row, stream, subject_set) for _, row in self.df.iterrows()]
        annotated = self.df.copy()
        annotated["eligibility_passed"] = [ok for ok, _ in notes]
        annotated["eligibility_note"] = [msg for _, msg in notes]
        eligible = annotated[annotated["eligibility_passed"]].copy()
        ineligible = annotated[~annotated["eligibility_passed"]].copy()
        if eligible.empty:
            return pd.DataFrame(columns=list(self.df.columns) + ["match_score", "recommendation_reason", "eligibility_note"]), ineligible

        interests_txt = ", ".join(student_interests) if not isinstance(student_interests, str) else student_interests
        skills_txt = ", ".join(student_skills) if not isinstance(student_skills, str) else student_skills
        profile = re.sub(r"[;,/|]+", " ", f"{interests_txt} {skills_txt}").strip()
        student_vec = self.vectorizer.transform([profile])
        scores = cosine_similarity(student_vec, self.feature_matrix)[0] if profile else np.zeros(len(self.df))

        ranked = sorted(eligible.index.tolist(), key=lambda i: (-float(scores[i]), i))[:max(1, top_n)]
        phrases = [p.lower() for p in split_items(f"{interests_txt},{skills_txt}", r"[,;\n]+")]
        words = _words(f"{interests_txt} {skills_txt}")

        recs = eligible.loc[ranked].copy()
        recs["match_score"] = [round(float(scores[i]) * 100, 2) for i in ranked]
        recs["recommendation_reason"] = [self._reason(eligible.loc[i], i, recs.loc[i, "match_score"], student_vec, phrases, words) for i in ranked]
        return recs.reset_index(drop=True), ineligible.reset_index(drop=True)
