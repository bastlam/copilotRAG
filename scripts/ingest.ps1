# Re-indexe les projets configurés dans config/projects.yaml
# Exemples :
#   .\scripts\ingest.ps1                    # tout indexer (incrémental)
#   .\scripts\ingest.ps1 -Project demo-api  # un seul projet
#   .\scripts\ingest.ps1 -Force             # tout ré-indexer
param(
    [string]$Project,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$argsList = @("-m", "copilot_rag.ingest")
if ($Project) { $argsList += @("--project", $Project) }
if ($Force)   { $argsList += "--force" }

& $python @argsList
exit $LASTEXITCODE
