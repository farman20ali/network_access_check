# Network Connectivity Checker (netcheck)

A powerful, feature-rich command-line tool for testing network connectivity to multiple hosts and ports with parallel processing, multiple output formats, and automatic dependency management.

## Features

- ✅ **Parallel Processing** - Check multiple hosts simultaneously (up to 256 jobs)
- ✅ **Multiple Output Formats** - Text, JSON, CSV, XML
- ✅ **Quick Test Mode** - Test single host without creating files
- ✅ **IP Range Support** - Check IP ranges (192.168.1.1-50) and CIDR (10.0.0.0/24)
- ✅ **Port Ranges** - Check port ranges (8000-8100) or multiple ports (80,443,8080)
- ✅ **CSV File Support** - Read from CSV files (host,port format)
- ✅ **DNS Lookup** - Resolve hostnames to IP addresses with reverse DNS
- ✅ **Progress Bar** - Real-time progress tracking
- ✅ **Response Time Measurement** - See connection latency in milliseconds
- ✅ **Version Information** - Check tool version with -v flag
- ✅ **Input Validation** - Prevents hanging with helpful error messages
- ✅ **Automatic Dependency Installation** - Installs telnet and netcat if missing
- ✅ **Flexible Input** - File, stdin, or quick test mode
- ✅ **Man Page & Tab Completion** - Full documentation and bash completion
- ✅ **Multi-OS Support** - Ubuntu, Debian, CentOS, Fedora, Arch, openSUSE

## Installation

### Option 1: From Snap Store (Recommended - Works on ALL Linux!)

```bash
sudo snap install netcheck
```

**Benefits:** Auto-updates, universal Linux support, sandboxed security

### Option 2: DEB Package (Ubuntu/Debian)

```bash
# Build the package
./build-deb.sh

# Install
sudo dpkg -i netcheck_1.0.0.deb
```

### Option 3: Manual System-wide Installation

```bash
# Using Makefile (recommended)
sudo make install

# Or directly
sudo ./install.sh
```

This will:
- Install the command as `netcheck` in `/usr/local/bin`
- Automatically detect your OS and install dependencies (telnet, netcat)
- Create a man page (`man netcheck`)
- Add bash tab completion
- Works on: Ubuntu, Debian, CentOS, RHEL, Fedora, Arch, openSUSE

### Option 4: Local Installation (No sudo)

```bash
chmod +x check_ip.sh
# Run directly: ./check_ip.sh
```

**See:** [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) for package publishing details

## Quick Start

### Quick Test (Single Host)

```bash
# Test a single host - no files created, instant results
netcheck -q google.com 443
netcheck -q 192.168.1.1 80
netcheck -q localhost 3306

# Test multiple ports at once
netcheck -q server.com 80,443,8080
netcheck -q localhost 80,443

# Test port range
netcheck -q localhost 8000-8100
netcheck -q server.com 9000-9010

# NEW: Test IP range (multiple hosts)
netcheck -q 10.90.95.72-75 50000
netcheck -q 192.168.1.1-10 22
```

### DNS Lookup

```bash
# Resolve hostname to IP addresses
netcheck -d google.com
netcheck -d github.com
netcheck -d example.com
```

Output:
```
DNS Lookup for: google.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hostname: google.com

IP Addresses:
  142.250.202.78
  2a00:1450:4019:812::200e (IPv6)

Aliases:

Reverse DNS:
  pnfjra-an-in-f14.1e100.net.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Version Information

```bash
# Check netcheck version
netcheck -v
netcheck --version
```

Output:
```
Quick Test Mode
Host: localhost
Port(s): 80,443
Timeout: 5s

Testing 2 port(s)...

┌─────────────────────────────────────────────┐
│ Host: localhost                             │
│ Port: 80                                    │
├─────────────────────────────────────────────┤
│ Status: ✓ CONNECTED                         │
│ Method: netcat                              │
│ Response Time: 1ms                          │
└─────────────────────────────────────────────┘

Quick Test Summary
════════════════════════════════════════════
Total Ports: 2
Successful:  1
Failed:      1
════════════════════════════════════════════
```

### CSV File Support

```bash
# Read from CSV file
netcheck --csv hosts.csv

# CSV from stdin
cat hosts.csv | netcheck --csv

# Piped CSV data
echo -e "host,port\ngoogle.com,443\nlocalhost,80" | netcheck --csv
```

**CSV Format:**
```csv
host,port
google.com,443
server.local,80
192.168.1.1,22
192.168.1.1-5,80
localhost,"80,443,8080"
10.0.0.0/24,22
```

**Features:**
- Automatic header detection and skipping
- Supports quoted fields for multiple ports
- Supports IP ranges in CSV: `192.168.1.1-50,80`
- Supports CIDR notation: `192.168.1.0/24,22`
- Supports multiple ports: `host,"80,443,8080"`

### Batch Testing

Create a file `hosts.txt`:
```
google.com 443
github.com 443
192.168.1.1 80
localhost 3306
8.8.8.8 53
```

Run the check:
```bash
netcheck hosts.txt
```

## Usage

```
netcheck [OPTIONS] [input_file]

OPTIONS:
    -t, --timeout <seconds>     Connection timeout (default: 5)
    -j, --jobs <number>         Max parallel jobs (default: 10)
    -V, --verbose               Verbose output
    -f, --format <format>       Output format: text, json, csv, xml (default: text)
    -c, --combined              Create combined report with all results
    -q, --quick <host> <port>   Quick test mode (no files created)
    -d, --dns <hostname>        Resolve DNS and show IP address
    -v, --version               Show version information
    -h, --help                  Show help message
```

## Examples

### Basic Usage
```bash
# Check hosts from file
netcheck hosts.txt

# From stdin
cat hosts.txt | netcheck

# Verbose mode
netcheck -V hosts.txt
echo "google.com 443" | netcheck -V
```

### DNS Resolution
```bash
# Lookup hostname
netcheck -d google.com
netcheck -d github.com

# Shows: IPv4, IPv6, aliases, reverse DNS
```

### Version Check
```bash
# Show netcheck version
netcheck -v
netcheck --version
```

### Fast Parallel Checking
```bash
# Check 20 hosts simultaneously with 2-second timeout
netcheck -t 2 -j 20 hosts.txt

# High-speed scanning with 100 parallel jobs
netcheck -j 100 -t 1 large-list.txt
```

### Different Output Formats

**JSON Output:**
```bash
netcheck -f json hosts.txt
```
Output: `result.txt`
```json
{"check_date":"2025-11-11 10:59:21","results":[
  {"status":"success","host":"google.com","port":443,"method":"netcat","timestamp":"2025-11-11 10:59:21"}
]}
```

**CSV Output:**
```bash
netcheck -f csv hosts.txt
```
Output: `result.txt`
```csv
Status,Host,Port,Method,Timestamp
"SUCCESS","google.com",443,"netcat","2025-11-11 11:00:05"
```

**XML Output:**
```bash
netcheck -f xml hosts.txt
```

### Combined Report
```bash
# Get all results (success + failures) in one file
netcheck -c hosts.txt
# Creates: combined-2025-11-11.txt
```

### Verbose Mode
```bash
# See detailed output for each host
netcheck -v hosts.txt
```

## Input Format

Each line should contain: `HOST PORT(S)`

```
# Basic format
192.168.1.1 80

# Multiple ports (comma-separated)
192.168.1.1 80,443,8080

# Port range
192.168.1.1 8000-8100

# IP range (last octet)
192.168.1.1-50 80

# CIDR notation (subnet)
192.168.1.0/24 80

# Combined: IP range + multiple ports
192.168.1.1-10 80,443,8080

# Comments are supported
# This is a comment
google.com 443
```

### Range Examples

**IP Ranges:**
- `192.168.1.1-50 80` - Checks 192.168.1.1 through 192.168.1.50 on port 80 (50 checks)
- `10.0.0.1-5 443` - Checks 5 IPs on port 443

**CIDR Notation:**
- `192.168.1.0/24 80` - Checks entire /24 subnet (254 hosts)
- `10.0.0.0/28 22` - Checks /28 subnet (14 usable hosts)
- Note: Network and broadcast addresses are skipped for /24 and smaller

**Multiple Ports:**
- `server.com 80,443,8080` - Checks 3 ports on same host
- `192.168.1.1 22,80,443,3306,8080` - Checks 5 ports

**Port Ranges:**
- `localhost 8000-8100` - Checks ports 8000 through 8100 (101 ports)
- `server.com 9000-9010` - Checks 11 ports
- Note: Port ranges >1000 ports are limited to first 1000

**Combined:**
- `192.168.1.1-10 80,443` - 10 IPs × 2 ports = 20 checks
- `10.0.0.0/28 22,80,443` - 14 IPs × 3 ports = 42 checks

## Output Files

- **result.txt** - Successful connections
- **fail-YYYY-MM-DD.txt** - Failed connections (dated)
- **combined-YYYY-MM-DD.txt** - All results (when using `-c` flag)

## Use in Scripts

```bash
#!/bin/bash

# Check if database is up
if netcheck -q db.example.com 3306 > /dev/null 2>&1; then
    echo "Database is online!"
else
    echo "Database is down!"
    exit 1
fi

# Batch check and parse JSON
netcheck -f json servers.txt
# Process result.txt with jq or other JSON tools
```

## Requirements

- Bash 4.0+
- telnet (auto-installed)
- netcat (auto-installed)
- timeout command (usually pre-installed)

## Troubleshooting

### Dependencies Not Installing Automatically

If automatic installation fails, install manually:

**Ubuntu/Debian:**
```bash
sudo apt install telnet netcat-openbsd
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install telnet nc
# or
sudo dnf install telnet nc
```

**Arch/Manjaro:**
```bash
sudo pacman -S inetutils openbsd-netcat
```

### Permission Denied

Make sure the script is executable:
```bash
chmod +x check_ip.sh
```

For system-wide installation, use sudo:
```bash
sudo ./install.sh
```

## Uninstallation

```bash
sudo ./uninstall.sh
```

This removes:
- `/usr/local/bin/netcheck`
- Man page
- Bash completion

Dependencies (telnet, netcat) are NOT removed.

## Documentation

View full manual:
```bash
man netcheck
```

## Advanced Examples

### Scan Entire Subnet
```bash
# Check SSH on entire /24 subnet
echo "192.168.1.0/24 22" | netcheck -j 50

# Check common web ports on subnet
echo "10.0.0.0/26 80,443,8080" | netcheck -f csv
```

### Port Scanning
```bash
# Scan port range on single host
echo "server.local 1-1024" | netcheck -j 100 > scan-results.txt

# Check common service ports
echo "192.168.1.1 22,80,443,3306,5432,6379,8080,9000" | netcheck
```

### Network Discovery
```bash
# Find active hosts in range
cat << EOF | netcheck -j 20
192.168.1.1-254 22
192.168.1.1-254 80
192.168.1.1-254 443
EOF
```

### Combined Scans
```bash
# Check multiple subnets with multiple ports
cat << EOF | netcheck -f json -c
192.168.1.0/24 80,443
192.168.2.0/24 80,443
10.0.0.0/24 22,3389
EOF
```

### Data Center Health Check
```bash
# Check web servers cluster
echo "web-{01..10}.prod.com 80,443" > servers.txt
# Expand in bash, then check
for i in {1..10}; do echo "web-$(printf %02d $i).prod.com 80,443"; done | netcheck -j 20
```
```bash
# Check every 5 minutes (add to crontab)
*/5 * * * * /usr/local/bin/netcheck /path/to/hosts.txt
```

### Export to Excel
```bash
# Generate CSV and open in Excel
netcheck -f csv hosts.txt
libreoffice result.txt
```

### JSON API Integration
```bash
# Check and POST results to monitoring API
netcheck -f json hosts.txt
curl -X POST https://api.monitor.com/results \
     -H "Content-Type: application/json" \
     -d @result.txt
```

### Quick Health Check Script
```bash
#!/bin/bash
# health-check.sh

CRITICAL_SERVICES=(
    "db.prod.com 3306"
    "api.prod.com 443"
    "cache.prod.com 6379"
)

for service in "${CRITICAL_SERVICES[@]}"; do
    if ! netcheck -q $service > /dev/null 2>&1; then
        echo "ALERT: $service is down!"
        # Send notification
    fi
done
```

## Documentation

- **[README.md](README.md)** - Main documentation (this file)
- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive examples and real-world scenarios
- **[INSTALL.md](INSTALL.md)** - Installation instructions
- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Understanding the Makefile
- **[DEB_PACKAGING.md](DEB_PACKAGING.md)** - How to create DEB packages
- **[SNAP_PACKAGING.md](SNAP_PACKAGING.md)** - How to create Snap packages
- **[PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md)** - Quick reference for publishing

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source. See LICENSE file for details.

## Author

Network Access Check Tool

## Support

- Report issues on GitHub
- Check man page: `man netcheck`
- See examples: [EXAMPLES.md](EXAMPLES.md)
        # Send alert email/SMS
    fi
done
```

## Contributing

Contributions welcome! Please test on your OS and submit pull requests.

## License

GNU General Public License v3 (GPL-3.0)

This project is licensed under GPL v3, which means:
- ✅ Free to use for any purpose
- ✅ Free to modify and improve
- ✅ Free to distribute
- ✅ Can be used commercially
- ⚠️ Any modifications must also be open source (copyleft)
- ⚠️ Cannot create proprietary closed-source versions

See [LICENSE](LICENSE) file for full details.

## Version

Version 1.0.0 - November 2025

Check version: `netcheck -v` or `netcheck --version`

## Documentation

- **[README.md](README.md)** - Main documentation (this file)
- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive examples and real-world scenarios
- **[INSTALL.md](INSTALL.md)** - Installation instructions
- **[MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)** - Understanding the Makefile
- **[DEB_PACKAGING.md](DEB_PACKAGING.md)** - How to create DEB packages
- **[SNAP_PACKAGING.md](SNAP_PACKAGING.md)** - How to create Snap packages
- **[PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md)** - Quick reference for publishing

## Support

For issues and questions:
- Check `man netcheck` for full documentation
- Run `netcheck --help` for quick reference
- Run `netcheck -v` for version information
- Run `netcheck -d <hostname>` for DNS lookup
- View logs in result.txt and fail-*.txt files
- Report issues on GitHub
