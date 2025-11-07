// -------------------------------
// Global Spinner Control
// -------------------------------
function showLoading() {
  document.getElementById("loadingOverlay").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loadingOverlay").style.display = "none";
}

// -------------------------------
// Logout handler
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      window.location.href = "login.html";
    });
  }
});

// -------------------------------
// Utility helpers
// -------------------------------
function createSpinner(text = "Processing...") {
  const wrapper = document.createElement("span");
  wrapper.classList.add("spinner-wrapper");
  wrapper.innerHTML = `<span class="loading"></span> <span>${text}</span>`;
  return wrapper;
}

function toggleButton(btn, disable = true) {
  btn.disabled = disable;
  btn.style.opacity = disable ? "0.7" : "1";
  btn.style.cursor = disable ? "not-allowed" : "pointer";
}

// -------------------------------
// Step 1: Resume → Extract Skills
// -------------------------------
document.getElementById("extractBtn").addEventListener("click", async (e) => {
  const file = document.getElementById("resumeFile").files[0];
  if (!file) return alert("Please upload a resume first.");

  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("Session expired. Please log in again.");
    window.location.href = "login.html";
    return;
  }

  const formData = new FormData();
  formData.append("resume_file", file);

  showLoading();
  try {
    const res = await fetch("http://127.0.0.1:8001/api/resume/parse", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to extract skills");

    const skills = data.skills?.technical?.join(", ") || "";
    document.getElementById("resumeSkillsBox").value = skills;
    document.getElementById("skills-section").style.display = "block";
    document
      .getElementById("skills-section")
      .scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("Error extracting skills: " + err.message);
  } finally {
    hideLoading();
  }
});

// -------------------------------
// Step 2: Confirm Skills → JD Section
// -------------------------------
document.getElementById("confirmSkillsBtn").addEventListener("click", () => {
  const edited = document
    .getElementById("resumeSkillsBox")
    .value.split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  if (edited.length === 0) {
    alert("Please add at least one skill before continuing.");
    return;
  }

  localStorage.setItem("confirmedSkills", JSON.stringify(edited));
  document.getElementById("jd-section").style.display = "block";
  document.getElementById("jd-section").scrollIntoView({ behavior: "smooth" });
});

// -------------------------------
// Step 3: Compare → Call Match API
// -------------------------------
document.getElementById("compareBtn").addEventListener("click", async (e) => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("Session expired. Please log in again.");
    window.location.href = "login.html";
    return;
  }

  const jd = document.getElementById("jobDescription").value.trim();
  if (!jd) return alert("Please paste a job description.");

  const resumeSkills = JSON.parse(localStorage.getItem("confirmedSkills") || "[]");
  if (resumeSkills.length === 0)
    return alert("No confirmed skills found. Please extract and confirm first.");

  const payload = {
    job_description: jd,
    resume_skills: { technical: resumeSkills, soft: [] },
  };

  showLoading();
  try {
    const res = await fetch("http://127.0.0.1:8001/api/match", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to compare skills");

    // ---------- Render Results ----------
    const renderBadges = (arr, cls) =>
      arr.length
        ? arr.map((s) => `<span class="badge ${cls}">${s}</span>`).join(" ")
        : `<span class="text-light">None</span>`;

    // Ring math
    const radius = 50;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (data.match_score / 100) * circumference;

    const color =
      data.match_score >= 80
        ? "var(--success)"
        : data.match_score >= 50
        ? "var(--accent)"
        : "var(--danger)";

    const div = document.getElementById("results");
    div.innerHTML = `
      <div class="fade-in highlight">
        <h3 style="text-align:center;">Overall Match Score</h3>
        <div class="score-ring">
          <svg>
            <circle class="bg" cx="55" cy="55" r="${radius}"></circle>
            <circle class="progress" cx="55" cy="55" r="${radius}" stroke="${color}"
              style="stroke-dashoffset:${circumference};"></circle>
          </svg>
          <div class="score-text">${data.match_score}%</div>
        </div>

        <h3>Technical Skills</h3>
        <p><strong>Matched:</strong> ${renderBadges(data.technical.matched, "matched")}</p>
        <p><strong>Missing:</strong> ${renderBadges(data.technical.missing, "missing")}</p>
        <p><strong>Extra:</strong> ${renderBadges(data.technical.extra, "extra")}</p>

        <h3>Soft Skills</h3>
        <p><strong>Matched:</strong> ${renderBadges(data.soft.matched, "matched")}</p>
        <p><strong>Missing:</strong> ${renderBadges(data.soft.missing, "missing")}</p>
        <p><strong>Extra:</strong> ${renderBadges(data.soft.extra, "extra")}</p>
      </div>
    `;

    // Animate ring
    const progress = div.querySelector(".progress");
    setTimeout(() => {
      progress.style.strokeDashoffset = offset;
    }, 150);

    // Show feedback message
    showFeedbackMessage(data.match_score);

    document.getElementById("results-section").style.display = "block";
    document
      .getElementById("results-section")
      .scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("Error comparing skills: " + err.message);
  } finally {
    hideLoading();
  }
});

// -------------------------------
// Dynamic feedback message
// -------------------------------
function showFeedbackMessage(score) {
  const feedback = document.getElementById("feedbackMessage");

  if (!feedback) return;

  if (score >= 80) {
  feedback.innerHTML =
    "<span>🎉</span> <strong><em>Amazing! You’re a great fit for this role. Keep showcasing your strengths!</em></strong>";
} else if (score >= 50) {
  feedback.innerHTML =
    "<span>😊</span> <strong><em>Nice work! You’ve got solid skills — just polish a few areas mentioned above to boost your match.</em></strong>";
} else if (score >= 30) {
  feedback.innerHTML =
    "<span>😐</span> <strong><em>You’re on the right track. Consider adding some of the missing skills to strengthen your resume.</em></strong>";
} else {
  feedback.innerHTML =
    "<span>😔</span> <strong><em>You’ve got good potential, but this role requires different skills. Time to skill up and bridge the gap!</em></strong>";
}

}