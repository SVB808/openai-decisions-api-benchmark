$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  Write-Host 'Python launcher (py) not found. Install Python from python.org and rerun.'
  exit 1
}
if (-not (Test-Path '.venv\Scripts\python.exe')) {
  py -m venv .venv
  if ($LASTEXITCODE -ne 0) { throw 'Could not create Python virtual environment' }
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
if (-not $env:OPENAI_API_KEY) {
  $secure = Read-Host 'Paste your OpenAI API key (input hidden)' -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $env:OPENAI_API_KEY) { throw 'No API key entered' }
Write-Host "`nRunning small API check..." -ForegroundColor Cyan
& $python benchmark.py --limit 2 --runs 1 --out smoke_results.csv
if ($LASTEXITCODE -ne 0) { throw 'Smoke test failed to execute' }
$smoke = Import-Csv smoke_results.csv
if (($smoke | Where-Object { $_.error }).Count -gt 0 -or $smoke.Count -ne 4) {
  Write-Host 'An API call failed. Full benchmark was NOT run. Share the displayed error (not your API key).' -ForegroundColor Yellow
  exit 1
}
Write-Host "`nSmoke test passed. Running full benchmark..." -ForegroundColor Green
& $python benchmark.py --runs 3
if ($LASTEXITCODE -ne 0) { throw 'Benchmark failed' }
Write-Host "`nComplete. Send results.csv here for analysis." -ForegroundColor Green
