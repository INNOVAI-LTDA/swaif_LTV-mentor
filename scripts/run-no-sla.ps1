# Just a tiny wrapper so bash doesn't have to escape `$false`.
# Usage: powershell -File scripts/run-no-sla.ps1
& "$PSScriptRoot\..\start-localhost.ps1" -EnforceResponseSla:$false
