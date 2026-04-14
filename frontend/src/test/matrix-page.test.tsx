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

    it("limits density by visual quadrant with controlled balanced dataset and removes limits on Todos", () => {
        const buildItem = (
            id: string,
            initials: string,
            progress: number,
            engagement: number
        ): MatrixItem => ({
            id,
            name: `Aluno ${id}`,
            initials,
            programName: "Master",
            progress,
            engagement,
            daysLeft: 30,
            urgency: "normal",
            ltv: 100000,
            renewalReason: "",
            suggestion: "",
            markers: [],
            quadrant: "bottomLeft"
        });

        const topRight = [
            buildItem("tr-1", "TR1", 0.92, 0.92),
            buildItem("tr-2", "TR2", 0.9, 0.88),
            buildItem("tr-3", "TR3", 0.86, 0.84),
            buildItem("tr-4", "TR4", 0.84, 0.82),
            buildItem("tr-5", "TR5", 0.82, 0.8),
            buildItem("tr-6", "TR6", 0.8, 0.78)
        ];
        const topLeft = [
            buildItem("tl-1", "TL1", 0.2, 0.9),
            buildItem("tl-2", "TL2", 0.24, 0.86),
            buildItem("tl-3", "TL3", 0.28, 0.82),
            buildItem("tl-4", "TL4", 0.3, 0.8),
            buildItem("tl-5", "TL5", 0.34, 0.78),
            buildItem("tl-6", "TL6", 0.38, 0.76)
        ];
        const bottomRight = [
            buildItem("br-1", "BR1", 0.9, 0.2),
            buildItem("br-2", "BR2", 0.86, 0.24),
            buildItem("br-3", "BR3", 0.82, 0.28),
            buildItem("br-4", "BR4", 0.78, 0.32)
        ];
        const bottomLeft = [
            buildItem("bl-1", "BL1", 0.2, 0.2),
            buildItem("bl-2", "BL2", 0.24, 0.24),
            buildItem("bl-3", "BL3", 0.28, 0.28),
            buildItem("bl-4", "BL4", 0.32, 0.32)
        ];

        mockItems = [...topRight, ...topLeft, ...bottomRight, ...bottomLeft];

        render(
            <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
                <Routes>
                    <Route path="/app/matriz-renovacao" element={<MatrixPage />} />
                </Routes>
            </MemoryRouter>
        );

        const densityRow = screen.getByLabelText("Quantidade de bolhas por quadrante");
        fireEvent.click(within(densityRow).getByRole("button", { name: "5 por quadrante" }));

        const board = document.querySelector(".mx-board-surface");
        expect(board).not.toBeNull();

        const visibleTopRight = board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="topRight"]') ?? [];
        const visibleTopLeft = board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="topLeft"]') ?? [];
        const visibleBottomRight = board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="bottomRight"]') ?? [];
        const visibleBottomLeft = board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="bottomLeft"]') ?? [];

        expect(visibleTopRight).toHaveLength(5);
        expect(visibleTopLeft).toHaveLength(5);
        expect(visibleBottomRight).toHaveLength(4);
        expect(visibleBottomLeft).toHaveLength(4);
        expect(screen.queryByRole("button", { name: /TR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /TL6/i })).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "Todos" }));

        expect(screen.getByRole("button", { name: /TR6/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /TL6/i })).toBeInTheDocument();
        expect(board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="topRight"]')).toHaveLength(6);
        expect(board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="topLeft"]')).toHaveLength(6);
        expect(board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="bottomRight"]')).toHaveLength(4);
        expect(board?.querySelectorAll('button.mx-bubble[data-visual-quadrant="bottomLeft"]')).toHaveLength(4);
    });
});
