import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
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
        internalMentorSurfaceEnabled: false,
        internalMentorDemoEnabled: false
    }
}));

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
        refresh: vi.fn()
    })
}));

vi.mock("../domain/hooks/useRadar", () => ({
    useStudentRadar: () => ({
        data: {
            axisScores: [
                {
                    axisKey: "cap",
                    axisLabel: "Captação",
                    axisSub: "",
                    baseline: 0.4,
                    current: 0.5,
                    projected: 0.8,
                    insight: null
                }
            ],
            avgBaseline: 0.4,
            avgCurrent: 0.5,
            avgProjected: 0.8
        },
        loading: false,
        error: null,
        refresh: vi.fn()
    })
}));

describe("RadarPage", () => {
    it("renders normalized radar values as percentages on the UI", () => {
        render(
            <MemoryRouter initialEntries={["/app/radar"]}>
                <Routes>
                    <Route path="/app/radar" element={<RadarPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(screen.getAllByText("40,0%").length).toBeGreaterThan(0);
        expect(screen.getAllByText("50,0%").length).toBeGreaterThan(0);
        expect(screen.getAllByText("80,0%").length).toBeGreaterThan(0);
        expect(screen.getAllByText("+10,0 pp").length).toBeGreaterThan(0);
        expect(screen.getAllByText("+30,0 pp").length).toBeGreaterThan(0);
    });
});