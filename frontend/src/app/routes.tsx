import { Navigate, Outlet, createBrowserRouter, type RouteObject } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { AccessDeniedPage } from "../pages/AccessDeniedPage";

import { CommandCenterPage } from "../features/command-center/pages/CommandCenterPage";
import { RadarPage } from "../features/radar/pages/RadarPage";
import { MatrixPage } from "../features/matrix/pages/MatrixPage";
import { StudentPage } from "../features/student/pages/StudentPage";
import { AdminPage } from "../features/admin/pages/AdminPage";

import { useAuth } from "./providers/AuthProvider";
import { getDefaultRouteForRole, isKnownUserRole } from "../shared/auth/roleRouting";
import { env } from "../shared/config/env";

// Entity List Components
import { MeasurementsList } from "../features/measurements/components/MeasurementsList";
import { ProtocolsList } from "../features/protocols/components/ProtocolsList";
import { OrganizationsList } from "../features/organizations/components/OrganizationsList";
import { EnrollmentsList } from "../features/enrollments/components/EnrollmentsList";
import { UsersList } from "../features/users/components/UsersList";
import { CheckpointsList } from "../features/checkpoints/components/CheckpointsList";

function AuthLoadingFallback() {
  return (
    <main className="page">
      <p>Validando sessao...</p>
    </main>
  );
}

function RequireAuth() {
  const { authReady, isAuthenticated } = useAuth();

  if (!authReady) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function RequireAdmin() {
  const { authReady, isAuthenticated, user } = useAuth();

  if (!authReady) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user || !isKnownUserRole(user.role)) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "admin") {
    return <Navigate to="/app/acesso-negado" replace />;
  }

  return <Outlet />;
}

function RequireMentorWorkspace() {
  const { authReady, isAuthenticated, user } = useAuth();

  if (!authReady) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user || user.role !== "mentor") {
    return <Navigate to="/app/acesso-negado" replace />;
  }

  return <Outlet />;
}

function RoleHomeRedirect() {
  const { authReady, isAuthenticated, user } = useAuth();

  if (!authReady) {
    return <AuthLoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user || !isKnownUserRole(user.role)) {
    return <Navigate to="/login" replace />;
  }

  return <Navigate to={getDefaultRouteForRole(user.role)} replace />;
}

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LoginPage /> },
      { path: "dashboard", element: <Navigate to="/app" replace /> },
      {
        path: "app",
        element: <RequireAuth />,
        children: [
          { index: true, element: <RoleHomeRedirect /> },
          { path: "acesso-negado", element: <AccessDeniedPage /> },
          {
            element: <RequireMentorWorkspace />,
            children: [

              { path: "centro-comando", element: <CommandCenterPage /> },
              { path: "radar", element: <RadarPage /> },
              { path: "matriz-renovacao", element: <MatrixPage /> }
              , { path: "measurements", element: <MeasurementsList /> }
              , { path: "protocols", element: <ProtocolsList /> }
              , { path: "organizations", element: <OrganizationsList /> }
              , { path: "enrollments", element: <EnrollmentsList /> }
              , { path: "users", element: <UsersList /> }
              , { path: "checkpoints", element: <CheckpointsList /> }
            ]
          },
          { path: "aluno", element: <StudentPage /> },
          {
            path: "admin",
            element: <RequireAdmin />,
            children: [{ index: true, element: <AdminPage /> }]
          }
        ]
      },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
];

export const appRouter = createBrowserRouter(appRoutes, {
  basename: env.routerBasePath
});
