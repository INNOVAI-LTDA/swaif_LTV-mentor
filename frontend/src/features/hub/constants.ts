export type HubModuleId = "comando" | "radar" | "matriz";

export type HubModuleMeta = {
  id: HubModuleId;
  title: string;
  subtitle: string;
  description: string;
  statusLabel: string;
  accent: "teal" | "amber" | "coral";
  tags: string[];
  route: string;
  available: boolean;
};

export const HUB_MODULES: HubModuleMeta[] = [
  {
    id: "comando",
    title: "Centro de Comando",
    subtitle: "Gestão por Exceção",
    description:
      "Priorize alunos em risco, acompanhe checkpoints da jornada e execute ações de recuperação com contexto.",
    statusLabel: "Disponível agora",
    accent: "teal",
    tags: ["Risco", "D-45", "Checkpoints"],
    route: "/app/centro-comando",
    available: true
  },
  {
    id: "radar",
    title: "Radar de Transformação",
    subtitle: "Evolução por Pilar",
    description:
      "Compare baseline, estado atual e projeção para sustentar conversas de valor e renovação com o aluno.",
    statusLabel: "Disponível agora",
    accent: "amber",
    tags: ["7 eixos", "Projeção", "Insight"],
    route: "/app/radar",
    available: true
  },
  {
    id: "matriz",
    title: "Matriz de Renovação",
    subtitle: "Priorização de Oportunidades",
    description:
      "Enxergue quadrantes de progresso x engajamento para direcionar renovação e plano de resgate com foco.",
    statusLabel: "Disponível agora",
    accent: "coral",
    tags: ["Quadrantes", "LTV", "Resgate"],
    route: "/app/matriz-renovacao",
    available: true
  }
];
