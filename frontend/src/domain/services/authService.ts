import type { LoginRequestDto, LoginResponseDto, MeResponseDto } from "../../contracts/auth";
import { httpClient } from "../../shared/api/httpClient";
import { AppError } from "../../shared/api/types";
import { clearAccessToken, getAccessToken, setAccessToken } from "../../shared/auth/tokenStorage";
import { isKnownUserRole } from "../../shared/auth/roleRouting";
import type { AuthSession } from "../models";

function normalizeAuthenticatedUser(me: MeResponseDto): NonNullable<AuthSession["user"]> {
  if (!isKnownUserRole(me.role)) {
    throw new AppError({
      message: "Perfil da conta nao reconhecido.",
      code: "AUTH_ROLE_INVALID"
    });
  }

  return {
    id: me.id,
    email: me.email,
    role: me.role
  };
}

export async function login(credentials: LoginRequestDto): Promise<AuthSession> {
  const payload = await httpClient.post<LoginResponseDto>("/auth/login", credentials, { token: null });
  if (payload.access_token) {
    setAccessToken(payload.access_token);
  }

  try {
    const me = await httpClient.get<MeResponseDto>("/me");
    return {
      accessToken: payload.access_token,
      tokenType: payload.token_type,
      user: normalizeAuthenticatedUser(me)
    };
  } catch (error) {
    if (error instanceof AppError && error.isNetworkError) {
      throw new AppError({
        message: "Autenticacao concluida, mas nao foi possivel validar seu perfil. Tente novamente.",
        code: "AUTH_BOOTSTRAP_RETRYABLE",
        isNetworkError: true,
        details: {
          accessToken: getAccessToken()
        }
      });
    }
    clearAccessToken();
    throw error;
  }
}

export async function getMe() {
  const me = await httpClient.get<MeResponseDto>("/me");
  return normalizeAuthenticatedUser(me);
}

export function logout() {
  clearAccessToken();
}
