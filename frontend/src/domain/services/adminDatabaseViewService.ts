import { httpClient } from "../../shared/api/httpClient";

export type DatabaseTablePage = {
  table: string;
  items: Array<Record<string, unknown>>;
  total: number;
  limit: number;
  offset: number;
};

export async function listDatabaseTables(): Promise<string[]> {
  const response = await httpClient.get<{ tables: string[] }>("/admin/database-view/tables");
  return response.tables;
}

export function listDatabaseRecords(table: string, offset: number): Promise<DatabaseTablePage> {
  return httpClient.get<DatabaseTablePage>(`/admin/database-view/tables/${table}/records?limit=10&offset=${offset}`);
}

export async function updateDatabaseRecord(table: string, recordId: string, changes: Record<string, unknown>): Promise<Record<string, unknown>> {
  const response = await httpClient.patch<{ item: Record<string, unknown> }>(`/admin/database-view/tables/${table}/records/${recordId}`, { changes });
  return response.item;
}
