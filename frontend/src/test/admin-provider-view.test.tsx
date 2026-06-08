import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AdminClientDto } from "../contracts/adminClient";
import type { AdminMetricDto } from "../contracts/adminMetric";
import type { AdminMentorDto } from "../contracts/adminMentor";
import type { AdminPillarDto } from "../contracts/adminPillar";
import type { AdminProductDto } from "../contracts/adminProduct";
import type { AdminStudentDto } from "../contracts/adminStudent";
import { AdminPage } from "../features/admin/pages/AdminPage";

const refreshStudentsMock = vi.fn();

const clientsMockData: AdminClientDto[] = [{
  id: "org_1",
  name: "Cliente Teste",
  brand_name: "Cliente",
  cnpj: "00000000000100",
  slug: "cliente-teste",
  status: "active",
  is_active: true,
  timezone: "America/Sao_Paulo",
  currency: "BRL",
  notes: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z"
}];

const productsMockData: AdminProductDto[] = [{
  id: "prd_1",
  client_id: "org_1",
  name: "Mentoria",
  code: "MENT",
  slug: "mentoria",
  status: "active",
  is_active: true,
  description: null,
  delivery_model: "live",
  mentor_id: "mtr_1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z"
}];

const mentorsMockData: AdminMentorDto[] = [{
  id: "mtr_1",
  full_name: "Mentor Teste",
  email: "mentor@test.local",
  cpf: null,
  phone: null,
  bio: null,
  notes: null,
  status: "active",
  is_active: true,
  organization_id: "org_1",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z"
}];

const pillarsMockData: AdminPillarDto[] = [{
  id: "plr_1",
  protocol_id: "prt_1",
  name: "Estrategia",
  code: "EST",
  order_index: 1,
  is_active: true
}];

const metricsMockData: AdminMetricDto[] = [{
  id: "met_1",
  protocol_id: "prt_1",
  pillar_id: "plr_1",
  name: "Clareza do plano",
  code: "clareza_plano",
  direction: "higher_better",
  unit: "%",
  is_active: true,
  pillar_name: "Estrategia"
}];

const studentsMockData: AdminStudentDto[] = [
  {
    id: "std_1",
    full_name: "Aluno Um",
    initials: "AU",
    email: "aluno1@test.local",
    cpf: null,
    phone: null,
    notes: null,
    status: "active",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    mentor_id: "mtr_1",
    organization_id: "org_1",
    enrollment_id: "enr_1"
  },
  {
    id: "std_2",
    full_name: "Aluno Dois",
    initials: "AD",
    email: "aluno2@test.local",
    cpf: null,
    phone: null,
    notes: null,
    status: "active",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    mentor_id: "mtr_1",
    organization_id: "org_1",
    enrollment_id: "enr_2"
  }
];

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({
    authReady: true,
    isAuthenticated: true,
    user: { id: "usr_admin", email: "admin@cliente.test", role: "admin" }
  })
}));

vi.mock("../domain/hooks/useAdminClients", () => ({
  useAdminClients: () => ({ data: clientsMockData, error: null, loading: false, refresh: vi.fn() }),
  useAdminClientDetail: () => ({ data: null, error: null, loading: false })
}));

vi.mock("../domain/hooks/useAdminProducts", () => ({
  useAdminProducts: () => ({ data: productsMockData, error: null, loading: false, refresh: vi.fn() })
}));

vi.mock("../domain/hooks/useAdminMentors", () => ({
  useAdminMentors: () => ({ data: mentorsMockData, error: null, loading: false, refresh: vi.fn() })
}));

vi.mock("../domain/hooks/useAdminPillars", () => ({
  useAdminPillars: () => ({ data: pillarsMockData, error: null, loading: false, refresh: vi.fn() })
}));

vi.mock("../domain/hooks/useAdminMetrics", () => ({
  useAdminMetrics: () => ({ data: metricsMockData, error: null, loading: false, refresh: vi.fn() })
}));

vi.mock("../domain/hooks/useAdminStudents", () => ({
  useAdminStudents: () => ({ data: studentsMockData, error: null, loading: false, refresh: refreshStudentsMock }),
  useAdminStudentRadar: () => ({
    data: {
      studentId: "std_1",
      axisScores: [{
        axisId: "plr_1",
        axisKey: "estrategia",
        axisLabel: "Estrategia",
        axisSub: "Plano",
        baseline: 0.2,
        current: 0.45,
        projected: 0.7,
        insight: "Pilar em evolucao"
      }],
      avgBaseline: 0.2,
      avgCurrent: 0.45,
      avgProjected: 0.7,
      context: { mentorName: "Mentor Teste", mentorId: "mtr_1" }
    },
    error: null,
    loading: false,
    refresh: vi.fn()
  })
}));

vi.mock("../domain/services/adminDatabaseViewService", () => ({
  listDatabaseTables: vi.fn(),
  listDatabaseRecords: vi.fn(),
  updateDatabaseRecord: vi.fn()
}));
vi.mock("../domain/services/adminClientService", () => ({ createAdminClient: vi.fn() }));
vi.mock("../domain/services/adminMetricService", () => ({ createAdminMetric: vi.fn(), listAdminMetricsByProduct: vi.fn() }));
vi.mock("../domain/services/adminMentorService", () => ({ createAdminMentor: vi.fn() }));
vi.mock("../domain/services/adminPillarService", () => ({ createAdminPillar: vi.fn() }));
vi.mock("../domain/services/adminProductService", () => ({ createAdminProduct: vi.fn() }));
vi.mock("../domain/services/adminStudentService", () => ({
  createAdminStudent: vi.fn(),
  loadAdminStudentIndicators: vi.fn(),
  reassignAdminStudent: vi.fn(),
  unlinkAdminStudent: vi.fn()
}));
vi.mock("../domain/services/adminApiOperationsService", () => ({
  listAdminApiOperations: vi.fn(),
  executeAdminApiOperation: vi.fn()
}));

describe("admin provider view", () => {
  beforeEach(() => {
    refreshStudentsMock.mockClear();
  });

  it("exibe matriz agregada e radar em abas sem Centro de Comando", async () => {
    render(<MemoryRouter initialEntries={["/app/admin?panel=provider"]}><AdminPage /></MemoryRouter>);

    const searchButton = await screen.findByRole("button", { name: "Buscar Alunos" });
    await waitFor(() => expect(searchButton).not.toBeDisabled());
    fireEvent.click(searchButton);

    expect(await screen.findByTestId("admin-provider-view-editable")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Centro de Comando" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Matriz de Decisão" })).toBeInTheDocument();
    expect(screen.getByText("Distribuição dos alunos por quadrante no contexto selecionado.")).toBeInTheDocument();
    expect(screen.queryByLabelText(/Provider View Matriz Progresso/)).not.toBeInTheDocument();

    expect(screen.getByRole("tab", { name: "Pilares" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("cell", { name: "Estrategia" })).toBeInTheDocument();
    expect(screen.queryByLabelText(/Provider View Radar Baseline/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Métricas" }));
    expect(await screen.findByLabelText("Provider View Radar Métrica Nome Clareza do plano")).toBeInTheDocument();
  });
});
