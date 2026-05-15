param(
  [string]$RepoRoot = "C:\Users\dmene\Projetos\innovai\git\swaif_LTV-mentor",
  [string]$SupabaseDbUrl = "postgresql://runtime-db",
  [string]$ClientCode = "accmed",
  [string]$CorsAllowOrigins = "http://127.0.0.1:4173",
  [string]$AdminEmail = "admin@swaif.local",
  [string]$AdminPassword = "admin123",
  [string]$MentorEmail = "mentor@swaif.local",
  [string]$MentorPassword = "mentor123",
  [string]$LogDir = ".tmp_story_1_2_validation",
  [switch]$SkipPytest,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok([string]$msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }

function Invoke-JsonPost {
  param([string]$Uri,[hashtable]$Body,[hashtable]$Headers=@{})
  $json = $Body | ConvertTo-Json -Depth 10
  try {
    $resp = Invoke-WebRequest -Method Post -Uri $Uri -ContentType "application/json" -Headers $Headers -Body $json -UseBasicParsing
    $raw = [string]$resp.Content
    $parsed = $null
    if (-not [string]::IsNullOrWhiteSpace($raw)) { try { $parsed = $raw | ConvertFrom-Json } catch {} }
    if ($null -eq $parsed) { $parsed = @{} }
    return @{ ok=$true; status=[int]$resp.StatusCode; data=$parsed; raw=$raw }
  } catch {
    $response = $_.Exception.Response
    if ($null -ne $response) {
      $statusCode = [int]$response.StatusCode
      $raw = ""
      try {
        $stream = $response.GetResponseStream()
        if ($stream) { $raw = (New-Object System.IO.StreamReader($stream)).ReadToEnd() }
      } catch {}
      if ([string]::IsNullOrWhiteSpace($raw) -and $_.ErrorDetails -and $_.ErrorDetails.Message) {
        $raw = [string]$_.ErrorDetails.Message
      }
      $parsed = $null
      if (-not [string]::IsNullOrWhiteSpace($raw)) { try { $parsed = $raw | ConvertFrom-Json } catch {} }
      return @{ ok=$false; status=$statusCode; data=$parsed; raw=$raw }
    }
    return @{ ok=$false; status=-1; data=$null; raw=$_.Exception.Message }
  }
}

function Add-Result([string]$Name,[bool]$Passed,[string]$Details) {
  $script:Results += [pscustomobject]@{ Test=$Name; Passed=$Passed; Details=$Details }
}

function Kill-Port([int]$Port) {
  try {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
      try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
  } catch {}
}

function Start-Backend {
  param(
    [string]$BackendPath,
    [string]$AppEnv,
    [string]$DbUrl,
    [int]$Port,
    [string]$ScenarioName,
    [string]$LogDir,
    [string]$ClientCode,
    [string]$CorsAllowOrigins
  )
  if ($AppEnv -eq "production") {
    if ([string]::IsNullOrWhiteSpace($ClientCode)) { throw "${ScenarioName}: CLIENT_CODE missing." }
    if ([string]::IsNullOrWhiteSpace($CorsAllowOrigins)) { throw "${ScenarioName}: CORS_ALLOW_ORIGINS missing." }
  }

  Kill-Port -Port $Port
  $stdout = Join-Path $LogDir "$ScenarioName-uvicorn.stdout.log"
  $stderr = Join-Path $LogDir "$ScenarioName-uvicorn.stderr.log"

  Push-Location $BackendPath
  $env:PYTHONPATH = ".vendor;."
  $env:APP_ENV = $AppEnv
  $env:SUPABASE_DB_URL = $DbUrl
  $env:CLIENT_CODE = $ClientCode
  $env:CORS_ALLOW_ORIGINS = $CorsAllowOrigins
  $env:APP_AUTH_SECRET = "story-1-2-validation-secret"
  $env:USER_STORE_PATH = ".\data\users.json"
  $env:ORG_STORE_PATH = ".\data\organizations.json"
  $env:MENTOR_STORE_PATH = ".\data\mentors.json"
  $env:PROTOCOL_STORE_PATH = ".\data\protocols.json"
  $env:PILLAR_STORE_PATH = ".\data\pillars.json"
  $env:METRIC_STORE_PATH = ".\data\metrics.json"
  $env:STUDENT_STORE_PATH = ".\data\students.json"
  $env:ENROLLMENT_STORE_PATH = ".\data\enrollments.json"
  Remove-Item Env:MEASUREMENT_STORE_PATH -ErrorAction SilentlyContinue
  Remove-Item Env:CHECKPOINT_STORE_PATH -ErrorAction SilentlyContinue

  $proc = Start-Process -FilePath "python" -ArgumentList @("-m","uvicorn","app.main:app","--host","127.0.0.1","--port",$Port) -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  Pop-Location

  return @{ proc=$proc; stdout=$stdout; stderr=$stderr; port=$Port; baseUrl="http://127.0.0.1:$Port" }
}

function Stop-Backend($ctx) {
  if ($ctx -and $ctx.proc -and -not $ctx.proc.HasExited) {
    Stop-Process -Id $ctx.proc.Id -Force -ErrorAction SilentlyContinue
  }
}

function Wait-ApiReady {
  param([string]$BaseUrl,[int]$TimeoutSec=60)
  $probes = @("/docs","/openapi.json","/health")
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  $attempt = 0
  while ((Get-Date) -lt $deadline) {
    $attempt++
    foreach ($path in $probes) {
      try {
        $res = Invoke-WebRequest -Uri ($BaseUrl + $path) -Method Get -TimeoutSec 2 -UseBasicParsing
        if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500) { return @{ ready=$true; details="probe=$path status=$($res.StatusCode) attempt=$attempt" } }
      } catch {
        Write-Warn "readiness attempt $attempt probe $path failed: $($_.Exception.Message)"
      }
    }
    Start-Sleep -Milliseconds 700
  }
  return @{ ready=$false; details="timeout ${TimeoutSec}s" }
}

function Login([string]$ApiBase,[string]$Email,[string]$Password) {
  $res = Invoke-JsonPost -Uri "$ApiBase/auth/login" -Body @{ email=$Email; password=$Password }
  if ($res.ok -and $res.data.access_token) { return [string]$res.data.access_token }
  return ""
}

function Setup-LocalFixture([string]$ApiBase,[hashtable]$Headers) {
  $suffix = [guid]::NewGuid().ToString("N").Substring(0,8)
  $org = Invoke-JsonPost -Uri "$ApiBase/admin/mentorias" -Headers $Headers -Body @{ name="Mentoria Script Story 1.2 $suffix" }
  if (-not $org.ok) { throw "org creation failed status=$($org.status)" }
  $student = Invoke-JsonPost -Uri "$ApiBase/admin/alunos" -Headers $Headers -Body @{ full_name="Aluno Script Story 1.2 $suffix"; email="aluno-$suffix@swaif.local" }
  if (-not $student.ok) { throw "student creation failed status=$($student.status)" }
  $link = Invoke-JsonPost -Uri "$ApiBase/admin/alunos/$($student.data.id)/vincular-mentoria" -Headers $Headers -Body @{ organization_id=$org.data.id; progress_score=0.35; engagement_score=0.6 }
  if (-not $link.ok) { throw "student link failed status=$($link.status)" }
  $protocol = Invoke-JsonPost -Uri "$ApiBase/admin/protocolos" -Headers $Headers -Body @{ organization_id=$org.data.id; name="Metodo Script Story 1.2 $suffix" }
  if (-not $protocol.ok) { throw "protocol creation failed status=$($protocol.status)" }
  $pillar = Invoke-JsonPost -Uri "$ApiBase/admin/pilares" -Headers $Headers -Body @{ protocol_id=$protocol.data.id; name="Compromisso" }
  if (-not $pillar.ok) { throw "pillar creation failed status=$($pillar.status)" }
  $metric = Invoke-JsonPost -Uri "$ApiBase/admin/metricas" -Headers $Headers -Body @{ protocol_id=$protocol.data.id; pillar_id=$pillar.data.id; name="Frequencia $suffix"; unit="%" }
  if (-not $metric.ok) { throw "metric creation failed status=$($metric.status)" }
  return @{ student_id=[string]$student.data.id; metric_id=[string]$metric.data.id }
}

function Error-Code($res) { if ($res.data -and $res.data.error) { return [string]$res.data.error.code }; return "" }

function New-PytestBaseTemp([string]$BackendPath) {
  $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
  $tempDir = Join-Path $BackendPath ".tmp_pytest_batchg_$suffix"
  New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
  return $tempDir
}

$script:Results = @()
$resolvedRepo = (Resolve-Path $RepoRoot).Path
$backendPath = Join-Path $resolvedRepo "backend"
$resolvedLogDir = Join-Path $resolvedRepo $LogDir
New-Item -ItemType Directory -Force -Path $resolvedLogDir | Out-Null

Write-Step "Story 1.2 Robustness Matrix"
Write-Host "Repo: $resolvedRepo"
Write-Host "Backend: $backendPath"
Write-Host "Log dir: $resolvedLogDir"

if ($WhatIf) {
  Write-Warn "WhatIf enabled."
  exit 0
}

$scenarios = @(
  @{ name="scenario1"; app_env="production"; dburl=$SupabaseDbUrl; port=8001 },
  @{ name="scenario2"; app_env="production"; dburl=""; port=8002 },
  @{ name="scenario3"; app_env="local"; dburl=""; port=8003 }
)

foreach ($s in $scenarios) {
  $ctx = $null
  try {
    Write-Step "$($s.name) startup"
    $ctx = Start-Backend -BackendPath $backendPath -AppEnv $s.app_env -DbUrl $s.dburl -Port $s.port -ScenarioName $s.name -LogDir $resolvedLogDir -ClientCode $ClientCode -CorsAllowOrigins $CorsAllowOrigins
    $ready = Wait-ApiReady -BaseUrl $ctx.baseUrl -TimeoutSec 60
    if (-not $ready.ready) {
      Add-Result -Name "$($s.name)_execution" -Passed $false -Details "backend not ready; stdout=$($ctx.stdout); stderr=$($ctx.stderr)"
      continue
    }
    Write-Ok "$($s.name) ready ($($ready.details))"

    if ($s.name -eq "scenario1") {
      $mentorToken = Login -ApiBase $ctx.baseUrl -Email $MentorEmail -Password $MentorPassword
      if ([string]::IsNullOrWhiteSpace($mentorToken)) { throw "mentor login failed" }
      $mentorCall = Invoke-JsonPost -Uri "$($ctx.baseUrl)/admin/alunos/std_1/indicadores/carga-inicial" -Headers @{ Authorization = "Bearer $mentorToken" } -Body @{ metric_values=@(); checkpoints=@() }
      Add-Result -Name "mentor_blocked_admin_endpoint" -Passed ((-not $mentorCall.ok) -and ($mentorCall.status -in @(401,403))) -Details "status=$($mentorCall.status) code=$(Error-Code $mentorCall); stdout=$($ctx.stdout); stderr=$($ctx.stderr)"

      $adminToken = Login -ApiBase $ctx.baseUrl -Email $AdminEmail -Password $AdminPassword
      if ([string]::IsNullOrWhiteSpace($adminToken)) { throw "admin login failed" }
      $fixture = Setup-LocalFixture -ApiBase $ctx.baseUrl -Headers @{ Authorization="Bearer $adminToken" }
      $call = Invoke-JsonPost -Uri "$($ctx.baseUrl)/admin/alunos/$($fixture.student_id)/indicadores/carga-inicial" -Headers @{ Authorization="Bearer $adminToken" } -Body @{ metric_values=@(@{metric_id=$fixture.metric_id;value_baseline=10;value_current=15}); checkpoints=@() }
      $rawSnippet = if ([string]::IsNullOrWhiteSpace($call.raw)) { "<empty>" } else { $call.raw.Substring(0, [Math]::Min(220, $call.raw.Length)) }
      $scenario1Pass = $call.ok -and $call.status -eq 200
      Add-Result -Name "production_like_uses_postgres_path" -Passed $scenario1Pass -Details "status=$($call.status) code=$(Error-Code $call) raw=$rawSnippet; stdout=$($ctx.stdout); stderr=$($ctx.stderr)"
    }

    if ($s.name -eq "scenario2") {
      $adminToken = Login -ApiBase $ctx.baseUrl -Email $AdminEmail -Password $AdminPassword
      if ([string]::IsNullOrWhiteSpace($adminToken)) { throw "admin login failed" }
      $fixture = Setup-LocalFixture -ApiBase $ctx.baseUrl -Headers @{ Authorization="Bearer $adminToken" }
      $call = Invoke-JsonPost -Uri "$($ctx.baseUrl)/admin/alunos/$($fixture.student_id)/indicadores/carga-inicial" -Headers @{ Authorization="Bearer $adminToken" } -Body @{ metric_values=@(@{metric_id=$fixture.metric_id;value_baseline=10;value_current=15}); checkpoints=@() }
      $rawSnippet = if ([string]::IsNullOrWhiteSpace($call.raw)) { "<empty>" } else { $call.raw.Substring(0, [Math]::Min(220, $call.raw.Length)) }
      Add-Result -Name "postgres_runtime_unavailable" -Passed ((-not $call.ok) -and ($call.status -eq 409) -and ((Error-Code $call) -eq "POSTGRES_RUNTIME_UNAVAILABLE")) -Details "status=$($call.status) code=$(Error-Code $call) raw=$rawSnippet; stdout=$($ctx.stdout); stderr=$($ctx.stderr)"
    }

    if ($s.name -eq "scenario3") {
      $adminToken = Login -ApiBase $ctx.baseUrl -Email $AdminEmail -Password $AdminPassword
      if ([string]::IsNullOrWhiteSpace($adminToken)) { throw "admin login failed" }
      $fixture = Setup-LocalFixture -ApiBase $ctx.baseUrl -Headers @{ Authorization="Bearer $adminToken" }
      $call = Invoke-JsonPost -Uri "$($ctx.baseUrl)/admin/alunos/$($fixture.student_id)/indicadores/carga-inicial" -Headers @{ Authorization="Bearer $adminToken" } -Body @{ metric_values=@(@{metric_id=$fixture.metric_id;value_baseline=55;value_current=68;value_projected=75}); checkpoints=@(@{week=1;status="green";label="Inicio consistente"},@{week=2;status="yellow";label="Ajustar rotina"}) }
      $rawSnippet = if ([string]::IsNullOrWhiteSpace($call.raw)) { "<empty>" } else { $call.raw.Substring(0, [Math]::Min(220, $call.raw.Length)) }
      $ok = (-not $call.ok) -and ($call.status -eq 409) -and ((Error-Code $call) -eq "POSTGRES_RUNTIME_UNAVAILABLE")
      Add-Result -Name "local_without_db_url_runtime_unavailable" -Passed $ok -Details "status=$($call.status) code=$(Error-Code $call) raw=$rawSnippet; stdout=$($ctx.stdout); stderr=$($ctx.stderr)"
    }
  } catch {
    Add-Result -Name "$($s.name)_execution" -Passed $false -Details "$($_.Exception.Message); stdout=$($ctx.stdout); stderr=$($ctx.stderr)"
  } finally {
    Stop-Backend $ctx
    Kill-Port -Port $s.port
  }
}

if (-not $SkipPytest) {
  try {
    Write-Step "scenario4 pytest coverage"
    Push-Location $backendPath
    $env:PYTHONPATH = ".vendor;."
    $pytestBaseTemp = New-PytestBaseTemp -BackendPath $backendPath
    $cmd = "python -m pytest tests/api/test_admin_indicator_load_api.py::test_indicator_load_returns_postgres_domain_not_ready_when_json_fallback_is_not_possible tests/unit/test_indicator_carga_service.py::test_load_initial_indicators_flags_unready_domains_in_production_like -q --basetemp `"$pytestBaseTemp`""
    cmd /c $cmd | Out-Host
    Add-Result -Name "domain_not_ready_coverage_pytest" -Passed ($LASTEXITCODE -eq 0) -Details "exit_code=$LASTEXITCODE basetemp=$pytestBaseTemp"
    Pop-Location
  } catch {
    Add-Result -Name "domain_not_ready_coverage_pytest" -Passed $false -Details $_.Exception.Message
    try { Pop-Location } catch {}
  }
} else {
  Add-Result -Name "domain_not_ready_coverage_pytest" -Passed $true -Details "skipped by -SkipPytest"
}

Write-Step "Summary"
$script:Results | Format-Table -AutoSize | Out-Host
$failed = @($script:Results | ? { -not $_.Passed })
if ($failed.Count -gt 0) { Write-Err "Robustness matrix failed: $($failed.Count) test(s)."; exit 1 }
Write-Ok "Robustness matrix passed."
exit 0
