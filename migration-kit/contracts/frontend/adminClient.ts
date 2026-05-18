export type AdminClientDto = {
  id: string;
  name: string;
  brand_name: string;
  cnpj: string;
  slug: string;
  status: string;
  is_active: boolean;
  timezone: string;
  currency: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminClientCreateDto = {
  name: string;
  cnpj: string;
  slug?: string;
  brand_name?: string;
  timezone?: string;
  currency?: string;
  notes?: string;
};
