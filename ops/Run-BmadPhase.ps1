param(
  [Parameter(Mandatory=$true)][string]$Workflow,
  [Parameter(Mandatory=$true)][string]$Batch,
  [Parameter(Mandatory=$true)][string]$Phase,
  [switch]$DryRun
)

$cmd = @("python", "ops/run_bmad_phase.py", "--workflow", $Workflow, "--batch", $Batch, "--phase", $Phase)
if ($DryRun) { $cmd += "--dry-run" }
& $cmd[0] $cmd[1..($cmd.Length-1)]
