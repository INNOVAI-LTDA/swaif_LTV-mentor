import { httpClient } from "../../shared/api/httpClient";

export type DatabaseTablePage = {
  table: string;
  items: Array<Record<string, unknown>>;
  total: number;
  limit: number;
  offset: number;
};

export type AdminDatabaseViewSnapshot = {
  organizations: Array<Record<string, unknown>>;
  users: {
    admins: Array<Record<string, unknown>>;
    providers: Array<Record<string, unknown>>;
    clients: Array<Record<string, unknown>>;
  };
  products: Array<Record<string, unknown>>;
  enrollments: Array<Record<string, unknown>>;
  pillars: Array<Record<string, unknown>>;
  metrics: Array<Record<string, unknown>>;
  measurements: Array<Record<string, unknown>>;
  checkpoints: Array<Record<string, unknown>>;
  integrity: Record<string, unknown>;
};

export function getDatabaseViewSnapshot(): Promise<AdminDatabaseViewSnapshot> {
  return httpClient.get<AdminDatabaseViewSnapshot>("/admin/database-view");
}

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
