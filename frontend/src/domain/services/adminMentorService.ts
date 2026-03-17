import type { AdminMentorCreateDto, AdminMentorDto } from "../../contracts/adminMentor";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminMentors(productId: string): Promise<AdminMentorDto[]> {
  return httpClient.get<AdminMentorDto[]>(`/admin/produtos/${encodeURIComponent(productId)}/mentores`);
}

export async function createAdminMentor(productId: string, payload: AdminMentorCreateDto): Promise<AdminMentorDto> {
  return httpClient.post<AdminMentorDto>(`/admin/produtos/${encodeURIComponent(productId)}/mentores`, payload);
}
