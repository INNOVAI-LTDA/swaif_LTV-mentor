import { describe, expect, it, vi } from "vitest";

const httpClientMock = vi.hoisted(() => ({
  get: vi.fn()
}));

vi.mock("../shared/api/httpClient", () => ({
  httpClient: httpClientMock
}));

import { getProviderMe } from "../domain/services/providerService";

describe("providerService", () => {
  it("consome /provider/me via httpClient e normaliza payload", async () => {
    httpClientMock.get.mockResolvedValueOnce({
      id: "101",
      email: "provider@accmed.com.br",
      fullName: "Nome Provider",
      role: "provider",
      organizationId: "1"
    });

    const payload = await getProviderMe();

    expect(httpClientMock.get).toHaveBeenCalledWith("/provider/me");
    expect(payload.role).toBe("provider");
    expect(payload.id).toBe("101");
  });
});
