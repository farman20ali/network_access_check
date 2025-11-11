# Publishing as Snap Package

## Overview

**Snap** is a universal Linux package format that works across Ubuntu, Debian, Fedora, Arch, and other distributions. Snaps are containerized, self-contained, and automatically updated.

## Benefits of Snap

- ✅ **Universal**: One package for all Linux distributions
- ✅ **Auto-updates**: Users get updates automatically
- ✅ **Secure**: Sandboxed with confined permissions
- ✅ **Dependencies**: All dependencies bundled
- ✅ **Easy Publishing**: Snap Store handles distribution

## Prerequisites

```bash
# Install snapd (if not already installed)
sudo apt install snapd

# Install snapcraft (build tool)
sudo snap install snapcraft --classic

# Login to Snap Store (create account at https://snapcraft.io)
snapcraft login
```

## Directory Structure

```
netcheck/
├── snap/
│   └── snapcraft.yaml   # Snap configuration
├── check_ip.sh          # Your script
├── README.md
└── other files...
```

## Step-by-Step Guide

### 1. Create snapcraft.yaml

```bash
# Create snap directory
mkdir -p snap

# Create snapcraft.yaml
cat << 'EOF' > snap/snapcraft.yaml
name: netcheck
version: '1.0.0'
summary: Network connectivity checker with advanced features
description: |
  A powerful bash-based network connectivity testing tool that supports:
  
  - Parallel connection testing (up to 256 concurrent jobs)
  - IP range support (192.168.1.1-50)
  - CIDR notation (10.0.0.0/24)
  - Port ranges (8000-8100) and multiple ports (80,443,3306)
  - CSV file input for bulk testing
  - Multiple output formats (text, JSON, CSV, XML)
  - Quick test mode for one-off checks
  - Real-time progress tracking
  - Combined reports for failed connections
  
  Perfect for:
  - System administrators monitoring infrastructure
  - DevOps engineers validating deployments
  - Network diagnostics and troubleshooting
  - Security auditing and port scanning
  - Load balancer health checks

grade: stable  # or 'devel' for unstable releases
confinement: strict  # or 'devmode' for development, 'classic' for full system access

base: core22  # Ubuntu 22.04 LTS base

architectures:
  - build-on: amd64
  - build-on: arm64
  - build-on: armhf

apps:
  netcheck:
    command: bin/netcheck
    plugs:
      - network
      - network-bind
      - home
    environment:
      LC_ALL: C.UTF-8

parts:
  netcheck:
    plugin: dump
    source: .
    source-type: local
    organize:
      check_ip.sh: bin/netcheck
    stage:
      - bin/netcheck
      - README.md
      - EXAMPLES.md
    override-build: |
      craftctl default
      chmod +x $CRAFT_PART_INSTALL/bin/netcheck
    stage-packages:
      - telnet
      - netcat-openbsd
      - coreutils
      - grep
      - sed
EOF
```

### 2. Configuration Explained

#### Metadata Section:
```yaml
name: netcheck                    # Package name (must be unique in Snap Store)
version: '1.0.0'                  # Version string
summary: Short one-line description  # Max 78 characters
description: |                    # Detailed multi-line description
  Longer description here...
```

#### Build Settings:
```yaml
grade: stable                     # stable = production, devel = testing
confinement: strict              # strict = sandboxed, classic = full access
base: core22                     # Ubuntu 22.04 base system
```

#### Application Definition:
```yaml
apps:
  netcheck:                       # Command name
    command: bin/netcheck         # Path to executable
    plugs:                        # Permissions needed
      - network                   # Network access
      - network-bind             # Bind to ports
      - home                     # Access user's home directory
```

#### Build Configuration:
```yaml
parts:
  netcheck:
    plugin: dump                  # Simple file copy
    source: .                     # Current directory
    organize:                     # Rename files
      check_ip.sh: bin/netcheck
    stage-packages:               # Dependencies to bundle
      - telnet
      - netcat-openbsd
```

### 3. Confinement Levels Explained

**Strict Confinement** (Recommended):
```yaml
confinement: strict
apps:
  netcheck:
    plugs:
      - network          # Can access network
      - home            # Can read/write user's home
      - network-bind    # Can listen on ports
```

**Classic Confinement** (Full System Access):
```yaml
confinement: classic
# No restrictions, like traditional packages
# Requires manual approval from Snap Store
```

**Devmode** (Development Only):
```yaml
confinement: devmode
# For testing, not allowed in Snap Store
```

### 4. Build the Snap

```bash
# Build locally
snapcraft

# This creates: netcheck_1.0.0_amd64.snap
```

### 5. Test Locally

```bash
# Install in devmode (for testing)
sudo snap install netcheck_1.0.0_amd64.snap --devmode --dangerous

# Test the command
netcheck --help
netcheck -q google.com 443
netcheck --csv hosts.csv

# Check snap info
snap info netcheck
snap list netcheck

# View logs
snap logs netcheck

# Uninstall
sudo snap remove netcheck
```

### 6. Publish to Snap Store

```bash
# Login (if not already)
snapcraft login

# Upload to Snap Store
snapcraft upload netcheck_1.0.0_amd64.snap

# Release to a channel
snapcraft release netcheck 1 stable
# Channels: stable, candidate, beta, edge

# Check status
snapcraft status netcheck
```

### 7. Users Install From Store

```bash
# Install from Snap Store
sudo snap install netcheck

# Auto-updates enabled by default!

# Update manually
sudo snap refresh netcheck

# Uninstall
sudo snap remove netcheck
```

## Advanced snapcraft.yaml Features

### Multiple Commands:
```yaml
apps:
  netcheck:
    command: bin/netcheck
    plugs: [network, home]
  
  netcheck-daemon:
    command: bin/netcheck-daemon
    daemon: simple
    plugs: [network, network-bind]
```

### Configuration Options:
```yaml
apps:
  netcheck:
    command: bin/netcheck
    plugs: [network, home]
    environment:
      NETCHECK_TIMEOUT: 5
      NETCHECK_JOBS: 10
```

### Build from Git:
```yaml
parts:
  netcheck:
    plugin: dump
    source: https://github.com/yourusername/netcheck.git
    source-type: git
    source-branch: main
```

### Custom Build Commands:
```yaml
parts:
  netcheck:
    plugin: dump
    source: .
    override-build: |
      craftctl default
      # Custom build steps
      chmod +x $CRAFT_PART_INSTALL/bin/netcheck
      mkdir -p $CRAFT_PART_INSTALL/share/doc
      cp README.md $CRAFT_PART_INSTALL/share/doc/
```

## Available Plugs (Permissions)

Common plugs for network tools:
```yaml
plugs:
  - network              # Network access (outgoing)
  - network-bind         # Listen on ports
  - home                 # Access home directory
  - removable-media      # Access USB drives
  - mount-observe        # Read /proc/mounts
  - system-observe       # Read system info
  - network-observe      # Read network info (/proc/net)
  - process-control      # Send signals to processes
  - hardware-observe     # Read hardware info
```

## Release Channels

Snap Store has 4 channels:
- **stable**: Production releases (default for users)
- **candidate**: Release candidates (pre-release testing)
- **beta**: Beta releases (early adopters)
- **edge**: Development builds (bleeding edge)

```bash
# Release to different channels
snapcraft upload netcheck_1.0.0_amd64.snap
snapcraft release netcheck 1 stable
snapcraft release netcheck 1 beta

# Users can choose channel
sudo snap install netcheck --channel=beta
```

## Complete Build Script

Save as `build-snap.sh`:

```bash
#!/bin/bash
set -e

echo "Building Snap package for netcheck..."

# Check if snapcraft is installed
if ! command -v snapcraft &> /dev/null; then
    echo "Error: snapcraft is not installed"
    echo "Install with: sudo snap install snapcraft --classic"
    exit 1
fi

# Clean previous builds
snapcraft clean
rm -f *.snap

# Build the snap
echo "Building snap package..."
snapcraft --verbose

# Get the snap filename
SNAP_FILE=$(ls netcheck_*.snap | head -1)

if [ -f "$SNAP_FILE" ]; then
    echo ""
    echo "✅ Snap package created: $SNAP_FILE"
    echo ""
    echo "To test locally:"
    echo "  sudo snap install $SNAP_FILE --devmode --dangerous"
    echo "  netcheck --help"
    echo ""
    echo "To publish to Snap Store:"
    echo "  snapcraft login"
    echo "  snapcraft upload $SNAP_FILE"
    echo "  snapcraft release netcheck <revision> stable"
    echo ""
    echo "Package info:"
    snap info --verbose "$SNAP_FILE" || true
else
    echo "❌ Build failed - no snap package found"
    exit 1
fi
```

## Debugging Snap Issues

```bash
# Run in devmode (no confinement)
sudo snap install netcheck_1.0.0_amd64.snap --devmode --dangerous

# Check logs
snap logs netcheck
snap logs netcheck -f  # Follow logs

# Check interfaces
snap connections netcheck

# Shell into snap environment
sudo snap run --shell netcheck
echo $PATH
ls /snap/netcheck/current/

# Check confinement
snap list netcheck  # Shows devmode/strict/classic
```

## Publishing Checklist

- [ ] Create snapcraft.io account
- [ ] Register app name: `snapcraft register netcheck`
- [ ] Test locally with `--devmode --dangerous`
- [ ] Test all features work in strict confinement
- [ ] Update version in snapcraft.yaml
- [ ] Build: `snapcraft`
- [ ] Upload: `snapcraft upload netcheck_x.x.x.snap`
- [ ] Release: `snapcraft release netcheck <rev> stable`
- [ ] Test install from store: `snap install netcheck`
- [ ] Update README with snap install instructions

## Automatic Builds (CI/CD)

Use GitHub Actions to auto-build:

```yaml
# .github/workflows/snap.yml
name: Build Snap

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: snapcore/action-build@v1
      - uses: snapcore/action-publish@v1
        with:
          snap: netcheck_*.snap
          release: stable
        env:
          SNAPCRAFT_STORE_CREDENTIALS: ${{ secrets.SNAP_TOKEN }}
```

## Resources

- **Snap Store**: https://snapcraft.io/
- **Documentation**: https://snapcraft.io/docs
- **Forum**: https://forum.snapcraft.io/
- **Dashboard**: https://dashboard.snapcraft.io/

## Summary

Creating and publishing a Snap:

1. ✅ Create `snap/snapcraft.yaml`
2. ✅ Configure confinement and plugs
3. ✅ Build with `snapcraft`
4. ✅ Test locally
5. ✅ Login to Snap Store
6. ✅ Upload and release
7. ✅ Users get auto-updates!

**Snap vs DEB:**
- **Snap**: Universal, auto-updates, sandboxed (modern)
- **DEB**: Traditional, manual updates, distribution-specific

Recommend publishing **both** for maximum reach!
