param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [string]$BackendHost = "127.0.0.1",
  [switch]$NoInstall
)

$ErrorActionPreference = "Stop"

function Ensure-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Comando '$Name' nao encontrado. Instale-o e tente novamente."
  }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $repoRoot "frontend"
$backendDir = Join-Path $repoRoot "backend"

if (-not (Test-Path $frontendDir)) { throw "Pasta frontend nao encontrada em $frontendDir" }
if (-not (Test-Path $backendDir)) { throw "Pasta backend nao encontrada em $backendDir" }

Ensure-Command "npm"
Ensure-Command "py"

Write-Host "[DEVA] Repo: $repoRoot" -ForegroundColor Cyan
Write-Host "[DEVA] Backend: http://$BackendHost`:$BackendPort" -ForegroundColor Cyan
Write-Host "[DEVA] Frontend: http://127.0.0.1:$FrontendPort" -ForegroundColor Cyan

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
$backendCommand = "Set-Location '$backendDir'; py -m uvicorn app.main:app --host $BackendHost --port $BackendPort --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null

Write-Host "[DEVA] Iniciando frontend em nova janela..." -ForegroundColor Green
$frontendCommand = "Set-Location '$frontendDir'; `\$env:VITE_DEPLOY_TARGET='local'; npm run dev -- --host 127.0.0.1 --port $FrontendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host "[DEVA] Pronto. Aguarde alguns segundos e abra: http://127.0.0.1:$FrontendPort" -ForegroundColor Green
Write-Host "[DEVA] Login admin local (documentado): admin@swaif.local / admin123" -ForegroundColor DarkGray
