#!/usr/bin/env pwsh
# Bootstrap script for plugin-urgence-fr (Windows / PowerShell)
#
# Vérifie et installe les pré-requis :
#   - Python 3.10+
#   - Git
#   - Claude Code CLI
#
# Usage (depuis le dossier du plugin) :
#   .\setup.ps1
#
# Si la politique d'exécution bloque, lance :
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$Msg) Write-Host "==> $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "[!]  $Msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$Msg) Write-Host "[X]  $Msg" -ForegroundColor Red }

Write-Host ""
Write-Host "  plugin-urgence-fr - bootstrap script (Windows)" -ForegroundColor Cyan
Write-Host "  Verifie/installe : Python 3.10+, Git, Claude Code CLI" -ForegroundColor Cyan
Write-Host ""

# 1. Python ----------------------------------------------------------
Write-Step "Verification de Python 3.10+"
$pythonOk = $false
try {
    $rawVersion = (& python --version 2>&1).ToString()
    $pyVersion = $rawVersion -replace '^Python\s+', ''
    $parts = $pyVersion.Split('.')
    if ([int]$parts[0] -ge 3 -and [int]$parts[1] -ge 10) {
        Write-Ok "Python $pyVersion detecte"
        $pythonOk = $true
    } else {
        Write-Warn "Python $pyVersion trouve, mais 3.10+ requis"
    }
} catch {
    Write-Warn "Python non installe (ou pas dans le PATH)"
}

if (-not $pythonOk) {
    $resp = Read-Host "Installer Python 3.12 via winget ? [O/n]"
    if ($resp -eq "" -or $resp -match '^[oOyY]') {
        Write-Host "Installation de Python 3.12..."
        winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        Write-Ok "Python 3.12 installe."
        Write-Warn "Relance ce script dans un NOUVEAU PowerShell pour que Python soit dans le PATH."
        exit 0
    } else {
        Write-Err "Python 3.10+ est obligatoire. Abandon."
        exit 1
    }
}

# 2. Git -------------------------------------------------------------
Write-Step "Verification de Git"
try {
    $gitVersion = (& git --version) -replace '^git version\s+', ''
    Write-Ok "Git $gitVersion detecte"
} catch {
    Write-Warn "Git non installe"
    $resp = Read-Host "Installer Git via winget ? [O/n]"
    if ($resp -eq "" -or $resp -match '^[oOyY]') {
        winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
        Write-Ok "Git installe."
        Write-Warn "Relance ce script dans un NOUVEAU PowerShell."
        exit 0
    } else {
        Write-Err "Git est requis pour cloner et versionner. Abandon."
        exit 1
    }
}

# 3. Claude Code CLI -------------------------------------------------
Write-Step "Verification de Claude Code CLI"
$claudeOk = $false
try {
    $claudeVersion = (& claude --version 2>&1).ToString().Trim()
    Write-Ok "Claude Code detecte : $claudeVersion"
    $claudeOk = $true
} catch {
    Write-Warn "Claude Code non installe"
}

if (-not $claudeOk) {
    $resp = Read-Host "Installer Claude Code CLI via le script officiel Anthropic ? [O/n]"
    if ($resp -eq "" -or $resp -match '^[oOyY]') {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
        Write-Ok "Claude Code installe."
        Write-Warn "Apres l'install, fais 'claude login' pour t'authentifier."
    } else {
        Write-Err "Claude Code est requis pour utiliser ce plugin. Abandon."
        exit 1
    }
}

# 4. Structure du plugin ---------------------------------------------
Write-Step "Verification de la structure du plugin"
if (-not (Test-Path ".claude-plugin/marketplace.json")) {
    Write-Err "marketplace.json introuvable. Es-tu dans le dossier 'plugin-urgence' ?"
    Write-Host ""
    Write-Host "Si non, fais d'abord :"
    Write-Host "  git clone https://github.com/Amu2ler/plugin-urgence.git" -ForegroundColor Cyan
    Write-Host "  cd plugin-urgence" -ForegroundColor Cyan
    Write-Host "  .\setup.ps1" -ForegroundColor Cyan
    exit 1
}
$marketplacePath = (Resolve-Path ".claude-plugin/marketplace.json").Path
Write-Ok "marketplace.json trouve : $marketplacePath"

# 5. Recap final -----------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Tous les pre-requis sont prets !" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Etapes suivantes (a faire manuellement dans Claude Code) :" -ForegroundColor White
Write-Host ""
Write-Host "1. Lance Claude Code :" -ForegroundColor White
Write-Host "     claude" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Dans Claude Code, tape ces 3 commandes :" -ForegroundColor White
Write-Host "     /plugin marketplace add $marketplacePath" -ForegroundColor Cyan
Write-Host "     /plugin install plugin-urgence-fr@local-marketplace" -ForegroundColor Cyan
Write-Host "     /reload-plugins" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Teste l'orchestration :" -ForegroundColor White
Write-Host "     /plugin-urgence-fr:urgence 29 rue de Strasbourg, 44000 Nantes" -ForegroundColor Cyan
Write-Host ""
Write-Host "Bonne demo." -ForegroundColor Green
Write-Host ""
