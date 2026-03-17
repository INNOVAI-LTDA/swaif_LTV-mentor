import { afterEach, describe, expect, it, vi } from "vitest";
import { clearAccessToken, setAccessToken } from "../shared/auth/tokenStorage";
import { listCommandCenterStudents } from "../domain/services/commandCenterService";
import { getRenewalMatrix } from "../domain/services/matrixService";
import { getStudentRadar } from "../domain/services/radarService";

function mockJsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    text: vi.fn().mockResolvedValue(JSON.stringify(body))
  } as unknown as Response;
}

describe("mentor services", () => {
  afterEach(() => {
    clearAccessToken();
    vi.restoreAllMocks();
  });

  it("consulta a matriz do mentor na rota dedicada", async () => {
    setAccessToken("mentor-token");
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse({ filter: "all", items: [], kpis: {} }));
    vi.stubGlobal("fetch", fetchMock);

    await getRenewalMatrix("all");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/mentor/matriz-renovacao?filter=all",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer mentor-token" })
      })
    );
  });

  it("consulta o centro de comando do mentor na rota dedicada", async () => {
    setAccessToken("mentor-token");
    const fetchMock = vi.fn().mockResolvedValue(mockJsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    await listCommandCenterStudents();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/mentor/centro-comando/alunos",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer mentor-token" })
      })
    );
  });

  it("consulta o radar do mentor na rota dedicada", async () => {
    setAccessToken("mentor-token");
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse({ studentId: "demo_student_01", axisScores: [], avgBaseline: 0, avgCurrent: 0, avgProjected: 0 })
    );
    vi.stubGlobal("fetch", fetchMock);

    await getStudentRadar("demo_student_01");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/mentor/radar/alunos/demo_student_01",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer mentor-token" })
      })
    );
  });
});
