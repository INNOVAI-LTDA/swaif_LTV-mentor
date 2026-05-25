param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [int]$PortSearchAttempts = 20,
  [switch]$NoInstall
)

$ErrorActionPreference = "Stop"
$BackendJobName = "deva-backend"
$FrontendJobName = "deva-frontend"

function Ensure-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Comando '$Name' nao encontrado. Instale-o e tente novamente."
  }
}

function Test-PortBindable([string]$BindHost, [int]$Port) {
  $listener = $null
  try {
    $ip = [System.Net.IPAddress]::Parse($BindHost)
    $listener = [System.Net.Sockets.TcpListener]::new($ip, $Port)
    $listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    if ($null -ne $listener) {
      try { $listener.Stop() } catch {}
    }
  }
}

function Resolve-Port([string]$BindHost, [int]$PreferredPort, [string]$Label, [int]$Attempts) {
  if (Test-PortBindable -BindHost $BindHost -Port $PreferredPort) {
    return $PreferredPort
  }

  Write-Host "[DEVA] Porta $PreferredPort ($Label) indisponivel para bind em $BindHost. Buscando alternativa..." -ForegroundColor Yellow
  for ($offset = 1; $offset -le $Attempts; $offset++) {
    $candidate = $PreferredPort + $offset
    if ($candidate -gt 65535) { break }
    if (Test-PortBindable -BindHost $BindHost -Port $candidate) {
      Write-Host "[DEVA] Porta alternativa selecionada para ${Label}: $candidate" -ForegroundColor Yellow
      return $candidate
    }
  }

  throw "Nao foi possivel encontrar porta disponivel para $Label a partir de $PreferredPort."
}

function Get-EnvFileValue([string]$EnvFilePath, [string]$Key) {
  if (-not (Test-Path $EnvFilePath)) {
    return ""
  }
  $line = Get-Content $EnvFilePath | Where-Object {
    $trimmed = $_.Trim()
    $trimmed -and -not $trimmed.StartsWith("#") -and $trimmed.StartsWith("$Key=")
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

function Stop-RuntimeJobs() {
  foreach ($jobName in @($BackendJobName, $FrontendJobName)) {
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($null -ne $job) {
      if ($job.State -eq "Running") {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
      }
      Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
  }
}

function Start-BackendJob(
  [string]$Dir,
  [string]$BackendBindHost,
  [int]$Port,
  [string]$SupabaseDbUrl
) {
  Start-Job -Name $BackendJobName -ScriptBlock {
    param($WorkingDir, $BackendBindHost, $BackendBindPort, $SupabaseUrl)
    Set-Location $WorkingDir
    if ($SupabaseUrl) {
      $env:SUPABASE_DB_URL = $SupabaseUrl
    }
    py -m uvicorn app.main:app --host $BackendBindHost --port $BackendBindPort --reload
  } -ArgumentList $Dir, $BackendBindHost, $Port, $SupabaseDbUrl | Out-Null
}

function Start-FrontendJob(
  [string]$Dir,
  [string]$FrontendBindHost,
  [int]$Port,
  [string]$ApiBaseUrl,
  [string]$ViteCliPath
) {
  Start-Job -Name $FrontendJobName -ScriptBlock {
    param($WorkingDir, $FrontendBindHost, $FrontendBindPort, $BackendApiBaseUrl, $ViteCli)
    Set-Location $WorkingDir
    $env:VITE_DEPLOY_TARGET = "local"
    $env:VITE_API_BASE_URL = $BackendApiBaseUrl
    node $ViteCli --host $FrontendBindHost --port $FrontendBindPort
  } -ArgumentList $Dir, $FrontendBindHost, $Port, $ApiBaseUrl, $ViteCliPath | Out-Null
}

function Show-RuntimeStatus() {
  $backendJob = Get-Job -Name $BackendJobName -ErrorAction SilentlyContinue
  $frontendJob = Get-Job -Name $FrontendJobName -ErrorAction SilentlyContinue
  Write-Host "[DEVA] Status backend job: $($backendJob.State)" -ForegroundColor Cyan
  Write-Host "[DEVA] Status frontend job: $($frontendJob.State)" -ForegroundColor Cyan
}

function Show-RuntimeLogs([int]$Tail = 25) {
  foreach ($jobName in @($BackendJobName, $FrontendJobName)) {
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($null -eq $job) {
      continue
    }
    Write-Host "[DEVA] Logs: $jobName" -ForegroundColor DarkGray
    $output = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
    if ($null -eq $output -or $output.Count -eq 0) {
      Write-Host "[DEVA] (sem output ainda)" -ForegroundColor DarkGray
      continue
    }
    $output | Select-Object -Last $Tail | ForEach-Object { Write-Host $_ }
  }
}

function Start-Runtime(
  [string]$RepoPath,
  [string]$BackendPath,
  [string]$FrontendPath,
  [string]$RuntimeHost,
  [int]$RequestedBackendPort,
  [int]$RequestedFrontendPort,
  [int]$Attempts
) {
  $effectiveBackendPort = Resolve-Port -BindHost $RuntimeHost -PreferredPort $RequestedBackendPort -Label "backend" -Attempts $Attempts
  $effectiveFrontendPort = Resolve-Port -BindHost "127.0.0.1" -PreferredPort $RequestedFrontendPort -Label "frontend" -Attempts $Attempts

  Write-Host "[DEVA] Backend: http://$RuntimeHost`:$effectiveBackendPort" -ForegroundColor Cyan
  Write-Host "[DEVA] Frontend: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Cyan

  $backendEnvFile = Join-Path $BackendPath ".env"
  $supabaseDbUrl = Get-EnvFileValue -EnvFilePath $backendEnvFile -Key "SUPABASE_DB_URL"
  if ($supabaseDbUrl) {
    Write-Host "[DEVA] SUPABASE_DB_URL carregado de backend/.env para o backend local." -ForegroundColor DarkGray
  }

  $viteCli = Join-Path $FrontendPath "node_modules/vite/bin/vite.js"
  $apiBaseUrl = "http://$RuntimeHost`:$effectiveBackendPort"

  Stop-RuntimeJobs
  Start-BackendJob -Dir $BackendPath -BackendBindHost $RuntimeHost -Port $effectiveBackendPort -SupabaseDbUrl $supabaseDbUrl
  Start-FrontendJob -Dir $FrontendPath -FrontendBindHost "127.0.0.1" -Port $effectiveFrontendPort -ApiBaseUrl $apiBaseUrl -ViteCliPath $viteCli

  Write-Host "[DEVA] Execucao silenciosa ativa no terminal atual (sem abrir novas janelas)." -ForegroundColor Green
  Write-Host "[DEVA] Abra: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Green
  if ($effectiveBackendPort -ne $RequestedBackendPort) {
    Write-Host "[DEVA] Aviso: backend iniciou em porta alternativa ($effectiveBackendPort) para evitar erro de permissao/uso da porta $RequestedBackendPort." -ForegroundColor Yellow
  }
  if ($effectiveFrontendPort -ne $RequestedFrontendPort) {
    Write-Host "[DEVA] Aviso: frontend iniciou em porta alternativa ($effectiveFrontendPort) por indisponibilidade da porta $RequestedFrontendPort." -ForegroundColor Yellow
  }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $repoRoot "frontend"
$backendDir = Join-Path $repoRoot "backend"

if (-not (Test-Path $frontendDir)) { throw "Pasta frontend nao encontrada em $frontendDir" }
if (-not (Test-Path $backendDir)) { throw "Pasta backend nao encontrada em $backendDir" }

Ensure-Command "npm"
Ensure-Command "py"
Ensure-Command "node"

Write-Host "[DEVA] Repo: $repoRoot" -ForegroundColor Cyan

if (-not $NoInstall) {
  Write-Host "[DEVA] Instalando dependencias do frontend (npm install)..." -ForegroundColor Yellow
  Push-Location $frontendDir
  npm install
  Pop-Location

  Write-Host "[DEVA] Instalando dependencias do backend (pip install -r requirements.txt)..." -ForegroundColor Yellow
  Push-Location $backendDir
  py -m pip install -r requirements.txt
  Pop-Location
}

Start-Runtime -RepoPath $repoRoot -BackendPath $backendDir -FrontendPath $frontendDir -RuntimeHost $BackendHost -RequestedBackendPort $BackendPort -RequestedFrontendPort $FrontendPort -Attempts $PortSearchAttempts

Write-Host "[DEVA] Login admin local (documentado): admin@swaif.local / admin123" -ForegroundColor DarkGray
Write-Host "[DEVA] Comandos: [R] reiniciar | [Q] encerrar | [S] status | [L] logs" -ForegroundColor DarkGray

while ($true) {
  $action = (Read-Host "[DEVA] Escolha (R/Q/S/L)").Trim().ToUpperInvariant()
  switch ($action) {
    "R" {
      Write-Host "[DEVA] Reiniciando runtime..." -ForegroundColor Yellow
      Start-Runtime -RepoPath $repoRoot -BackendPath $backendDir -FrontendPath $frontendDir -RuntimeHost $BackendHost -RequestedBackendPort $BackendPort -RequestedFrontendPort $FrontendPort -Attempts $PortSearchAttempts
    }
    "S" {
      Show-RuntimeStatus
    }
    "L" {
      Show-RuntimeLogs
    }
    "Q" {
      Write-Host "[DEVA] Encerrando runtime..." -ForegroundColor Yellow
      Stop-RuntimeJobs
      break
    }
    default {
      Write-Host "[DEVA] Comando invalido. Use R, Q, S ou L." -ForegroundColor Yellow
    }
  }
}
