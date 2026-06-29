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

    # Use the standalone man page from packaging/linux/ if available
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$SCRIPT_DIR/netcheck.1" ]]; then
        cp "$SCRIPT_DIR/netcheck.1" "$man_dir/netcheck.1"
    else
        # Inline fallback
        cat > "$man_dir/netcheck.1" << 'EOF'
.TH NETCHECK 1 "June 2026" "version 2.2.0" "Network Intelligence Engine"
.SH NAME
netcheck \- cross-platform network diagnostics, connectivity and path analysis
.SH SYNOPSIS
.B netcheck
\fISUBCOMMAND\fR [\fIARGS\fR]
.br
.B netcheck
[\fIOPTIONS\fR]
.SH DESCRIPTION
.B netcheck
is a zero-dependency, cross-platform network diagnostic engine.
Run 'netcheck --help' for full documentation.
.SH SUBCOMMANDS
.TP
.B tcp, dns, http, ssl, ping, interfaces, traceroute, scan, whois
See netcheck --help for full subcommand reference.
EOF
    fi

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

    # Use the standalone bash completion from packaging/linux/ if available
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$SCRIPT_DIR/netcheck.bash-completion" ]]; then
        cp "$SCRIPT_DIR/netcheck.bash-completion" "$completion_dir/netcheck"
    else
        # Inline fallback with all v2.2.0 subcommands
        cat > "$completion_dir/netcheck" << 'EOF'
_netcheck() {
    local cur prev opts subcmds
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    subcmds="tcp dns http ssl ping interfaces traceroute scan whois"
    opts="-t --timeout -j --jobs -f --format -c --combined -q --quick -d --dns -p --ping -s --status --cert -ip --my-ip --mcp --csv --retry --retry-delay -h --help -v --version -V --verbose --no-color"

    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        -X|--method)
            COMPREPLY=( $(compgen -W "GET HEAD POST PUT DELETE PATCH" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

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
complete -F _netcheck netcheckx
EOF
    fi
    echo -e "${GREEN}✓ Bash completion installed${NC}"
}

# Create zsh completion
create_zsh_completion() {
    local SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [[ -f "$SCRIPT_DIR/netcheck.zsh-completion" ]]; then
        local zsh_dir="/usr/local/share/zsh/site-functions"
        if [[ $USE_USER -eq 1 ]]; then
            zsh_dir="${HOME}/.zsh/completions"
        fi
        if mkdir -p "$zsh_dir" 2>/dev/null; then
            cp "$SCRIPT_DIR/netcheck.zsh-completion" "$zsh_dir/_netcheck"
            echo -e "${GREEN}✓ Zsh completion installed ($zsh_dir/_netcheck)${NC}"
            echo -e "${YELLOW}  Tip: add 'fpath=(${zsh_dir} \$fpath)' to ~/.zshrc if not already set${NC}"
        fi
    fi
}

# Create man page and completions if permissions allow
if [[ $USE_USER -eq 0 ]]; then
    create_man_page
    create_bash_completion
    create_zsh_completion
else
    # Install in user home directory
    create_man_page || true
    create_bash_completion || true
    create_zsh_completion || true
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Installation completed successfully!         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Usage examples:"
echo -e "  ${GREEN}netcheck tcp google.com 443${NC}           # TCP connect"
echo -e "  ${GREEN}netcheck dns github.com${NC}               # DNS lookup"
echo -e "  ${GREEN}netcheck ssl google.com -V${NC}            # SSL + cipher info"
echo -e "  ${GREEN}netcheck traceroute 8.8.8.8${NC}           # Trace network path"
echo -e "  ${GREEN}netcheck scan 192.168.1.1${NC}             # Port scan"
echo -e "  ${GREEN}netcheck whois google.com${NC}             # WHOIS/RDAP lookup"
echo -e "  ${GREEN}netcheck tcp google.com 443 -w${NC}        # Watch/loop mode"
echo -e "  ${GREEN}netcheck interfaces${NC}                   # Active interfaces"
echo -e "  ${GREEN}netcheck --mcp${NC}                        # Start MCP Server"
echo -e ""
echo -e "Tab completion enabled for bash/zsh. Run: ${YELLOW}man netcheck${NC} for full docs."
echo ""
