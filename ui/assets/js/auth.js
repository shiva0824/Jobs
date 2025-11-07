// assets/js/auth.js
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  try {
    const result = await apiLogin(username, password);
    setAuthToken(result.access_token);

    Swal.fire({
      icon: "success",
      title: "Login successful!",
      showConfirmButton: false,
      timer: 1500,
    });

    setTimeout(() => {
      window.location.href = "index.html";
    }, 1600);

  } catch (err) {
    Swal.fire({
      icon: "error",
      title: "Login failed",
      text: err.message || "Invalid username or password",
    });
  }
});