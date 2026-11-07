param(
    [switch]$SkipBuild,
    [int]$Port = 8000,
    [string]$Python = "python",
    [string]$Npm = "npm",
    [string]$Cloudflared = "cloudflared"
)
$ErrorActionPreference = "Stop"
$repoPath = Split-Path $PSScriptRoot -Parent
Push-Location $repoPath
$server = $null
try {
    if (Test-Path -LiteralPath ".venv/Scripts/python.exe") { $Python = (Resolve-Path ".venv/Scripts/python.exe").Path }
    if (-not (Get-Command $Cloudflared -ErrorAction SilentlyContinue)) { throw "Install cloudflared first, or pass -Cloudflared <path-to-exe>." }
    if (-not $SkipBuild) {
        Push-Location app
        try {
            & $Npm ci
            if ($LASTEXITCODE -ne 0) { throw "npm ci failed" }
            & $Npm run build
            if ($LASTEXITCODE -ne 0) { throw "App build failed" }
        } finally { Pop-Location }
    }
    if (-not (Test-Path -LiteralPath "app/dist/index.html")) { throw "Build the app before using -SkipBuild." }
    $env:DEMO_MODE = "1"
    # Start-Process runs the API hidden; the foreground tunnel prints its HTTPS URL.
    $server = Start-Process -FilePath $Python -ArgumentList @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$Port") -WorkingDirectory $repoPath -WindowStyle Hidden -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        if ($server.HasExited) { throw "API exited. Install api/requirements.txt and check the database path." }
        try { $health = Invoke-RestMethod "http://127.0.0.1:$Port/health" -TimeoutSec 1; if ($health.ok) { $ready = $true; break } } catch { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) { throw "API did not become healthy." }
    Write-Host "Open the HTTPS URL printed below on your phone. Press Ctrl+C to stop."
    & $Cloudflared tunnel --url "http://127.0.0.1:$Port"
    if ($LASTEXITCODE -ne 0) { throw "cloudflared exited with code $LASTEXITCODE" }
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id }
    Pop-Location
}
