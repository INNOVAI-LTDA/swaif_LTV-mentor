import { describe, expect, it, vi } from "vitest";

const httpClientMock = vi.hoisted(() => ({
  get: vi.fn(),
  patch: vi.fn()
}));

vi.mock("../shared/api/httpClient", () => ({
  httpClient: httpClientMock
}));

import { getSelfPillarMetrics, getSelfRadar, updateSelfMeasurementValueCurrent } from "../domain/services/studentWorkspaceService";

describe("studentWorkspaceService", () => {
  it("consome radar self-scoped sem student_id no path", async () => {
    httpClientMock.get.mockResolvedValueOnce({ studentId: "std_1", axisScores: [] });

    await getSelfRadar();

    expect(httpClientMock.get).toHaveBeenCalledWith("/aluno/workspace/radar");
  });

  it("busca metricas por pilar self-scoped", async () => {
    httpClientMock.get.mockResolvedValueOnce({
      studentId: "std_1",
      enrollmentId: "enr_1",
      pillar: { id: "plr_1", name: "Pilar", code: "pilar" },
      items: []
    });

    const payload = await getSelfPillarMetrics("plr_1");

    expect(httpClientMock.get).toHaveBeenCalledWith("/aluno/workspace/pilares/plr_1/metricas");
    expect(payload.pillar.id).toBe("plr_1");
  });

  it("atualiza value_current no endpoint pontual", async () => {
    httpClientMock.patch.mockResolvedValueOnce({ measurementId: "mea_1", valueCurrent: 7.2 });

    const payload = await updateSelfMeasurementValueCurrent("mea_1", 7.2);

    expect(httpClientMock.patch).toHaveBeenCalledWith("/aluno/workspace/measurements/mea_1", { value_current: 7.2 });
    expect(payload.valueCurrent).toBe(7.2);
  });
});
