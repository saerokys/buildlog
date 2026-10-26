import { apiRequest } from "./client.js";

export function signup({ email, password, nickname }) {
  return apiRequest("/api/auth/signup", { method: "POST", body: { email, password, nickname } });
}

export function login({ email, password }) {
  return apiRequest("/api/auth/login", { method: "POST", body: { email, password } });
}

export function logout() {
  return apiRequest("/api/auth/logout", { method: "POST" });
}

export function getMe() {
  return apiRequest("/api/auth/me");
}

export function changeNickname(nickname) {
  return apiRequest("/api/account/nickname", { method: "PATCH", body: { nickname } });
}
