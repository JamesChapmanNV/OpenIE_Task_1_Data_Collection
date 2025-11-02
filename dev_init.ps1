<#  dev_init.ps1
    Boots local dev services for OpenIE_Task_1_Data_Collection.

    - Ensures Docker engine is running (starts Docker Desktop if needed)
    - Ensures volumes exist (oie_pgdata, openie_mongo_data)
    - Ensures containers exist and are running:
        * Postgres 16 on localhost:5432  (container: openie-pg)
        * MongoDB 7 on localhost:27017    (container: oie-mongo)

    Usage:
      pwsh -File .\scripts\dev_init.ps1
#>

$ErrorActionPreference = "Stop"

# -------- Helpers --------
function Write-Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERR]   $msg" -ForegroundColor Red }

function Test-Command($name) {
    $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Wait-ForDocker([int]$retries = 60, [int]$delaySec = 2) {
    for ($i=0; $i -lt $retries; $i++) {
        try {
            docker info --format '{{.ServerVersion}}' | Out-Null
            return $true
        } catch {
            Start-Sleep -Seconds $delaySec
        }
    }
    return $false
}

function Ensure-DockerEngine {
    if (Wait-ForDocker) {
        Write-Ok "Docker engine is running."
        return
    }

    Write-Warn "Docker engine not reachable. Attempting to start Docker Desktop…"
    $dockerDesktop = Join-Path $Env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
    if (-Not (Test-Path $dockerDesktop)) {
        throw "Docker Desktop not found at '$dockerDesktop'. Please install/start Docker Desktop and re-run."
    }

    Start-Process -FilePath $dockerDesktop | Out-Null

    if (-Not (Wait-ForDocker)) {
        throw "Docker engine did not become ready. Open Docker Desktop and ensure 'Engine running', then retry."
    }
    Write-Ok "Docker engine started."
}

function Ensure-Volume($name) {
    try {
        docker volume inspect $name | Out-Null
        Write-Ok "Volume '$name' exists."
    } catch {
        Write-Info "Creating volume '$name'…"
        docker volume create $name | Out-Null
        Write-Ok "Volume '$name' created."
    }
}

function Get-ContainerState($name) {
    $state = docker ps -a --filter "name=^/$name$" --format '{{.Status}}'
    return $state
}

function Ensure-ContainerRunning($name, $runArgs) {
    $state = Get-ContainerState $name
    if (-not $state) {
        Write-Info "Creating container '$name'…"
        # NB: $runArgs is a single string with full 'docker run' args
        Invoke-Expression "docker run $runArgs"
        Write-Ok "Container '$name' created and started."
        return
    }

    if ($state -match '^Up') {
        Write-Ok "Container '$name' is already running."
        return
    } else {
        Write-Info "Starting existing container '$name'…"
        docker start $name | Out-Null
        Write-Ok "Container '$name' started."
    }
}


# -------- Script start --------
# Move to repo root (script may be run from anywhere)
Set-Location -Path (Resolve-Path (Join-Path $PSScriptRoot '..'))

Write-Info "Ensuring Docker engine is available…"
Ensure-DockerEngine

# Volumes
Ensure-Volume -name 'oie_pgdata'
Ensure-Volume -name 'openie_mongo_data'

# Containers
# Postgres 16
$pgRun = @"
--name openie-pg `
-e POSTGRES_PASSWORD=postgres `
-e POSTGRES_DB=openie `
-p 5432:5432 `
-v oie_pgdata:/var/lib/postgresql/data `
-d postgres:16
"@.Replace("`r`n"," ").Replace("`n"," ")
Ensure-ContainerRunning -name 'openie-pg' -runArgs $pgRun

# MongoDB 7
$mongoRun = @"
--name oie-mongo `
-p 27017:27017 `
-v openie_mongo_data:/data/db `
-d mongo:7
"@.Replace("`r`n"," ").Replace("`n"," ")
Ensure-ContainerRunning -name 'oie-mongo' -runArgs $mongoRun


# Summary
Write-Host ""
Write-Ok "Dev services are up."
Write-Host " Postgres:   host=localhost port=5432 db=openie user=postgres password=postgres"
Write-Host " MongoDB:    mongodb://localhost:27017   db=openie"
Write-Host ""
Write-Host " Useful:"
Write-Host "   docker ps"
Write-Host "   docker logs --tail=50 openie-pg"
Write-Host "   docker exec -it openie-pg psql -U postgres -d openie"
Write-Host "   docker exec -it oie-mongo mongosh --eval `"db.getSiblingDB('openie').stats()`""
Write-Host ""
Write-Ok "Done."
