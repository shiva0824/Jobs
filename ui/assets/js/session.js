// assets/js/session.js
// Auto-logout after 10 minutes of inactivity
const IDLE_MINUTES = 10;
let lastActive = Date.now();
let idleTimer;

function resetIdleTimer() {
  lastActive = Date.now();
  clearTimeout(idleTimer);
  idleTimer = setTimeout(checkIdle, IDLE_MINUTES * 60 * 1000 + 500);
}

function checkIdle() {
  const elapsed = Date.now() - lastActive;
  if (elapsed >= IDLE_MINUTES * 60 * 1000) {
    localStorage.removeItem("access_token");
    alert("You were logged out due to inactivity.");
    window.location.href = "login.html";
  } else {
    resetIdleTimer();
  }
}

// count as “activity”
["click", "mousemove", "keydown", "scroll", "touchstart", "touchmove"].forEach(evt =>
  document.addEventListener(evt, resetIdleTimer, { passive: true })
);

resetIdleTimer();