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
        expect(screen.getByRole("button", { name: "5 por quadrante" })).toHaveClass("is-active");

        fireEvent.click(screen.getByRole("button", { name: /ap/i }));

        expect(screen.getByText("Contexto de Renovação")).toBeInTheDocument();
        expect(screen.getByText("Boa aderencia ao metodo.")).toBeInTheDocument();
        expect(screen.getByText("Abrir conversa de renovacao.")).toBeInTheDocument();

        fireEvent.pointerDown(document.body);

        expect(screen.queryByText("Contexto de Renovação")).toBeNull();
    });

    it("applies density strictly with large datasets per quadrant when toggling 5, 10, 20 and back to 5", () => {
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

        const buildQuadrantItems = (
            prefix: "tr" | "tl" | "br" | "bl",
            count: number
        ) => Array.from({ length: count }, (_, index) => {
            const itemNumber = index + 1;

            if (prefix === "tr") {
                return buildItem(`tr-${itemNumber}`, `TR${itemNumber}`, 0.7 + index * 0.01, 0.7 + index * 0.01);
            }
            if (prefix === "tl") {
                return buildItem(`tl-${itemNumber}`, `TL${itemNumber}`, 0.2 + index * 0.01, 0.7 + index * 0.01);
            }
            if (prefix === "br") {
                return buildItem(`br-${itemNumber}`, `BR${itemNumber}`, 0.7 + index * 0.01, 0.2 + index * 0.01);
            }
            return buildItem(`bl-${itemNumber}`, `BL${itemNumber}`, 0.2 + index * 0.01, 0.2 + index * 0.01);
        });

        const topRight = buildQuadrantItems("tr", 22);
        const topLeft = buildQuadrantItems("tl", 22);
        const bottomRight = buildQuadrantItems("br", 22);
        const bottomLeft = buildQuadrantItems("bl", 22);

        mockItems = [...topRight, ...topLeft, ...bottomRight, ...bottomLeft];

        render(
            <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
                <Routes>
                    <Route path="/app/matriz-renovacao" element={<MatrixPage />} />
                </Routes>
            </MemoryRouter>
        );

        const countByVisualQuadrant = (quadrant: "topRight" | "topLeft" | "bottomRight" | "bottomLeft") =>
            document.querySelectorAll(`.mx-board-surface button.mx-bubble[data-visual-quadrant="${quadrant}"]`).length;

        const expectVisibleCounts = (expected: { topRight: number; topLeft: number; bottomRight: number; bottomLeft: number }) => {
            expect(countByVisualQuadrant("topRight")).toBe(expected.topRight);
            expect(countByVisualQuadrant("topLeft")).toBe(expected.topLeft);
            expect(countByVisualQuadrant("bottomRight")).toBe(expected.bottomRight);
            expect(countByVisualQuadrant("bottomLeft")).toBe(expected.bottomLeft);
        };

        const densityRow = screen.getByLabelText("Quantidade de bolhas por quadrante");

        expectVisibleCounts({ topRight: 5, topLeft: 5, bottomRight: 5, bottomLeft: 5 });
        expect(screen.queryByRole("button", { name: /TR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /TL6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BL6/i })).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "10 por quadrante" }));
        expectVisibleCounts({ topRight: 10, topLeft: 10, bottomRight: 10, bottomLeft: 10 });
        expect(screen.getByTitle("Aluno tr-10 - Master")).toBeInTheDocument();
        expect(screen.getByTitle("Aluno tl-10 - Master")).toBeInTheDocument();
        expect(screen.queryByTitle("Aluno tr-11 - Master")).toBeNull();
        expect(screen.queryByTitle("Aluno tl-11 - Master")).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "20 por quadrante" }));
        expectVisibleCounts({ topRight: 20, topLeft: 20, bottomRight: 20, bottomLeft: 20 });
        expect(screen.getByTitle("Aluno tr-20 - Master")).toBeInTheDocument();
        expect(screen.getByTitle("Aluno tl-20 - Master")).toBeInTheDocument();
        expect(screen.queryByTitle("Aluno tr-21 - Master")).toBeNull();
        expect(screen.queryByTitle("Aluno tl-21 - Master")).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "5 por quadrante" }));
        expectVisibleCounts({ topRight: 5, topLeft: 5, bottomRight: 5, bottomLeft: 5 });
        expect(screen.queryByRole("button", { name: /TR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /TL6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BL6/i })).toBeNull();

        fireEvent.click(within(densityRow).getByRole("button", { name: "Todos" }));
        expectVisibleCounts({ topRight: 22, topLeft: 22, bottomRight: 22, bottomLeft: 22 });
        expect(screen.getByTitle("Aluno tr-22 - Master")).toBeInTheDocument();
        expect(screen.getByTitle("Aluno tl-22 - Master")).toBeInTheDocument();

        fireEvent.click(within(densityRow).getByRole("button", { name: "5 por quadrante" }));
        expectVisibleCounts({ topRight: 5, topLeft: 5, bottomRight: 5, bottomLeft: 5 });
        expect(screen.queryByRole("button", { name: /TR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /TL6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BR6/i })).toBeNull();
        expect(screen.queryByRole("button", { name: /BL6/i })).toBeNull();
    });
});
