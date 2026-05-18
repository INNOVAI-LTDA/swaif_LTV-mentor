export type LoginRequestDto = {
  email: string;
  password: string;
};

export type LoginResponseDto = {
  access_token: string;
  token_type: string;
};

export type MeResponseDto = {
  id: string;
  email: string;
  role: string;
};
