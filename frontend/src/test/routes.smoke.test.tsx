import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { appRoutes } from "../app/routes";
import { AuthProvider } from "../app/providers/AuthProvider";

describe("app routes", () => {
  it("renderiza a pagina de login", () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/login"]
    });

    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    );

    expect(screen.getByRole("heading", { name: "Entrar na nova experiencia" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrar como Mentor" })).toBeInTheDocument();
  });

  it("renderiza pagina 404 para rota desconhecida", () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/rota-inexistente"]
    });

    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    );

    expect(screen.getByRole("heading", { name: "Pagina nao encontrada" })).toBeInTheDocument();
  });

  it("renderiza a tela do aluno", async () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/app/aluno"]
    });

    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    );

    expect(await screen.findByRole("heading", { name: "Acompanhe seu radar de evolucao" })).toBeInTheDocument();
  });

  it("renderiza a tela do admin", async () => {
    const router = createMemoryRouter(appRoutes, {
      initialEntries: ["/app/admin"]
    });

    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    );

    expect(await screen.findByRole("heading", { name: "Centro Institucional" })).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Clientes ativos" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Clientes" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cadastrar cliente" })).toBeInTheDocument();
  });
});
