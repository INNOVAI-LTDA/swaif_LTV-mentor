import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { ReactNode } from "react";

const mockRadarRefresh = vi.fn();
const mockPillarRefresh = vi.fn();
const mockUpdate = vi.fn();

vi.mock("../domain/hooks/useStudentWorkspace", () => ({
  useSelfRadar: () => ({
    data: {
      studentId: "std_1",
      axisScores: [
        { axisKey: "plr-code", axisLabel: "Consistencia", axisSub: "", baseline: 0.4, current: 0.6, projected: 0.7, insight: null }
      ],
      avgBaseline: 0.4,
      avgCurrent: 0.6,
      avgProjected: 0.7,
      context: { mentorName: "", mentorId: "", protocolName: "", protocolId: "" }
    },
    loading: false,
    error: null,
    refresh: mockRadarRefresh
  }),
  useSelfPillarMetrics: () => ({
    data: {
      studentId: "std_1",
      enrollmentId: "enr_1",
      pillar: { id: "plr_1", name: "Consistencia", code: "plr-code" },
      items: [
        {
          measurementId: "mea_1",
          metricId: "met_1",
          metricLabel: "Ritmo",
          direction: "higher_better",
          unit: null,
          valueBaseline: 4,
          valueCurrent: 6,
          valueProjected: 7,
          improvingTrend: true,
          minScore: 0,
          maxScore: 10
        }
      ]
    },
    loading: false,
    error: null,
    refresh: mockPillarRefresh
  })
}));

vi.mock("../domain/services/studentWorkspaceService", () => ({
  updateSelfMeasurementValueCurrent: (...args: unknown[]) => mockUpdate(...args)
}));

vi.mock("../features/student/components/StudentShell", () => ({
  StudentShell: ({ children }: { children: ReactNode }) => <div>{children}</div>
}));

vi.mock("../features/radar/components/RadarChart", () => ({
  RadarChart: () => <div>Radar</div>
}));

import { StudentPage } from "../features/student/pages/StudentPage";

function renderPage(initialPath = "/app/aluno?view=indicadores") {
  render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/app/aluno" element={<StudentPage />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("StudentPage workspace flow", () => {
  beforeEach(() => {
    mockRadarRefresh.mockReset();
    mockPillarRefresh.mockReset();
    mockUpdate.mockReset();
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("confirma e persiste update de valueCurrent com refresh", async () => {
    mockUpdate.mockResolvedValue({ measurementId: "mea_1", valueCurrent: 8 });

    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Editar atual" }));
    fireEvent.change(screen.getByLabelText("Valor atual de Ritmo"), { target: { value: "8" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith("mea_1", 8);
    });

    expect(window.confirm).toHaveBeenCalled();
    expect(mockRadarRefresh).toHaveBeenCalled();
    expect(mockPillarRefresh).toHaveBeenCalled();
    expect(await screen.findByText("Valor atualizado com sucesso.")).toBeInTheDocument();
  });

  it("exibe seletor de pilares na view de indicadores", () => {
    renderPage();

    expect(screen.getByRole("tablist", { name: "Seleção de pilar para indicadores" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Consistencia/i })).toBeInTheDocument();
  });


  it("nao exibe seletor de pilares clicaveis na view de radar", () => {
    renderPage("/app/aluno?view=radar");

    expect(screen.queryByRole("tablist", { name: "Seleção de pilar para indicadores" })).not.toBeInTheDocument();
  });
});
