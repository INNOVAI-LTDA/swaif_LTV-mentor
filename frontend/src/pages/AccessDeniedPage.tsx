import { Link } from "react-router-dom";
import { useAuth } from "../app/providers/AuthProvider";
import { getDefaultRouteForRole, getRoleHomeLabel, isKnownUserRole } from "../shared/auth/roleRouting";
import { env } from "../shared/config/env";

export function AccessDeniedPage() {
  const { user, logout } = useAuth();
  const role = user?.role;
  const isMentorWithoutPublishedWorkspace = role === "mentor" && !env.internalMentorDemoEnabled;
  const destination = role && isKnownUserRole(role) ? getDefaultRouteForRole(role) : "/app";
  const destinationLabel = role && isKnownUserRole(role) ? getRoleHomeLabel(role) : "voltar ao inicio";

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Erro 403</p>
        <h1>Acesso negado</h1>
        <p>
          {isMentorWithoutPublishedWorkspace
            ? "Seu perfil autenticado foi reconhecido, mas a superficie de mentor permanece restrita ao modo interno local nesta entrega."
            : "Seu perfil autenticado nao tem permissao para acessar esta area desta entrega."}
        </p>
        {isMentorWithoutPublishedWorkspace ? (
          <button className="button-link" type="button" onClick={logout}>
            {destinationLabel}
          </button>
        ) : (
          <Link className="button-link" to={destination}>
            {destinationLabel}
          </Link>
        )}
      </div>
    </section>
  );
}
