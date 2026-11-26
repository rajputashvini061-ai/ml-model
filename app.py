"""Streamlit web application for the SISTec Course Recommendation System."""

from __future__ import annotations

import html

import streamlit as st

from recommender import (
    ALL_SUBJECTS,
    OFFICIAL_NOTE,
    STREAM_SUBJECTS,
    VALID_STREAMS,
    CourseRecommender,
    load_courses,
    split_items,
)

st.set_page_config(page_title="SISTec Course Recommender", page_icon="🎓", layout="wide")

SAMPLE_PROFILES = {
    "PCM": (["Artificial Intelligence", "Data Science", "Programming"], ["Python", "Statistics", "Problem Solving"]),
    "PCB": (["Healthcare", "Medicines", "Pharmaceutical Science"], ["Laboratory Skills", "Scientific Analysis", "Research"]),
    "PCMB": (["Robotics", "Automation", "Healthcare"], ["Python", "Problem Solving", "Research"]),
    "Commerce": (["Business", "Marketing", "Finance"], ["Communication", "Leadership", "Business Analysis"]),
    "Arts": (["Entrepreneurship", "Management", "Marketing"], ["Communication", "Leadership", "Decision Making"]),
}

UI_CSS = """
<style>
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1180px; }
.hero {
    background: linear-gradient(120deg, #0f172a 0%, #1e3a8a 58%, #0284c7 100%);
    padding: 1.25rem 1.5rem; border-radius: 12px; color: #fff; margin-bottom: 1rem;
}
.hero h1 { margin: 0 0 0.3rem 0; font-size: 1.65rem; font-weight: 700; color: #fff; }
.hero p { margin: 0; font-size: 0.94rem; color: #e2e8f0; }
.card {
    background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #0284c7;
    border-radius: 10px; padding: 1rem 1.15rem; margin-bottom: 0.4rem;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}
.card-top { display: flex; justify-content: space-between; align-items: center; gap: 0.8rem; flex-wrap: wrap; }
.card-title { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 0; }
.card-meta { font-size: 0.86rem; color: #475569; margin-top: 0.2rem; }
.pill { display: inline-block; padding: 0.18rem 0.6rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }
.pill-deg { background: #dbeafe; color: #1e40af; margin-right: 0.35rem; }
.pill-ok { background: #dcfce7; color: #166534; }
.pill-wait { background: #f1f5f9; color: #475569; }
.reason { background: #f8fafc; border-radius: 8px; padding: 0.6rem 0.8rem; margin-top: 0.65rem; font-size: 0.9rem; color: #1e293b; }
</style>
"""


@st.cache_resource
def get_engine() -> tuple[CourseRecommender, list[str], list[str]]:
    df = load_courses()
    interests = sorted({t for val in df["interests"] for t in split_items(val)}, key=str.lower)
    skills = sorted({t for val in df["skills"] for t in split_items(val)}, key=str.lower)
    return CourseRecommender(df), interests, skills


def _apply_stream_defaults() -> None:
    stream = st.session_state["stream"]
    st.session_state["subjects"] = list(STREAM_SUBJECTS[stream])
    sample_i, sample_s = SAMPLE_PROFILES[stream]
    st.session_state["picked_interests"] = [x for x in sample_i if x in st.session_state["all_interests"]]
    st.session_state["picked_skills"] = [x for x in sample_s if x in st.session_state["all_skills"]]


def main() -> None:
    st.markdown(UI_CSS, unsafe_allow_html=True)
    engine, interest_opts, skill_opts = get_engine()
    st.session_state["all_interests"], st.session_state["all_skills"] = interest_opts, skill_opts

    if "stream" not in st.session_state:
        st.session_state["stream"] = "PCM"
        _apply_stream_defaults()

    st.markdown(
        '<div class="hero"><h1>🎓 SISTec Course Recommendation System</h1>'
        '<p>Class 12 stream & subject eligibility filtering + TF-IDF & Cosine Similarity matching across SISTec UG courses.</p></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Student Profile")
        stream = st.selectbox("Class 12 Stream", VALID_STREAMS, key="stream", on_change=_apply_stream_defaults)
        subjects = st.multiselect("Class 12 Subjects", ALL_SUBJECTS, key="subjects")
        picked_interests = st.multiselect("Interests", interest_opts, key="picked_interests")
        custom_interests = st.text_input("Other interests (comma-separated)", placeholder="e.g., AI, Robotics, Finance")
        picked_skills = st.multiselect("Skills", skill_opts, key="picked_skills")
        custom_skills = st.text_input("Other skills (comma-separated)", placeholder="e.g., Python, Communication")
        top_n = st.slider("Max recommendations", 1, len(engine.df), 5)

    interests = ", ".join(p for p in [*picked_interests, custom_interests.strip()] if p)
    skills = ", ".join(p for p in [*picked_skills, custom_skills.strip()] if p)
    recs, inelig = engine.recommend(stream, subjects, interests, skills, top_n=top_n)

    with st.expander("Official Admission Eligibility vs. Recommendation Logic"):
        st.info(OFFICIAL_NOTE)
        st.caption("Pre-filter uses `eligible_streams` and `required_subjects` from courses.csv; ranking uses TF-IDF + Cosine Similarity on your interests and skills.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected Stream", stream)
    c2.metric("Eligible SISTec Courses", f"{len(engine.df) - len(inelig)} / {len(engine.df)}")
    c3.metric("Top Match Score", f"{recs['match_score'].max():.2f}%" if not recs.empty else "0.00%")

    tab_rec, tab_filtered, tab_all = st.tabs(["Recommended Courses", "Filtered-Out Courses", "All SISTec Courses"])

    with tab_rec:
        if recs.empty:
            st.error("No SISTec courses matched your stream and selected subjects. Adjust subjects in the sidebar.")
        else:
            if not interests and not skills:
                st.info("Add interests or skills in the sidebar for personalized match scores.")
            for rank, (_, row) in enumerate(recs.iterrows(), start=1):
                score = float(row["match_score"])
                pill_cls = "pill-ok" if score > 0 else "pill-wait"
                pill_txt = f"Match: {score:.2f}%" if (interests or skills) else "Awaiting Interests"
                careers = ", ".join(split_items(row["career_paths"])) or "Not listed"
                st.markdown(
                    f'<div class="card"><div class="card-top">'
                    f'<div><div class="card-title">#{rank}. {html.escape(row["programme"])}</div>'
                    f'<div class="card-meta"><span class="pill pill-deg">{html.escape(row["level"])}</span>'
                    f'<strong>Dept:</strong> {html.escape(row["department"])} &nbsp;|&nbsp; '
                    f'<strong>Campus:</strong> {html.escape(row["campus"] or "Verify Campus")}</div></div>'
                    f'<span class="pill {pill_cls}">{pill_txt}</span></div>'
                    f'<div class="reason"><strong>Why recommended:</strong> {html.escape(row["recommendation_reason"])}'
                    f'<div class="card-meta" style="margin-top:0.35rem;"><strong>Career paths:</strong> {html.escape(careers)}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
                if score > 0:
                    st.progress(min(max(score / 100.0, 0.0), 1.0))
                with st.expander(f"Official Eligibility Details — {row['programme']}"):
                    st.write(f"**Allowed Streams (App Filter):** {', '.join(split_items(row['eligible_streams']))} | **Required Subjects:** {', '.join(split_items(row['required_subjects']))}")
                    st.write(f"**Official Criteria:** {row['eligibility_criteria']}")
                    st.caption(f"Source: {row['eligibility_source'] or 'Not specified in courses.csv — verify with SISTec / DTE / RGPV / PCI.'}")

    with tab_filtered:
        if inelig.empty:
            st.success("All courses in courses.csv are eligible for your selection.")
        else:
            clean_inelig = inelig[["programme", "level", "eligible_streams", "required_subjects", "eligibility_note"]].copy()
            clean_inelig["eligible_streams"] = clean_inelig["eligible_streams"].map(lambda v: ", ".join(split_items(v)))
            clean_inelig["required_subjects"] = clean_inelig["required_subjects"].map(lambda v: ", ".join(split_items(v)))
            clean_inelig.columns = ["Course Name", "Degree", "Allowed Streams", "Required Subjects", "Filter Reason"]
            st.dataframe(clean_inelig, hide_index=True, width="stretch")

    with tab_all:
        clean_all = engine.df[["programme", "level", "department", "eligible_streams", "required_subjects", "campus"]].copy()
        clean_all["eligible_streams"] = clean_all["eligible_streams"].map(lambda v: ", ".join(split_items(v)))
        clean_all["required_subjects"] = clean_all["required_subjects"].map(lambda v: ", ".join(split_items(v)))
        clean_all.columns = ["Course Name", "Degree", "Department", "Allowed Streams", "Required Subjects", "Campus"]
        st.dataframe(clean_all, hide_index=True, width="stretch")


if __name__ == "__main__":
    main()
