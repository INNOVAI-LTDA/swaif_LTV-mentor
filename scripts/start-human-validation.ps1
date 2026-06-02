param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [int]$BackendStartupTimeoutSeconds = 600,
  [int]$FrontendStartupTimeoutSeconds = 60,
  [switch]$Install,
  [switch]$StrictTcpPrecheck
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backendEnvPath = Join-Path $repoRoot "backend/.env"
$runtimeScript = Join-Path $repoRoot "start-localhost.ps1"

function Resolve-SupabaseDbUrl([string]$EnvFilePath) {
  if (-not (Test-Path $EnvFilePath)) {
    if ($env:SUPABASE_DB_URL) {
      return $env:SUPABASE_DB_URL.Trim()
    }
    return ""
  }

  $line = Get-Content $EnvFilePath | Where-Object {
    $trimmed = $_.Trim()
    $trimmed -and -not $trimmed.StartsWith("#") -and $trimmed.StartsWith("SUPABASE_DB_URL=")
  } | Select-Object -First 1

  if (-not $line) {
    if ($env:SUPABASE_DB_URL) {
      return $env:SUPABASE_DB_URL.Trim()
    }
    return ""
  }

  $parts = $line.Split("=", 2)
  if ($parts.Count -lt 2) {
    if ($env:SUPABASE_DB_URL) {
      return $env:SUPABASE_DB_URL.Trim()
    }
    return ""
  }

  return $parts[1].Trim()
}

function Test-TcpEndpoint([string]$EndpointHost, [int]$Port, [int]$TimeoutMs = 8000) {
  $targets = New-Object System.Collections.Generic.List[string]
  if (-not [string]::IsNullOrWhiteSpace($EndpointHost)) {
    $targets.Add($EndpointHost)
  }

  try {
    $addresses = [System.Net.Dns]::GetHostAddresses($EndpointHost)
    foreach ($address in $addresses) {
      if ($null -ne $address) {
        $candidate = $address.ToString()
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and -not $targets.Contains($candidate)) {
          $targets.Add($candidate)
        }
      }
    }
  } catch {
    # keep best-effort behavior with original host
  }

  foreach ($target in $targets) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
      $async = $client.BeginConnect($target, $Port, $null, $null)
      if (-not $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)) {
        continue
      }
      $client.EndConnect($async)
      return $true
    } catch {
      continue
    } finally {
      try { $client.Close() } catch {}
    }
  }

  return $false
}

function Test-TcpEndpointWithNetConnection([string]$EndpointHost, [int]$Port) {
  if (-not (Get-Command Test-NetConnection -ErrorAction SilentlyContinue)) {
    return $false
  }
  try {
    $result = Test-NetConnection -ComputerName $EndpointHost -Port $Port -WarningAction SilentlyContinue
    return [bool]$result.TcpTestSucceeded
  } catch {
    return $false
  }
}

function Build-SupabasePoolerUrl([string]$DbUrl) {
  try {
    $uri = [System.Uri]$DbUrl
  } catch {
    return ""
  }

  $dbHost = ""
  if ($null -ne $uri.Host) {
    $dbHost = $uri.Host.Trim().ToLowerInvariant()
  }
  $segments = $dbHost.Split(".")
  if ($segments.Count -lt 4) {
    return ""
  }
  if ($segments[0] -ne "db" -or $segments[2] -ne "supabase" -or $segments[3] -ne "co") {
    return ""
  }

  $projectRef = $segments[1]
  if (-not $projectRef) {
    return ""
  }

  $userinfo = $uri.UserInfo
  if (-not $userinfo) {
    return ""
  }
  $parts = $userinfo.Split(":", 2)
  if ($parts.Count -lt 2) {
    return ""
  }

  $username = $parts[0]
  $password = $parts[1]
  if (-not $username -or -not $password) {
    return ""
  }

  if (-not $username.Contains(".")) {
    $username = "$username.$projectRef"
  }

  $databasePath = $uri.AbsolutePath
  if (-not $databasePath -or $databasePath -eq "/") {
    $databasePath = "/postgres"
  }

  $query = $uri.Query
  if (-not $query) {
    $query = "?sslmode=require"
  } elseif (-not ($query.ToLowerInvariant().Contains("sslmode="))) {
    $query = "$query&sslmode=require"
  }

  return "$($uri.Scheme)://$username`:$password@aws-1-us-east-1.pooler.supabase.com:6543$databasePath$query"
}

if (-not (Test-Path $runtimeScript)) {
  throw "Script base nao encontrado: $runtimeScript"
}

$supabaseDbUrl = Resolve-SupabaseDbUrl -EnvFilePath $backendEnvPath
if (-not $supabaseDbUrl) {
  throw "Defina SUPABASE_DB_URL no ambiente atual ou em backend/.env."
}

$env:APP_ENV = "local"
$env:SUPABASE_RUNTIME_REQUIRED = "true"
$env:SUPABASE_DB_URL = $supabaseDbUrl

try {
  $uri = [System.Uri]$supabaseDbUrl
} catch {
  throw "SUPABASE_DB_URL invalido: $supabaseDbUrl"
}

$port = if ($uri.Port -gt 0) { $uri.Port } else { 5432 }
$tcpReachable = Test-TcpEndpoint -EndpointHost $uri.Host -Port $port
if (-not $tcpReachable) {
  $tcpReachable = Test-TcpEndpointWithNetConnection -EndpointHost $uri.Host -Port $port
}
if (-not $tcpReachable) {
  $poolerDbUrl = Build-SupabasePoolerUrl -DbUrl $supabaseDbUrl
  if ($poolerDbUrl) {
    try {
      $poolerUri = [System.Uri]$poolerDbUrl
      $poolerPort = if ($poolerUri.Port -gt 0) { $poolerUri.Port } else { 6543 }
      Write-Host "[VALIDACAO] Tentando fallback pooler: $($poolerUri.Host):$poolerPort" -ForegroundColor Yellow
      $poolerReachable = Test-TcpEndpoint -EndpointHost $poolerUri.Host -Port $poolerPort -TimeoutMs 12000
      if (-not $poolerReachable) {
        $poolerReachable = Test-TcpEndpointWithNetConnection -EndpointHost $poolerUri.Host -Port $poolerPort
      }
      if ($poolerReachable) {
        $supabaseDbUrl = $poolerDbUrl
        $env:SUPABASE_DB_URL = $supabaseDbUrl
        $uri = $poolerUri
        $port = $poolerPort
        $tcpReachable = $true
        Write-Host "[VALIDACAO] Fallback automatico para pooler Supabase aplicado." -ForegroundColor Yellow
      }
    } catch {
      # no-op: keep original connectivity failure message below
    }
  }
}

Write-Host "[VALIDACAO] APP_ENV=$($env:APP_ENV)" -ForegroundColor Cyan
Write-Host "[VALIDACAO] SUPABASE_RUNTIME_REQUIRED=$($env:SUPABASE_RUNTIME_REQUIRED)" -ForegroundColor Cyan
Write-Host "[VALIDACAO] Backend host/porta: $BackendHost`:$BackendPort" -ForegroundColor Cyan
Write-Host "[VALIDACAO] Frontend porta: $FrontendPort" -ForegroundColor Cyan
if ($tcpReachable) {
  Write-Host "[VALIDACAO] Supabase TCP: $($uri.Host):$port (ok)" -ForegroundColor Cyan
} else {
  $message = "Sem conectividade TCP confirmada com Supabase ($($uri.Host):$port). Prosseguindo para diagnostico de runtime."
  if ($StrictTcpPrecheck) {
    throw $message
  }
  Write-Host "[VALIDACAO] $message" -ForegroundColor Yellow
}

$runtimeArgs = @{
  BackendHost                  = $BackendHost
  BackendPort                  = $BackendPort
  FrontendPort                 = $FrontendPort
  BackendStartupTimeoutSeconds = $BackendStartupTimeoutSeconds
  FrontendStartupTimeoutSeconds = $FrontendStartupTimeoutSeconds
}

if (-not $Install) {
  $runtimeArgs["NoInstall"] = $true
}

& $runtimeScript @runtimeArgs
