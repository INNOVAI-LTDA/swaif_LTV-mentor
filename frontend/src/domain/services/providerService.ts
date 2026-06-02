import type { ProviderMeResponseDto } from "../../contracts/provider";
import { httpClient } from "../../shared/api/httpClient";
import { AppError } from "../../shared/api/types";

function normalizeProviderMe(payload: unknown): ProviderMeResponseDto {
  if (!payload || typeof payload !== "object") {
    throw new AppError({
      code: "PROVIDER_ME_INVALID_PAYLOAD",
      message: "Payload invalido em /provider/me."
    });
  }

  const record = payload as Record<string, unknown>;
  const role = String(record.role ?? "").trim().toLowerCase();
  if (role !== "provider") {
    throw new AppError({
      code: "PROVIDER_ME_INVALID_ROLE",
      message: "Perfil provider esperado em /provider/me."
    });
  }

  return {
    id: String(record.id ?? ""),
    email: String(record.email ?? ""),
    fullName: String(record.fullName ?? ""),
    role: "provider",
    organizationId: String(record.organizationId ?? "")
  };
}

export async function getProviderMe(): Promise<ProviderMeResponseDto> {
  const payload = await httpClient.get<unknown>("/provider/me");
  return normalizeProviderMe(payload);
}
