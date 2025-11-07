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
// Step 1: Upload → Extract Skills
// -------------------------------
document.getElementById("extractBtn").addEventListener("click", async (e) => {
  const file = document.getElementById("resumeFile").files[0];
  if (!file) return alert("Please upload your resume first.");

  const accessToken = localStorage.getItem("access_token");
  if (!accessToken) {
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
      headers: { Authorization: `Bearer ${accessToken}` },
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
// Step 2: Confirm → Get Recommendations
// -------------------------------
document
  .getElementById("confirmSkillsBtn")
  .addEventListener("click", async (e) => {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
      alert("Session expired. Please log in again.");
      window.location.href = "login.html";
      return;
    }

    const editedSkills = document
      .getElementById("resumeSkillsBox")
      .value.split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (editedSkills.length === 0) {
      alert("Please add at least one skill before getting recommendations.");
      return;
    }

    const payload = { resume_skills: { technical: editedSkills, soft: [] } };

    showLoading();
    try {
      const res = await fetch("http://127.0.0.1:8001/api/recommend/jobs", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok)
        throw new Error(data.detail || "Failed to get recommendations");

      const renderBadges = (arr, cls) =>
        arr.length
          ? arr.map((s) => `<span class="badge ${cls}">${s}</span>`).join(" ")
          : `<span class="text-light">None</span>`;

      const div = document.getElementById("results");

      if (!data.recommendations?.length) {
        div.innerHTML =
          "<p>No matching jobs found. Try adding more skills.</p>";
      } else {
        div.innerHTML = data.recommendations
          .map((job) => {
            const scoreClass =
              job.score >= 80 ? "high" : job.score >= 50 ? "mid" : "low";
            return `
              <div class="job-card fade-in" data-score="${scoreClass}">
                <h3>${job.title} <small>(${job.level})</small></h3>
                <p><strong>Match Score:</strong> ${job.score}%</p>
                <p><strong>Missing Skills:</strong> ${renderBadges(
                  job.breakdown.technical.missing,
                  "missing"
                )}</p>
                <p><strong>Matched Skills:</strong> ${renderBadges(
                  job.breakdown.technical.matched,
                  "matched"
                )}</p>
              </div>`;
          })
          .join("");

        // show overall feedback below recommendations
        showRecommendationFeedback(data.recommendations);
      }

      document.getElementById("results-section").style.display = "block";
      document
        .getElementById("results-section")
        .scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      alert("Error getting recommendations: " + err.message);
    } finally {
      hideLoading();
    }
  });

// -------------------------------
// Dynamic Overall Feedback
// -------------------------------
function showRecommendationFeedback(jobs) {
  const feedback = document.getElementById("recommendFeedback");
  if (!feedback || !jobs.length) return;

  const avgScore =
    jobs.reduce((sum, job) => sum + (job.score || 0), 0) / jobs.length;

  if (avgScore >= 80) {
    feedback.innerHTML =
      "<span>🎯</span> <strong><em>Excellent portfolio! You’re highly aligned with several top roles — keep applying and showcasing these strengths.</em></strong>";
  } else if (avgScore >= 50) {
    feedback.innerHTML =
      "<span>💡</span> <strong><em>Good potential! You match well with a few roles. Try improving skills from the missing areas to expand your options.</em></strong>";
  } else if (avgScore >= 30) {
    feedback.innerHTML =
      "<span>📈</span> <strong><em>You’re getting there! Focus on building skills that appear most frequently in the missing sections.</em></strong>";
  } else {
    feedback.innerHTML =
      "<span>🚀</span> <strong><em>Don’t worry — every expert started small! Upskill in core areas shown above to boost your opportunities.</em></strong>";
  }

  feedback.classList.add("fade-in");
}