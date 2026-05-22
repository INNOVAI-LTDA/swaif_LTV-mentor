const ACCESS_TOKEN_KEY = "swaif_mvp_access_token";

let inMemoryToken: string | null = null;

function hasLocalStorage(): boolean {
  return typeof localStorage !== "undefined";
}

export function getAccessToken(): string | null {
  if (hasLocalStorage()) {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }
  return inMemoryToken;
}

export function setAccessToken(token: string): void {
  if (hasLocalStorage()) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    return;
  }
  inMemoryToken = token;
}

export function clearAccessToken(): void {
  if (hasLocalStorage()) {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    return;
  }
  inMemoryToken = null;
}
