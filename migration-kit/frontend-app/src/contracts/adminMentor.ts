export type AdminMentorDto = {
  id: string;
  full_name: string;
  email: string;
  cpf: string | null;
  phone: string | null;
  bio: string | null;
  notes: string | null;
  status: string | null;
  is_active: boolean;
  organization_id: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type AdminMentorCreateDto = {
  full_name: string;
  cpf: string;
  email: string;
  phone?: string;
  bio?: string;
  notes?: string;
};
