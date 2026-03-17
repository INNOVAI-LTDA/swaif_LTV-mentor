import type {
  AdminEnrollmentDto,
  AdminIndicatorLoadDto,
  AdminIndicatorLoadResultDto,
  AdminStudentCreateDto,
  AdminStudentDto,
  AdminStudentReassignDto,
  AdminStudentUnlinkDto
} from "../../contracts/adminStudent";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminStudentsByProduct(productId: string): Promise<AdminStudentDto[]> {
  return httpClient.get<AdminStudentDto[]>(`/admin/produtos/${encodeURIComponent(productId)}/alunos`);
}

export async function listAdminStudentsByMentor(mentorId: string): Promise<AdminStudentDto[]> {
  return httpClient.get<AdminStudentDto[]>(`/admin/mentores/${encodeURIComponent(mentorId)}/alunos`);
}

export async function createAdminStudent(mentorId: string, payload: AdminStudentCreateDto): Promise<AdminStudentDto> {
  return httpClient.post<AdminStudentDto>(`/admin/mentores/${encodeURIComponent(mentorId)}/alunos`, payload);
}

export async function reassignAdminStudent(studentId: string, payload: AdminStudentReassignDto): Promise<AdminStudentDto> {
  return httpClient.post<AdminStudentDto>(`/admin/alunos/${encodeURIComponent(studentId)}/reatribuir-mentor`, payload);
}

export async function unlinkAdminStudent(studentId: string, payload: AdminStudentUnlinkDto): Promise<AdminEnrollmentDto> {
  return httpClient.post<AdminEnrollmentDto>(`/admin/alunos/${encodeURIComponent(studentId)}/desvincular`, payload);
}

export async function loadAdminStudentIndicators(studentId: string, payload: AdminIndicatorLoadDto): Promise<AdminIndicatorLoadResultDto> {
  return httpClient.post<AdminIndicatorLoadResultDto>(`/admin/alunos/${encodeURIComponent(studentId)}/indicadores/carga-inicial`, payload);
}
