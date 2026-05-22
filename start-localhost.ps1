param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [int]$PortSearchAttempts = 20,
  [switch]$NoInstall
)

$ErrorActionPreference = "Stop"

function Ensure-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Comando '$Name' nao encontrado. Instale-o e tente novamente."
  }
}

function Test-PortBindable([string]$Host, [int]$Port) {
  $listener = $null
  try {
    $ip = [System.Net.IPAddress]::Parse($Host)
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

function Resolve-Port([string]$Host, [int]$PreferredPort, [string]$Label, [int]$Attempts) {
  if (Test-PortBindable -Host $Host -Port $PreferredPort) {
    return $PreferredPort
  }

  Write-Host "[DEVA] Porta $PreferredPort ($Label) indisponivel para bind em $Host. Buscando alternativa..." -ForegroundColor Yellow
  for ($offset = 1; $offset -le $Attempts; $offset++) {
    $candidate = $PreferredPort + $offset
    if ($candidate -gt 65535) { break }
    if (Test-PortBindable -Host $Host -Port $candidate) {
      Write-Host "[DEVA] Porta alternativa selecionada para ${Label}: $candidate" -ForegroundColor Yellow
      return $candidate
    }
  }

  throw "Nao foi possivel encontrar porta disponivel para $Label a partir de $PreferredPort."
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $repoRoot "frontend"
$backendDir = Join-Path $repoRoot "backend"

if (-not (Test-Path $frontendDir)) { throw "Pasta frontend nao encontrada em $frontendDir" }
if (-not (Test-Path $backendDir)) { throw "Pasta backend nao encontrada em $backendDir" }

Ensure-Command "npm"
Ensure-Command "py"

Write-Host "[DEVA] Repo: $repoRoot" -ForegroundColor Cyan
$effectiveBackendPort = Resolve-Port -Host $BackendHost -PreferredPort $BackendPort -Label "backend" -Attempts $PortSearchAttempts
$effectiveFrontendPort = Resolve-Port -Host "127.0.0.1" -PreferredPort $FrontendPort -Label "frontend" -Attempts $PortSearchAttempts

Write-Host "[DEVA] Backend: http://$BackendHost`:$effectiveBackendPort" -ForegroundColor Cyan
Write-Host "[DEVA] Frontend: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Cyan

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

Write-Host "[DEVA] Iniciando backend em nova janela..." -ForegroundColor Green
$backendCommand = "Set-Location '$backendDir'; py -m uvicorn app.main:app --host $BackendHost --port $effectiveBackendPort --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null

Write-Host "[DEVA] Iniciando frontend em nova janela..." -ForegroundColor Green
$frontendCommand = "Set-Location '$frontendDir'; `\$env:VITE_DEPLOY_TARGET='local'; `\$env:VITE_API_BASE_URL='http://$BackendHost`:$effectiveBackendPort'; npm run dev -- --host 127.0.0.1 --port $effectiveFrontendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host "[DEVA] Pronto. Aguarde alguns segundos e abra: http://127.0.0.1:$effectiveFrontendPort" -ForegroundColor Green
if ($effectiveBackendPort -ne $BackendPort) {
  Write-Host "[DEVA] Aviso: backend iniciou em porta alternativa ($effectiveBackendPort) para evitar erro de permissao/uso da porta $BackendPort." -ForegroundColor Yellow
}
Write-Host "[DEVA] Login admin local (documentado): admin@swaif.local / admin123" -ForegroundColor DarkGray
