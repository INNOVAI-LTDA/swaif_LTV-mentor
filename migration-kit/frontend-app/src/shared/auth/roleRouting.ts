export type KnownUserRole = "admin" | "mentor" | "aluno";

export function isKnownUserRole(role: string | null | undefined): role is KnownUserRole {
  return role === "admin" || role === "mentor" || role === "aluno";
}

export function getDefaultRouteForRole(role: KnownUserRole): string {
  switch (role) {
    case "admin":
      return "/app/admin";
    case "mentor":
      return "/app/matriz-renovacao";
    case "aluno":
      return "/app/aluno";
  }
}

export function getRoleHomeLabel(role: KnownUserRole): string {
  switch (role) {
    case "admin":
      return "Ir para a area administrativa";
    case "mentor":
      return "Ir para a matriz de renovacao";
    case "aluno":
      return "Ir para a area do aluno";
  }
}
