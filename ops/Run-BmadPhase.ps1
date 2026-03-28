param(
  [Parameter(Mandatory=$true)][string]$Workflow,
  [Parameter(Mandatory=$true)][string]$Batch,
  [Parameter(Mandatory=$true)][string]$Phase,
  [string]$State,
  [string]$CodexBin,
  [string]$OutputLastMessage,
  [string]$StateResult,
  [string[]]$ContextFile,
  [switch]$DryRun,
  [switch]$Execute
)

$cmd = @("python", "ops/run_bmad_phase.py", "--workflow", $Workflow, "--batch", $Batch, "--phase", $Phase)
if ($DryRun) { $cmd += "--dry-run" }
if ($Execute) { $cmd += "--execute" }
if ($State) { $cmd += @("--state", $State) }
if ($CodexBin) { $cmd += @("--codex-bin", $CodexBin) }
if ($OutputLastMessage) { $cmd += @("--output-last-message", $OutputLastMessage) }
if ($StateResult) { $cmd += @("--state-result", $StateResult) }
if ($ContextFile) {
  foreach ($File in $ContextFile) {
    $cmd += @("--context-file", $File)
  }
}
& $cmd[0] $cmd[1..($cmd.Length-1)]
