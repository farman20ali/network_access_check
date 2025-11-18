# Changelog

All notable changes to netcheck will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.2.0]: https://github.com/farman20ali/network_access_check/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/farman20ali/network_access_check/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/farman20ali/network_access_check/releases/tag/v1.0.0
