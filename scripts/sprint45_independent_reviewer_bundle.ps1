param(
  [Parameter(Mandatory = $true)]
  [string]$HostedEndpoint,
  [Parameter(Mandatory = $true)]
  [string]$ProtectedRoute,
  [Parameter(Mandatory = $true)]
  [string]$ForgedToken,
  [Parameter(Mandatory = $true)]
  [string]$ExpiredToken,
  [Parameter(Mandatory = $true)]
  [string]$RevokedToken,
  [Parameter(Mandatory = $true)]
  [string]$WrongAudienceToken
)

$ErrorActionPreference = "Stop"

Write-Host "1) Validating Sprint 45 evidence schema"
uv run --with jsonschema python -c "import json,glob; from jsonschema import validate; s=json.load(open('releases/enki-hosted-1.0-rc2/production-control-evidence.schema.json','r',encoding='utf-8')); files=glob.glob('releases/enki-hosted-1.0-rc2/evidence/sprint45/*.json'); [validate(instance=json.load(open(f,'r',encoding='utf-8')), schema=s) for f in files]; print(f'validated {len(files)} files')"

Write-Host "2) Enforcing zero-cost invariants"
uv run python scripts/validate_sprint45_zero_cost.py

Write-Host "3) Enforcing fail-closed acceptance gates"
uv run python scripts/validate_sprint45_acceptance_gates.py

Write-Host "4) Running OWASP ZAP baseline"
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t $HostedEndpoint -r zap-baseline-report.html -J zap-baseline-report.json

Write-Host "5) Running identity denial abuse cases"
curl.exe -i -H "Authorization: Bearer $ForgedToken" "$HostedEndpoint/api/$ProtectedRoute"
curl.exe -i -H "Authorization: Bearer $ExpiredToken" "$HostedEndpoint/api/$ProtectedRoute"
curl.exe -i -H "Authorization: Bearer $RevokedToken" "$HostedEndpoint/api/$ProtectedRoute"
curl.exe -i -H "Authorization: Bearer $WrongAudienceToken" "$HostedEndpoint/api/$ProtectedRoute"

Write-Host "6) Hashing rehearsal and billing artifacts"
Get-FileHash raw-evidence\sprint45\*.log -Algorithm SHA256
Get-FileHash raw-evidence\sprint45\billing\* -Algorithm SHA256

Write-Host "Bundle complete. Update evidence files with reviewer identity, hosted artifacts, and final attestations."
