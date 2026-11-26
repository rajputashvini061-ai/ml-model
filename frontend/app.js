const SAMPLES = {
  PCM: { interests: ["Artificial Intelligence", "Data Science", "Programming"], skills: ["Python", "Statistics", "Problem Solving"] },
  PCB: { interests: ["Healthcare", "Medicines", "Pharmaceutical Science"], skills: ["Laboratory Skills", "Scientific Analysis", "Research"] },
  PCMB: { interests: ["Robotics", "Automation", "Healthcare"], skills: ["Python", "Problem Solving", "Research"] },
  Commerce: { interests: ["Business", "Marketing", "Finance"], skills: ["Communication", "Leadership", "Business Analysis"] },
  Arts: { interests: ["Entrepreneurship", "Management", "Marketing"], skills: ["Communication", "Leadership", "Decision Making"] },
};

const state = {
  meta: null,
  stream: "PCM",
  subjects: new Set(),
  interests: new Set(),
  skills: new Set(),
};

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtSemi = (v) => String(v ?? "").split(";").map((s) => s.trim()).filter(Boolean).join(", ");

function renderChipSet(containerId, items, activeSet, onToggle) {
  const el = document.getElementById(containerId);
  el.innerHTML = items.map((item) =>
    `<button type="button" class="chip ${activeSet.has(item) ? "active" : ""}" data-val="${esc(item)}">${esc(item)}</button>`
  ).join("");
  el.querySelectorAll(".chip").forEach((btn) =>
    btn.addEventListener("click", () => { onToggle(btn.dataset.val); })
  );
}

function applyStreamDefaults(stream) {
  state.stream = stream;
  state.subjects = new Set(state.meta.stream_subjects[stream] || []);
  const sample = SAMPLES[stream] || { interests: [], skills: [] };
  state.interests = new Set(sample.interests.filter((x) => state.meta.interests.includes(x)));
  state.skills = new Set(sample.skills.filter((x) => state.meta.skills.includes(x)));
  renderControls();
  fetchRecommendations();
}

function renderControls() {
  renderChipSet("streamPills", state.meta.streams, new Set([state.stream]), applyStreamDefaults);
  renderChipSet("subjectChips", state.meta.all_subjects, state.subjects, (val) => {
    state.subjects.has(val) ? state.subjects.delete(val) : state.subjects.add(val);
    renderControls();
    fetchRecommendations();
  });
  renderChipSet("interestChips", state.meta.interests, state.interests, (val) => {
    state.interests.has(val) ? state.interests.delete(val) : state.interests.add(val);
    renderControls();
    fetchRecommendations();
  });
  renderChipSet("skillChips", state.meta.skills, state.skills, (val) => {
    state.skills.has(val) ? state.skills.delete(val) : state.skills.add(val);
    renderControls();
    fetchRecommendations();
  });
}

async function fetchRecommendations() {
  const customInterests = document.getElementById("customInterests").value.trim();
  const customSkills = document.getElementById("customSkills").value.trim();
  const topN = Number(document.getElementById("topNSlider").value);
  const interests = [...state.interests, ...(customInterests ? [customInterests] : [])].join(", ");
  const skills = [...state.skills, ...(customSkills ? [customSkills] : [])].join(", ");

  const res = await fetch("/api/recommend", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ stream: state.stream, subjects: [...state.subjects], interests, skills, top_n: topN }),
  });
  const data = await res.json();
  if (!res.ok) {
    document.getElementById("tab-recommended").innerHTML = `<div class="alert">${esc(data.error || "Recommendation failed.")}</div>`;
    return;
  }
  renderResults(data);
}

function renderResults(data) {
  document.getElementById("mStream").textContent = data.stream;
  document.getElementById("mEligible").textContent = `${data.total_eligible} / ${data.total_courses}`;
  const topScore = data.recommendations.length ? Math.max(...data.recommendations.map((r) => Number(r.match_score))) : 0;
  document.getElementById("mTopScore").textContent = `${topScore.toFixed(2)}%`;

  const recPane = document.getElementById("tab-recommended");
  if (!data.recommendations.length) {
    recPane.innerHTML = `<div class="alert">No SISTec courses matched your selected stream and Class 12 subjects. Adjust subjects on the left.</div>`;
  } else {
    recPane.innerHTML = data.recommendations.map((r, i) => {
      const score = Number(r.match_score);
      const badgeCls = score > 0 ? "badge-score" : "badge-zero";
      return `
        <article class="course-card">
          <div class="card-head">
            <div>
              <h3>#${i + 1}. ${esc(r.programme)}</h3>
              <div class="meta">
                <span class="badge badge-deg">${esc(r.level)}</span>
                <strong>Dept:</strong> ${esc(r.department)} &nbsp;|&nbsp; <strong>Campus:</strong> ${esc(r.campus || "Verify Campus")}
              </div>
            </div>
            <span class="badge ${badgeCls}">Match: ${score.toFixed(2)}%</span>
          </div>
          <div class="bar-track"><div class="bar-fill" style="width:${Math.min(100, Math.max(0, score))}%"></div></div>
          <div class="reason-box">
            <strong>Why recommended:</strong> ${esc(r.recommendation_reason)}
            <div class="meta"><strong>Career paths:</strong> ${esc(fmtSemi(r.career_paths) || "Not listed")}</div>
          </div>
          <button type="button" class="details-toggle">Show Official Eligibility Details ▾</button>
          <div class="details-body hidden">
            <div><strong>Allowed Streams (App Filter):</strong> ${esc(fmtSemi(r.eligible_streams))} &nbsp;|&nbsp; <strong>Required Subjects:</strong> ${esc(fmtSemi(r.required_subjects))}</div>
            <div style="margin-top:0.35rem;"><strong>Official Criteria:</strong> ${esc(r.eligibility_criteria)}</div>
            <div style="margin-top:0.25rem;"><em>Source: ${esc(r.eligibility_source || "Not specified in courses.csv — verify with SISTec / DTE / RGPV / PCI.")}</em></div>
          </div>
        </article>`;
    }).join("");

    recPane.querySelectorAll(".details-toggle").forEach((btn) =>
      btn.addEventListener("click", () => {
        const body = btn.nextElementSibling;
        const hidden = body.classList.toggle("hidden");
        btn.textContent = hidden ? "Show Official Eligibility Details ▾" : "Hide Official Eligibility Details ▴";
      })
    );
  }

  const filtPane = document.getElementById("tab-filtered");
  filtPane.innerHTML = !data.ineligible_courses.length
    ? `<div class="notice">All courses in courses.csv are eligible for your selection.</div>`
    : `<table class="data-table"><thead><tr><th>Course Name</th><th>Degree</th><th>Allowed Streams</th><th>Required Subjects</th><th>Filter Reason</th></tr></thead><tbody>` +
      data.ineligible_courses.map((c) => `<tr><td>${esc(c.programme)}</td><td>${esc(c.level)}</td><td>${esc(fmtSemi(c.eligible_streams))}</td><td>${esc(fmtSemi(c.required_subjects))}</td><td>${esc(c.eligibility_note)}</td></tr>`).join("") +
      `</tbody></table>`;
}

function renderCatalog(query = "") {
  const q = query.trim().toLowerCase();
  const rows = state.meta.courses.filter((c) =>
    !q || `${c.programme} ${c.level} ${c.department} ${c.eligible_streams}`.toLowerCase().includes(q)
  );
  document.getElementById("catalogTable").innerHTML =
    `<table class="data-table"><thead><tr><th>Course Name</th><th>Degree</th><th>Department</th><th>Allowed Streams</th><th>Required Subjects</th><th>Campus</th></tr></thead><tbody>` +
    rows.map((c) => `<tr><td>${esc(c.programme)}</td><td>${esc(c.level)}</td><td>${esc(c.department)}</td><td>${esc(fmtSemi(c.eligible_streams))}</td><td>${esc(fmtSemi(c.required_subjects))}</td><td>${esc(c.campus)}</td></tr>`).join("") +
    `</tbody></table>`;
}

async function init() {
  state.meta = await (await fetch("/api/meta")).json();
  document.getElementById("officialNoteText").textContent = state.meta.official_note;
  document.getElementById("topNSlider").max = state.meta.courses.length;

  document.getElementById("toggleNoticeBtn").addEventListener("click", () =>
    document.getElementById("noticeBanner").classList.toggle("hidden")
  );
  document.getElementById("topNSlider").addEventListener("input", (e) => {
    document.getElementById("topNValue").textContent = e.target.value;
    fetchRecommendations();
  });
  document.getElementById("recommendBtn").addEventListener("click", fetchRecommendations);
  document.getElementById("clearBtn").addEventListener("click", () => {
    state.interests.clear();
    state.skills.clear();
    document.getElementById("customInterests").value = "";
    document.getElementById("customSkills").value = "";
    renderControls();
    fetchRecommendations();
  });
  ["customInterests", "customSkills"].forEach((id) =>
    document.getElementById(id).addEventListener("keyup", (e) => { if (e.key === "Enter") fetchRecommendations(); })
  );
  document.getElementById("catalogSearch").addEventListener("input", (e) => renderCatalog(e.target.value));
  document.querySelectorAll(".tab").forEach((tab) =>
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab, .tab-pane").forEach((el) => el.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
    })
  );

  renderCatalog();
  applyStreamDefaults("PCM");
}

init();
