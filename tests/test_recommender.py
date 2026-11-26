"""Tests for CSV handling, all 5 Class 12 streams, TF-IDF engine, and Starlette API."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from api import build_recommend_payload, get_meta_payload, is_authorized
from recommender import CourseRecommender, STREAM_SUBJECTS, VALID_STREAMS, load_courses
from train_model import recommend_courses


class TestCourseRecommendationSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = CourseRecommender(load_courses())

    def test_csv_missing_and_whitespace_handling(self) -> None:
        raw = (
            "programme,level,department,campus,interests,skills,subjects,eligible_streams,required_subjects,eligibility_criteria,career_paths,eligibility_source\n"
            "  Test Course , B.Tech , CS , , AI ; ML , Python ; , Algo , PCM ; PCMB , Physics ; Chemistry ; Mathematics , 10+2 , Dev , \n"
            ",,,,,,,,,,,\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.csv"
            p.write_text(raw, encoding="utf-8")
            df = load_courses(p)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "programme"], "Test Course")
        self.assertEqual(df.loc[0, "interests"], "AI;ML")

    def test_all_five_streams(self) -> None:
        cases = {
            "PCM": ("Artificial Intelligence, Data Science", "Python, Statistics", 12, "CSE with Artificial Intelligence and Data Science"),
            "PCB": ("Healthcare, Medicines", "Laboratory Skills, Research", 2, "Bachelor of Pharmacy"),
            "PCMB": ("Cyber Security, Network Security", "Networking, Programming", 13, "CSE with Cyber Security"),
            "Commerce": ("Business, Marketing, Finance", "Communication, Leadership", 1, "Bachelor of Business Administration"),
            "Arts": ("Entrepreneurship, Management", "Communication, Decision Making", 1, "Bachelor of Business Administration"),
        }
        for stream, (interests, skills, expected_count, expected_top) in cases.items():
            recs, inelig = self.engine.recommend(stream, STREAM_SUBJECTS[stream], interests, skills, top_n=13)
            self.assertEqual(len(recs), expected_count, stream)
            self.assertEqual(len(recs) + len(inelig), 13)
            self.assertEqual(recs.loc[0, "programme"], expected_top)
            self.assertGreater(recs.loc[0, "match_score"], 0.0)
            self.assertTrue(recs.loc[0, "recommendation_reason"])

    def test_edge_cases_and_bug_fixes(self) -> None:
        custom = self.engine.df.head(1).copy()
        custom.loc[0, "eligible_streams"] = "Arts"
        custom.loc[0, "required_subjects"] = "History;Information Practices"
        eng = CourseRecommender(custom)
        self.assertEqual(len(eng.recommend("Arts", ["History"], "Design", "CAD")[0]), 0)
        self.assertEqual(len(eng.recommend("Arts", ["History", "Information Practices"], "Design", "CAD")[0]), 1)

        custom.loc[0, "required_subjects"] = ""
        self.assertEqual(len(CourseRecommender(custom).recommend("Arts", ["History"], "Design", "CAD")[0]), 0)

        self.assertGreater(self.engine.recommend("PCM", STREAM_SUBJECTS["PCM"], "Programming", "C")[0]["match_score"].max(), 0.0)
        self.assertTrue((self.engine.recommend("PCM", STREAM_SUBJECTS["PCM"], "", "")[0]["match_score"] == 0.0).all())

        with self.assertRaises(ValueError):
            self.engine.recommend("Diploma", [], "AI", "Python")

    def test_train_model_and_api_payloads(self) -> None:
        meta = get_meta_payload()
        self.assertEqual(len(meta["courses"]), 13)
        self.assertTrue(is_authorized({}))
        os.environ["API_KEY"] = "secret-test-key"
        try:
            self.assertFalse(is_authorized({}))
            self.assertTrue(is_authorized({"x-api-key": "secret-test-key"}))
            self.assertTrue(is_authorized({"Authorization": "Bearer secret-test-key"}))
        finally:
            os.environ.pop("API_KEY", None)
        for stream in VALID_STREAMS:
            df = recommend_courses(stream, STREAM_SUBJECTS[stream], "Technology, Business, Healthcare", "Python, Communication")
            self.assertFalse(df.empty)
            res = build_recommend_payload({"stream": stream, "subjects": STREAM_SUBJECTS[stream], "interests": "Business, AI, Healthcare", "skills": "Python, Communication", "top_n": 5})
            self.assertGreater(res["total_eligible"], 0)
            self.assertTrue(res["recommendations"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
