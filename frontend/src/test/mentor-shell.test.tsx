import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { MentorShell } from "../features/mentor/components/MentorShell";

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
    internalMentorDemoEnabled: false,
    clientCode: "local"
  }
}));

describe("MentorShell", () => {
  it("does not render the sidebar spotlight copy", () => {
    render(
      <MemoryRouter initialEntries={["/app/matriz-renovacao"]}>
        <MentorShell activeView="matrix">
          <div>Conteudo</div>
        </MentorShell>
      </MemoryRouter>
    );

    expect(screen.getByText("Visoes principais")).toBeInTheDocument();
    expect(screen.getByText("Areas de Apoio")).toBeInTheDocument();
    expect(screen.queryByText("Leitura da carteira")).not.toBeInTheDocument();
  });
});
