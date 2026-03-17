import { useState } from "react";

export default function CadastroModal({ onClose, programName, onCreated }) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2000,
        background: "rgba(0,0,0,.6)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          width: 420,
          background: "#0b1320",
          border: "1px solid rgba(255,255,255,.12)",
          borderRadius: 12,
          padding: 20,
          color: "#e2e8f0",
          fontFamily: "sans-serif",
        }}
      >
        <h3 style={{ margin: "0 0 8px", fontSize: 18 }}>Novo Aluno</h3>
        <p style={{ margin: "0 0 16px", fontSize: 12, color: "#94a3b8" }}>
          Programa atual: {programName || "-"}
        </p>

        <div style={{ display: "grid", gap: 10 }}>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Nome do aluno"
            style={{
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,.15)",
              background: "#020817",
              color: "#e2e8f0",
            }}
          />
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="Email (opcional)"
            style={{
              padding: "10px 12px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,.15)",
              background: "#020817",
              color: "#e2e8f0",
            }}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 12px",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,.2)",
              background: "transparent",
              color: "#cbd5e1",
              cursor: "pointer",
            }}
          >
            Cancelar
          </button>
          <button
            onClick={() => {
              if (typeof onCreated === "function") onCreated({ fullName, email });
            }}
            style={{
              padding: "8px 12px",
              borderRadius: 8,
              border: "none",
              background: "#2563eb",
              color: "#fff",
              cursor: "pointer",
            }}
          >
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}

