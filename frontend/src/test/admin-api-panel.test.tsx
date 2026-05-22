import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AdminPage } from "../features/admin/pages/AdminPage";

const listAdminApiOperationsMock = vi.fn();

vi.mock("../app/providers/AuthProvider", () => ({
  useAuth: () => ({ authReady: true, isAuthenticated: true, user: { id: "usr_admin", email: "admin@cliente.test", role: "admin" } })
}));
const emptyResource = { data: [], error: null, loading: false, refresh: vi.fn() };
vi.mock("../domain/hooks/useAdminClients", () => ({ useAdminClients: () => emptyResource, useAdminClientDetail: () => ({ data: null, error: null, loading: false }) }));
vi.mock("../domain/hooks/useAdminProducts", () => ({ useAdminProducts: () => emptyResource }));
vi.mock("../domain/hooks/useAdminMentors", () => ({ useAdminMentors: () => emptyResource }));
vi.mock("../domain/hooks/useAdminPillars", () => ({ useAdminPillars: () => emptyResource }));
vi.mock("../domain/hooks/useAdminMetrics", () => ({ useAdminMetrics: () => emptyResource }));
vi.mock("../domain/hooks/useAdminStudents", () => ({ useAdminStudents: () => emptyResource }));
vi.mock("../domain/hooks/useRadar", () => ({ useStudentRadar: () => ({ data: { axisScores: [] }, error: null, loading: false, refresh: vi.fn() }) }));
vi.mock("../domain/services/adminDatabaseViewService", () => ({ listDatabaseTables: vi.fn(), listDatabaseRecords: vi.fn(), updateDatabaseRecord: vi.fn() }));
vi.mock("../domain/services/adminClientService", () => ({ createAdminClient: vi.fn() }));
vi.mock("../domain/services/adminMetricService", () => ({ createAdminMetric: vi.fn(), listAdminMetricsByProduct: vi.fn() }));
vi.mock("../domain/services/adminMentorService", () => ({ createAdminMentor: vi.fn() }));
vi.mock("../domain/services/adminPillarService", () => ({ createAdminPillar: vi.fn() }));
vi.mock("../domain/services/adminProductService", () => ({ createAdminProduct: vi.fn() }));
vi.mock("../domain/services/adminStudentService", () => ({ createAdminStudent: vi.fn(), loadAdminStudentIndicators: vi.fn(), reassignAdminStudent: vi.fn(), unlinkAdminStudent: vi.fn() }));
vi.mock("../domain/services/adminApiOperationsService", () => ({
  listAdminApiOperations: (...args: unknown[]) => listAdminApiOperationsMock(...args),
  executeAdminApiOperation: vi.fn()
}));

describe("admin api panel", () => {
  beforeEach(() => {
    listAdminApiOperationsMock.mockReset();
  });

  it("renderiza catalogo de API e consulta servico", async () => {
    listAdminApiOperationsMock.mockResolvedValue([]);
    render(<MemoryRouter initialEntries={["/app/admin?panel=api"]}><AdminPage /></MemoryRouter>);
    expect(await screen.findByText("Catalogo didatico de requests monitoraveis")).toBeInTheDocument();
    await waitFor(() => expect(listAdminApiOperationsMock).toHaveBeenCalled());
  });
});
