import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="page">
      <h1>Pagina nao encontrada</h1>
      <p>A rota solicitada nao existe.</p>
      <Link to="/">Voltar para inicio</Link>
    </section>
  );
}
