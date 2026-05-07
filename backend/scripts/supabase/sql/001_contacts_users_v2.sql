CREATE TABLE IF NOT EXISTS contacts_users_v2 (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  role TEXT NOT NULL,
  full_name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  organization_id TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  password_hash TEXT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_contacts_users_v2_email_lower
  ON contacts_users_v2 (LOWER(email));
