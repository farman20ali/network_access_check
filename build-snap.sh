#!/bin/bash
set -e

echo "=========================================="
echo "Building Snap Package for netcheck"
echo "=========================================="
echo ""

# Check if snapcraft is installed
if ! command -v snapcraft &> /dev/null; then
    echo "❌ Error: snapcraft is not installed"
    echo ""
    echo "Install with:"
    echo "  sudo snap install snapcraft --classic"
    echo ""
    exit 1
fi

# Check if snap directory exists
if [ ! -d "snap" ]; then
    echo "Creating snap directory..."
    mkdir -p snap
fi

# Create snapcraft.yaml if it doesn't exist
if [ ! -f "snap/snapcraft.yaml" ]; then
    echo "Creating snapcraft.yaml..."
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

grade: stable
confinement: strict

base: core22

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
      - INSTALL.md
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
    echo "✅ snapcraft.yaml created"
fi

# Clean previous builds
echo "Cleaning previous builds..."
snapcraft clean 2>/dev/null || true
rm -f *.snap 2>/dev/null || true

# Build the snap
echo ""
echo "Building snap package (this may take a few minutes)..."
echo ""
snapcraft --verbose

# Get the snap filename
SNAP_FILE=$(ls netcheck_*.snap 2>/dev/null | head -1)

if [ -f "$SNAP_FILE" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Snap package created: $SNAP_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Package info:"
    ls -lh "$SNAP_FILE"
    echo ""
    
    # Show snap info if possible
    if snap info --verbose "$SNAP_FILE" 2>/dev/null; then
        :
    else
        echo "To view package info:"
        echo "  snap info --verbose $SNAP_FILE"
    fi
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing Instructions:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Install locally (devmode for testing):"
    echo "   sudo snap install $SNAP_FILE --devmode --dangerous"
    echo ""
    echo "2. Test the command:"
    echo "   netcheck --help"
    echo "   netcheck -q google.com 443"
    echo "   netcheck --csv hosts.csv"
    echo ""
    echo "3. Check logs if issues:"
    echo "   snap logs netcheck"
    echo "   snap logs netcheck -f  # Follow logs"
    echo ""
    echo "4. Uninstall:"
    echo "   sudo snap remove netcheck"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Publishing Instructions:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Create Snap Store account:"
    echo "   https://snapcraft.io/"
    echo ""
    echo "2. Register app name (one-time):"
    echo "   snapcraft login"
    echo "   snapcraft register netcheck"
    echo ""
    echo "3. Upload package:"
    echo "   snapcraft upload $SNAP_FILE"
    echo ""
    echo "4. Release to stable channel:"
    echo "   snapcraft release netcheck <revision> stable"
    echo ""
    echo "5. Check status:"
    echo "   snapcraft status netcheck"
    echo ""
    echo "6. Users install with:"
    echo "   sudo snap install netcheck"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Build failed - no snap package found"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Check the build output above for errors."
    echo ""
    echo "Common issues:"
    echo "  - Missing check_ip.sh file"
    echo "  - Snapcraft not installed properly"
    echo "  - Insufficient disk space"
    echo "  - Network issues downloading base snap"
    echo ""
    exit 1
fi
