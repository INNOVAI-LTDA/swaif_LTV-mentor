import { useEffect, useState } from "react";

// TODO: Replace with actual session/context logic to get current mentor/org
function getCurrentMentorOrganizationId(): string | null {
  // Example: return "org_2";
  // In production, get from auth/session context
  return window.localStorage.getItem("mentor_org_id") || null;
}

export type Protocol = {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  metadata: Record<string, unknown>;
  is_active: boolean;
};

export function useMentorProducts() {
  const [products, setProducts] = useState<Protocol[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const orgId = getCurrentMentorOrganizationId();

  useEffect(() => {
    if (!orgId) {
      setProducts([]);
      setLoading(false);
      setError("Organização do mentor não encontrada.");
      return;
    }
    setLoading(true);
    fetch(`/api/protocols?organization_id=${orgId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Erro ao buscar produtos");
        return res.json();
      })
      .then((data) => {
        setProducts(Array.isArray(data.items) ? data.items : []);
        setError(null);
      })
      .catch((err) => {
        setError(err.message || "Erro desconhecido");
        setProducts([]);
      })
      .finally(() => setLoading(false));
  }, [orgId]);

  return { products, loading, error };
}
