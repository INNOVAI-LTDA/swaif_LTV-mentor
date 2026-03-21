import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider";
import { env } from "../../shared/config/env";
import { isKnownUserRole } from "../../shared/auth/roleRouting";

function getRoleLabel(role: string | undefined): string {
  switch (role) {
    case "admin":
      return "Admin";
    case "mentor":
      return "Mentor";
    case "aluno":
      return "Aluno";
    default:
      return "Visitante";
  }
}

export function AppLayout() {
  const location = useLocation();
  const { isAuthenticated, isPreviewSession, user, logout } = useAuth();
  const role = user?.role;
  const hasKnownRole = isKnownUserRole(role);
  const canUseInternalMentorWorkspace = role === "mentor" && env.internalMentorDemoEnabled;

  if (location.pathname === "/login") {
    return (
      <main>
        <Outlet />
      </main>
    );
  }

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <nav className="app-topbar__inner">
          <Link className="app-brand" to="/login">
            <img src={env.brandingIconUrl} alt="" aria-hidden="true" />
            <span>
              <strong>{env.clientName}</strong>
              <small>{env.appName}</small>
            </span>
          </Link>
          <Link to="/">{env.appTagline}</Link>
          <Link to="/login">Login</Link>
          {isAuthenticated && hasKnownRole && role === "admin" ? <Link to="/app/admin">Admin</Link> : null}
          {isAuthenticated && hasKnownRole && role === "aluno" ? <Link to="/app/aluno">Aluno</Link> : null}
          {isAuthenticated && canUseInternalMentorWorkspace ? (
            <>
              <Link to="/app/hub-interno">Hub interno</Link>
              <Link to="/app/centro-comando">Centro</Link>
              <Link to="/app/radar">Radar</Link>
              <Link to="/app/matriz-renovacao">Matriz</Link>
            </>
          ) : null}
          <span className="app-session-indicator">
            {isAuthenticated ? `${isPreviewSession ? "Sessao interna" : "Sessao"}: ${getRoleLabel(user?.role)}` : "Sessao: anonima"}
          </span>
          {isAuthenticated && (
            <button className="app-logout-button" type="button" onClick={logout}>
              Sair
            </button>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
