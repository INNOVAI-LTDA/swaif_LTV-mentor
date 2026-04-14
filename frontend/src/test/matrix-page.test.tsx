import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import type { MatrixItem } from "../domain/models";
import { MatrixPage } from "../features/matrix/pages/MatrixPage";

vi.mock("../features/mentor/components/MentorShell", () => ({
    MentorShell: ({ children, showSpotlight, brandLabel, brandTitle }: { children: React.ReactNode; showSpotlight?: boolean; brandLabel?: string; brandTitle?: string }) => (
        <div data-show-spotlight={String(showSpotlight)} data-brand-label={brandLabel ?? ""} data-brand-title={brandTitle ?? ""}>{children}</div>
    )
}));

let mockItems: MatrixItem[] = [
    {
        id: "enr_1",
        name: "Ana Paula",
        initials: "AP",
        programName: "Master AccMed",
        progress: 0.82,
        engagement: 0.74,
        daysLeft: 30,
        urgency: "watch",
        ltv: 250000,
        renewalReason: "Boa aderencia ao metodo.",
        suggestion: "Abrir conversa de renovacao.",
        markers: [
            { label: "Captação", value: 0.8, target: 1, pct: 80, improving: true }
        ],
        quadrant: "topRight"
    }
];

vi.mock("../domain/hooks/useMatrix", () => ({
    useRenewalMatrix: () => ({
        data: {
            items: mockItems,
            kpis: {
                totalLTV: 250000,
                criticalRenewals: 1,
                rescueCount: 0,
                avgEngagement: 0.74
            },
            context: {
                mentorName: "Dr. José Netto",
                mentorId: "mtr_2",
                protocolName: "Master Acelerador Médico",
                protocolId: "prt_3",
            },
        },
        loading: false,
        error: null,
        refresh: vi.fn()
    })
}));

describe("MatrixPage", () => {
    it("opens renewal context only after bubble click and keeps matrix visible without side panel", () => {
        mockItems = [
            {
                id: "enr_1",
                name: "Ana Paula",
                initials: "AP",
                programName: "Master AccMed",
                progress: 0.82,
                engagement: 0.74,
                daysLeft: 30,
                urgency: "watch",
                ltv: 250000,
                renewalReason: "Boa aderencia ao metodo.",
                suggestion: "Abrir conversa de renovacao.",
                markers: [
                    { label: "Captação", value: 0.8, target: 1, pct: 80, improving: true }
                ],
                quadrant: "topRight"
            }
        ];

        render(
            <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
                <Routes>
                    <Route path="/app/matriz-renovacao" element={<MatrixPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(screen.queryByText("Contexto de Renovação")).toBeNull();
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-show-spotlight]")).toHaveAttribute("data-show-spotlight", "false");
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-brand-label]")).toHaveAttribute("data-brand-label", "Dr. José Netto");
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-brand-title]")).toHaveAttribute("data-brand-title", "Master Acelerador Médico");
        expect(screen.getByRole("heading", { name: "Renovar" })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "Ajustar plano" })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "Resgatar valor" })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "Recuperação urgente" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "10 por quadrante" })).toHaveClass("is-active");

        fireEvent.click(screen.getByRole("button", { name: /ap/i }));

        expect(screen.getByText("Contexto de Renovação")).toBeInTheDocument();
        expect(screen.getByText("Boa aderencia ao metodo.")).toBeInTheDocument();
        expect(screen.getByText("Abrir conversa de renovacao.")).toBeInTheDocument();

        fireEvent.pointerDown(document.body);

        expect(screen.queryByText("Contexto de Renovação")).toBeNull();
    });

    it("limits density by visual quadrant instead of backend quadrant field", () => {
        mockItems = [
            { id: "enr_1", name: "Aluno 1", initials: "A1", programName: "Master", progress: 0.9, engagement: 0.9, daysLeft: 30, urgency: "watch", ltv: 120000, renewalReason: "", suggestion: "", markers: [], quadrant: "topRight" },
            { id: "enr_2", name: "Aluno 2", initials: "A2", programName: "Master", progress: 0.88, engagement: 0.88, daysLeft: 31, urgency: "normal", ltv: 130000, renewalReason: "", suggestion: "", markers: [], quadrant: "topLeft" },
            { id: "enr_3", name: "Aluno 3", initials: "A3", programName: "Master", progress: 0.86, engagement: 0.86, daysLeft: 32, urgency: "normal", ltv: 140000, renewalReason: "", suggestion: "", markers: [], quadrant: "bottomRight" },
            { id: "enr_4", name: "Aluno 4", initials: "A4", programName: "Master", progress: 0.84, engagement: 0.84, daysLeft: 33, urgency: "normal", ltv: 150000, renewalReason: "", suggestion: "", markers: [], quadrant: "bottomLeft" },
            { id: "enr_5", name: "Aluno 5", initials: "A5", programName: "Master", progress: 0.82, engagement: 0.82, daysLeft: 34, urgency: "normal", ltv: 160000, renewalReason: "", suggestion: "", markers: [], quadrant: "topRight" },
            { id: "enr_6", name: "Aluno 6", initials: "A6", programName: "Master", progress: 0.8, engagement: 0.8, daysLeft: 35, urgency: "normal", ltv: 170000, renewalReason: "", suggestion: "", markers: [], quadrant: "topLeft" }
        ];

        render(
            <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
                <Routes>
                    <Route path="/app/matriz-renovacao" element={<MatrixPage />} />
                </Routes>
            </MemoryRouter>
        );

        const densityRow = screen.getByLabelText("Quantidade de bolhas por quadrante");
        fireEvent.click(within(densityRow).getByRole("button", { name: "5 por quadrante" }));

        expect(screen.getByRole("button", { name: /a1/i })).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: /a6/i })).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "Todos" }));

        expect(screen.getByRole("button", { name: /a6/i })).toBeInTheDocument();
    });
});
