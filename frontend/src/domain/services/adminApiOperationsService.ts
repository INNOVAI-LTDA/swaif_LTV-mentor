import { httpClient } from "../../shared/api/httpClient";

type CatalogResponse = {
  items?: Array<{ name?: string; description?: string; method?: string; endpoint?: string }>;
};

export type AdminApiOperationItem = {
  name: string;
  description: string;
  method: string;
  endpoint: string;
};

export type AdminApiOperationExecution = {
  status: string;
  operation: string;
  method: string;
  endpoint: string;
  requestedBy: string;
  requestedAt: string;
};

export async function listAdminApiOperations(): Promise<AdminApiOperationItem[]> {
  const payload = await httpClient.get<CatalogResponse>("/admin/api-operations/catalog");
  return (payload.items ?? []).map((item) => ({
    name: String(item.name ?? ""),
    description: String(item.description ?? ""),
    method: String(item.method ?? "GET"),
    endpoint: String(item.endpoint ?? "")
  }));
}

export async function executeAdminApiOperation(endpoint: string): Promise<AdminApiOperationExecution> {
  return httpClient.post<AdminApiOperationExecution>("/admin/api-operations/execute", { endpoint });
}
