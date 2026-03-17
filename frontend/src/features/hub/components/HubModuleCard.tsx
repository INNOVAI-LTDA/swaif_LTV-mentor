import { Link } from "react-router-dom";
import type { HubModuleMeta } from "../constants";

type HubModuleCardProps = {
  module: HubModuleMeta;
  index: number;
};

export function HubModuleCard({ module, index }: HubModuleCardProps) {
  return (
    <article className={`hub-module-card hub-module-card--${module.accent}`}>
      <header className="hub-module-card__header">
        <span className="hub-module-card__index">{String(index + 1).padStart(2, "0")}</span>
        <span className="hub-module-card__status">{module.statusLabel}</span>
      </header>

      <h2 className="hub-module-card__title">{module.title}</h2>
      <p className="hub-module-card__subtitle">{module.subtitle}</p>
      <p className="hub-module-card__description">{module.description}</p>

      <div className="hub-module-card__tags">
        {module.tags.map((tag) => (
          <span key={tag} className="hub-module-card__tag">
            {tag}
          </span>
        ))}
      </div>

      <footer className="hub-module-card__footer">
        {module.available ? (
            <Link to={module.route} className="hub-module-card__action hub-module-card__action--link">
            abrir módulo
            </Link>
        ) : (
          <button type="button" className="hub-module-card__action" disabled>
            módulo em construção
          </button>
        )}
      </footer>
    </article>
  );
}
