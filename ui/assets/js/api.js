// assets/js/api.js
const API_BASE = "http://127.0.0.1:8001";

async function apiLogin(username, password) {
  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Invalid username or password");
  }
  return await response.json(); // { access_token, token_type }
}

function setAuthToken(token) {
  localStorage.setItem("access_token", token);
}

function getAuthToken() {
  return localStorage.getItem("access_token");
}

function logoutUser() {
  localStorage.removeItem("access_token");
  window.location.href = "login.html";
}