# Universal Snap Packaging with `build_packages.py` (v2.3.0)

## Overview

**Snap** is a universal Linux package format that runs securely across Ubuntu, Debian, Fedora, Arch, and other distributions. Snaps are containerised, self-contained, sandboxed, and receive automatic background updates from the Snap Store.

The `netcheck` build system automates Snap package creation using the `build_packages.py` builder and `publish_packages.py` publisher.

---

## The Build Process

When you run `python build_packages.py --snap`, the package orchestrator performs the following actions:

1. **Prerequisite Check**: Validates that `snapcraft` is installed on your host system.
2. **Template Expansion**:
   - Reads the template file `packaging/snap/snapcraft.yaml`.
   - Replaces the version placeholder `{version}` with the target synchronized package version (e.g. `2.3.0`).
   - Writes the rendered file to a temporary building folder (`snap/snapcraft.yaml`).
3. **Asset Migration**: Copies Snap icon assets from `packaging/snap/gui/` to the build workspace (`snap/gui/`).
4. **Execution**: Runs `snapcraft pack --destructive-mode` to compile the snap directly on the host machine without needing container virtualization (LXD/Multipass).
5. **Clean up**: Removes intermediate build paths (`stage/`, `prime/`, `parts/`, `snap/`) and relocates the finished `.snap` artifact to `dist/snap/`.

---

## Confinement & Interface Plugs

`netcheck` is packaged under `strict` confinement for maximum user safety. Because raw socket access (needed for ICMP ping tests), interface sniffing (needed for network interface discovery), and socket querying (needed for listing listening ports) are restricted by standard sandboxing, `netcheck` requests specific interface plugs:

```yaml
apps:
  netcheck:
    command: bin/netcheck
    plugs:
      - network            # Allow TCP/UDP client connections
      - network-bind       # Allow binding ports (for MCP server/port checks)
      - network-observe    # Required for ICMP ping and network interface enumeration
      - system-observe     # Required for local listening ports process-mapping
      - home               # Allow reading target files from users' homes
```

### Critical Post-Installation Steps
Because `network-observe` and `system-observe` are privileged interfaces, Snapd will not connect them automatically upon install. Users must connect them manually via:
```bash
sudo snap connect netcheck:network-observe
sudo snap connect netcheck:system-observe
```
*Note: Without these connections, TCP port checks, DNS resolution, HTTP status checks, and SSL validation will work normally, but ICMP ping and port process mapping will return permission/socket errors.*

---

## Building the Snap

### Prerequisites
Install the Snapcraft compiler on your build system:
```bash
sudo snap install snapcraft --classic
```

### Run Builder
```bash
python build_packages.py --snap
```
**Output**: The compiled snap package will be copied to `dist/snap/netcheck_2.3.0_amd64.snap` (or the respective architecture of your host).

---

## Local Verification & Testing

Install the compiled snap locally in developer mode:
```bash
# Install package locally
sudo snap install dist/snap/netcheck_2.3.0_amd64.snap --dangerous

# Manually connect security plugs
sudo snap connect netcheck:network-observe
sudo snap connect netcheck:system-observe

# Test CLI commands
netcheck interfaces --public
netcheck ping 8.8.8.8
```

To uninstall:
```bash
sudo snap remove netcheck
```

---

## Publishing to the Snap Store

Publishing is automated using `publish_packages.py`:

### Step 1: Login to Snapcraft
Register or sign in to your developer profile at https://snapcraft.io/ and log in from your terminal:
```bash
snapcraft login
```

### Step 2: Register Application Name (One-time)
If you are publishing this application for the first time:
```bash
snapcraft register netcheck
```

### Step 3: Run Publisher
Uploads the newest compiled `.snap` file to the stable channel:
```bash
python publish_packages.py --snap
```

To test releases in a pre-release channel first (e.g. edge or beta):
```bash
python publish_packages.py --snap --channel edge
```
Users can install the edge variant using:
```bash
sudo snap install netcheck --channel=edge
```
