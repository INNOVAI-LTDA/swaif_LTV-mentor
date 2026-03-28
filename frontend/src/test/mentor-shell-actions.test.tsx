import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CommandCenterPage } from "../features/command-center/pages/CommandCenterPage";
import { RadarPage } from "../features/radar/pages/RadarPage";

vi.mock("../shared/config/env", () => ({
  env: {
    brandingIconUrl: "/branding/icon.png",
    brandingLogoUrl: "/branding/logo.png",
    clientName: "Cliente",
    appName: "Plataforma",
    appTagline: "Tagline",
    shellSubtitle: "Subtitulo",
    routerBasePath: "/",
    appBasePath: "/",
    deployTarget: "local",
    isLocalDeployTarget: true,
    apiBaseUrl: "http://localhost:8000",
    httpTimeoutMs: 15000,
    demoModeEnabled: false,
    internalMentorDemoEnabled: false
  }
}));

vi.mock("../domain/adapters/radarAdapter", () => ({
  simulateRadar: () => ({
    axisScores: [],
    insight: null
  })
}));

vi.mock("../domain/adapters/commandCenterAdapter", () => ({
  deriveCommandCenterTopKpis: () => ({ active: 0, alerts: 0, d45: 0 })
}));

const refreshMock = vi.fn();

vi.mock("../domain/hooks/useCommandCenter", () => ({
  useCommandCenterStudents: () => ({
    data: [
      {
        id: "stu_1",
        name: "Aluno 1",
        initials: "A1",
        programName: "Mentoria",
        urgency: "normal",
        progress: 0.5,
        engagement: 0.5,
        ltv: 1000,
        daysLeft: 30,
        hormoziScore: 7.2
      }
    ],
    loading: false,
    error: null,
    refresh: refreshMock
  }),
  useCommandCenterStudentDetail: () => ({
    data: {
      metricValues: [],
      checkpoints: []
    },
    loading: false,
    error: null,
    refresh: refreshMock
  }),
  useCommandCenterTimeline: () => ({
    data: {
      anomalies: [],
      timeline: []
    },
    loading: false,
    error: null,
    refresh: refreshMock
  })
}));

vi.mock("../domain/hooks/useRadar", () => ({
  useStudentRadar: () => ({
    data: {
      axisScores: [],
      insight: null
    },
    loading: false,
    error: null,
    refresh: refreshMock
  })
}));

describe("Mentor shell header actions removal", () => {
  beforeEach(() => {
    refreshMock.mockReset();
  });

  it("Radar page renders without header actions", () => {
    render(
      <MemoryRouter initialEntries={["/app/radar"]}>
        <Routes>
          <Route path="/app/radar" element={<RadarPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: /Pilares de transforma/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Insight principal do ciclo" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Atualizar leitura" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Abrir centro" })).toBeNull();
  });

  it("Command Center page renders without header actions", () => {
    render(
      <MemoryRouter initialEntries={["/app/centro-comando"]}>
        <Routes>
          <Route path="/app/centro-comando" element={<CommandCenterPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("heading", { name: "Alunos monitorados" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Painel do aluno" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Atualizar leitura" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Abrir matriz" })).toBeNull();
  });
});
