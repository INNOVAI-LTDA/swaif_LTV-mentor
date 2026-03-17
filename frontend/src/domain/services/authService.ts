import type { LoginRequestDto, LoginResponseDto, MeResponseDto } from "../../contracts/auth";
import { httpClient } from "../../shared/api/httpClient";
import { clearAccessToken, setAccessToken } from "../../shared/auth/tokenStorage";
import type { AuthSession } from "../models";

export async function login(credentials: LoginRequestDto): Promise<AuthSession> {
  const payload = await httpClient.post<LoginResponseDto>("/auth/login", credentials);
  if (payload.access_token) {
    setAccessToken(payload.access_token);
  }

  let me: MeResponseDto | null = null;
  try {
    me = await httpClient.get<MeResponseDto>("/me");
  } catch {
    me = null;
  }

  return {
    accessToken: payload.access_token,
    tokenType: payload.token_type,
    user: me
      ? {
          id: me.id,
          email: me.email,
          role: me.role
        }
      : null
  };
}

export async function getMe() {
  const me = await httpClient.get<MeResponseDto>("/me");
  return {
    id: me.id,
    email: me.email,
    role: me.role
  };
}

export function logout() {
  clearAccessToken();
}
