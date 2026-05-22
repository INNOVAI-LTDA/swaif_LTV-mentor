param(
  [string]$Context = "docs/mvp-mentoria/contracts-freeze-v1.md",
  [string]$SpecInstruction = "Criar quick spec para resolver baixa cobertura de radar em runtime Supabase strict. Contexto: somente 3 de 250 enrollments com dados em runtime_measurements. Definir desenho idempotente para popular deva_accmed_runtime_measurements e deva_accmed_runtime_checkpoints para todos enrollments ativos no sync de startup. Preservar contrato v1 e envelope de erro padronizado. Incluir criterios de aceitacao com validacao das rotas mentor centro, matriz e radar.",
  [string]$DevInstruction = "Implementar o quick spec aprovado para garantir cobertura de runtime Supabase no radar. Popular runtime_measurements e runtime_checkpoints para todos os enrollments ativos no sync. Manter guardrails do backend, sem quebrar contratos. Adicionar ou ajustar testes de regressao para cobertura de radar e validar endpoints mentor.",
  [string]$ReviewInstruction = "Revisar criticamente a implementacao focando regressao de contrato, cobertura real de runtime Supabase para radar, riscos de performance no sync e consistencia entre enrollment, metricas e pilares.",
  [switch]$ConfirmSteps
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Confirm-Or-Stop {
  param([string]$Message)

  if (-not $ConfirmSteps) {
    return
  }

  $answer = (Read-Host "$Message [s/N]").Trim().ToLowerInvariant()
  if ($answer -notin @("s", "sim", "y", "yes")) {
    throw "Execucao interrompida pelo operador."
  }
}

function Invoke-BmadMake {
  param(
    [Parameter(Mandatory = $true)][string]$Target,
    [Parameter(Mandatory = $true)][string]$Instruction,
    [Parameter(Mandatory = $true)][string]$ContextFile
  )

  $makeArgs = @(
    $Target,
    "EXECUTE=1",
    "INSTRUCTION=$Instruction",
    "CONTEXT=$ContextFile"
  )

  Write-Host ("==> make {0} EXECUTE=1 CONTEXT={1}" -f $Target, $ContextFile)
  & make @makeArgs

  if ($LASTEXITCODE -ne 0) {
    throw ("Falha no alvo make: {0}" -f $Target)
  }
}

if (-not (Get-Command make -ErrorAction SilentlyContinue)) {
  throw "Comando 'make' nao encontrado no PATH."
}

Invoke-BmadMake -Target "bmad-quick-spec" -Instruction $SpecInstruction -ContextFile $Context
Confirm-Or-Stop -Message "Prosseguir para quick-dev?"

Invoke-BmadMake -Target "bmad-quick-dev" -Instruction $DevInstruction -ContextFile $Context
Confirm-Or-Stop -Message "Prosseguir para code-review?"

Invoke-BmadMake -Target "bmad-code-review" -Instruction $ReviewInstruction -ContextFile $Context

Write-Host "==> make bmad-status"
& make bmad-status
if ($LASTEXITCODE -ne 0) {
  throw "Falha no alvo make: bmad-status"
}

Write-Host "Fluxo concluido com sucesso."
