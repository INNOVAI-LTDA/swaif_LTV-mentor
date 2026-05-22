import { adaptCommandCenterListPayload } from "../domain/adapters/commandCenterAdapter";
import { adaptRadarPayload } from "../domain/adapters/radarAdapter";

describe("adapters", () => {
  it("normaliza lista do centro", () => {
    const result = adaptCommandCenterListPayload([
      {
        id: "stu_1",
        name: "Aluno Um",
        programName: "Mentoria A",
        urgency: "watch",
        daysLeft: 30,
        day: 60,
        totalDays: 180,
        engagement: 0.5,
        progress: 0.3,
        hormoziScore: 42,
        ltv: 12000
      }
    ]);

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("stu_1");
    expect(result[0].urgency).toBe("watch");
  });

  it("aplica fallback projected no radar", () => {
    const result = adaptRadarPayload({
      studentId: "stu_1",
      axisScores: [
        {
          axisKey: "eixo_1",
          axisLabel: "Eixo 1",
          baseline: 10,
          current: 20
        }
      ],
      avgBaseline: 10,
      avgCurrent: 20,
      avgProjected: 20
    });

    expect(result.axisScores[0].projected).toBe(20);
  });
});
