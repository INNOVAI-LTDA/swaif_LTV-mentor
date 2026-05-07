CREATE TABLE IF NOT EXISTS contacts_users_v2 (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  full_name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  organization_id TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  -- Regra única (Opção A): password_hash existe somente para papéis autenticáveis
  -- (admin/provider). Contatos client não devem carregar senha.
  password_hash TEXT NULL,
  CONSTRAINT chk_contacts_users_v2_password_hash_by_role CHECK (
    (
      role IN ('admin', 'provider')
      AND password_hash IS NOT NULL
      AND btrim(password_hash) <> ''
    )
    OR (
      role = 'client'
      AND password_hash IS NULL
    )
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_contacts_users_v2_email_lower
  ON contacts_users_v2 (LOWER(email));

CREATE INDEX IF NOT EXISTS ix_contacts_users_v2_role_password_hash
  ON contacts_users_v2 (role, password_hash);
