import type { AdminProductCreateDto, AdminProductDto } from "../../contracts/adminProduct";
import { httpClient } from "../../shared/api/httpClient";

export async function listAdminProducts(clientId: string): Promise<AdminProductDto[]> {
  return httpClient.get<AdminProductDto[]>(`/admin/clientes/${encodeURIComponent(clientId)}/produtos`);
}

export async function getAdminProductDetail(clientId: string, productId: string): Promise<AdminProductDto> {
  return httpClient.get<AdminProductDto>(
    `/admin/clientes/${encodeURIComponent(clientId)}/produtos/${encodeURIComponent(productId)}`
  );
}

export async function createAdminProduct(clientId: string, payload: AdminProductCreateDto): Promise<AdminProductDto> {
  return httpClient.post<AdminProductDto>(`/admin/clientes/${encodeURIComponent(clientId)}/produtos`, payload);
}
