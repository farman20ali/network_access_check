#!/bin/bash
set -e

VERSION=$(PYTHONPATH=. python3 -c "import netcheck; print(netcheck.__version__)")
PACKAGE_NAME="netcheck"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}"

echo "=========================================="
echo "Building ${PACKAGE_NAME} v${VERSION} DEB Package"
echo "=========================================="
echo ""

# Clean previous builds
if [ -d "${BUILD_DIR}" ]; then
    echo "Cleaning previous build directory..."
    rm -rf "${BUILD_DIR}"
fi
if [ -f "${BUILD_DIR}.deb" ]; then
    echo "Removing old package..."
    rm -f "${BUILD_DIR}.deb"
fi

# Create directory structure
echo "Creating package structure..."
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/man/man1"
mkdir -p "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}"
mkdir -p "${BUILD_DIR}/usr/share/bash-completion/completions"

# Copy main script (entrypoint) and packaging library
echo "Copying main script (entrypoint) and packaging library..."
mkdir -p "${BUILD_DIR}/usr/bin"
cat << 'ENTRYEOF' > "${BUILD_DIR}/usr/bin/netcheck"
#!/usr/bin/env python3
import sys
from netcheck.cli import main
if __name__ == '__main__':
    sys.exit(main())
ENTRYEOF
chmod 755 "${BUILD_DIR}/usr/bin/netcheck"

mkdir -p "${BUILD_DIR}/usr/lib/python3/dist-packages"
cp -r netcheck "${BUILD_DIR}/usr/lib/python3/dist-packages/"
find "${BUILD_DIR}/usr/lib/python3/dist-packages/netcheck" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy documentation
echo "Copying documentation..."
for doc in README.md EXAMPLES.md docs/examples.md docs/guides/summary.md docs/guides/publishing.md; do
    if [ -f "$doc" ]; then
        cp "$doc" "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/" 2>/dev/null || true
    fi
done

# Create man page
echo "Creating man page..."
cat << 'MANEOF' > /tmp/netcheck.1
.TH NETCHECK 1 "November 2025" "netcheck 1.1.0" "User Commands"
.SH NAME
netcheck \- network connectivity checker with DNS, ping, and port testing
.SH SYNOPSIS
.B netcheck
[\fIOPTIONS\fR] [\fIFILE\fR]
.br
.B netcheck
.B \-q
.I HOST PORT
.br
.B netcheck
.B \-d
.I HOSTNAME
.br
.B netcheck
.B \-p
.I HOST
.br
.B netcheck
.B \-\-csv
.I FILE
.SH DESCRIPTION
A powerful bash-based network connectivity testing tool that supports ICMP ping, DNS resolution with URL support, parallel TCP testing, IP ranges, port ranges, CSV input, and multiple output formats.
.SH OPTIONS
.TP
.BR \-t ", " \-\-timeout " " \fISECONDS\fR
Connection timeout in seconds (default: 5)
.TP
.BR \-j ", " \-\-jobs " " \fINUMBER\fR
Number of parallel jobs (default: 10, max: 256)
.TP
.BR \-V ", " \-\-verbose
Enable verbose output with detailed connection attempts
.TP
.BR \-f ", " \-\-format " " \fIFORMAT\fR
Output format: text, json, csv, xml (default: text)
.TP
.BR \-c ", " \-\-combined
Create combined report of all results
.TP
.BR \-q ", " \-\-quick " " \fIHOST\fR " " \fIPORT\fR
Quick test mode - test a single host and port immediately
.br
PORT can be: single (80), multiple (80,443), or range (8000-8100)
.TP
.BR \-d ", " \-\-dns " " \fIHOST\fR
Resolve DNS and show IP addresses (accepts URLs)
.br
Automatically strips http://, https://, paths, and ports
.TP
.BR \-p ", " \-\-ping " " \fIHOST\fR
Ping host using ICMP (4 packets, 2s timeout per packet)
.br
Accepts IP addresses, hostnames, and URLs
.TP
.BR \-\-csv " " \fIFILE\fR
Read hosts from CSV file (format: host,port)
.TP
.BR \-v ", " \-\-version
Display version information and exit
.TP
.BR \-h ", " \-\-help
Display help message and exit
.SH INPUT FORMATS
.SS Space-Separated Format
.nf
host1.example.com 80
192.168.1.10 22
.fi
.SS IP Ranges
.nf
192.168.1.1-50 80        # Last octet range
10.0.0.0/24 22          # CIDR notation
.fi
.SS Port Ranges
.nf
server.com 80,443,8080  # Multiple ports
server.com 8000-8100    # Port range
.fi
.SS CSV Format
.nf
host,port
server1.com,80
server2.com,"80,443"
192.168.1.0/24,22
.fi
.SH EXAMPLES
.TP
DNS lookup (accepts URLs):
.B netcheck \-d https://api.example.com
.TP
Ping test (accepts URLs):
.B netcheck \-p https://github.com
.TP
Quick test single port:
.B netcheck \-q google.com 443
.TP
Quick test multiple ports:
.B netcheck \-q server.com 80,443,8080
.TP
Test from file:
.B netcheck hosts.txt
.TP
CSV file input:
.B netcheck \-\-csv servers.csv \-j 50
.TP
JSON output with high parallelism:
.B netcheck hosts.txt \-f json \-j 100 \-t 3
.TP
IP range scanning:
.B echo "192.168.1.0/24 22" | netcheck
.TP
Port range scanning:
.B netcheck \-q target.local 8000-8100
.SH OUTPUT FORMATS
.TP
.B text
Human-readable formatted text (default)
.TP
.B json
Structured JSON format for scripts
.TP
.B csv
Comma-separated values for spreadsheets
.TP
.B xml
XML format for system integration
.SH FILES
.TP
.I result-YYYY-MM-DD.txt
Main results file (format depends on \-f option, includes date)
.TP
.I fail-YYYY-MM-DD.txt
Failed connections list (created for each run, dated)
.TP
.I combined-YYYY-MM-DD.txt
Combined report (created with \-c option, dated)
.SH EXIT STATUS
.TP
.B 0
All connections successful
.TP
.B 1
Some or all connections failed
.SH NOTES
Requires \fBtelnet\fR or \fBnetcat\fR (nc) for TCP port testing.
.PP
DNS resolution uses multiple fallback methods: host, getent, dig, nslookup.
.PP
ICMP ping requires appropriate network permissions (works in snap with network-observe plug).
.PP
Port ranges are limited to 1000 ports to prevent excessive scanning.
.PP
Progress bar updates in real-time during parallel processing.
.SH SEE ALSO
.BR telnet (1),
.BR nc (1),
.BR ping (1),
.BR host (1),
.BR nmap (1)
.SH AUTHOR
Network Access Check Tool
.SH LICENSE
GNU GPL v3 - https://www.gnu.org/licenses/gpl-3.0.html
.SH REPORTING BUGS
https://github.com/farman20ali/network_access_check/issues
MANEOF

# Use SOURCE_DATE_EPOCH to avoid timestamped gzip warning
export SOURCE_DATE_EPOCH=$(date -d "$(grep -m1 '^Version:' <<< "" || echo '2026-01-01')" +%s 2>/dev/null || echo 1735689600)
gzip -9cn /tmp/netcheck.1 > "${BUILD_DIR}/usr/share/man/man1/netcheck.1.gz"
rm /tmp/netcheck.1

# Create bash completion (modern path: usr/share/bash-completion/completions/)
echo "Creating bash completion..."
cat << 'COMPEOF' > "${BUILD_DIR}/usr/share/bash-completion/completions/netcheck"
# Bash completion for netcheck
_netcheck() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-t -j -V -f -c -q -o -d -p -s -h -v --timeout --jobs --verbose --format --combined --quick --output --dns --ping --status --cert --my-ip --retry --retry-delay --csv --help --version --all"
    
    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        -t|--timeout)
            COMPREPLY=( $(compgen -W "1 2 3 5 10 15 30" -- ${cur}) )
            return 0
            ;;
        -j|--jobs)
            COMPREPLY=( $(compgen -W "10 20 50 100 200" -- ${cur}) )
            return 0
            ;;
        --retry)
            COMPREPLY=( $(compgen -W "1 2 3 5 10" -- ${cur}) )
            return 0
            ;;
        --retry-delay)
            COMPREPLY=( $(compgen -W "1 2 3 5" -- ${cur}) )
            return 0
            ;;
        -o|--output)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        --csv)
            COMPREPLY=( $(compgen -f -X '!*.csv' -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # File completion for non-option arguments
    COMPREPLY=( $(compgen -f -- ${cur}) )
    return 0
}
complete -F _netcheck netcheck
COMPEOF
chmod 644 "${BUILD_DIR}/usr/share/bash-completion/completions/netcheck"

# Create required Debian changelog.gz
echo "Creating changelog..."
cat << CHANGEEOF > /tmp/netcheck.changelog
netcheck (${VERSION}) stable; urgency=medium

  * v${VERSION} release - cross-platform Python 3 engine.
  * DNS, HTTP, SSL, Ping, TCP, and Interfaces diagnostic modules.
  * MCP server support for AI editor integrations.
  * Multiple output formats: text, JSON, CSV, XML.

 -- Network Tools <admin@example.com>  $(date -R)
CHANGEEOF
gzip -9cn /tmp/netcheck.changelog > "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/changelog.gz"
rm /tmp/netcheck.changelog

# Create required Debian copyright file
echo "Creating copyright..."
cat << 'COPYEOF' > "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright"
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: netcheck
Upstream-Contact: https://github.com/farman20ali/network_access_check
Source: https://github.com/farman20ali/network_access_check

Files: *
Copyright: 2024-2026 Network Tools <admin@example.com>
License: GPL-3

License: GPL-3
 On Debian systems, the full text of the GNU General Public
 License version 3 can be found in the file
 '/usr/share/common-licenses/GPL-3'.
COPYEOF

# Create control file
echo "Creating control file..."
cat << CTRLEOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-cryptography, iproute2 | net-tools, iputils-ping
Maintainer: Network Tools <admin@example.com>
Description: Network connectivity checker with advanced features
 A powerful python-based network connectivity testing tool that supports:
  - ICMP ping testing with statistics and URL support
  - DNS lookup with multiple fallback methods (accepts URLs)
  - HTTP/HTTPS status checking with performance metrics
  - SSL/TLS certificate validation with expiry warnings
  - Network interface display with filtering (--my-ip)
  - Retry logic with configurable count and delay
  - Parallel connection testing (up to 256 concurrent jobs)
  - Quick mode parallel processing for wide IP ranges
  - Output file support for quick mode results (-o flag)
  - IP range support (192.168.1.1-50, 10.0.0.0/24)
  - Port ranges (8000-8100) and multiple ports (80,443,3306)
  - CSV file input for bulk testing
  - Multiple output formats (text, JSON, CSV, XML)
  - Comprehensive input validation with helpful warnings
  - Real-time progress tracking
  - Combined reports with dated filenames
 .
 Perfect for system administrators, DevOps engineers, and network diagnostics.
Homepage: https://github.com/yourusername/netcheck
CTRLEOF

# Create conffiles declaration (only for /etc/ files; /usr/ must NOT be listed)
# bash-completion is now in /usr/share/ so no conffiles needed
# (leaving file empty or omitting is fine; omit entirely)

# Create postinst script
echo "Creating post-installation script..."
cat << 'POSTEOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/bash
set -e

# Update man page database
if command -v mandb > /dev/null 2>&1; then
    mandb -q 2>/dev/null || true
fi

# Dependencies are managed by python3 stdlib and system depends.

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ netcheck installed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick start:"
echo "  netcheck --help              # Show help"
echo "  netcheck -q google.com 443   # Quick test"
echo "  netcheck --csv hosts.csv     # Test from CSV"
echo ""
echo "Documentation:"
echo "  man netcheck                 # Manual page"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
POSTEOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# Create prerm script
echo "Creating pre-removal script..."
cat << 'PREEOF' > "${BUILD_DIR}/DEBIAN/prerm"
#!/bin/bash
set -e

# Clean up any cached runtime files (no /tmp usage)
find /var/cache/netcheck -name "*.tmp" -delete 2>/dev/null || true

exit 0
PREEOF
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"

# Fix permissions for standard Debian guidelines
find "${BUILD_DIR}" -type d -exec chmod 755 {} +
find "${BUILD_DIR}" -type f -exec chmod 644 {} +
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"
chmod 755 "${BUILD_DIR}/usr/bin/netcheck"

# Calculate installed size
echo "Calculating package size..."
INSTALLED_SIZE=$(du -sk "${BUILD_DIR}" | cut -f1)
echo "Installed-Size: ${INSTALLED_SIZE}" >> "${BUILD_DIR}/DEBIAN/control"

# Fix ownership: all files must be owned by root:root in a proper deb package
# Use fakeroot if available (it fakes root ownership without requiring sudo)
if command -v fakeroot > /dev/null 2>&1; then
    BUILD_CMD="fakeroot dpkg-deb --build ${BUILD_DIR}"
else
    BUILD_CMD="dpkg-deb --build ${BUILD_DIR}"
fi

# Build the package
echo ""
echo "Building DEB package..."
eval ${BUILD_CMD}

# Verify package
echo ""
echo "Verifying package..."
dpkg-deb --info "${BUILD_DIR}.deb"

echo ""
echo "Package contents:"
dpkg-deb --contents "${BUILD_DIR}.deb"

# Check with lintian if available
if command -v lintian > /dev/null 2>&1; then
    echo ""
    echo "Running lintian checks..."
    lintian "${BUILD_DIR}.deb" || true
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Package created successfully: ${BUILD_DIR}.deb"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To test installation:"
echo "  sudo dpkg -i ${BUILD_DIR}.deb"
echo "  sudo apt-get install -f  # Fix dependencies if needed"
echo ""
echo "To test the tool:"
echo "  netcheck --help"
echo "  netcheck -q google.com 443"
echo ""
echo "To uninstall:"
echo "  sudo apt remove ${PACKAGE_NAME}"
echo ""
echo "Package info:"
ls -lh "${BUILD_DIR}.deb"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
