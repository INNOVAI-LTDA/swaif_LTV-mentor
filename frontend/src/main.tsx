import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { appRouter } from "./app/routes";
import { AuthProvider } from "./app/providers/AuthProvider";
import { env } from "./shared/config/env";
import "./styles/global.css";

function hexToRgbChannels(hex: string): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return "0, 0, 0";
  return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
}

const root = document.documentElement;

root.style.setProperty("--color-bg-primary", env.themeColors.bgPrimary);
root.style.setProperty("--color-bg-secondary", env.themeColors.bgSecondary);
root.style.setProperty("--color-surface-primary", env.themeColors.surfacePrimary);
root.style.setProperty("--color-surface-secondary", env.themeColors.surfaceSecondary);
root.style.setProperty("--color-border-default", env.themeColors.borderDefault);
root.style.setProperty("--color-text-primary", env.themeColors.textPrimary);
root.style.setProperty("--color-text-secondary", env.themeColors.textSecondary);
root.style.setProperty("--color-accent-primary", env.themeColors.accentPrimary);
root.style.setProperty("--color-accent-secondary", env.themeColors.accentSecondary);
root.style.setProperty("--color-success", env.themeColors.success);
root.style.setProperty("--color-warning", env.themeColors.warning);
root.style.setProperty("--color-danger", env.themeColors.danger);
// RGB channel vars enable rgba() tokenization in CSS: rgba(var(--color-accent-primary-rgb), 0.24)
root.style.setProperty("--color-accent-primary-rgb", hexToRgbChannels(env.themeColors.accentPrimary));
root.style.setProperty("--color-bg-primary-rgb", hexToRgbChannels(env.themeColors.bgPrimary));
root.style.setProperty("--color-success-rgb", hexToRgbChannels(env.themeColors.success));
root.style.setProperty("--color-warning-rgb", hexToRgbChannels(env.themeColors.warning));
root.style.setProperty("--color-danger-rgb", hexToRgbChannels(env.themeColors.danger));
root.style.setProperty("--login-hero-url", `url("${env.brandingLoginHeroUrl}")`);
document.title = `${env.appName} | ${env.clientName}`;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={appRouter} />
    </AuthProvider>
  </React.StrictMode>
);
