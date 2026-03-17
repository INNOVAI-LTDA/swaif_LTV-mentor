const ACCESS_TOKEN_KEY = "swaif_mvp_access_token";

let memoryToken = null;

function hasLocalStorage() {
  return typeof localStorage !== "undefined" && localStorage !== null;
}

export function getAccessToken() {
  if (hasLocalStorage()) {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }
  return memoryToken;
}

export function setAccessToken(token) {
  if (hasLocalStorage()) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }
  memoryToken = token;
}

export function clearAccessToken() {
  if (hasLocalStorage()) {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    return;
  }
  memoryToken = null;
}

