import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { StudentShell } from "../features/student/components/StudentShell";

vi.mock("../features/student/hooks/useStudentProducts", () => ({
  useStudentProducts: () => ({ products: [], loading: false, error: null })
}));

vi.mock("../features/student/hooks/useStudentProfile", () => ({
  useStudentProfile: () => ({ profile: null, loading: false, error: null })
}));

describe("StudentShell navigation", () => {
  it("renderiza apenas os atalhos solicitados na sidebar", () => {
    render(
      <MemoryRouter initialEntries={["/app/aluno?view=radar"]}>
        <StudentShell eyebrow="Aluno" title="Radar" description="Descricao">
          <div>Conteudo</div>
        </StudentShell>
      </MemoryRouter>
    );

    expect(screen.getByRole("link", { name: "Radar de Evolução" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Indicadores" })).toBeInTheDocument();

    expect(screen.queryByRole("link", { name: "Linha do Tempo" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Sua Jornada" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Mentores" })).not.toBeInTheDocument();
    expect(screen.queryByText("Jornada do aluno")).not.toBeInTheDocument();
  });
});
