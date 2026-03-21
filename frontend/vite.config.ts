import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { normalizeApiBaseUrl, normalizeBasePath, normalizeDeployTarget } from "./src/shared/config/envContract";

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const appBasePath = normalizeBasePath(env.VITE_APP_BASE_PATH);
  const isBuild = command === "build";
  const deployTarget = normalizeDeployTarget(env.VITE_DEPLOY_TARGET || (mode === "test" ? "local" : undefined));

  if (isBuild && deployTarget === "client") {
    normalizeApiBaseUrl(env.VITE_API_BASE_URL, deployTarget);
  }

  return {
    base: appBasePath,
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173
    },
    preview: {
      host: "127.0.0.1",
      port: 4173
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      css: true
    }
  };
});
