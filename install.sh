#!/bin/bash

# Network Connectivity Checker - Installation Script
# This script installs the tool system-wide and ensures all dependencies are met

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
SCRIPT_NAME="check_ip.sh"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Network Connectivity Checker - Installer           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}This script requires root privileges to install system-wide.${NC}"
   echo -e "${YELLOW}Please run with sudo:${NC}"
   echo -e "${GREEN}  sudo ./install.sh${NC}"
   echo ""
   echo -e "${YELLOW}Or run with --user flag to install in your home directory:${NC}"
   echo -e "${GREEN}  ./install.sh --user${NC}"
   exit 1
fi

# Detect OS and package manager
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    elif [[ -f /etc/redhat-release ]]; then
        OS="rhel"
    elif [[ -f /etc/debian_version ]]; then
        OS="debian"
    else
        OS=$(uname -s)
    fi
    
    echo -e "${BLUE}Detected OS:${NC} $OS"
}

# Check and install dependencies
install_dependencies() {
    echo ""
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for telnet
    if ! command -v telnet &> /dev/null; then
        echo -e "${YELLOW}  ✗ telnet not found${NC}"
        missing_deps+=("telnet")
    else
        echo -e "${GREEN}  ✓ telnet installed${NC}"
    fi
    
    # Check for netcat (nc)
    if ! command -v nc &> /dev/null; then
        echo -e "${YELLOW}  ✗ netcat not found${NC}"
        missing_deps+=("netcat")
    else
        echo -e "${GREEN}  ✓ netcat installed${NC}"
    fi
    
    # Check for timeout command (part of coreutils)
    if ! command -v timeout &> /dev/null; then
        echo -e "${YELLOW}  ✗ timeout not found${NC}"
        missing_deps+=("coreutils")
    else
        echo -e "${GREEN}  ✓ timeout installed${NC}"
    fi
    
    # Install missing dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}Installing missing dependencies: ${missing_deps[*]}${NC}"
        
        case $OS in
            ubuntu|debian|linuxmint|pop)
                apt-get update -qq
                for dep in "${missing_deps[@]}"; do
                    case $dep in
                        telnet)
                            apt-get install -y telnet
                            ;;
                        netcat)
                            apt-get install -y netcat-openbsd || apt-get install -y netcat
                            ;;
                        coreutils)
                            apt-get install -y coreutils
                            ;;
                    esac
                done
                ;;
            centos|rhel|fedora|rocky|alma)
                for dep in "${missing_deps[@]}"; do
                    case $dep in
                        telnet)
                            yum install -y telnet || dnf install -y telnet
                            ;;
                        netcat)
                            yum install -y nc || dnf install -y nc || yum install -y nmap-ncat || dnf install -y nmap-ncat
                            ;;
                        coreutils)
                            yum install -y coreutils || dnf install -y coreutils
                            ;;
                    esac
                done
                ;;
            arch|manjaro)
                for dep in "${missing_deps[@]}"; do
                    case $dep in
                        telnet)
                            pacman -S --noconfirm inetutils
                            ;;
                        netcat)
                            pacman -S --noconfirm openbsd-netcat
                            ;;
                        coreutils)
                            pacman -S --noconfirm coreutils
                            ;;
                    esac
                done
                ;;
            opensuse*|sles)
                for dep in "${missing_deps[@]}"; do
                    case $dep in
                        telnet)
                            zypper install -y telnet
                            ;;
                        netcat)
                            zypper install -y netcat-openbsd
                            ;;
                        coreutils)
                            zypper install -y coreutils
                            ;;
                    esac
                done
                ;;
            *)
                echo -e "${RED}Unsupported OS: $OS${NC}"
                echo -e "${YELLOW}Please manually install: ${missing_deps[*]}${NC}"
                exit 1
                ;;
        esac
        
        echo -e "${GREEN}Dependencies installed successfully!${NC}"
    else
        echo -e "${GREEN}All dependencies are already installed!${NC}"
    fi
}

# Install the script
install_script() {
    echo ""
    echo -e "${BLUE}Installing $COMMAND_NAME...${NC}"
    
    if [[ ! -f "$SCRIPT_NAME" ]]; then
        echo -e "${RED}Error: $SCRIPT_NAME not found in current directory${NC}"
        exit 1
    fi
    
    # Copy script to install directory
    cp "$SCRIPT_NAME" "$INSTALL_DIR/$COMMAND_NAME"
    chmod +x "$INSTALL_DIR/$COMMAND_NAME"
    
    echo -e "${GREEN}✓ Installed to: $INSTALL_DIR/$COMMAND_NAME${NC}"
}

# Create man page
create_man_page() {
    echo ""
    echo -e "${BLUE}Creating man page...${NC}"
    
    local man_dir="/usr/local/share/man/man1"
    mkdir -p "$man_dir"
    
    cat > "$man_dir/netcheck.1" << 'EOF'
.TH NETCHECK 1 "November 2025" "version 1.0" "Network Connectivity Checker"
.SH NAME
netcheck \- check network connectivity to hosts and ports
.SH SYNOPSIS
.B netcheck
[\fIOPTIONS\fR] [\fIinput_file\fR]
.SH DESCRIPTION
.B netcheck
is a network connectivity testing tool that checks if specified hosts and ports are reachable.
It supports parallel processing, multiple output formats, and both batch and single-host testing modes.
.SH OPTIONS
.TP
.BR \-t ", " \-\-timeout " \fIseconds\fR"
Connection timeout in seconds (default: 5)
.TP
.BR \-j ", " \-\-jobs " \fInumber\fR"
Maximum number of parallel jobs (default: 10)
.TP
.BR \-v ", " \-\-verbose
Enable verbose output
.TP
.BR \-f ", " \-\-format " \fIformat\fR"
Output format: text, json, csv, or xml (default: text)
.TP
.BR \-c ", " \-\-combined
Create combined report with all results
.TP
.BR \-q ", " \-\-quick " \fIhost\fR \fIport\fR"
Quick test mode for single host (no files created)
.TP
.BR \-h ", " \-\-help
Display help message and exit
.SH EXAMPLES
.TP
Test hosts from file:
.B netcheck hosts.txt
.TP
Quick test single host:
.B netcheck -q google.com 443
.TP
JSON output with parallel processing:
.B netcheck -f json -j 20 hosts.txt
.TP
Verbose mode from stdin:
.B cat hosts.txt | netcheck -v
.SH INPUT FORMAT
Each line should contain: HOST PORT
.br
Example: 192.168.1.1 80
.SH FILES
.TP
.I result.txt
Successful connection results
.TP
.I fail-YYYY-MM-DD.txt
Failed connection attempts
.TP
.I combined-YYYY-MM-DD.txt
Combined report (when -c option is used)
.SH EXIT STATUS
.TP
.B 0
Success (in quick mode: connection successful)
.TP
.B 1
Failure (in quick mode: connection failed)
.SH AUTHOR
Written by Network Tools Team
.SH SEE ALSO
.BR telnet (1),
.BR nc (1),
.BR ping (8)
EOF
    
    # Update man database
    mandb -q 2>/dev/null || true
    
    echo -e "${GREEN}✓ Man page created: man netcheck${NC}"
}

# Create bash completion
create_bash_completion() {
    echo ""
    echo -e "${BLUE}Creating bash completion...${NC}"
    
    local completion_dir="/etc/bash_completion.d"
    mkdir -p "$completion_dir"
    
    cat > "$completion_dir/netcheck" << 'EOF'
# Bash completion for netcheck

_netcheck() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    opts="-t --timeout -j --jobs -v --verbose -f --format -c --combined -q --quick -h --help"
    
    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        -t|--timeout|-j|--jobs)
            # Numeric argument expected
            return 0
            ;;
        *)
            ;;
    esac
    
    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # File completion
    COMPREPLY=( $(compgen -f -- ${cur}) )
}

complete -F _netcheck netcheck
EOF
    
    echo -e "${GREEN}✓ Bash completion installed${NC}"
}

# Main installation
main() {
    detect_os
    install_dependencies
    install_script
    create_man_page
    create_bash_completion
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          Installation completed successfully!         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Command installed as:${NC} ${GREEN}$COMMAND_NAME${NC}"
    echo ""
    echo -e "${BLUE}Usage examples:${NC}"
    echo -e "  ${GREEN}netcheck -q google.com 443${NC}         # Quick test"
    echo -e "  ${GREEN}netcheck hosts.txt${NC}                 # Batch test"
    echo -e "  ${GREEN}netcheck -f json -c hosts.txt${NC}      # JSON output"
    echo -e "  ${GREEN}netcheck --help${NC}                    # Show help"
    echo -e "  ${GREEN}man netcheck${NC}                       # View manual"
    echo ""
    echo -e "${YELLOW}Note: Restart your shell or run 'source /etc/bash_completion.d/netcheck' for tab completion${NC}"
    echo ""
}

# Run installation
main
