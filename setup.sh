#!/usr/bin/env bash
# Bootstrap script for plugin-urgence-fr (macOS / Linux)
#
# Vérifie et installe les pré-requis :
#   - Python 3.10+
#   - Git
#   - Claude Code CLI
#
# Usage (depuis le dossier du plugin) :
#   chmod +x setup.sh
#   ./setup.sh

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

step() { printf "${CYAN}==> %s${NC}\n" "$1"; }
ok()   { printf "${GREEN}[OK] %s${NC}\n" "$1"; }
warn() { printf "${YELLOW}[!]  %s${NC}\n" "$1"; }
err()  { printf "${RED}[X]  %s${NC}\n" "$1"; }

cat <<'EOF'

  plugin-urgence-fr - bootstrap script (macOS/Linux)
  Verifie/installe : Python 3.10+, Git, Claude Code CLI

EOF

OS="$(uname -s)"

ask() {
    local prompt="$1"
    local default="${2:-O}"
    read -r -p "$prompt [${default}/$([ "$default" = "O" ] && echo n || echo o)] " resp
    resp="${resp:-$default}"
    [[ "$resp" =~ ^[OoYy]$ ]]
}

# 1. Python ----------------------------------------------------------
step "Verification de Python 3.10+"
PY_OK=false
if command -v python3 >/dev/null 2>&1; then
    PY_VERSION=$(python3 --version 2>&1 | sed 's/Python //')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        ok "Python $PY_VERSION detecte"
        PY_OK=true
    else
        warn "Python $PY_VERSION trouve, mais 3.10+ requis"
    fi
else
    warn "Python 3 non installe"
fi

if [ "$PY_OK" = "false" ]; then
    if ask "Installer Python 3.12 ?"; then
        if [ "$OS" = "Darwin" ]; then
            if ! command -v brew >/dev/null; then
                err "Homebrew requis. Installe-le d'abord depuis https://brew.sh/"
                exit 1
            fi
            brew install python@3.12
        elif command -v apt-get >/dev/null; then
            sudo apt-get update && sudo apt-get install -y python3 python3-pip
        elif command -v dnf >/dev/null; then
            sudo dnf install -y python3
        elif command -v pacman >/dev/null; then
            sudo pacman -S --noconfirm python
        else
            err "Gestionnaire de paquets non reconnu. Installe Python 3.10+ manuellement."
            exit 1
        fi
        ok "Python installe"
    else
        err "Python 3.10+ est obligatoire. Abandon."
        exit 1
    fi
fi

# 2. Git -------------------------------------------------------------
step "Verification de Git"
if command -v git >/dev/null 2>&1; then
    ok "Git $(git --version 2>&1 | sed 's/git version //') detecte"
else
    warn "Git non installe"
    if ask "Installer Git ?"; then
        if [ "$OS" = "Darwin" ]; then
            xcode-select --install || brew install git
        elif command -v apt-get >/dev/null; then
            sudo apt-get install -y git
        elif command -v dnf >/dev/null; then
            sudo dnf install -y git
        elif command -v pacman >/dev/null; then
            sudo pacman -S --noconfirm git
        else
            err "Installe Git manuellement."
            exit 1
        fi
        ok "Git installe"
    else
        err "Git est requis. Abandon."
        exit 1
    fi
fi

# 3. Claude Code CLI -------------------------------------------------
step "Verification de Claude Code CLI"
if command -v claude >/dev/null 2>&1; then
    ok "Claude Code detecte : $(claude --version 2>&1)"
else
    warn "Claude Code non installe"
    if ask "Installer Claude Code CLI via le script officiel Anthropic ?"; then
        curl -fsSL https://claude.ai/install.sh | bash
        ok "Claude Code installe."
        warn "Apres l'install, fais 'claude login' pour t'authentifier."
    else
        err "Claude Code est requis. Abandon."
        exit 1
    fi
fi

# 4. Structure du plugin ---------------------------------------------
step "Verification de la structure du plugin"
if [ ! -f ".claude-plugin/marketplace.json" ]; then
    err "marketplace.json introuvable. Es-tu dans le dossier 'plugin-urgence' ?"
    echo ""
    echo "Si non, fais d'abord :"
    printf "  ${CYAN}git clone https://github.com/Amu2ler/plugin-urgence.git${NC}\n"
    printf "  ${CYAN}cd plugin-urgence${NC}\n"
    printf "  ${CYAN}./setup.sh${NC}\n"
    exit 1
fi
MARKETPLACE_PATH="$(cd "$(dirname ".claude-plugin/marketplace.json")" && pwd)/marketplace.json"
ok "marketplace.json trouve : $MARKETPLACE_PATH"

# 5. Recap final -----------------------------------------------------
echo ""
printf "${GREEN}============================================================\n"
printf "  Tous les pre-requis sont prets !\n"
printf "============================================================${NC}\n"
echo ""
echo "Etapes suivantes (a faire manuellement dans Claude Code) :"
echo ""
echo "1. Lance Claude Code :"
printf "     ${CYAN}claude${NC}\n"
echo ""
echo "2. Dans Claude Code, tape ces 3 commandes :"
printf "     ${CYAN}/plugin marketplace add %s${NC}\n" "$MARKETPLACE_PATH"
printf "     ${CYAN}/plugin install plugin-urgence-fr@local-marketplace${NC}\n"
printf "     ${CYAN}/reload-plugins${NC}\n"
echo ""
echo "3. Teste l'orchestration :"
printf "     ${CYAN}/plugin-urgence-fr:urgence 29 rue de Strasbourg, 44000 Nantes${NC}\n"
echo ""
printf "${GREEN}Bonne demo.${NC}\n"
echo ""
