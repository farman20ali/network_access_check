#!/bin/bash

# Network Connectivity Checker - Uninstall Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/usr/local/bin"
COMMAND_NAME="netcheck"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Network Connectivity Checker - Uninstaller         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   echo -e "${YELLOW}Please run: sudo ./uninstall.sh${NC}"
   exit 1
fi

echo -e "${YELLOW}This will remove netcheck from your system.${NC}"
read -p "Are you sure? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Uninstallation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Uninstalling netcheck...${NC}"

# Remove main script
if [[ -f "$INSTALL_DIR/$COMMAND_NAME" ]]; then
    rm -f "$INSTALL_DIR/$COMMAND_NAME"
    echo -e "${GREEN}✓ Removed: $INSTALL_DIR/$COMMAND_NAME${NC}"
else
    echo -e "${YELLOW}  Command not found: $INSTALL_DIR/$COMMAND_NAME${NC}"
fi

# Remove man page
if [[ -f "/usr/local/share/man/man1/netcheck.1" ]]; then
    rm -f "/usr/local/share/man/man1/netcheck.1"
    mandb -q 2>/dev/null || true
    echo -e "${GREEN}✓ Removed: man page${NC}"
else
    echo -e "${YELLOW}  Man page not found${NC}"
fi

# Remove bash completion
if [[ -f "/etc/bash_completion.d/netcheck" ]]; then
    rm -f "/etc/bash_completion.d/netcheck"
    echo -e "${GREEN}✓ Removed: bash completion${NC}"
else
    echo -e "${YELLOW}  Bash completion not found${NC}"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Uninstallation completed successfully!         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Note: Dependencies (telnet, netcat) were not removed.${NC}"
echo -e "${YELLOW}Remove them manually if no longer needed.${NC}"
echo ""
