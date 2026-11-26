"""Lightweight Starlette API linking the HTML/CSS/JS frontend to recommender.py."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from recommender import (
    ALL_SUBJECTS,
    OFFICIAL_NOTE,
    STREAM_SUBJECTS,
    VALID_STREAMS,
    CourseRecommender,
    load_courses,
    split_items,
)

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
_ENGINE = CourseRecommender(load_courses())


def get_meta_payload() -> dict:
    """Build metadata payload for initializing the frontend controls and catalog."""
    df = _ENGINE.df
    return {
        "streams": list(VALID_STREAMS),
        "stream_subjects": STREAM_SUBJECTS,
        "all_subjects": ALL_SUBJECTS,
        "interests": sorted({t for v in df["interests"] for t in split_items(v)}, key=str.lower),
        "skills": sorted({t for v in df["skills"] for t in split_items(v)}, key=str.lower),
        "official_note": OFFICIAL_NOTE,
        "courses": df[["programme", "level", "department", "campus", "eligible_streams", "required_subjects", "eligibility_criteria"]].to_dict("records"),
    }


def build_recommend_payload(body: dict) -> dict:
    """Run eligibility + TF-IDF recommendation from a JSON request payload."""
    stream = body.get("stream", "PCM")
    subjects = body.get("subjects", [])
    interests = body.get("interests", "")
    skills = body.get("skills", "")
    top_n = max(1, min(int(body.get("top_n", 5)), len(_ENGINE.df)))

    recs, inelig = _ENGINE.recommend(stream, subjects, interests, skills, top_n=top_n)
    return {
        "stream": stream,
        "total_courses": len(_ENGINE.df),
        "total_eligible": len(_ENGINE.df) - len(inelig),
        "recommendations": recs.to_dict("records"),
        "ineligible_courses": inelig[["programme", "level", "department", "eligible_streams", "required_subjects", "eligibility_note"]].to_dict("records"),
    }


async def index(_: Request) -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


async def meta(_: Request) -> JSONResponse:
    return JSONResponse(get_meta_payload())


async def recommend_endpoint(request: Request) -> JSONResponse:
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object.")
        return JSONResponse(build_recommend_payload(body))
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/meta", meta, methods=["GET"]),
        Route("/api/recommend", recommend_endpoint, methods=["POST"]),
        Mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static"),
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if "PORT" in os.environ else "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
