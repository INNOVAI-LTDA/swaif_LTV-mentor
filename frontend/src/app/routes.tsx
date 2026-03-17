import { Navigate, createBrowserRouter, type RouteObject } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { LoginPage } from "../pages/LoginPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { HubPage } from "../features/hub/pages/HubPage";
import { CommandCenterPage } from "../features/command-center/pages/CommandCenterPage";
import { RadarPage } from "../features/radar/pages/RadarPage";
import { MatrixPage } from "../features/matrix/pages/MatrixPage";
import { StudentPage } from "../features/student/pages/StudentPage";
import { AdminPage } from "../features/admin/pages/AdminPage";

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/login" replace /> },
      { path: "login", element: <LoginPage /> },
      { path: "app", element: <HubPage /> },
      { path: "app/admin", element: <AdminPage /> },
      { path: "app/centro-comando", element: <CommandCenterPage /> },
      { path: "app/radar", element: <RadarPage /> },
      { path: "app/aluno", element: <StudentPage /> },
      { path: "app/matriz-renovacao", element: <MatrixPage /> },
      { path: "*", element: <NotFoundPage /> }
    ]
  }
];

export const appRouter = createBrowserRouter(appRoutes);
