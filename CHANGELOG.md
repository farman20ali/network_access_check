# Changelog

All notable changes to netcheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-06-21

### Added
- **`packaging/` directory** — all platform-specific templates live in one place:
  - `packaging/snap/snapcraft.yaml` — Snap template with `{version}` placeholder
  - `packaging/linux/install.sh` / `uninstall.sh` — installer scripts
  - `packaging/windows/netcheck.nsi` — NSIS installer template
  - `packaging/chocolatey/` — Chocolatey `.nuspec` + install script
  - `packaging/macos/scripts/` — placeholder for macOS PKG scripts
- **`--sync-version VERSION`** flag in `build_packages.py` — propagates a new version to `__init__.py`, `pyproject.toml`, `netcheck/mcp/server.py`, and `packaging/snap/snapcraft.yaml` in one command.
- **`netcheck/__main__.py`** — standard `python3 -m netcheck` entry point.
- **CI workflow** (`.github/workflows/ci.yml`) — matrix tests across Python 3.8–3.12 on Ubuntu, macOS, Windows.
- **Comprehensive CLI test suite** (`tests/test_cli.py`) — 15 tests covering all subcommands and flags.
- **Snap packaging overhaul** (`packaging/snap/snapcraft.yaml`):
  - Moved Snap icon to `packaging/snap/gui/icon.png` (copied to `snap/gui/` at build time by `build_packages.py`).
  - Re-added multi-architecture builds: `amd64`, `arm64`, `armhf`.
  - Switched plugin from `dump` (bash) to `python` (pure Python 3); only `iputils-ping` needed as a stage-package.
  - Added `PYTHONPATH` environment variable so the snap runtime resolves installed site-packages correctly.
  - Expanded Snap Store description to reflect all v2.x features: subcommand CLI, MCP server, structured output, lenient target parsing, build orchestration, and the `sudo snap connect` instruction.
- **Icon & asset management** (`assets/icons/`):
  - `assets/icons/icon.png` — 512×512 master PNG (source of truth for all icon variants).
  - `assets/icons/icon.ico` — 256×256 Windows ICO (used for `.exe`, NSIS installer, and Add/Remove Programs entry).
  - `packaging/snap/gui/icon.png` — 512×512 PNG for Snap Store listing.
  - `packaging/windows/netcheck.nsi` — wired `Icon`, `UninstallIcon`, and `DisplayIcon` registry key to `assets/icons/icon.ico`.
  - `packaging/chocolatey/netcheck.nuspec` — added `<iconUrl>` pointing to the raw master PNG on GitHub.
  - `build_packages.py` — `--win` target now passes `--icon assets/icons/icon.ico` to PyInstaller; `--snap` copies `packaging/snap/gui/` → `snap/gui/` before `snapcraft` runs.

### Changed
- `build_packages.py` refactored to render templates from `packaging/` instead of embedding inline script strings.
- `build_snap()` now auto-cleans `snap/`, `stage/`, `prime/`, `parts/` artefact directories from the repo root after each build.
- `Makefile` `install`/`uninstall` targets updated to point to `packaging/linux/`.
- `README.md` fully rewritten to reflect Python-native packaging, all install options, and build commands.

### Removed
- `build-deb.sh`, `build-snap.sh` — superseded by `build_packages.py`.
- `check_ip.py`, `check_ip.sh` — legacy wrappers deleted.
- `PYTHON_README.md` — stub file removed; `README.md` is now the single source of truth.
- Root-level `install.sh`, `uninstall.sh`, `snap/` — moved to `packaging/linux/` and `packaging/snap/`.

## [2.0.0] - 2026-06-06


### Added
- **Complete Pure Python 3 Rewrite**:
  - Eliminated legacy Bash scripts and subprocess dependencies in core checking logic.
  - Native cross-platform execution (Linux, macOS, Windows).
  - High-performance, concurrent connectivity checking powered by Python's `concurrent.futures`.
- **Model Context Protocol (MCP) Server**:
  - Built-in MCP integration (run with `netcheck --mcp` or `python3 -m netcheck.mcp.server`).
  - Exposes network diagnostic tools (`dns_lookup`, `ping_host`, `check_tcp_port`, `check_http_status`, `check_ssl_certificate`, and `list_interfaces`) to AI assistants.
- **Lenient Target Parsing & Normalizer**:
  - Input lines are parsed flexibly, extracting hosts and ports from colon-separated lists, comma-separated lists, bracketed IPv6 addresses, and raw URLs (automatically stripping schemes, paths, and slashes).
  - Handles inline comments (`#`), IP ranges, CIDR subnets, and port ranges seamlessly.
- **Advanced Subcommands**:
  - Introduced CLI subcommands (`tcp`, `dns`, `http`, `ssl`, `ping`, `interfaces`) for direct usage, while maintaining full backward-compatible legacy flags (`-q`, `-d`, `-p`, `-s`, `--cert`, `--my-ip`).
- **Robust SSL & Fallback Engine**:
  - Sequential IP attempt loop across all resolved DNS records (IPv4 & IPv6).
  - Custom `cryptography` fallback parsing to fetch certificates details (subject, issuer, dates, SANs) even when validation fails strictly.
- **Color-Coded Output Alignments**:
  - Strips ANSI escape codes dynamically to maintain box alignment and layout padding in terminal outputs.
  - Safe, color-free logging when saving outputs to date-based result files (`result-*.txt`, `fail-*.txt`, `combined-*.txt`).

### Changed
- Promoted standard library network calls over external CLI binary dependency wrapping.
- Switched default output formatting to colored CLI panels with clean fallbacks.
- Updated versioning configuration in `pyproject.toml`.

## [1.2.0] - 2025-01-18

### Added
- **Network Interface Display** (`--my-ip`, `-ip`)
  - Show all network interfaces with IPv4/IPv6 addresses
  - Display interface status (UP/DOWN), gateway, and public IP
  - Default shows only active (UP) interfaces
  - `--my-ip --all` flag shows all interfaces including inactive ones
  - Sorted output with filtered loopback and virtual ethernet pairs

- **HTTP Status Checking** (`-s`, `--status`)
  - Check HTTP/HTTPS response codes with curl
  - Display response time in milliseconds
  - Show content size in human-readable format (bytes, KB, MB)
  - Categorize status codes (2xx success, 3xx redirect, 4xx client error, 5xx server error)
  - Verbose mode shows response headers
  - Comprehensive error messages for connection failures

- **SSL Certificate Validation** (`--cert`)
  - Check SSL/TLS certificate validity and expiration
  - Display certificate subject, issuer, and validity dates
  - Calculate days until expiry
  - Warn if certificate expires within 30 days (yellow) or 7 days (red)
  - Verbose mode shows Subject Alternative Names (SANs)
  - Support for URL or hostname:port format

- **Retry Logic** (`--retry`, `--retry-delay`)
  - Retry failed connections with configurable count (default: 1, no retry)
  - Configurable delay between retries in seconds (default: 1)
  - Works with both file mode and quick mode
  - Verbose mode shows retry attempts
  - Helps with intermittent connection issues

### Changed
- Updated help text with all new flags and options
- Improved error messages and user guidance
- Enhanced documentation with v1.2.0 examples

### Dependencies
- Added `curl` for HTTP status checks
- Added `openssl` for SSL certificate validation
- Added `bc` for time calculations
- Added `iproute2` for network interface display

## [1.1.0] - 2024-11-18

### Added
- **ICMP Ping Testing** (`-p`, `--ping`)
  - Ping hosts using ICMP with 4 packets
  - Accept URLs (automatically strips scheme/path)
  - Show detailed statistics
  
- **DNS Lookup** (`-d`, `--dns`)
  - Resolve hostnames to IP addresses
  - Multiple fallback methods (host, getent, dig, nslookup)
  - Accept URLs (automatically extracts hostname)
  - Show IPv4, IPv6, aliases, and reverse DNS

- **Quick Mode Enhancements**
  - Automatic parallel processing for >5 tests
  - Output file support with `-o/--output` flag
  - IP range support (192.168.1.1-50)
  - Streaming results as they complete

- **Input Validation**
  - Comprehensive validation for host and port formats
  - Inline comment removal (supports # comments)
  - Graceful handling of malformed input
  - Helpful warnings for invalid entries
  - Protection against script hanging

- **Dated Result Files**
  - Automatic timestamped output files (result-YYYY-MM-DD.txt)
  - Dated failure reports (fail-YYYY-MM-DD.txt)
  - Easier tracking of test history

### Changed
- Version information with `-v/--version` flag
- Improved snap packaging with proper permissions
- Updated documentation with all new features

### Fixed
- DNS lookup hanging on malformed URLs
- Script hanging on invalid input
- Missing ping statistics in output

## [1.0.0] - 2024-10-15

### Added
- Initial release
- Parallel TCP port connectivity testing
- IP range support (192.168.1.1-50)
- CIDR notation support (10.0.0.0/24)
- Port ranges (8000-8100) and multiple ports (80,443,8080)
- CSV file input support
- Multiple output formats (text, JSON, CSV, XML)
- Quick test mode for one-off checks
- Real-time progress bar
- Response time measurement
- Combined reports
- Man page and bash completion
- Multi-OS support (Ubuntu, Debian, CentOS, Fedora, Arch, openSUSE)
- Three installation methods (manual, DEB, Snap)

[2.1.0]: https://github.com/farman20ali/network_access_check/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/farman20ali/network_access_check/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/farman20ali/network_access_check/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/farman20ali/network_access_check/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/farman20ali/network_access_check/releases/tag/v1.0.0
