import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { MatrixPage } from "../features/matrix/pages/MatrixPage";

vi.mock("../features/mentor/components/MentorShell", () => ({
    MentorShell: ({ children, showSpotlight, brandLabel, brandTitle }: { children: React.ReactNode; showSpotlight?: boolean; brandLabel?: string; brandTitle?: string }) => (
        <div data-show-spotlight={String(showSpotlight)} data-brand-label={brandLabel ?? ""} data-brand-title={brandTitle ?? ""}>{children}</div>
    )
}));

vi.mock("../domain/hooks/useMatrix", () => ({
    useRenewalMatrix: () => ({
        data: {
            items: [
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
            ],
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
        render(
            <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
                <Routes>
                    <Route path="/app/matriz-renovacao" element={<MatrixPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(screen.queryByRole("heading", { name: "Painel de ação rápida" })).toBeNull();
        expect(screen.queryByText("Clique em uma bolha da matriz para abrir os detalhes.")).toBeNull();
        expect(screen.queryByText("Contexto de Renovação")).toBeNull();
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-show-spotlight]")).toHaveAttribute(
            "data-show-spotlight",
            "false"
        );
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-brand-label]")).toHaveAttribute(
            "data-brand-label",
            "Dr. José Netto"
        );
        expect(screen.getByText("Bolhas por quadrante").closest("div[data-brand-title]")).toHaveAttribute(
            "data-brand-title",
            "Master Acelerador Médico"
        );
        expect(screen.queryByText("Alto progresso · Alto engajamento")).toBeNull();
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
});