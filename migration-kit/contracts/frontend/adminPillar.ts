export type AdminPillarDto = {
  id: string;
  protocol_id: string;
  name: string;
  code: string;
  order_index: number;
  is_active: boolean;
};

export type AdminPillarCreateDto = {
  name: string;
  code?: string;
  order_index?: number;
};
