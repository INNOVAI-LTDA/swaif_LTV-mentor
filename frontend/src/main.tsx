import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { appRouter } from "./app/routes";
import { AuthProvider } from "./app/providers/AuthProvider";
import { env } from "./shared/config/env";
import "./styles/global.css";

document.documentElement.style.setProperty("--login-hero-url", `url("${env.brandingLoginHeroUrl}")`);
document.title = `${env.appName} | ${env.clientName}`;

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={appRouter} />
    </AuthProvider>
  </React.StrictMode>
);
