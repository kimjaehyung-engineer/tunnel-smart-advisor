param(
    [switch]$Restart,
    [switch]$Stop,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BackendUrl = "http://127.0.0.1:8080/health"
$FrontendUrl = "http://127.0.0.1:2000/"

function Stop-PortProcess($Port) {
    Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Where-Object { $_ -ne 0 } |
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

function Assert-Command($CommandName) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Required command '$CommandName' was not found in PATH."
    }
}

function Wait-ForHttp($Name, $Url, $TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Name ready: $Url"
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
    } while ((Get-Date) -lt $deadline)

    throw "$Name did not become ready within $TimeoutSeconds seconds: $Url"
}

function Start-DevWindow($Title, $CommandLine) {
    Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/k", "title $Title && $CommandLine" `
        -WorkingDirectory $Root
}

if ($Stop) {
    Stop-PortProcess 8080
    Stop-PortProcess 2000
    Write-Host "Stopped dev servers on ports 8080 and 2000."
    exit 0
}

Assert-Command "python"
Assert-Command "npm"

if ($Restart) {
    Stop-PortProcess 8080
    Stop-PortProcess 2000
    Start-Sleep -Seconds 1
}

if (-not (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue)) {
    Start-DevWindow "Tunnel Backend" "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8080"
}

if (-not (Get-NetTCPConnection -LocalPort 2000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-DevWindow "Tunnel Frontend" "npm run dev --prefix frontend"
}

try {
    Wait-ForHttp "Backend" $BackendUrl 45
    Wait-ForHttp "Frontend" $FrontendUrl 45
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Check the 'Tunnel Backend' and 'Tunnel Frontend' windows for the real error output."
    exit 1
}

Write-Host "Backend:  http://127.0.0.1:8080"
Write-Host "Frontend: http://127.0.0.1:2000"
Write-Host "Stop:     npm run dev:stop"

Get-NetTCPConnection -LocalPort 8080,2000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object LocalAddress, LocalPort, State, OwningProcess |
    Format-Table -AutoSize

if (-not $NoBrowser) {
    Start-Process $FrontendUrl
}
