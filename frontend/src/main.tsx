import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { appRouter } from "./app/routes";
import { AuthProvider } from "./app/providers/AuthProvider";
import { env } from "./shared/config/env";
import "./styles/global.css";

document.documentElement.style.setProperty("--color-bg-primary", env.themeColors.bgPrimary);
document.documentElement.style.setProperty("--color-bg-secondary", env.themeColors.bgSecondary);
document.documentElement.style.setProperty("--color-surface-primary", env.themeColors.surfacePrimary);
document.documentElement.style.setProperty("--color-surface-secondary", env.themeColors.surfaceSecondary);
document.documentElement.style.setProperty("--color-border-default", env.themeColors.borderDefault);
document.documentElement.style.setProperty("--color-text-primary", env.themeColors.textPrimary);
document.documentElement.style.setProperty("--color-text-secondary", env.themeColors.textSecondary);
document.documentElement.style.setProperty("--color-accent-primary", env.themeColors.accentPrimary);
document.documentElement.style.setProperty("--color-accent-secondary", env.themeColors.accentSecondary);
document.documentElement.style.setProperty("--color-success", env.themeColors.success);
document.documentElement.style.setProperty("--color-warning", env.themeColors.warning);
document.documentElement.style.setProperty("--color-danger", env.themeColors.danger);
document.documentElement.style.setProperty("--login-hero-url", `url("${env.brandingLoginHeroUrl}")`);
document.title = `${env.appName} | ${env.clientName}`;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={appRouter} />
    </AuthProvider>
  </React.StrictMode>
);
