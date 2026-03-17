export type AdminProductDto = {
  id: string;
  client_id: string;
  name: string;
  code: string;
  slug: string;
  status: string;
  is_active: boolean;
  description: string | null;
  delivery_model: string;
  mentor_id: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminProductCreateDto = {
  name: string;
  code: string;
  slug?: string;
  description?: string;
  delivery_model?: string;
};
