import { describe, expect, it, vi } from "vitest";

const httpClientMock = vi.hoisted(() => ({
  get: vi.fn(),
  patch: vi.fn()
}));

vi.mock("../shared/api/httpClient", () => ({
  httpClient: httpClientMock
}));

import { getDatabaseViewSnapshot } from "../domain/services/adminDatabaseViewService";

describe("adminDatabaseViewService", () => {
  it("consome GET /admin/database-view", async () => {
    httpClientMock.get.mockResolvedValueOnce({
      organizations: [],
      users: { admins: [], providers: [], clients: [] },
      products: [],
      enrollments: [],
      pillars: [],
      metrics: [],
      measurements: [],
      checkpoints: [],
      integrity: {}
    });

    const payload = await getDatabaseViewSnapshot();

    expect(httpClientMock.get).toHaveBeenCalledWith("/admin/database-view");
    expect(payload.users.admins).toEqual([]);
  });
});
