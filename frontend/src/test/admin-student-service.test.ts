import { afterEach, describe, expect, it, vi } from "vitest";
import { getAdminStudentRadar } from "../domain/services/adminStudentService";
import { clearAccessToken, setAccessToken } from "../shared/auth/tokenStorage";

function mockJsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    text: vi.fn().mockResolvedValue(JSON.stringify(body))
  } as unknown as Response;
}

describe("admin student service", () => {
  afterEach(() => {
    clearAccessToken();
    vi.restoreAllMocks();
  });

  it("consulta radar admin com escopo de mentor e aluno", async () => {
    setAccessToken("admin-token");
    const fetchMock = vi.fn().mockResolvedValue(
      mockJsonResponse({
        studentId: "182",
        axisScores: [{ axisKey: "cap", axisLabel: "Captacao", baseline: 0.2, current: 0.4, projected: 0.6 }],
        avgBaseline: 0.2,
        avgCurrent: 0.4,
        avgProjected: 0.6
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const radar = await getAdminStudentRadar("usr_2", "std_182");

    expect(radar.axisScores).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/admin/mentores/usr_2/alunos/std_182/radar",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({ Authorization: "Bearer admin-token" })
      })
    );
  });
});
