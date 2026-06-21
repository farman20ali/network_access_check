#!/bin/bash
# Network Connectivity Checker - Uninstaller Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Network Connectivity Checker - Uninstaller         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Find pip3
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="python3 -m pip"
fi

echo -e "${YELLOW}Uninstalling netcheck...${NC}"

# Check for pep668 flags
INSTALL_FLAGS=""
if $PIP_CMD uninstall --help 2>&1 | grep -q "break-system-packages"; then
    INSTALL_FLAGS="--break-system-packages"
fi

# Uninstall python package
if $PIP_CMD show netcheck &>/dev/null; then
    if $PIP_CMD show netcheck | grep -q "Location:.*\.local"; then
        $PIP_CMD uninstall -y netcheck
    else
        sudo $PIP_CMD uninstall -y netcheck $INSTALL_FLAGS
    fi
    echo -e "${GREEN}✓ Python package uninstalled.${NC}"
else
    echo -e "${YELLOW}netcheck is not registered via pip. Cleaning up binary files...${NC}"
fi

# Clean executable binaries
sudo rm -f /usr/local/bin/netcheck 2>/dev/null || true
rm -f ~/.local/bin/netcheck 2>/dev/null || true

# Remove man pages and completions
sudo rm -f /usr/local/share/man/man1/netcheck.1 2>/dev/null || true
rm -f ~/.local/share/man/man1/netcheck.1 2>/dev/null || true
sudo rm -f /etc/bash_completion.d/netcheck 2>/dev/null || true
rm -f ~/.local/share/bash-completion/completions/netcheck 2>/dev/null || true

# Update man database
if command -v mandb > /dev/null 2>&1; then
    mandb -q 2>/dev/null || true
fi

echo -e "${GREEN}✓ Uninstallation completed successfully!${NC}"
echo ""
