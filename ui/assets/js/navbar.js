// -------------------------------
// Dynamic Navbar with Responsive Toggle (Fixed Version)
// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname.split("/").pop();

  const navbarHTML = `
    <nav class="navbar glassy">
      <div class="nav-left">
        <h2><a href="index.html" class="brand-link">JobSkillMatcher</a></h2>
      </div>

      <div class="nav-right" id="navLinks">
        <a href="index.html" class="${path === 'index.html' ? 'active' : ''}">Home</a>
        <a href="match.html" class="${path === 'match.html' ? 'active' : ''}">Match Jobs</a>
        <a href="recommend.html" class="${path === 'recommend.html' ? 'active' : ''}">Recommendations</a>
        <a href="about.html" class="${path === 'about.html' ? 'active' : ''}">About Us</a>
        <button id="logoutBtn" class="btn small-btn danger-btn">Logout</button>
      </div>

      <!-- Hamburger on the right -->
      <div class="hamburger" id="hamburger">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </nav>
  `;

  document.getElementById("navbar").innerHTML = navbarHTML;

  const logoutBtn = document.getElementById("logoutBtn");
  const hamburger = document.getElementById("hamburger");
  const navLinks = document.getElementById("navLinks");

  // Handle logout
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("access_token");
    window.location.href = "login.html";
  });

  // Toggle menu (mobile)
  hamburger.addEventListener("click", () => {
    hamburger.classList.toggle("active");
    navLinks.classList.toggle("show-menu");
  });

  // Auto-close when a link is clicked
  document.querySelectorAll("#navLinks a").forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("show-menu");
      hamburger.classList.remove("active");
    });
  });

  // Reset when resizing back to desktop
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      navLinks.classList.remove("show-menu");
      hamburger.classList.remove("active");
    }
  });
});