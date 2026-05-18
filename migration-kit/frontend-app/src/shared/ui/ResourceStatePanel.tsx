import type { ReactNode } from "react";

type ResourceStatePanelProps = {
  title: string;
  status: "idle" | "loading" | "success" | "empty" | "error";
  error?: string | null;
  onRetry?: () => void;
  children?: ReactNode;
};

export function ResourceStatePanel(props: ResourceStatePanelProps) {
  const { title, status, error, onRetry, children } = props;
  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>{title}</h3>
      <p style={{ marginTop: 0 }}>
        <strong>Status:</strong> {status}
      </p>
      {status === "error" && error && (
        <p style={{ color: "#b91c1c" }}>
          <strong>Erro:</strong> {error}
        </p>
      )}
      {onRetry && (
        <button type="button" onClick={onRetry}>
          Atualizar
        </button>
      )}
      {children}
    </div>
  );
}
