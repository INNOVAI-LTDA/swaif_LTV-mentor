import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { CommandCenterPage } from "../features/command-center/pages/CommandCenterPage";

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
    internalMentorSurfaceEnabled: false,
    internalMentorDemoEnabled: false
  }
}));

vi.mock("../domain/adapters/commandCenterAdapter", async () => {
  const actual = await vi.importActual<typeof import("../domain/adapters/commandCenterAdapter")>("../domain/adapters/commandCenterAdapter");
  return {
    ...actual,
    deriveCommandCenterTopKpis: () => ({ active: 20, alerts: 2, d45: 5 })
  };
});

const topItems = Array.from({ length: 10 }, (_, idx) => ({
  id: `top_${idx + 1}`,
  name: `Top ${idx + 1}`,
  initials: "TP",
  programName: "Mentoria",
  urgency: "normal" as const,
  risk: "low" as const,
  daysLeft: 90,
  day: 10,
  totalDays: 100,
  engagement: 0.9,
  progress: 0.9,
  d45: false,
  hormoziScore: 90,
  ltv: 1000
}));

const bottomItems = Array.from({ length: 10 }, (_, idx) => ({
  id: `bottom_${idx + 1}`,
  name: `Bottom ${idx + 1}`,
  initials: "BT",
  programName: "Mentoria",
  urgency: "watch" as const,
  risk: "medium" as const,
  daysLeft: 30,
  day: 70,
  totalDays: 100,
  engagement: 0.2,
  progress: 0.2,
  d45: true,
  hormoziScore: 20,
  ltv: 500
}));

vi.mock("../domain/hooks/useCommandCenter", () => ({
  useCommandCenterStudentCollection: () => ({
    data: {
      items: [...topItems, ...bottomItems],
      topItems,
      bottomItems,
      totalStudents: 42,
      rankingMode: "top_bottom" as const
    },
    loading: false,
    error: null,
    refresh: vi.fn()
  }),
  useCommandCenterStudents: () => ({
    data: [...topItems, ...bottomItems],
    loading: false,
    error: null,
    refresh: vi.fn()
  }),
  useCommandCenterStudentDetail: () => ({
    data: { metricValues: [], checkpoints: [] },
    loading: false,
    error: null,
    refresh: vi.fn()
  }),
  useCommandCenterTimeline: () => ({
    data: { anomalies: [], timeline: [] },
    loading: false,
    error: null,
    refresh: vi.fn()
  })
}));

describe("CommandCenterPage", () => {
  it("renders top and bottom 10 students using tabs", () => {
    render(
      <MemoryRouter initialEntries={["/app/centro-comando"]}>
        <Routes>
          <Route path="/app/centro-comando" element={<CommandCenterPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByRole("tab", { name: "Top 10" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Bottom 10" })).toBeInTheDocument();
    expect(screen.getByText("42 monitorados")).toBeInTheDocument();
    expect(screen.getAllByText("Top 1").length).toBeGreaterThan(0);
    expect(screen.queryByText("Bottom 1")).toBeNull();

    fireEvent.click(screen.getByRole("tab", { name: "Bottom 10" }));

    expect(screen.getAllByText("Bottom 1").length).toBeGreaterThan(0);
    expect(screen.queryByText("Top 1")).toBeNull();
  });
});
