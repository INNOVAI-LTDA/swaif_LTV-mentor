import { normalizeApiBaseUrl, normalizeBasePath, normalizeDeployTarget } from "./envContract";

function parseTimeout(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
}

function parseBoolean(value: string | undefined): boolean {
  const normalized = (value || "").trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

function parseText(value: string | undefined, fallback: string): string {
  const candidate = (value || "").trim();
  return candidate || fallback;
}

export function buildPublicAssetUrl(relativePath: string): string {
  const normalizedPath = relativePath.replace(/^\/+/, "");
  return `${appBasePath}${normalizedPath}`;
}

const appBasePath = normalizeBasePath(import.meta.env.VITE_APP_BASE_PATH || import.meta.env.BASE_URL);
const routerBasePath = appBasePath === "/" ? "/" : appBasePath.replace(/\/$/, "");
const deployTarget = normalizeDeployTarget(import.meta.env.VITE_DEPLOY_TARGET);
const isLocalDeployTarget = deployTarget === "local";
const demoModeEnabled = isLocalDeployTarget && parseBoolean(import.meta.env.VITE_ENABLE_DEMO_MODE);
const internalMentorDemoEnabled = isLocalDeployTarget && parseBoolean(import.meta.env.VITE_ENABLE_INTERNAL_MENTOR_DEMO);
const clientName = parseText(import.meta.env.VITE_CLIENT_NAME, "Cliente");
const appName = parseText(import.meta.env.VITE_APP_NAME, "Plataforma de Mentoria");
const appTagline = parseText(import.meta.env.VITE_APP_TAGLINE, "Acompanhamento com visao operacional");
const shellSubtitle = parseText(import.meta.env.VITE_SHELL_SUBTITLE, "Operacao, acompanhamento e governanca");
const brandingIconPath = parseText(import.meta.env.VITE_BRANDING_ICON_PATH, "branding/app-icon.png");
const brandingLogoPath = parseText(import.meta.env.VITE_BRANDING_LOGO_PATH, "branding/app-logo.png");
const brandingLoginHeroPath = parseText(import.meta.env.VITE_BRANDING_LOGIN_HERO_PATH, "branding/login-hero.png");

export const env = {
  deployTarget,
  isLocalDeployTarget,
  appBasePath,
  routerBasePath,
  apiBaseUrl: normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL, deployTarget),
  httpTimeoutMs: parseTimeout(import.meta.env.VITE_HTTP_TIMEOUT_MS, 15000),
  demoModeEnabled,
  internalMentorDemoEnabled,
  clientName,
  appName,
  appTagline,
  shellSubtitle,
  brandingIconUrl: buildPublicAssetUrl(brandingIconPath),
  brandingLogoUrl: buildPublicAssetUrl(brandingLogoPath),
  brandingLoginHeroUrl: buildPublicAssetUrl(brandingLoginHeroPath)
};
