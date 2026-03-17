import { httpClient } from "../lib/httpClient.js";
import { setAccessToken } from "../lib/authStorage.js";

export async function login({ email, password }) {
  const payload = await httpClient.post("/auth/login", { email, password });
  if (payload && payload.access_token) {
    setAccessToken(payload.access_token);
  }
  return payload;
}

export function getMe() {
  return httpClient.get("/me");
}

