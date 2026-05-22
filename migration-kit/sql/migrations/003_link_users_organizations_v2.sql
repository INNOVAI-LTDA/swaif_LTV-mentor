ALTER TABLE deva_accmed_users
  ADD COLUMN IF NOT EXISTS organization_id BIGINT;

UPDATE deva_accmed_users AS u
SET organization_id = o.id
FROM deva_accmed_organizations AS o
WHERE o.slug = 'org_innovai'
  AND LOWER(u.email) LIKE '%@innovai%';

UPDATE deva_accmed_users AS u
SET organization_id = o.id
FROM deva_accmed_organizations AS o
WHERE o.slug = 'org_accmed'
  AND LOWER(u.email) NOT LIKE '%@innovai%';

CREATE INDEX IF NOT EXISTS ix_deva_accmed_users_organization_id
  ON deva_accmed_users (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_deva_accmed_users_organization_id'
  ) THEN
    ALTER TABLE deva_accmed_users
      ADD CONSTRAINT fk_deva_accmed_users_organization_id
      FOREIGN KEY (organization_id)
      REFERENCES deva_accmed_organizations (id)
      ON UPDATE RESTRICT
      ON DELETE SET NULL;
  END IF;
END $$;

-- Validacao rapida pos-migracao
SELECT
  o.slug,
  o.name,
  COUNT(u.id) AS users_count
FROM deva_accmed_organizations AS o
LEFT JOIN deva_accmed_users AS u
  ON u.organization_id = o.id
GROUP BY o.slug, o.name
ORDER BY o.slug;

SELECT COUNT(*) AS users_without_organization
FROM deva_accmed_users
WHERE organization_id IS NULL;
