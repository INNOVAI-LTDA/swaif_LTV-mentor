import type { AdminMetricCreateDto, AdminMetricDto } from "../../contracts/adminMetric";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminMetrics(pillarId: string): Promise<AdminMetricDto[]> {
  return httpClient.get<AdminMetricDto[]>(`/admin/pilares/${encodeURIComponent(pillarId)}/metricas`);
}

export async function listAdminMetricsByProduct(productId: string): Promise<AdminMetricDto[]> {
  return httpClient.get<AdminMetricDto[]>(`/admin/produtos/${encodeURIComponent(productId)}/metricas`);
}

export async function createAdminMetric(pillarId: string, payload: AdminMetricCreateDto): Promise<AdminMetricDto> {
  return httpClient.post<AdminMetricDto>(`/admin/pilares/${encodeURIComponent(pillarId)}/metricas`, payload);
}
