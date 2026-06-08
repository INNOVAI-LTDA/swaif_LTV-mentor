param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [int]$PortSearchAttempts = 20,
  [int]$BackendStartupTimeoutSeconds = 180,
  [int]$FrontendStartupTimeoutSeconds = 60,
  [int]$ResponseSlaMs = 1000,
  [string]$AdminEmail = "admin@innovai-solutions.com.br",
  [string]$AdminPassword = "admin123",
  [bool]$EnforceResponseSla = $true,
  [switch]$NoInstall
)

$ErrorActionPreference = "Stop"
$BackendJobName = "deva-backend"
$FrontendJobName = "deva-frontend"
$RuntimeLogDir = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) ".logs/runtime"
$BackendLogFile = Join-Path $RuntimeLogDir "backend.log"
$FrontendLogFile = Join-Path $RuntimeLogDir "frontend.log"
$script:EffectiveBackendPort = $BackendPort
$script:EffectiveFrontendPort = $FrontendPort

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

function Ensure-RuntimeLogDir() {
  if (-not (Test-Path $RuntimeLogDir)) {
    New-Item -ItemType Directory -Path $RuntimeLogDir -Force | Out-Null
  }
}

function Reset-RuntimeLogFiles() {
  Ensure-RuntimeLogDir
  foreach ($path in @($BackendLogFile, $FrontendLogFile)) {
    if (-not (Test-Path $path)) {
      Set-Content -Path $path -Value "" -Encoding utf8
      continue
    }

    $cleared = $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
      try {
        Set-Content -Path $path -Value "" -Encoding utf8 -Force -ErrorAction Stop
        $cleared = $true
        break
      } catch {
        Start-Sleep -Milliseconds 250
      }
    }
    if (-not $cleared) {
      Write-Host "[DEVA] Aviso: nao foi possivel limpar log em uso ($path). Mantendo arquivo atual para append." -ForegroundColor Yellow
    }
  }
}

function Get-JobOutputText([string]$JobName) {
  $job = Get-Job -Name $JobName -ErrorAction SilentlyContinue
  if ($null -eq $job) {
    return ""
  }
  $output = Receive-Job -Job $job -Keep -ErrorAction SilentlyContinue
  if ($null -eq $output -or $output.Count -eq 0) {
    return ""
  }
  return ($output | ForEach-Object { "$_" }) -join "`n"
}

function Stop-RuntimeJobs() {
  foreach ($jobName in @($BackendJobName, $FrontendJobName)) {
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($null -ne $job) {
      if ($job.State -eq "Running") {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Wait-Job -Job $job -Timeout 5 -ErrorAction SilentlyContinue | Out-Null
      }
      Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
  }
}

function Start-BackendJob(
  [string]$Dir,
  [string]$BackendBindHost,
  [int]$Port,
  [string]$SupabaseDbUrl,
  [string]$LogFile
) {
  Start-Job -Name $BackendJobName -ScriptBlock {
    param($WorkingDir, $BackendBindHost, $BackendBindPort, $SupabaseUrl, $BackendRuntimeLogFile)
    $ErrorActionPreference = "Continue"
    Set-Location $WorkingDir
    $env:PYTHONPATH = ".vendor"
    $env:PYTHONUNBUFFERED = "1"
    if ($SupabaseUrl) {
      $env:SUPABASE_DB_URL = $SupabaseUrl
    }
    Add-Content -Path $BackendRuntimeLogFile -Encoding utf8 -Value ("[DEVA] backend start: host={0} port={1} cwd={2}" -f $BackendBindHost, $BackendBindPort, $WorkingDir)
    $exitCode = 1
    try {
      & py -m uvicorn app.main:app --host $BackendBindHost --port $BackendBindPort --log-level info 2>&1 |
        ForEach-Object { Add-Content -Path $BackendRuntimeLogFile -Encoding utf8 -Value "$_" }
      if ($null -ne $LASTEXITCODE) {
        $exitCode = [int]$LASTEXITCODE
      } else {
        $exitCode = 0
      }
    } catch {
      $message = $_ | Out-String
      Add-Content -Path $BackendRuntimeLogFile -Encoding utf8 -Value "[DEVA] backend launcher exception:"
      Add-Content -Path $BackendRuntimeLogFile -Encoding utf8 -Value $message
      $exitCode = 1
    }
    Add-Content -Path $BackendRuntimeLogFile -Encoding utf8 -Value ("[DEVA] backend process exit code: {0}" -f $exitCode)
  } -ArgumentList $Dir, $BackendBindHost, $Port, $SupabaseDbUrl, $LogFile | Out-Null
}

function Start-FrontendJob(
  [string]$Dir,
  [string]$FrontendBindHost,
  [int]$Port,
  [string]$ApiBaseUrl,
  [string]$ViteCliPath,
  [string]$LogFile
) {
  Start-Job -Name $FrontendJobName -ScriptBlock {
    param($WorkingDir, $FrontendBindHost, $FrontendBindPort, $BackendApiBaseUrl, $ViteCli, $FrontendRuntimeLogFile)
    Set-Location $WorkingDir
    $env:VITE_DEPLOY_TARGET = "local"
    $env:VITE_API_BASE_URL = $BackendApiBaseUrl
    Add-Content -Path $FrontendRuntimeLogFile -Encoding utf8 -Value ("[DEVA] frontend start: host={0} port={1} cwd={2}" -f $FrontendBindHost, $FrontendBindPort, $WorkingDir)
    $exitCode = 1
    try {
      & node $ViteCli --host $FrontendBindHost --port $FrontendBindPort 2>&1 |
        ForEach-Object { Add-Content -Path $FrontendRuntimeLogFile -Encoding utf8 -Value "$_" }
      if ($null -ne $LASTEXITCODE) {
        $exitCode = [int]$LASTEXITCODE
      } else {
        $exitCode = 0
      }
    } catch {
      $message = $_ | Out-String
      Add-Content -Path $FrontendRuntimeLogFile -Encoding utf8 -Value "[DEVA] frontend launcher exception:"
      Add-Content -Path $FrontendRuntimeLogFile -Encoding utf8 -Value $message
      $exitCode = 1
    }
    Add-Content -Path $FrontendRuntimeLogFile -Encoding utf8 -Value ("[DEVA] frontend process exit code: {0}" -f $exitCode)
  } -ArgumentList $Dir, $FrontendBindHost, $Port, $ApiBaseUrl, $ViteCliPath, $LogFile | Out-Null
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
      $fallbackPath = if ($jobName -eq $BackendJobName) { $BackendLogFile } else { $FrontendLogFile }
      if (Test-Path $fallbackPath) {
        Write-Host "[DEVA] logs arquivo ($fallbackPath):" -ForegroundColor DarkGray
        Get-Content $fallbackPath -Tail $Tail | ForEach-Object { Write-Host $_ }
      }
      continue
    }
    $output | Select-Object -Last $Tail | ForEach-Object { Write-Host $_ }
  }
}

function Test-HttpReachable([string]$Url) {
  try {
    $null = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
    return $true
  } catch {
    if ($_.Exception.Response -ne $null) {
      return $true
    }
    return $false
  }
}

function Wait-HttpReachable(
  [string]$Url,
  [string]$Label,
  [int]$TimeoutSeconds = 60
) {
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if ($Label -eq "Backend") {
      $backendJob = Get-Job -Name $BackendJobName -ErrorAction SilentlyContinue
      if ($null -eq $backendJob -or $backendJob.State -eq "Failed" -or $backendJob.State -eq "Stopped" -or $backendJob.State -eq "Completed") {
        return $false
      }
    }
    if (Test-HttpReachable -Url $Url) {
      Write-Host "[DEVA] $Label pronto em $Url" -ForegroundColor Green
      return $true
    }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Measure-ApiGet(
  [string]$Name,
  [string]$Uri,
  [hashtable]$Headers,
  [int]$SlaMs
) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $response = Invoke-RestMethod -Method Get -Uri $Uri -Headers $Headers -TimeoutSec 30
  $sw.Stop()
  $elapsed = [int]$sw.ElapsedMilliseconds
  $count = 0
  if ($response -is [System.Array]) {
    $count = $response.Count
  } elseif ($response -is [hashtable] -and $response.ContainsKey("items") -and $response.items -is [System.Array]) {
    $count = $response.items.Count
  } elseif ($response -is [pscustomobject] -and $null -ne $response.PSObject.Properties["items"] -and $response.items -is [System.Array]) {
    $count = $response.items.Count
  } elseif ($null -ne $response) {
    $count = 1
  }

  if ($elapsed -gt $SlaMs) {
    throw "[SLA] endpoint '$Name' excedeu o limite: ${elapsed}ms > ${SlaMs}ms (uri=$Uri)"
  }

  Write-Host ("[SLA] {0}: {1}ms (ok <= {2}ms) count={3}" -f $Name, $elapsed, $SlaMs, $count) -ForegroundColor Green
  return $response
}

function Convert-ToApiList([object]$Response) {
  if ($Response -is [System.Array]) {
    return @($Response)
  }
  if ($Response -is [hashtable]) {
    if ($Response.ContainsKey("items") -and $Response.items -is [System.Array]) {
      return @($Response.items)
    }
    if ($Response.ContainsKey("data") -and $Response.data -is [System.Array]) {
      return @($Response.data)
    }
    if ($Response.ContainsKey("id")) {
      return @($Response)
    }
  }
  if ($Response -is [pscustomobject]) {
    if ($null -ne $Response.PSObject.Properties["items"] -and $Response.items -is [System.Array]) {
      return @($Response.items)
    }
    if ($null -ne $Response.PSObject.Properties["data"] -and $Response.data -is [System.Array]) {
      return @($Response.data)
    }
    if ($null -ne $Response.PSObject.Properties["id"]) {
      return @($Response)
    }
  }
  return @()
}

function Invoke-ResponseSlaAcceptance(
  [string]$RuntimeHost,
  [int]$RuntimeBackendPort,
  [int]$SlaMs,
  [string]$Email,
  [string]$Password
) {
  $baseUrl = "http://$RuntimeHost`:$RuntimeBackendPort"
  Write-Host "[SLA] Validando criterio de aceite (<= ${SlaMs}ms por endpoint)..." -ForegroundColor Cyan

  $health = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing -TimeoutSec 10
  if ($health.StatusCode -ne 200) {
    throw "[SLA] backend indisponivel para validacao de desempenho: $baseUrl/health"
  }

  $loginPayload = @{ email = $Email; password = $Password } | ConvertTo-Json
  $login = Invoke-RestMethod -Method Post -Uri "$baseUrl/auth/login" -ContentType "application/json" -Body $loginPayload -TimeoutSec 30
  $token = $login.access_token
  if (-not $token) {
    throw "[SLA] falha ao obter token de acesso para validacao de desempenho."
  }

  $headers = @{ Authorization = "Bearer $token" }
  $clientsResponse = Measure-ApiGet -Name "admin_clientes" -Uri "$baseUrl/admin/clientes" -Headers $headers -SlaMs $SlaMs
  $clients = Convert-ToApiList -Response $clientsResponse
  if ($clients.Count -eq 0) {
    throw "[SLA] sem clientes para validar cadeia de dropdowns."
  }

  $clientId = $clients[0].id
  $productsResponse = Measure-ApiGet -Name "admin_produtos_por_cliente" -Uri ("$baseUrl/admin/clientes/{0}/produtos" -f $clientId) -Headers $headers -SlaMs $SlaMs
  $products = Convert-ToApiList -Response $productsResponse
  if ($products.Count -eq 0) {
    throw "[SLA] sem produtos para validar cadeia de dropdowns (clientId=$clientId)."
  }

  $productId = $products[0].id
  $mentorsResponse = Measure-ApiGet -Name "admin_mentores_por_produto" -Uri ("$baseUrl/admin/produtos/{0}/mentores" -f $productId) -Headers $headers -SlaMs $SlaMs
  $mentors = Convert-ToApiList -Response $mentorsResponse
  if ($mentors.Count -eq 0) {
    throw "[SLA] sem mentores para validar cadeia de dropdowns (productId=$productId)."
  }

  $mentorId = $mentors[0].id
  $null = Measure-ApiGet -Name "admin_alunos_por_mentor" -Uri ("$baseUrl/admin/mentores/{0}/alunos" -f $mentorId) -Headers $headers -SlaMs $SlaMs
  Write-Host "[SLA] Criterio de aceite atendido: todos endpoints <= ${SlaMs}ms." -ForegroundColor Green
}

function Start-Runtime(
  [string]$RepoPath,
  [string]$BackendPath,
  [string]$FrontendPath,
  [string]$RuntimeHost,
  [int]$RequestedBackendPort,
  [int]$RequestedFrontendPort,
  [int]$Attempts,
  [int]$BackendTimeoutSeconds,
  [int]$FrontendTimeoutSeconds
) {
  $effectiveBackendPort = Resolve-Port -BindHost $RuntimeHost -PreferredPort $RequestedBackendPort -Label "backend" -Attempts $Attempts
  $effectiveFrontendPort = Resolve-Port -BindHost "127.0.0.1" -PreferredPort $RequestedFrontendPort -Label "frontend" -Attempts $Attempts
  $script:EffectiveBackendPort = $effectiveBackendPort
  $script:EffectiveFrontendPort = $effectiveFrontendPort
  $script:BackendLogFile = Join-Path $RuntimeLogDir ("backend-{0}.log" -f $effectiveBackendPort)
  $script:FrontendLogFile = Join-Path $RuntimeLogDir ("frontend-{0}.log" -f $effectiveFrontendPort)

  Write-Host "[DEVA] Backend: http://$RuntimeHost`:$effectiveBackendPort" -ForegroundColor Cyan
  Write-Host "[DEVA] Frontend: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Cyan

  $backendEnvFile = Join-Path $BackendPath ".env"
  $supabaseDbUrl = ""
  if ($null -ne $env:SUPABASE_DB_URL) {
    $supabaseDbUrl = $env:SUPABASE_DB_URL.Trim()
  }
  if (-not $supabaseDbUrl) {
    $supabaseDbUrl = Get-EnvFileValue -EnvFilePath $backendEnvFile -Key "SUPABASE_DB_URL"
  }
  $secondarySupabaseDbUrl = Get-EnvFileValue -EnvFilePath $backendEnvFile -Key "TEST_POSTGRES_DB_URL"
  if ($supabaseDbUrl) {
    Write-Host "[DEVA] SUPABASE_DB_URL carregado para o backend local." -ForegroundColor DarkGray
  }

  $viteCli = Join-Path $FrontendPath "node_modules/vite/bin/vite.js"
  $apiBaseUrl = "http://$RuntimeHost`:$effectiveBackendPort"

  Stop-RuntimeJobs
  Reset-RuntimeLogFiles
  Start-BackendJob -Dir $BackendPath -BackendBindHost $RuntimeHost -Port $effectiveBackendPort -SupabaseDbUrl $supabaseDbUrl -LogFile $BackendLogFile
  Start-FrontendJob -Dir $FrontendPath -FrontendBindHost "127.0.0.1" -Port $effectiveFrontendPort -ApiBaseUrl $apiBaseUrl -ViteCliPath $viteCli -LogFile $FrontendLogFile

  $backendReady = Wait-HttpReachable -Url "$apiBaseUrl/openapi.json" -Label "Backend" -TimeoutSeconds $BackendTimeoutSeconds
  $frontendReady = Wait-HttpReachable -Url "http://127.0.0.1:$effectiveFrontendPort" -Label "Frontend" -TimeoutSeconds $FrontendTimeoutSeconds

  if (-not $backendReady -or -not $frontendReady) {
    $backendLogs = Get-JobOutputText -JobName $BackendJobName
    $canRetryWithSecondaryDb =
      (-not $backendReady) -and
      ($secondarySupabaseDbUrl) -and
      ($secondarySupabaseDbUrl -ne $supabaseDbUrl) -and
      ($backendLogs -match "password authentication failed")

    if ($canRetryWithSecondaryDb) {
      Write-Host "[DEVA] Falha de autenticacao no banco detectada. Tentando fallback com TEST_POSTGRES_DB_URL..." -ForegroundColor Yellow
      Stop-RuntimeJobs
      Reset-RuntimeLogFiles
      Start-BackendJob -Dir $BackendPath -BackendBindHost $RuntimeHost -Port $effectiveBackendPort -SupabaseDbUrl $secondarySupabaseDbUrl -LogFile $BackendLogFile
      Start-FrontendJob -Dir $FrontendPath -FrontendBindHost "127.0.0.1" -Port $effectiveFrontendPort -ApiBaseUrl $apiBaseUrl -ViteCliPath $viteCli -LogFile $FrontendLogFile
      $backendReady = Wait-HttpReachable -Url "$apiBaseUrl/openapi.json" -Label "Backend" -TimeoutSeconds $BackendTimeoutSeconds
      $frontendReady = Wait-HttpReachable -Url "http://127.0.0.1:$effectiveFrontendPort" -Label "Frontend" -TimeoutSeconds $FrontendTimeoutSeconds
    }
  }

  if (-not $backendReady -or -not $frontendReady) {
    $backendLogs = Get-JobOutputText -JobName $BackendJobName
    if ((-not $backendReady) -and $backendLogs -match "Waiting for application startup") {
      Write-Host "[DEVA] Backend ainda em startup (FastAPI lifespan). Isso costuma indicar sync inicial com banco ainda em andamento." -ForegroundColor Yellow
      Write-Host "[DEVA] Considere aumentar -BackendStartupTimeoutSeconds ou revisar conectividade/latencia com Supabase." -ForegroundColor Yellow
    }
    Write-Host "[DEVA] Falha ao iniciar runtime. Status/logs atuais:" -ForegroundColor Red
    Show-RuntimeStatus
    Show-RuntimeLogs -Tail 60
    throw "Runtime nao respondeu dentro do timeout. Revise logs acima."
  }

  Write-Host "[DEVA] Execucao silenciosa ativa no terminal atual (sem abrir novas janelas)." -ForegroundColor Green
  Write-Host "[DEVA] Abra: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Green
  Write-Host "[DEVA] API base usada pelo frontend: $apiBaseUrl" -ForegroundColor DarkGray
  Write-Host "[DEVA] Arquivos de log: $BackendLogFile | $FrontendLogFile" -ForegroundColor DarkGray
  if ($effectiveBackendPort -ne $RequestedBackendPort) {
    Write-Host "[DEVA] Aviso: backend iniciou em porta alternativa ($effectiveBackendPort) para evitar erro de permissao/uso da porta $RequestedBackendPort." -ForegroundColor Yellow
  }
  if ($effectiveFrontendPort -ne $RequestedFrontendPort) {
    Write-Host "[DEVA] Aviso: frontend iniciou em porta alternativa ($effectiveFrontendPort) por indisponibilidade da porta $RequestedFrontendPort." -ForegroundColor Yellow
  }

  if ($EnforceResponseSla) {
    Invoke-ResponseSlaAcceptance `
      -RuntimeHost $RuntimeHost `
      -RuntimeBackendPort $effectiveBackendPort `
      -SlaMs $ResponseSlaMs `
      -Email $AdminEmail `
      -Password $AdminPassword
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

Start-Runtime `
  -RepoPath $repoRoot `
  -BackendPath $backendDir `
  -FrontendPath $frontendDir `
  -RuntimeHost $BackendHost `
  -RequestedBackendPort $BackendPort `
  -RequestedFrontendPort $FrontendPort `
  -Attempts $PortSearchAttempts `
  -BackendTimeoutSeconds $BackendStartupTimeoutSeconds `
  -FrontendTimeoutSeconds $FrontendStartupTimeoutSeconds

Write-Host "[DEVA] Login admin local (documentado): admin@swaif.local / admin123" -ForegroundColor DarkGray
Write-Host "[DEVA] Comandos: [R] reiniciar | [Q] encerrar | [S] status | [L] logs | [T] teste SLA" -ForegroundColor DarkGray

while ($true) {
  $rawAction = Read-Host "[DEVA] Escolha (R/Q/S/L)"
  if ($null -eq $rawAction) {
    Start-Sleep -Milliseconds 300
    continue
  }
  $action = $rawAction.Trim().ToUpperInvariant()
  switch ($action) {
    "R" {
      Write-Host "[DEVA] Reiniciando runtime..." -ForegroundColor Yellow
      Start-Runtime `
        -RepoPath $repoRoot `
        -BackendPath $backendDir `
        -FrontendPath $frontendDir `
        -RuntimeHost $BackendHost `
        -RequestedBackendPort $BackendPort `
        -RequestedFrontendPort $FrontendPort `
        -Attempts $PortSearchAttempts `
        -BackendTimeoutSeconds $BackendStartupTimeoutSeconds `
        -FrontendTimeoutSeconds $FrontendStartupTimeoutSeconds
    }
    "S" {
      Show-RuntimeStatus
    }
    "L" {
      Show-RuntimeLogs
    }
    "T" {
      Invoke-ResponseSlaAcceptance `
        -RuntimeHost $BackendHost `
        -RuntimeBackendPort $script:EffectiveBackendPort `
        -SlaMs $ResponseSlaMs `
        -Email $AdminEmail `
        -Password $AdminPassword
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
