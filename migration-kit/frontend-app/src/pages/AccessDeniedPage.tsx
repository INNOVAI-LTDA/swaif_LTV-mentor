import { Link } from "react-router-dom";
import { useAuth } from "../app/providers/AuthProvider";
import { getDefaultRouteForRole, getRoleHomeLabel, isKnownUserRole } from "../shared/auth/roleRouting";

export function AccessDeniedPage() {
  const { user } = useAuth();
  const role = user?.role;
  const destination = role && isKnownUserRole(role) ? getDefaultRouteForRole(role) : "/app";
  const destinationLabel = role && isKnownUserRole(role) ? getRoleHomeLabel(role) : "voltar ao inicio";

  return (
    <section className="page">
      <div className="card">
        <p className="eyebrow">Erro 403</p>
        <h1>Acesso negado</h1>
        <p>Seu perfil autenticado nao tem permissao para acessar esta area desta entrega.</p>
        <Link className="button-link" to={destination}>
          {destinationLabel}
        </Link>
      </div>
    </section>
  );
}
