# Release Notes — NetCheck v2.2.0

**Release Date:** 2026-06-28
**Type:** Feature — Tier 3 Diagnostics & Advanced CLI Engine

---

## Overview

v2.2.0 is a major feature update that introduces Tier 3 diagnostics (traceroute, port scan, and WHOIS/RDAP lookup), advanced SSL connection details (TLS version, cipher suite, SHA-256 fingerprint), expanded HTTP checking parameters, watch loop mode, global runtime overrides, and native shell completion support for Snap packages. 

Furthermore, this release includes a premium **Local Listening Ports & Services** dashboard integrated directly into the `interfaces` subcommand, displaying active listening sockets, identifying PIDs/processes, and automatically mapping them to Docker container names.

---

## What's New

### 1. Tier 3 Diagnostics Modules
- **`traceroute <host>`**: Identifies the network path to a target host hop-by-hop. Uses native raw ICMP sockets when run with elevated privileges, falling back automatically to standard system utilities (`traceroute`, `tracepath`, or Windows `tracert`).
- **`scan <host> [options]`**: Runs a high-concurrency TCP port scanner to map open ports and identify running services using an integrated services registry.
- **`whois <target>`**: Queries domain and IP registration information using modern RDAP JSON APIs, falling back to classic port 43 WHOIS lookups when needed.

### 2. Local Listening Ports & Services (with Docker Integration)
- The **`interfaces`** command (or `-ip` / `--my-ip`) now automatically detects local listening TCP sockets.
- Displays local address, port, and process name/PID.
- Resolves process names to active **Docker container names** (e.g. `Docker: <container-name>`) by querying Docker's port-forwarding configuration.
- Falls back to well-known service descriptions for system/hidden services when running without root privileges.

### 3. Advanced HTTP & SSL parameters
- **Custom HTTP Execution**: Subcommand `http` supports `-X/--method` (GET, HEAD, POST, PUT, DELETE, PATCH), `-H/--header` (custom request headers), and `--auth` (Basic Authentication `user:pass`).
- **SSL Security Details**: Subcommand `ssl` now queries and prints connection security details, including the negotiated TLS version, cipher suite, and certificate SHA-256 fingerprint.

### 4. Structured Machine-Readable Output for CI/CD (all formats)
- `ports`, `scan`, `traceroute`, and `whois` subcommands now emit **fully-typed structured records** when `-f json`, `-f csv`, or `-f xml` is requested — previously these fell through to the generic TCP batch format.
- **JSON**: type-tagged root objects (`"type": "scan"`, `"check_type": "whois"`), with typed arrays (`open_ports[]`, `hops[]`, `listening_ports[]`).
- **CSV**: per-type column headers (e.g. `Hop,IP,Hostname,Latency_MS` for traceroute; `Proto,Address,Port,Process,PID` for ports).
- **XML**: per-type root elements (`<port_scan>`, `<traceroute>`, `<listening_ports>`, `<whois_lookup>`).
- Makes `netcheck` a fully CI/CD-ready tool: pipe JSON output directly into `jq`, `python -c`, or GitHub Actions steps.

### 5. Watch Loop Mode
- Any subcommand can be watched continuously by appending `-w` or `--watch`. The terminal screen clears and refreshes at a polling rate configured by `-i` or `--interval` (defaults to 2 seconds).

### 5. Native Snap Completions
- The Snap package configuration now declares shell completion files natively via Snapcraft's `completer` property, enabling tab completion for `netcheck` subcommands and flags out-of-the-box.

---

## Breaking Changes

None. All legacy CLI flags and subcommands remain fully backward-compatible.

---

## Files Added / Changed

| File | Change |
|---|---|
| `netcheck/modules/interfaces.py` | **Modified** — Added listening socket parser, Docker API mapping, and `--all` interface filtering |
| `netcheck/utils/formatters.py` | **Modified** — Added formatted local listening ports table, plus JSON/CSV/XML branches for `ports`, `scan`, `traceroute`, `whois` result types |
| `packaging/snap/snapcraft.yaml` | **Modified** — Added native shell completer registration |
| `tests/test_netcheck.py` | **Modified** — Added `TestFormatterTier3` (12 new tests); total suite: **60 tests** |
| `docs/releases/RELEASE_NOTES_V2.2.0.md` | **New** — Release notes for v2.2.0 |
| `docs/examples.md` | **Modified** — Added documentation and examples for Tier 3 commands and listening ports |
| `CHANGELOG.md` | **Modified** — Added comparison link and final details for v2.2.0 |

---

## Release Artefacts

| Artefact | Platform |
|---|---|
| `netcheckx-2.2.0-py3-none-any.whl` | PyPI / All platforms |
| `netcheckx-2.2.0.tar.gz` | Source distribution (PyPI) |
| `netcheck_2.2.0_amd64.deb` | Debian / Ubuntu |
| `netcheck_2.2.0_amd64.snap` | All Linux (Snap Store) |
| `netcheck-2.2.0-setup.exe` | Windows NSIS Installer |
| `netcheck-2.2.0.nupkg` | Windows Chocolatey |

---

## Upgrade Guide

### Pip Install
```bash
pip install --upgrade netcheckx
```

### Snap Package (Linux)
```bash
sudo snap refresh netcheck
```

### Debian Package (.deb)
```bash
sudo dpkg -i netcheck_2.2.0_amd64.deb
```

---

## Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for the complete history.
