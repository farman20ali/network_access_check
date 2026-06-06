#!/bin/bash
# Network Connectivity Checker - Installer Script (Python Native)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Network Connectivity Checker - Python Installer    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is required but not installed.${NC}" >&2
    exit 1
fi

# Detect pip3
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    if python3 -m pip --version &> /dev/null; then
        PIP_CMD="python3 -m pip"
    else
        echo -e "${YELLOW}Warning: pip3 not found. Attempting to install it...${NC}"
        sudo apt-get update -qq && sudo apt-get install -y python3-pip || true
        if ! command -v pip3 &> /dev/null; then
            echo -e "${RED}Error: pip could not be installed. Please install python3-pip manually.${NC}" >&2
            exit 1
        fi
    fi
fi

# Determine install scope
USE_USER=0
if [[ "$1" == "--user" ]]; then
    USE_USER=1
elif [[ $EUID -ne 0 ]]; then
    echo -e "${YELLOW}Not running as root. Installing in user directory (--user).${NC}"
    USE_USER=1
fi

# Install python package
echo -e "${BLUE}Installing Python package...${NC}"
INSTALL_FLAGS=""
# Handle PEP 668 (externally-managed-environment)
if $PIP_CMD install --help 2>&1 | grep -q "break-system-packages"; then
    INSTALL_FLAGS="--break-system-packages"
fi

if [[ $USE_USER -eq 1 ]]; then
    $PIP_CMD install --user . $INSTALL_FLAGS
    # Find user bin directory
    USER_BIN=$(python3 -c "import site; import os; print(os.path.join(site.getuserbase(), 'bin'))")
    export PATH="$USER_BIN:$PATH"
    echo -e "${GREEN}✓ Installed in user environment: $USER_BIN/netcheck${NC}"
    echo -e "${YELLOW}Ensure $USER_BIN is in your PATH environment variable.${NC}"
else
    sudo $PIP_CMD install . $INSTALL_FLAGS
    echo -e "${GREEN}✓ Installed system-wide: /usr/local/bin/netcheck${NC}"
fi

# Create man page
create_man_page() {
    echo -e "${BLUE}Creating man page...${NC}"
    local man_dir="/usr/local/share/man/man1"
    if [[ $USE_USER -eq 1 ]]; then
        man_dir="${HOME}/.local/share/man/man1"
    fi
    
    mkdir -p "$man_dir"
    
    cat > "$man_dir/netcheck.1" << 'EOF'
.TH NETCHECK 1 "May 2026" "version 2.0.0" "Network Intelligence Engine"
.SH NAME
netcheck \- network diagnostics, connectivity checks, and interfaces listing
.SH SYNOPSIS
.B netcheck
\fISUBCOMMAND\fR [\fIARGS\fR]
.br
.B netcheck
[\fIOPTIONS\fR]
.SH DESCRIPTION
.B netcheck
is a cross-platform, production-grade network diagnostic engine.
It resolves DNS, tests TCP connectivity, checks HTTP response metrics, inspects SSL lifetimes, pings targets, and lists active interfaces (including WiFi and Hotspots).
It can also run in Model Context Protocol (MCP) server mode for AI editors.
.SH SUBCOMMANDS
.TP
.B tcp \fIhost\fR \fIport\fR
Check TCP port reachability (supports port lists e.g. 80,443 and ranges e.g. 8000-8010).
.TP
.B dns \fIhost\fR
Lookup IP addresses (A/AAAA) for a host.
.TP
.B http \fIurl\fR
Inspect status code, redirects, size, and response time.
.TP
.B ssl \fIhost\fR [\fIport\fR]
Inspect SSL certificate subject, issuer, and days remaining.
.TP
.B ping \fIhost\fR
Ping a host via ICMP and show RTT stats.
.TP
.B interfaces
List local interfaces and highlight the active outbound route.
.SH LEGACY OPTIONS
.TP
.BR -q ", " --quick " \fIhost\fR \fIport\fR"
Quick TCP connection test.
.TP
.BR -d ", " --dns " \fIhost\fR"
Perform DNS lookup.
.TP
.BR -p ", " --ping " \fIhost\fR"
Ping host.
.TP
.BR -s ", " --status " \fIurl\fR"
HTTP status check.
.TP
.BR --cert " \fIhost\fR"
SSL certificate check.
.TP
.BR -ip ", " --my-ip
List network interfaces.
.TP
.BR --mcp
Start standard Model Context Protocol JSON-RPC stdio server.
.TP
.BR -t ", " --timeout " \fIsec\fR"
Set connection timeout (default: 5).
.TP
.BR -j ", " --jobs " \fInum\fR"
Configure thread pool size for concurrent bulk checks (default: 10).
.TP
.BR -f ", " --format " \fIformat\fR"
Output format: text, json, csv, xml.
.TP
.BR --retry " \fIcount\fR"
Number of connection attempts (default: 1).
.TP
.BR --retry-delay " \fIsec\fR"
Delay between connection attempts.
.SH EXAMPLES
.TP
Quick TCP check:
.B netcheck -q google.com 443
.TP
HTTP check:
.B netcheck http https://github.com
.TP
Show active WiFi interface:
.B netcheck interfaces
.TP
Start MCP Server:
.B netcheck --mcp
EOF

    # Update man database
    if command -v mandb > /dev/null 2>&1; then
        mandb -q 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Man page installed: man netcheck${NC}"
}

# Create bash completion
create_bash_completion() {
    echo -e "${BLUE}Installing bash completion...${NC}"
    local completion_dir="/etc/bash_completion.d"
    if [[ $USE_USER -eq 1 ]]; then
        completion_dir="${HOME}/.local/share/bash-completion/completions"
    fi
    
    mkdir -p "$completion_dir"
    
    cat > "$completion_dir/netcheck" << 'EOF'
_netcheck() {
    local cur prev opts subcmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    subcmds="tcp dns http ssl ping interfaces"
    opts="-t --timeout -j --jobs -f --format -c --combined -q --quick -d --dns -p --ping -s --status --cert -ip --my-ip --mcp --csv --retry --retry-delay -h --help -v --version"
    
    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    # If starting with subcommands
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${subcmds} ${opts}" -- ${cur}) )
        return 0
    fi
    
    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}
complete -F _netcheck netcheck
EOF
    echo -e "${GREEN}✓ Bash completion installed${NC}"
}

# Create man page and bash completion if permissions allow
if [[ $USE_USER -eq 0 ]]; then
    create_man_page
    create_bash_completion
else
    # Install man page in user home directory
    create_man_page || true
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Installation completed successfully!         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Usage examples:"
echo -e "  ${GREEN}netcheck tcp google.com 443${NC}       # TCP connect"
echo -e "  ${GREEN}netcheck interfaces${NC}               # Active interfaces"
echo -e "  ${GREEN}netcheck --mcp${NC}                    # Start MCP Server"
echo ""
