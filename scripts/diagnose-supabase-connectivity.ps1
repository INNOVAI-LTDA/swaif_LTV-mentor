param(
  [string]$BackendEnvPath = "",
  [string]$SupabaseDbUrl = "",
  [int]$TcpTimeoutMs = 8000
)

$ErrorActionPreference = "Stop"

function Resolve-BackendEnvPath([string]$ProvidedPath) {
  if ($ProvidedPath) {
    return $ProvidedPath
  }
  $repoRoot = Split-Path -Parent $PSScriptRoot
  return (Join-Path $repoRoot "backend/.env")
}

function Resolve-SupabaseDbUrl([string]$InlineDbUrl, [string]$EnvFilePath) {
  if ($InlineDbUrl) {
    return $InlineDbUrl.Trim()
  }
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

function Resolve-Targets([string]$EndpointHost) {
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
    # best effort
  }
  return $targets
}

function Test-TcpEndpoint([string]$EndpointHost, [int]$Port, [int]$TimeoutMs) {
  $targets = Resolve-Targets -EndpointHost $EndpointHost
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

function Test-NetConnectionSupported([string]$EndpointHost, [int]$Port) {
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

function Test-PythonSocket([string]$EndpointHost, [int]$Port, [int]$TimeoutMs) {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($null -eq $py) {
    return @{
      available = $false
      success = $false
      output = "py launcher nao encontrado."
    }
  }

  $scriptPath = Join-Path $env:TEMP "diag_supabase_socket.py"
  @'
import socket
import sys

host = sys.argv[1]
port = int(sys.argv[2])
timeout_s = float(sys.argv[3])

try:
    with socket.create_connection((host, port), timeout=timeout_s):
        print("PY_SOCKET_OK")
    sys.exit(0)
except Exception as exc:
    print(f"PY_SOCKET_FAIL: {type(exc).__name__}: {exc}")
    sys.exit(2)
'@ | Set-Content -Path $scriptPath -Encoding ascii

  $timeoutSeconds = [Math]::Max([Math]::Ceiling($TimeoutMs / 1000.0), 1)
  try {
    $output = & py $scriptPath $EndpointHost $Port $timeoutSeconds 2>&1
    $exitCode = $LASTEXITCODE
    return @{
      available = $true
      success = ($exitCode -eq 0)
      output = (($output | ForEach-Object { "$_" }) -join "`n")
      exit_code = $exitCode
      python = $py.Source
    }
  } catch {
    return @{
      available = $true
      success = $false
      output = ($_ | Out-String)
      exit_code = 1
      python = $py.Source
    }
  } finally {
    Remove-Item $scriptPath -Force -ErrorAction SilentlyContinue
  }
}

function Show-FirewallHints() {
  if (-not (Get-Command Get-NetFirewallRule -ErrorAction SilentlyContinue)) {
    Write-Host "[DIAG] NetSecurity cmdlets indisponiveis nesta sessao." -ForegroundColor Yellow
    return
  }

  Write-Host "[DIAG] Regras outbound BLOCK relacionadas a python:" -ForegroundColor Cyan
  try {
    $rules = Get-NetFirewallRule -Enabled True -Direction Outbound -Action Block -ErrorAction Stop
    $matches = foreach ($rule in $rules) {
      $apps = $rule | Get-NetFirewallApplicationFilter -ErrorAction SilentlyContinue
      foreach ($app in $apps) {
        $programPath = [string]$app.Program
        if ($programPath -match "(?i)python|\\py\.exe$") {
          [PSCustomObject]@{
            Name = $rule.Name
            DisplayName = $rule.DisplayName
            Program = $programPath
            Profile = $rule.Profile
          }
        }
      }
    }

    if ($matches) {
      $matches | Sort-Object DisplayName -Unique | Format-Table -AutoSize
    } else {
      Write-Host "[DIAG] Nenhuma regra BLOCK outbound explicita para python encontrada." -ForegroundColor DarkGray
    }
  } catch {
    Write-Host "[DIAG] Falha ao ler regras de firewall: $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

$resolvedBackendEnvPath = Resolve-BackendEnvPath -ProvidedPath $BackendEnvPath
$resolvedDbUrl = Resolve-SupabaseDbUrl -InlineDbUrl $SupabaseDbUrl -EnvFilePath $resolvedBackendEnvPath

if (-not $resolvedDbUrl) {
  throw "SUPABASE_DB_URL nao encontrado. Informe -SupabaseDbUrl ou configure em backend/.env."
}

try {
  $uri = [System.Uri]$resolvedDbUrl
} catch {
  throw "SUPABASE_DB_URL invalido: $resolvedDbUrl"
}

$hostName = $uri.Host
$port = if ($uri.Port -gt 0) { $uri.Port } else { 5432 }

Write-Host "[DIAG] backend/.env: $resolvedBackendEnvPath" -ForegroundColor Cyan
Write-Host "[DIAG] db host/port: $hostName`:$port" -ForegroundColor Cyan

Write-Host "[DIAG] DNS targets:" -ForegroundColor Cyan
$targets = Resolve-Targets -EndpointHost $hostName
$targets | ForEach-Object { Write-Host " - $_" }

$tcpDotNet = Test-TcpEndpoint -EndpointHost $hostName -Port $port -TimeoutMs $TcpTimeoutMs
$tcpNetConnection = Test-NetConnectionSupported -EndpointHost $hostName -Port $port
$pythonSocket = Test-PythonSocket -EndpointHost $hostName -Port $port -TimeoutMs $TcpTimeoutMs

Write-Host "[DIAG] TCP via .NET TcpClient: $tcpDotNet" -ForegroundColor Cyan
Write-Host "[DIAG] TCP via Test-NetConnection: $tcpNetConnection" -ForegroundColor Cyan
if ($pythonSocket.available) {
  Write-Host "[DIAG] TCP via python (py): $($pythonSocket.success) (exit=$($pythonSocket.exit_code))" -ForegroundColor Cyan
  Write-Host "[DIAG] py path: $($pythonSocket.python)" -ForegroundColor DarkGray
  if ($pythonSocket.output) {
    Write-Host "[DIAG] python output: $($pythonSocket.output)" -ForegroundColor DarkGray
  }
} else {
  Write-Host "[DIAG] Teste python nao executado: $($pythonSocket.output)" -ForegroundColor Yellow
}

Show-FirewallHints

if ($pythonSocket.available -and -not $pythonSocket.success -and ($pythonSocket.output -match "10013|Permission denied")) {
  Write-Host "[DIAG] Resultado: bloqueio de socket para processo python detectado (WinError 10013)." -ForegroundColor Red
  Write-Host "[DIAG] Acao sugerida: liberar python.exe/py.exe para conexoes outbound no firewall/antivirus/VPN e reexecutar." -ForegroundColor Yellow
} elseif (-not $tcpDotNet -and -not $tcpNetConnection) {
  Write-Host "[DIAG] Resultado: conectividade TCP indisponivel para o endpoint." -ForegroundColor Red
  Write-Host "[DIAG] Acao sugerida: verificar rede, VPN e egress para $hostName`:$port." -ForegroundColor Yellow
} else {
  Write-Host "[DIAG] Resultado: conectividade basica parece disponivel; se o runtime falhar, revisar credenciais e politicas locais por processo." -ForegroundColor Green
}
