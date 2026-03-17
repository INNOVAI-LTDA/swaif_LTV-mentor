import type { AdminClientCreateDto, AdminClientDto } from "../../contracts/adminClient";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminClients(): Promise<AdminClientDto[]> {
  return httpClient.get<AdminClientDto[]>("/admin/clientes");
}

export async function getAdminClientDetail(clientId: string): Promise<AdminClientDto> {
  return httpClient.get<AdminClientDto>(`/admin/clientes/${encodeURIComponent(clientId)}`);
}

export async function createAdminClient(payload: AdminClientCreateDto): Promise<AdminClientDto> {
  return httpClient.post<AdminClientDto>("/admin/clientes", payload);
}
