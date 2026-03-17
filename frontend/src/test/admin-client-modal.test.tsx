import { fireEvent, render, screen, waitForElementToBeRemoved } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AdminClientDto } from "../contracts/adminClient";
import type { AdminMetricDto } from "../contracts/adminMetric";
import type { AdminMentorDto } from "../contracts/adminMentor";
import type { AdminPillarDto } from "../contracts/adminPillar";
import type { AdminProductDto } from "../contracts/adminProduct";
import type { AdminStudentDto } from "../contracts/adminStudent";
import { AdminPage } from "../features/admin/pages/AdminPage";

const refreshClientsMock = vi.fn();
const refreshProductsMock = vi.fn();
const refreshMentorsMock = vi.fn();
const refreshPillarsMock = vi.fn();
const refreshMetricsMock = vi.fn();
const refreshStudentsMock = vi.fn();
const createAdminClientMock = vi.fn();
const createAdminMetricMock = vi.fn();
const listAdminMetricsByProductMock = vi.fn();
const createAdminProductMock = vi.fn();
const createAdminMentorMock = vi.fn();
const createAdminPillarMock = vi.fn();
const createAdminStudentMock = vi.fn();
const loadAdminStudentIndicatorsMock = vi.fn();
const reassignAdminStudentMock = vi.fn();
const unlinkAdminStudentMock = vi.fn();
const clientDetailMock = vi.fn();

let clientsMockData: AdminClientDto[] = [];
let productsMockData: AdminProductDto[] = [];
let mentorsMockData: AdminMentorDto[] = [];
let pillarsMockData: AdminPillarDto[] = [];
let metricsMockData: AdminMetricDto[] = [];
let studentsMockData: AdminStudentDto[] = [];

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: { id: "usr_admin", email: "admin@swaif.local", role: "admin" }
  })
}));

vi.mock("../domain/hooks/useAdminClients", () => ({
  useAdminClients: () => ({
    data: clientsMockData,
    error: null,
    loading: false,
    refresh: refreshClientsMock
  }),
  useAdminClientDetail: () => ({
    data: clientDetailMock(),
    error: null,
    loading: false
  })
}));

vi.mock("../domain/hooks/useAdminProducts", () => ({
  useAdminProducts: () => ({
    data: productsMockData,
    error: null,
    loading: false,
    refresh: refreshProductsMock
  })
}));

vi.mock("../domain/hooks/useAdminMentors", () => ({
  useAdminMentors: () => ({
    data: mentorsMockData,
    error: null,
    loading: false,
    refresh: refreshMentorsMock
  })
}));

vi.mock("../domain/hooks/useAdminMetrics", () => ({
  useAdminMetrics: () => ({
    data: metricsMockData,
    error: null,
    loading: false,
    refresh: refreshMetricsMock
  })
}));

vi.mock("../domain/hooks/useAdminPillars", () => ({
  useAdminPillars: () => ({
    data: pillarsMockData,
    error: null,
    loading: false,
    refresh: refreshPillarsMock
  })
}));

vi.mock("../domain/hooks/useAdminStudents", () => ({
  useAdminStudents: () => ({
    data: studentsMockData,
    error: null,
    loading: false,
    refresh: refreshStudentsMock
  })
}));

vi.mock("../domain/services/adminClientService", () => ({
  createAdminClient: (...args: unknown[]) => createAdminClientMock(...args)
}));

vi.mock("../domain/services/adminMetricService", () => ({
  createAdminMetric: (...args: unknown[]) => createAdminMetricMock(...args),
  listAdminMetricsByProduct: (...args: unknown[]) => listAdminMetricsByProductMock(...args)
}));

vi.mock("../domain/services/adminProductService", () => ({
  createAdminProduct: (...args: unknown[]) => createAdminProductMock(...args)
}));

vi.mock("../domain/services/adminMentorService", () => ({
  createAdminMentor: (...args: unknown[]) => createAdminMentorMock(...args)
}));

vi.mock("../domain/services/adminPillarService", () => ({
  createAdminPillar: (...args: unknown[]) => createAdminPillarMock(...args)
}));

vi.mock("../domain/services/adminStudentService", () => ({
  createAdminStudent: (...args: unknown[]) => createAdminStudentMock(...args),
  loadAdminStudentIndicators: (...args: unknown[]) => loadAdminStudentIndicatorsMock(...args),
  reassignAdminStudent: (...args: unknown[]) => reassignAdminStudentMock(...args),
  unlinkAdminStudent: (...args: unknown[]) => unlinkAdminStudentMock(...args)
}));

function buildClient(): AdminClientDto {
  return {
    id: "cli_1",
    name: "Clinica Horizonte",
    brand_name: "Horizonte",
    cnpj: "12345678000199",
    slug: "clinica-horizonte",
    status: "active",
    is_active: true,
    timezone: "America/Sao_Paulo",
    currency: "BRL",
    notes: null,
    created_at: "2026-03-15T00:00:00Z",
    updated_at: "2026-03-15T00:00:00Z"
  };
}

function buildProduct(): AdminProductDto {
  return {
    id: "org_1",
    client_id: "cli_1",
    name: "Acelerador Medico Premium",
    code: "AMP-PREMIUM",
    slug: "acelerador-medico-premium",
    status: "active",
    is_active: true,
    description: "Produto premium do cliente",
    delivery_model: "live",
    mentor_id: "mtr_1",
    created_at: "2026-03-15T00:00:00Z",
    updated_at: "2026-03-15T00:00:00Z"
  };
}

function buildMentor(): AdminMentorDto {
  return {
    id: "mtr_1",
    full_name: "Ana Mentora",
    email: "ana@swaif.local",
    cpf: "12345678900",
    phone: null,
    bio: null,
    notes: null,
    status: "active",
    is_active: true,
    organization_id: "org_1",
    created_at: "2026-03-15T00:00:00Z",
    updated_at: "2026-03-15T00:00:00Z"
  };
}

function buildStudent(): AdminStudentDto {
  return {
    id: "std_1",
    full_name: "Aluno Teste",
    initials: "AT",
    email: "aluno@swaif.local",
    cpf: "12345678900",
    phone: null,
    notes: null,
    status: "active",
    is_active: true,
    created_at: "2026-03-15T00:00:00Z",
    updated_at: "2026-03-15T00:00:00Z",
    mentor_id: "mtr_1",
    organization_id: "org_1"
    ,
    enrollment_id: "enr_1"
  };
}

function buildPillar(): AdminPillarDto {
  return {
    id: "plr_1",
    protocol_id: "prt_1",
    name: "Performance",
    code: "performance",
    order_index: 1,
    is_active: true
  };
}

function buildMetric(): AdminMetricDto {
  return {
    id: "met_1",
    protocol_id: "prt_1",
    pillar_id: "plr_1",
    name: "Comparecimento",
    code: "comparecimento",
    direction: "higher_better",
    unit: "%",
    is_active: true
  };
}

describe("admin client product mentor and student modals", () => {
  beforeEach(() => {
    clientsMockData = [];
    productsMockData = [];
    mentorsMockData = [];
    pillarsMockData = [];
    metricsMockData = [];
    studentsMockData = [];
    refreshClientsMock.mockReset();
    refreshProductsMock.mockReset();
    refreshMentorsMock.mockReset();
    refreshPillarsMock.mockReset();
    refreshMetricsMock.mockReset();
    refreshStudentsMock.mockReset();
    createAdminClientMock.mockReset();
    createAdminMetricMock.mockReset();
    listAdminMetricsByProductMock.mockReset();
    createAdminProductMock.mockReset();
    createAdminMentorMock.mockReset();
    createAdminPillarMock.mockReset();
    createAdminStudentMock.mockReset();
    loadAdminStudentIndicatorsMock.mockReset();
    reassignAdminStudentMock.mockReset();
    unlinkAdminStudentMock.mockReset();
    clientDetailMock.mockReset();
    clientDetailMock.mockReturnValue(null);
  });

  it("abre modal de cliente, confirma cadastro e fecha apos sucesso", async () => {
    refreshClientsMock.mockResolvedValue([]);
    createAdminClientMock.mockResolvedValue(buildClient());

    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar cliente" }));
    fireEvent.change(screen.getByLabelText("Nome empresarial"), { target: { value: "Clinica Horizonte" } });
    fireEvent.change(screen.getByLabelText("CNPJ"), { target: { value: "12.345.678/0001-99" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cadastro" }));

    expect(await screen.findByRole("heading", { name: "Cliente cadastrado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("mantem a area Clientes limpa com card de cliente e cards de produto", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=clientes"]}>
        <AdminPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Clinica Horizonte")).toBeInTheDocument();
    expect(screen.getByText("Acelerador Medico Premium")).toBeInTheDocument();
  });

  it("renderiza a area Produtos com mentor real na hierarquia", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Acelerador Medico Premium")).toBeInTheDocument();
    expect(screen.getByText("Ana Mentora")).toBeInTheDocument();
    expect(screen.getByText("Nenhum Pilar Cadastrado")).toBeInTheDocument();
  });

  it("expande os pilares reais na area Produtos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    pillarsMockData = [buildPillar()];
    metricsMockData = [buildMetric()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: /Clique para abrir/i }));

    expect(screen.getByText("Performance")).toBeInTheDocument();
    expect(screen.getByText("Comparecimento")).toBeInTheDocument();
  });

  it("renderiza a area Mentores com lista por produto", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=mentores"]}>
        <AdminPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Mentor principal")).toBeInTheDocument();
    expect(screen.getByText("Ana Mentora")).toBeInTheDocument();
  });

  it("renderiza a area Alunos com mentor e cards de alunos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    expect(screen.getByText("Ana Mentora")).toBeInTheDocument();
    expect(screen.getByText("Aluno Teste")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Gerir vinculo" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Carga inicial" })).toBeInTheDocument();
  });

  it("abre modal de produto a partir do menu Cadastrar na area de apoio", () => {
    clientsMockData = [buildClient()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Produto" }));

    expect(screen.getByRole("heading", { name: "Cadastrar produto" })).toBeInTheDocument();
  });

  it("abre modal de mentor a partir do menu Cadastrar na area Produtos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Mentor" }));

    expect(screen.getByRole("heading", { name: "Cadastrar mentor" })).toBeInTheDocument();
  });

  it("abre modal de pilar a partir do menu Cadastrar na area Produtos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Pilar" }));

    expect(screen.getByRole("heading", { name: "Cadastrar pilar" })).toBeInTheDocument();
  });

  it("abre modal de metrica a partir do menu Cadastrar na area Produtos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    pillarsMockData = [buildPillar()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Metrica" }));

    expect(screen.getByRole("heading", { name: "Cadastrar metrica" })).toBeInTheDocument();
  });

  it("abre modal de aluno a partir do menu Cadastrar na area Alunos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Aluno" }));

    expect(screen.getByRole("heading", { name: "Cadastrar aluno" })).toBeInTheDocument();
  });

  it("abre modal de gerir vinculo na area Alunos", () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor(), { ...buildMentor(), id: "mtr_2", full_name: "Bea Mentora", email: "bea@swaif.local" }];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Gerir vinculo" }));

    expect(screen.getByRole("heading", { name: "Gerir vinculo do aluno" })).toBeInTheDocument();
  });

  it("abre modal de carga inicial na area Alunos", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    listAdminMetricsByProductMock.mockResolvedValue([buildMetric()]);

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Carga inicial" }));

    expect(await screen.findByRole("heading", { name: "Carregar indicadores iniciais" })).toBeInTheDocument();
    expect(await screen.findByLabelText("Baseline - Comparecimento")).toBeInTheDocument();
  });

  it("abre modal de mentor, confirma cadastro e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshProductsMock.mockResolvedValue([]);
    refreshMentorsMock.mockResolvedValue([]);
    createAdminMentorMock.mockResolvedValue(buildMentor());

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Mentor" }));
    fireEvent.change(screen.getByLabelText("Nome completo"), { target: { value: "Ana Mentora" } });
    fireEvent.change(screen.getByLabelText("CPF"), { target: { value: "123.456.789-00" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ana@swaif.local" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cadastro" }));

    expect(await screen.findByRole("heading", { name: "Mentor cadastrado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("abre modal de aluno, confirma cadastro e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshStudentsMock.mockResolvedValue([]);
    createAdminStudentMock.mockResolvedValue(buildStudent());

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Aluno" }));
    fireEvent.change(screen.getByLabelText("Nome completo"), { target: { value: "Aluno Teste" } });
    fireEvent.change(screen.getByLabelText("CPF"), { target: { value: "123.456.789-00" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "aluno@swaif.local" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cadastro" }));

    expect(await screen.findByRole("heading", { name: "Aluno cadastrado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("reatribui aluno para outro mentor e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor(), { ...buildMentor(), id: "mtr_2", full_name: "Bea Mentora", email: "bea@swaif.local" }];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshStudentsMock.mockResolvedValue([]);
    reassignAdminStudentMock.mockResolvedValue({ ...buildStudent(), mentor_id: "mtr_2" });

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Gerir vinculo" }));
    fireEvent.change(screen.getByLabelText("Novo mentor"), { target: { value: "mtr_2" } });
    fireEvent.change(screen.getByLabelText("Justificativa"), { target: { value: "Redistribuicao operacional" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByRole("heading", { name: "Vinculo atualizado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("desvincula aluno logicamente e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshStudentsMock.mockResolvedValue([]);
    unlinkAdminStudentMock.mockResolvedValue({
      id: "enr_1",
      student_id: "std_1",
      organization_id: "org_1",
      mentor_id: "mtr_1",
      is_active: false,
      deactivated_reason: "Aluno pausado"
    });

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Gerir vinculo" }));
    fireEvent.change(screen.getByLabelText("Acao"), { target: { value: "unlink" } });
    fireEvent.change(screen.getByLabelText("Justificativa"), { target: { value: "Aluno pausado" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    expect(await screen.findByRole("heading", { name: "Vinculo atualizado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("carrega indicadores iniciais e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    studentsMockData = [buildStudent()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    listAdminMetricsByProductMock.mockResolvedValue([buildMetric()]);
    loadAdminStudentIndicatorsMock.mockResolvedValue({
      student_id: "std_1",
      enrollment_id: "enr_1",
      measurement_count: 1,
      checkpoint_count: 1
    });

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=alunos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Carga inicial" }));
    fireEvent.change(await screen.findByLabelText("Baseline - Comparecimento"), { target: { value: "55" } });
    fireEvent.change(screen.getByLabelText("Atual - Comparecimento"), { target: { value: "68" } });
    fireEvent.change(screen.getByLabelText("Projetado - Comparecimento"), { target: { value: "75" } });
    fireEvent.change(screen.getByLabelText("Label do checkpoint"), { target: { value: "Inicio consistente" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar carga" }));

    expect(await screen.findByRole("heading", { name: "Carga inicial concluida" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("abre modal de pilar, confirma cadastro e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    mentorsMockData = [buildMentor()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshPillarsMock.mockResolvedValue([]);
    createAdminPillarMock.mockResolvedValue(buildPillar());

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Pilar" }));
    fireEvent.change(screen.getByLabelText("Nome do pilar"), { target: { value: "Performance" } });
    fireEvent.change(screen.getByLabelText("Codigo"), { target: { value: "performance" } });
    fireEvent.change(screen.getByLabelText("Ordem"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cadastro" }));

    expect(await screen.findByRole("heading", { name: "Pilar cadastrado" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);

  it("abre modal de metrica, confirma cadastro e fecha apos sucesso", async () => {
    clientsMockData = [buildClient()];
    productsMockData = [buildProduct()];
    pillarsMockData = [buildPillar()];
    clientDetailMock.mockReturnValue(clientsMockData[0]);
    refreshMetricsMock.mockResolvedValue([]);
    createAdminMetricMock.mockResolvedValue(buildMetric());

    render(
      <MemoryRouter initialEntries={["/app/admin?panel=produtos"]}>
        <AdminPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Cadastrar..." }));
    fireEvent.click(screen.getByRole("button", { name: "Metrica" }));
    fireEvent.change(screen.getByLabelText("Nome da metrica"), { target: { value: "Comparecimento" } });
    fireEvent.change(screen.getByLabelText("Codigo"), { target: { value: "comparecimento" } });
    fireEvent.change(screen.getByLabelText("Unidade"), { target: { value: "%" } });
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar cadastro" }));

    expect(await screen.findByRole("heading", { name: "Metrica cadastrada" })).toBeInTheDocument();
    await waitForElementToBeRemoved(() => screen.queryByRole("dialog"), { timeout: 2500 });
  }, 10000);
});
