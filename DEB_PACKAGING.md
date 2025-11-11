# Publishing as DEB Package (for Ubuntu/Debian)

## Overview

A **.deb** package is the standard software package format for Debian-based Linux distributions (Ubuntu, Debian, Linux Mint, etc.).

## Directory Structure

```bash
netcheck-1.0.0/
├── DEBIAN/
│   ├── control          # Package metadata
│   ├── postinst         # Post-installation script
│   └── prerm            # Pre-removal script
└── usr/
    ├── local/
    │   └── bin/
    │       └── netcheck # Main script
    └── share/
        ├── man/
        │   └── man1/
        │       └── netcheck.1.gz  # Man page
        └── doc/
            └── netcheck/
                ├── README.md
                ├── EXAMPLES.md
                └── copyright
```

## Step-by-Step Guide

### 1. Create Package Structure

```bash
#!/bin/bash
# build-deb.sh

VERSION="1.0.0"
PACKAGE_NAME="netcheck"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}"

# Create directory structure
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/local/bin"
mkdir -p "${BUILD_DIR}/usr/share/man/man1"
mkdir -p "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}"
mkdir -p "${BUILD_DIR}/etc/bash_completion.d"

# Copy main script
cp check_ip.sh "${BUILD_DIR}/usr/local/bin/netcheck"
chmod 755 "${BUILD_DIR}/usr/local/bin/netcheck"

# Copy documentation
cp README.md EXAMPLES.md INSTALL.md "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/"
gzip -9 < README.md > "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/README.gz"

# Create man page
./install.sh --man-only  # Or manually create
gzip -9c netcheck.1 > "${BUILD_DIR}/usr/share/man/man1/netcheck.1.gz"

# Create bash completion
cat << 'EOF' > "${BUILD_DIR}/etc/bash_completion.d/netcheck"
_netcheck() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-t -j -v -f -c -q --timeout --jobs --verbose --format --combined --quick --csv --help --version"

    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        -t|--timeout)
            COMPREPLY=( $(compgen -W "1 2 3 5 10" -- ${cur}) )
            return 0
            ;;
        -j|--jobs)
            COMPREPLY=( $(compgen -W "10 20 50 100" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _netcheck netcheck
EOF
chmod 644 "${BUILD_DIR}/etc/bash_completion.d/netcheck"

# Create copyright file
cat << 'EOF' > "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/copyright"
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: netcheck
Source: https://github.com/yourusername/netcheck

Files: *
Copyright: 2025 Your Name <your.email@example.com>
License: MIT

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

echo "Package structure created: ${BUILD_DIR}"
```

### 2. Create DEBIAN/control File

```bash
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/control"
Package: netcheck
Version: 1.0.0
Section: utils
Priority: optional
Architecture: all
Depends: bash (>= 4.0), telnet | netcat-openbsd | netcat-traditional
Maintainer: Your Name <your.email@example.com>
Description: Network connectivity checker with advanced features
 A powerful bash-based network connectivity testing tool that supports:
  - Parallel connection testing
  - IP range and CIDR notation
  - Port ranges and multiple ports
  - CSV file input
  - Multiple output formats (text, JSON, CSV, XML)
  - Quick test mode
  - Progress tracking
 .
 Perfect for system administrators, DevOps engineers, and network diagnostics.
Homepage: https://github.com/yourusername/netcheck
EOF
```

### 3. Create Post-Installation Script

```bash
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/bash
set -e

# Update man page database
if command -v mandb > /dev/null 2>&1; then
    mandb -q 2>/dev/null || true
fi

# Check for required dependencies
if ! command -v telnet > /dev/null 2>&1 && ! command -v nc > /dev/null 2>&1; then
    echo ""
    echo "WARNING: Neither telnet nor netcat (nc) is installed."
    echo "Please install one of them:"
    echo "  sudo apt install telnet"
    echo "  sudo apt install netcat-openbsd"
    echo ""
fi

echo ""
echo "netcheck installed successfully!"
echo "Run 'netcheck --help' to get started."
echo ""

exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
```

### 4. Create Pre-Removal Script

```bash
cat << 'EOF' > "${BUILD_DIR}/DEBIAN/prerm"
#!/bin/bash
set -e

# Clean up any temporary files if they exist
rm -f /tmp/netcheck-*.tmp 2>/dev/null || true

exit 0
EOF
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"
```

### 5. Build the Package

```bash
# Build the .deb package
dpkg-deb --build "${BUILD_DIR}"

# Check the package
dpkg-deb --info "${BUILD_DIR}.deb"
dpkg-deb --contents "${BUILD_DIR}.deb"

# Verify with lintian (checks for common issues)
sudo apt install lintian -y
lintian "${BUILD_DIR}.deb"

echo ""
echo "Package created: ${BUILD_DIR}.deb"
echo ""
```

### 6. Test Installation

```bash
# Install locally
sudo dpkg -i netcheck_1.0.0.deb

# Fix dependencies if needed
sudo apt-get install -f

# Test
netcheck --help
netcheck -q google.com 443

# Uninstall
sudo apt remove netcheck
```

## Publishing to APT Repository

### Option 1: Ubuntu PPA (Personal Package Archive)

```bash
# 1. Create Launchpad account
# Visit: https://launchpad.net/

# 2. Install packaging tools
sudo apt install devscripts debhelper dh-make

# 3. Create source package
cd netcheck-1.0.0
debuild -S -sa

# 4. Upload to PPA
dput ppa:yourusername/netcheck ../netcheck_1.0.0_source.changes

# 5. Users can install with:
sudo add-apt-repository ppa:yourusername/netcheck
sudo apt update
sudo apt install netcheck
```

### Option 2: Custom APT Repository

```bash
# 1. Set up web server (GitHub Pages, S3, etc.)

# 2. Create repository structure
mkdir -p apt-repo/pool/main
mkdir -p apt-repo/dists/stable/main/binary-amd64

# 3. Copy package
cp netcheck_1.0.0.deb apt-repo/pool/main/

# 4. Generate Packages file
cd apt-repo
dpkg-scanpackages pool/main /dev/null | gzip -9c > dists/stable/main/binary-amd64/Packages.gz

# 5. Create Release file
cd dists/stable
cat << EOF > Release
Origin: Your Name
Label: netcheck
Suite: stable
Codename: stable
Architectures: amd64 all
Components: main
Description: Network connectivity checker repository
EOF

# 6. Sign the repository (optional but recommended)
gpg --armor --detach-sign -o Release.gpg Release

# 7. Upload to web server

# 8. Users can add your repository:
echo "deb https://your-domain.com/apt-repo stable main" | sudo tee /etc/apt/sources.list.d/netcheck.list
sudo apt update
sudo apt install netcheck
```

## Complete Build Script

Save this as `build-deb.sh`:

```bash
#!/bin/bash
set -e

VERSION="1.0.0"
PACKAGE_NAME="netcheck"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}"

echo "Building ${PACKAGE_NAME} version ${VERSION} DEB package..."

# Clean previous builds
rm -rf "${BUILD_DIR}" "${BUILD_DIR}.deb"

# Create directory structure
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/local/bin"
mkdir -p "${BUILD_DIR}/usr/share/man/man1"
mkdir -p "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}"
mkdir -p "${BUILD_DIR}/etc/bash_completion.d"

# Copy main script
cp check_ip.sh "${BUILD_DIR}/usr/local/bin/netcheck"
chmod 755 "${BUILD_DIR}/usr/local/bin/netcheck"

# Copy documentation
cp README.md EXAMPLES.md INSTALL.md "${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}/"

# Create man page (simplified version)
cat << 'MANEOF' > /tmp/netcheck.1
.TH NETCHECK 1 "November 2025" "netcheck 1.0.0" "User Commands"
.SH NAME
netcheck \- network connectivity checker
.SH SYNOPSIS
.B netcheck
[\fIOPTIONS\fR] [\fIFILE\fR]
.SH DESCRIPTION
A powerful network connectivity testing tool with parallel processing, IP ranges, port ranges, and multiple output formats.
.SH OPTIONS
.TP
.BR \-t ", " \-\-timeout " " \fISECONDS\fR
Connection timeout (default: 5)
.TP
.BR \-j ", " \-\-jobs " " \fINUMBER\fR
Parallel jobs (default: 10)
.TP
.BR \-f ", " \-\-format " " \fIFORMAT\fR
Output format: text, json, csv, xml (default: text)
.TP
.BR \-q ", " \-\-quick " " \fIHOST\fR " " \fIPORT\fR
Quick test mode
.TP
.BR \-\-csv " " \fIFILE\fR
Read hosts from CSV file
.SH EXAMPLES
netcheck -q google.com 443
.br
netcheck --csv hosts.csv -j 50
.SH AUTHOR
Written by Your Name.
MANEOF
gzip -9c /tmp/netcheck.1 > "${BUILD_DIR}/usr/share/man/man1/netcheck.1.gz"
rm /tmp/netcheck.1

# Create bash completion
cat << 'COMPEOF' > "${BUILD_DIR}/etc/bash_completion.d/netcheck"
_netcheck() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-t -j -v -f -c -q --timeout --jobs --verbose --format --combined --quick --csv --help --version"
    
    case "${prev}" in
        -f|--format)
            COMPREPLY=( $(compgen -W "text json csv xml" -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac
    
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}
complete -F _netcheck netcheck
COMPEOF

# Create control file
cat << CTRLEOF > "${BUILD_DIR}/DEBIAN/control"
Package: netcheck
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: bash (>= 4.0), telnet | netcat-openbsd | netcat-traditional
Maintainer: Your Name <your.email@example.com>
Description: Network connectivity checker with advanced features
 A powerful bash-based network connectivity testing tool that supports:
  - Parallel connection testing
  - IP range and CIDR notation
  - Port ranges and multiple ports
  - CSV file input
  - Multiple output formats (text, JSON, CSV, XML)
  - Quick test mode
  - Progress tracking
CTRLEOF

# Create postinst script
cat << 'POSTEOF' > "${BUILD_DIR}/DEBIAN/postinst"
#!/bin/bash
set -e
if command -v mandb > /dev/null 2>&1; then
    mandb -q 2>/dev/null || true
fi
echo "netcheck installed successfully! Run 'netcheck --help' to get started."
exit 0
POSTEOF
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# Build package
dpkg-deb --build "${BUILD_DIR}"

echo ""
echo "✅ Package created: ${BUILD_DIR}.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i ${BUILD_DIR}.deb"
echo ""
echo "To test:"
echo "  dpkg-deb --info ${BUILD_DIR}.deb"
echo "  dpkg-deb --contents ${BUILD_DIR}.deb"
echo ""
```

Make it executable and run:
```bash
chmod +x build-deb.sh
./build-deb.sh
```

## Summary

Creating a DEB package:
1. ✅ Create proper directory structure
2. ✅ Write DEBIAN/control metadata
3. ✅ Add post-install/pre-remove scripts
4. ✅ Build with `dpkg-deb --build`
5. ✅ Test locally with `sudo dpkg -i`
6. ✅ Publish to PPA or custom repository

Next: See SNAP_GUIDE.md for Snap package creation!
