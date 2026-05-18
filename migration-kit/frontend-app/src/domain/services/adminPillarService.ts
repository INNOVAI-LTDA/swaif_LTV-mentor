import type { AdminPillarCreateDto, AdminPillarDto } from "../../contracts/adminPillar";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminPillars(productId: string): Promise<AdminPillarDto[]> {
  return httpClient.get<AdminPillarDto[]>(`/admin/produtos/${encodeURIComponent(productId)}/pilares`);
}

export async function createAdminPillar(productId: string, payload: AdminPillarCreateDto): Promise<AdminPillarDto> {
  return httpClient.post<AdminPillarDto>(`/admin/produtos/${encodeURIComponent(productId)}/pilares`, payload);
}
