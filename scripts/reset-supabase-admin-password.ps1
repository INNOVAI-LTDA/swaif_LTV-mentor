param(
  [string]$Email = "admin@innovai-solutions.com.br",
  [Parameter(Mandatory = $true)]
  [string]$NewPassword,
  [string]$BackendEnvPath = "",
  [switch]$Activate
)

$ErrorActionPreference = "Stop"

function Resolve-BackendEnvPath([string]$ProvidedPath) {
  if ($ProvidedPath) {
    return $ProvidedPath
  }
  $repoRoot = Split-Path -Parent $PSScriptRoot
  return (Join-Path $repoRoot "backend/.env")
}

function Resolve-SupabaseDbUrl([string]$EnvFilePath) {
  if ($env:SUPABASE_DB_URL) {
    return $env:SUPABASE_DB_URL.Trim()
  }
  if (-not (Test-Path $EnvFilePath)) {
    return ""
  }

  $line = Get-Content $EnvFilePath | Where-Object {
    $trimmed = $_.Trim()
    $trimmed -and -not $trimmed.StartsWith("#") -and $trimmed.StartsWith("SUPABASE_DB_URL=")
  } | Select-Object -First 1

  if (-not $line) {
    return ""
  }

  $parts = $line.Split("=", 2)
  if ($parts.Count -lt 2) {
    return ""
  }
  return $parts[1].Trim()
}

$resolvedEnvPath = Resolve-BackendEnvPath -ProvidedPath $BackendEnvPath
$supabaseDbUrl = Resolve-SupabaseDbUrl -EnvFilePath $resolvedEnvPath

if (-not $supabaseDbUrl) {
  throw "SUPABASE_DB_URL nao encontrado. Defina no ambiente ou em backend/.env."
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
if (-not (Test-Path $backendDir)) {
  throw "Diretorio backend nao encontrado: $backendDir"
}

$env:SUPABASE_DB_URL = $supabaseDbUrl
$env:RESET_ADMIN_EMAIL = $Email.Trim().ToLowerInvariant()
$env:RESET_ADMIN_PASSWORD = $NewPassword
$env:RESET_ADMIN_ACTIVATE = if ($Activate) { "1" } else { "0" }

Push-Location $backendDir
try {
  @'
import os
import sys

sys.path.insert(0, os.path.abspath(".vendor"))
sys.path.insert(0, os.path.abspath("."))

import psycopg
from app.core.security import hash_password

db_url = os.environ["SUPABASE_DB_URL"].strip()
email = os.environ["RESET_ADMIN_EMAIL"].strip().lower()
new_password = os.environ["RESET_ADMIN_PASSWORD"]
activate = os.environ.get("RESET_ADMIN_ACTIVATE", "0") == "1"

connect_timeout = int(os.getenv("SUPABASE_DB_CONNECT_TIMEOUT_SECONDS", "15") or "15")
new_hash = hash_password(new_password)

with psycopg.connect(db_url, prepare_threshold=None, connect_timeout=connect_timeout) as conn:
    with conn.cursor() as cur:
        if activate:
            cur.execute(
                """
                UPDATE deva_accmed_users
                SET password_hash = %s, is_active = true
                WHERE lower(email) = %s
                RETURNING id, email, role, is_active
                """,
                (new_hash, email),
            )
        else:
            cur.execute(
                """
                UPDATE deva_accmed_users
                SET password_hash = %s
                WHERE lower(email) = %s
                RETURNING id, email, role, is_active
                """,
                (new_hash, email),
            )
        row = cur.fetchone()
    conn.commit()

if row is None:
    raise RuntimeError(f"Usuario nao encontrado: {email}")

print(f"RESET_OK id={row[0]} email={row[1]} role={row[2]} is_active={row[3]}")
'@ | py -
  if ($LASTEXITCODE -ne 0) {
    throw "Falha ao atualizar senha no Supabase (exit code: $LASTEXITCODE)."
  }
}
finally {
  Pop-Location
}

Write-Host "[RESET] Senha atualizada para $($env:RESET_ADMIN_EMAIL)." -ForegroundColor Green
if ($Activate) {
  Write-Host "[RESET] Usuario marcado como ativo (is_active=true)." -ForegroundColor Green
}
