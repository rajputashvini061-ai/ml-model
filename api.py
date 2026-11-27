"""Pure Starlette ML API backend for the SISTec Course Recommendation System."""

from __future__ import annotations

import hmac
import os

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from recommender import (
    ALL_SUBJECTS,
    OFFICIAL_NOTE,
    STREAM_SUBJECTS,
    VALID_STREAMS,
    CourseRecommender,
    load_courses,
    split_items,
)

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


def is_authorized(headers: dict[str, str] | object) -> bool:
    """Verify optional x-api-key or Authorization: Bearer token when API_KEY is set."""
    expected = os.environ.get("API_KEY", "").strip()
    if not expected:
        return True
    lowered = {str(k).lower(): str(v).strip() for k, v in dict(headers).items()}
    api_key = lowered.get("x-api-key", "")
    auth = lowered.get("authorization", "")
    bearer = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    return hmac.compare_digest(api_key or bearer, expected)


async def api_root(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "service": "SISTec Course Recommendation ML API",
            "status": "ok",
            "auth": "Optional API_KEY via 'Authorization: Bearer <API_KEY>' or 'x-api-key: <API_KEY>'",
            "endpoints": {
                "GET /api/health": "Service health check",
                "GET /api/meta": "Streams, subjects, interests, skills, and 13 SISTec courses",
                "POST /api": "Recommend SISTec courses (same as POST /api/recommend)",
                "POST /api/recommend": "Recommend SISTec courses from JSON student profile",
            },
            "sample_request": {
                "stream": "PCM",
                "subjects": ["Physics", "Chemistry", "Mathematics"],
                "interests": "Artificial Intelligence, Data Science",
                "skills": "Python, Statistics",
                "top_n": 5,
            },
        }
    )


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "total_courses": len(_ENGINE.df)})


async def meta(request: Request) -> JSONResponse:
    if not is_authorized(request.headers):
        return JSONResponse({"error": "Invalid or missing API key."}, status_code=401)
    return JSONResponse(get_meta_payload())


async def recommend_endpoint(request: Request) -> JSONResponse:
    if not is_authorized(request.headers):
        return JSONResponse({"error": "Invalid or missing API key."}, status_code=401)
    try:
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object.")
        return JSONResponse(build_recommend_payload(body))
    except (ValueError, TypeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


allowed_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app = Starlette(
    routes=[
        Route("/", api_root, methods=["GET"]),
        Route("/api", api_root, methods=["GET"]),
        Route("/api", recommend_endpoint, methods=["POST"]),
        Route("/api/health", health, methods=["GET"]),
        Route("/api/meta", meta, methods=["GET"]),
        Route("/api/recommend", recommend_endpoint, methods=["POST"]),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )
    ],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if "PORT" in os.environ else "127.0.0.1")
    uvicorn.run(app, host=host, port=port)
