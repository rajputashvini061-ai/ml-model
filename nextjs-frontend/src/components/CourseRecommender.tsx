"use client";

import { useCallback, useEffect, useState } from "react";

export interface CourseCatalogItem {
  programme: string;
  level: string;
  department: string;
  campus: string;
  eligible_streams: string;
  required_subjects: string;
  eligibility_criteria: string;
}

export interface RecommendationItem extends CourseCatalogItem {
  match_score: number;
  recommendation_reason: string;
  career_paths: string;
  eligibility_source: string;
}

export interface IneligibleItem {
  programme: string;
  level: string;
  eligible_streams: string;
  required_subjects: string;
  eligibility_note: string;
}

export interface MetaPayload {
  streams: string[];
  stream_subjects: Record<string, string[]>;
  all_subjects: string[];
  interests: string[];
  skills: string[];
  official_note: string;
  courses: CourseCatalogItem[];
}

interface RecommendResponse {
  stream: string;
  total_courses: number;
  total_eligible: number;
  recommendations: RecommendationItem[];
  ineligible_courses: IneligibleItem[];
  error?: string;
}

const SAMPLES: Record<string, { interests: string[]; skills: string[] }> = {
  PCM: { interests: ["Artificial Intelligence", "Data Science", "Programming"], skills: ["Python", "Statistics", "Problem Solving"] },
  PCB: { interests: ["Healthcare", "Medicines", "Pharmaceutical Science"], skills: ["Laboratory Skills", "Scientific Analysis", "Research"] },
  PCMB: { interests: ["Robotics", "Automation", "Healthcare"], skills: ["Python", "Problem Solving", "Research"] },
  Commerce: { interests: ["Business", "Marketing", "Finance"], skills: ["Communication", "Leadership", "Business Analysis"] },
  Arts: { interests: ["Entrepreneurship", "Management", "Marketing"], skills: ["Communication", "Leadership", "Decision Making"] },
};

const fmtSemi = (v: string) => (v || "").split(";").map((s) => s.trim()).filter(Boolean).join(", ");

export default function CourseRecommender({ initialMeta }: { initialMeta: MetaPayload }) {
  const [stream, setStream] = useState("PCM");
  const [subjects, setSubjects] = useState<string[]>(initialMeta.stream_subjects.PCM || []);
  const [interests, setInterests] = useState<string[]>(SAMPLES.PCM.interests.filter((x) => initialMeta.interests.includes(x)));
  const [skills, setSkills] = useState<string[]>(SAMPLES.PCM.skills.filter((x) => initialMeta.skills.includes(x)));
  const [customInterests, setCustomInterests] = useState("");
  const [customSkills, setCustomSkills] = useState("");
  const [topN, setTopN] = useState(5);
  const [activeTab, setActiveTab] = useState<"recommended" | "filtered" | "catalog">("recommended");
  const [showNotice, setShowNotice] = useState(false);
  const [openCards, setOpenCards] = useState<Record<string, boolean>>({});
  const [catalogQuery, setCatalogQuery] = useState("");
  const [apiStatus, setApiStatus] = useState<"warming" | "ready" | "error">("warming");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<RecommendResponse | null>(null);

  const fetchRecommendations = useCallback(
    async (nextStream: string, nextSubjects: string[], nextInterests: string[], nextSkills: string[], nextCustomI: string, nextCustomS: string, nextTopN: number) => {
      setLoading(true);
      setError("");
      try {
        const res = await fetch("/api/recommend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            stream: nextStream,
            subjects: nextSubjects,
            interests: [...nextInterests, nextCustomI.trim()].filter(Boolean).join(", "),
            skills: [...nextSkills, nextCustomS.trim()].filter(Boolean).join(", "),
            top_n: nextTopN,
          }),
        });
        const data: RecommendResponse = await res.json();
        if (!res.ok) {
          setError(data.error || "Unable to fetch recommendations.");
        } else {
          setResult(data);
          setApiStatus("ready");
        }
      } catch {
        setError("Network error contacting Next.js / Render API.");
        setApiStatus("error");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetch("/api/health").then((r) => setApiStatus(r.ok ? "ready" : "error")).catch(() => setApiStatus("error"));
    fetchRecommendations("PCM", initialMeta.stream_subjects.PCM || [], SAMPLES.PCM.interests, SAMPLES.PCM.skills, "", "", 5);
  }, [fetchRecommendations, initialMeta.stream_subjects]);

  const toggleItem = (list: string[], value: string) =>
    list.includes(value) ? list.filter((x) => x !== value) : [...list, value];

  const handleStreamSelect = (nextStream: string) => {
    const nextSubjects = initialMeta.stream_subjects[nextStream] || [];
    const sample = SAMPLES[nextStream] || { interests: [], skills: [] };
    const nextInterests = sample.interests.filter((x) => initialMeta.interests.includes(x));
    const nextSkills = sample.skills.filter((x) => initialMeta.skills.includes(x));
    setStream(nextStream);
    setSubjects(nextSubjects);
    setInterests(nextInterests);
    setSkills(nextSkills);
    fetchRecommendations(nextStream, nextSubjects, nextInterests, nextSkills, customInterests, customSkills, topN);
  };

  const filteredCatalog = initialMeta.courses.filter((c) => {
    const q = catalogQuery.trim().toLowerCase();
    return !q || `${c.programme} ${c.level} ${c.department} ${c.eligible_streams}`.toLowerCase().includes(q);
  });

  const topScore = result?.recommendations.length ? Math.max(...result.recommendations.map((r) => Number(r.match_score))) : 0;

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <h1>🎓 SISTec Course Recommendation System</h1>
          <p>Pre-loaded Next.js Frontend + Render TF-IDF &amp; Cosine Similarity ML API</p>
        </div>
        <div className="hero-actions">
          <span className={`api-status ${apiStatus === "ready" ? "ready" : "warn"}`}>
            {apiStatus === "ready" ? "ML API: Connected" : apiStatus === "warming" ? "ML API: Waking up..." : "ML API: Offline"}
          </span>
          <button className="btn-ghost" type="button" onClick={() => setShowNotice((s) => !s)}>
            Eligibility vs. ML Logic
          </button>
        </div>
      </header>

      {showNotice && (
        <section className="notice">
          <strong>Official Admission Eligibility vs. Recommendation Logic:</strong> {initialMeta.official_note}
          <p>App filtering uses <code>eligible_streams</code> and <code>required_subjects</code> from <code>courses.csv</code>, while TF-IDF + Cosine Similarity ranks eligible courses by your interests and skills.</p>
        </section>
      )}

      <main className="layout">
        <aside className="panel controls">
          <h2>Student Profile</h2>

          <div className="field">
            <label>1. Class 12 Stream</label>
            <div className="pill-group">
              {initialMeta.streams.map((s) => (
                <button key={s} type="button" className={`chip ${stream === s ? "active" : ""}`} onClick={() => handleStreamSelect(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>2. Class 12 Subjects Passed</label>
            <div className="chip-box">
              {initialMeta.all_subjects.map((sub) => (
                <button
                  key={sub}
                  type="button"
                  className={`chip ${subjects.includes(sub) ? "active" : ""}`}
                  onClick={() => {
                    const next = toggleItem(subjects, sub);
                    setSubjects(next);
                    fetchRecommendations(stream, next, interests, skills, customInterests, customSkills, topN);
                  }}
                >
                  {sub}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>3. Your Interests</label>
            <div className="chip-box scrollable">
              {initialMeta.interests.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`chip ${interests.includes(item) ? "active" : ""}`}
                  onClick={() => {
                    const next = toggleItem(interests, item);
                    setInterests(next);
                    fetchRecommendations(stream, subjects, next, skills, customInterests, customSkills, topN);
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
            <input type="text" value={customInterests} onChange={(e) => setCustomInterests(e.target.value)} placeholder="Other interests (comma-separated)..." />
          </div>

          <div className="field">
            <label>4. Your Skills</label>
            <div className="chip-box scrollable">
              {initialMeta.skills.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`chip ${skills.includes(item) ? "active" : ""}`}
                  onClick={() => {
                    const next = toggleItem(skills, item);
                    setSkills(next);
                    fetchRecommendations(stream, subjects, interests, next, customInterests, customSkills, topN);
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
            <input type="text" value={customSkills} onChange={(e) => setCustomSkills(e.target.value)} placeholder="Other skills (comma-separated)..." />
          </div>

          <div className="field">
            <label htmlFor="topNSlider">5. Max Recommendations: <strong>{topN}</strong></label>
            <input
              id="topNSlider"
              type="range"
              min={1}
              max={initialMeta.courses.length}
              value={topN}
              onChange={(e) => {
                const next = Number(e.target.value);
                setTopN(next);
                fetchRecommendations(stream, subjects, interests, skills, customInterests, customSkills, next);
              }}
            />
          </div>

          <div className="actions">
            <button type="button" className="btn-primary" onClick={() => fetchRecommendations(stream, subjects, interests, skills, customInterests, customSkills, topN)}>
              {loading ? "Matching..." : "Find Best Courses"}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                setInterests([]);
                setSkills([]);
                setCustomInterests("");
                setCustomSkills("");
                fetchRecommendations(stream, subjects, [], [], "", "", topN);
              }}
            >
              Clear Tags
            </button>
          </div>
        </aside>

        <section>
          <div className="metrics">
            <div className="metric-card"><span>Selected Stream</span><strong>{stream}</strong></div>
            <div className="metric-card"><span>Eligible SISTec Courses</span><strong>{result ? `${result.total_eligible} / ${result.total_courses}` : `— / ${initialMeta.courses.length}`}</strong></div>
            <div className="metric-card"><span>Top Match Score</span><strong>{result ? `${topScore.toFixed(2)}%` : "—"}</strong></div>
          </div>

          <div className="tabs">
            <button type="button" className={`tab ${activeTab === "recommended" ? "active" : ""}`} onClick={() => setActiveTab("recommended")}>Recommended Courses</button>
            <button type="button" className={`tab ${activeTab === "filtered" ? "active" : ""}`} onClick={() => setActiveTab("filtered")}>Filtered-Out Courses</button>
            <button type="button" className={`tab ${activeTab === "catalog" ? "active" : ""}`} onClick={() => setActiveTab("catalog")}>All {initialMeta.courses.length} SISTec Courses</button>
          </div>

          {error && <div className="alert">{error}</div>}
          {loading && !result && <div className="info-box">Pre-loaded UI ready — fetching personalized ML rankings from your backend API...</div>}

          {activeTab === "recommended" && result && (
            result.recommendations.length === 0 ? (
              <div className="alert">No SISTec courses matched your selected stream and Class 12 subjects. Adjust subjects on the left.</div>
            ) : (
              result.recommendations.map((r, i) => {
                const score = Number(r.match_score);
                const isOpen = !!openCards[r.programme];
                return (
                  <article key={r.programme} className="course-card">
                    <div className="card-head">
                      <div>
                        <h3>#{i + 1}. {r.programme}</h3>
                        <div className="meta">
                          <span className="badge badge-deg">{r.level}</span>
                          <strong>Dept:</strong> {r.department} &nbsp;|&nbsp; <strong>Campus:</strong> {r.campus || "Verify Campus"}
                        </div>
                      </div>
                      <span className={`badge ${score > 0 ? "badge-score" : "badge-zero"}`}>Match: {score.toFixed(2)}%</span>
                    </div>
                    <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, Math.max(0, score))}%` }} /></div>
                    <div className="reason-box">
                      <strong>Why recommended:</strong> {r.recommendation_reason}
                      <div className="meta"><strong>Career paths:</strong> {fmtSemi(r.career_paths) || "Not listed"}</div>
                    </div>
                    <button type="button" className="details-toggle" onClick={() => setOpenCards((p) => ({ ...p, [r.programme]: !p[r.programme] }))}>
                      {isOpen ? "Hide Official Eligibility Details ▴" : "Show Official Eligibility Details ▾"}
                    </button>
                    {isOpen && (
                      <div className="details-body">
                        <div><strong>Allowed Streams (App Filter):</strong> {fmtSemi(r.eligible_streams)} &nbsp;|&nbsp; <strong>Required Subjects:</strong> {fmtSemi(r.required_subjects)}</div>
                        <div style={{ marginTop: "0.35rem" }}><strong>Official Criteria:</strong> {r.eligibility_criteria}</div>
                        <div style={{ marginTop: "0.25rem" }}><em>Source: {r.eligibility_source || "Not specified in courses.csv — verify with SISTec / DTE / RGPV / PCI."}</em></div>
                      </div>
                    )}
                  </article>
                );
              })
            )
          )}

          {activeTab === "filtered" && result && (
            result.ineligible_courses.length === 0 ? (
              <div className="notice">All courses in courses.csv are eligible for your selection.</div>
            ) : (
              <table className="data-table">
                <thead><tr><th>Course Name</th><th>Degree</th><th>Allowed Streams</th><th>Required Subjects</th><th>Filter Reason</th></tr></thead>
                <tbody>
                  {result.ineligible_courses.map((c) => (
                    <tr key={c.programme}><td>{c.programme}</td><td>{c.level}</td><td>{fmtSemi(c.eligible_streams)}</td><td>{fmtSemi(c.required_subjects)}</td><td>{c.eligibility_note}</td></tr>
                  ))}
                </tbody>
              </table>
            )
          )}

          {activeTab === "catalog" && (
            <>
              <input className="search-input" type="text" value={catalogQuery} onChange={(e) => setCatalogQuery(e.target.value)} placeholder="Search SISTec courses by name, department, degree, or stream..." />
              <table className="data-table" style={{ marginTop: "0.7rem" }}>
                <thead><tr><th>Course Name</th><th>Degree</th><th>Department</th><th>Allowed Streams</th><th>Required Subjects</th><th>Campus</th></tr></thead>
                <tbody>
                  {filteredCatalog.map((c) => (
                    <tr key={c.programme}><td>{c.programme}</td><td>{c.level}</td><td>{c.department}</td><td>{fmtSemi(c.eligible_streams)}</td><td>{fmtSemi(c.required_subjects)}</td><td>{c.campus}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
