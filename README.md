# Network Connectivity Checker (`netcheck`)

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](#)

A premium, cross-platform, production-grade **Network Intelligence Engine & CLI** written in pure Python 3. Overhauled from the legacy hybrid Bash scripts to support high-concurrency diagnostics, lenient target input normalization, and an integrated **Model Context Protocol (MCP) Server** for AI assistants.

---

## 🚀 Key Features

* **Zero-Dependency Core**: Built with the Python standard library for high portability, with optional `cryptography` integration for certificate inspection fallbacks.
* **Cross-Platform**: Run natively on **Linux**, **macOS**, and **Windows** with consistent terminal layouts and behaviors.
* **Model Context Protocol (MCP)**: Turn `netcheck` into a local MCP server to empower Claude, ChatGPT, or other AI agents with real-time network diagnostic capabilities.
* **Lenient Target Parsing**: Accepts raw inputs from CSVs, space/comma-separated lines, bracketed IPv6, and raw URLs (automatically stripping paths and schemes).
* **Network & Port Range Expansions**: Full support for IP ranges (`192.168.1.1-50`), CIDR subnets (`10.0.0.0/24`), multiple ports (`80,443`), and port ranges (`8000-8100`).
* **Robust SSL Validation**: Loops sequentially over all resolved IPv4 & IPv6 records and falls back to DER parsing when certificates fail strict trust verification.
* **Interface Auto-Discovery**: Detects active network interfaces, dynamically parses default gateways (via `/proc/net/route` on Linux), and queries public IP addresses.
* **High-Speed Concurrency**: Execute batch checks concurrently with custom thread pools and real-time progress bars.

---

## 📦 Installation

### Option 1: System-wide (Pip / Setup)
Install directly from the source directory:
```bash
sudo make install
```
Or manually using pip:
```bash
pip install .
```
Once installed, the `netcheck` command is available system-wide.

### Option 2: Snap Store (Linux Universal)
```bash
sudo snap install netcheck
```
*Note: To grant permission for ICMP Ping (`-p`) and Network Interfaces (`--my-ip`), connect the network-observe interface:*
```bash
sudo snap connect netcheck:network-observe
```

### Option 3: Developer / Local Run
Run without installation using the Python module syntax:
```bash
PYTHONPATH=. python3 -c "from netcheck.cli import main; main()" [OPTIONS]
```

---

## 🛠️ CLI Subcommands

`netcheck` 2.0.0 introduces dedicated subcommands for modular diagnostics.

### 1. TCP Connectivity Check (`tcp`)
Check if TCP ports are open. Supports lists and ranges.
```bash
netcheck tcp google.com 80,443
netcheck tcp 192.168.1.1-10 22,80 --timeout 2
```

### 2. DNS Resolution (`dns`)
Resolve hostnames to IPv4/IPv6, query reverse DNS, and extract aliases.
```bash
netcheck dns google.com
netcheck dns https://api.github.com/v3/repos   # Automatically extracts host
```

### 3. HTTP Status Check (`http`)
Measure HTTP/HTTPS response latency, descriptive status codes, redirects, and content size.
```bash
netcheck http https://google.com
netcheck http my-service.local -V              # -V / --verbose prints headers
```

### 4. SSL Certificate Inspection (`ssl`)
Verify SSL/TLS certificate validity, expiry, subject common names, issuers, and SANs.
```bash
netcheck ssl google.com
netcheck ssl expired-cert.local -V             # Prints SANs and validation errors
```

### 5. ICMP Ping Test (`ping`)
Send raw ICMP packets to verify host reachability.
```bash
netcheck ping 8.8.8.8
netcheck ping https://github.com               # Automatically extracts IP/host
```

### 6. Interface Auto-Discovery (`interfaces`)
List active network interfaces, default gateways, and retrieve your public IP address.
```bash
netcheck interfaces
netcheck interfaces --all                      # Include inactive (DOWN) interfaces
```

---

## 🤖 Model Context Protocol (MCP) Server

`netcheck` includes an integrated MCP server, allowing LLMs (like Claude Desktop) to invoke network diagnostics directly.

### Running the MCP Server
```bash
netcheck --mcp
```
Or via Python:
```bash
python3 -m netcheck.mcp.server
```

### Claude Desktop Configuration
Add the following to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "netcheck": {
      "command": "python3",
      "args": [
        "-m",
        "netcheck.mcp.server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/network_access_check"
      }
    }
  }
}
```

#### Exposed MCP Tools:
* `dns_lookup`: Resolve a hostname to its IP addresses.
* `ping_host`: Ping a host (ICMP) and returns packet statistics.
* `check_tcp_port`: Check if a port is open on a host.
* `check_http_status`: Perform an HTTP GET request to check status, size, and latency.
* `check_ssl_certificate`: Validate and retrieve SSL certificate attributes.
* `list_interfaces`: Retrieve network interface details, gateway, and public IP.

---

## 📝 Input Normalization & Ranges

The `netcheck` engine is designed with a **Lenient Target Parser**. It reads from files or standard input and accepts diverse formats.

### Supported Formats:
* **Basic space-separated**: `google.com 443`
* **Colon-separated**: `192.168.1.1:80`
* **IPv6 bracketed**: `[2a00:1450:4018:80f::200e]:443`
* **HTTP/HTTPS URLs**: `https://api.github.com:8443/users/octocat` (extracts `api.github.com` and port `8443`)
* **CSV Files** (using `--csv` flag):
  ```csv
  host,port
  google.com,443
  192.168.1.1-5,"80,443"
  ```

### Ranges & CIDR Expansions:
* **IP Ranges**: `192.168.1.1-10 80` (Checks `.1` through `.10` on port 80)
* **Subnet CIDRs**: `192.168.1.0/24 22` (Scans the entire `/24` subnet on SSH)
* **Port Lists**: `localhost 80,443,8080`
* **Port Ranges**: `localhost 8000-8100`

---

## 💾 Legacy Option Map

`netcheck` maintains full backward compatibility with all legacy parameters:

| Legacy Flag | Description | Equivalent Subcommand |
|---|---|---|
| `-q, --quick <host> <port>` | Quick test mode (no file creation) | `netcheck tcp` |
| `-d, --dns <host>` | Resolve DNS hostname | `netcheck dns` |
| `-p, --ping <host>` | Ping host | `netcheck ping` |
| `-s, --status <url>` | Check HTTP/HTTPS status | `netcheck http` |
| `--cert <host>` | Validate SSL certificate | `netcheck ssl` |
| `--my-ip, -ip` | Show network interfaces | `netcheck interfaces` |
| `--all` | Include down interfaces (with `--my-ip`) | `netcheck interfaces --all` |
| `-t, --timeout <sec>` | Set connection timeout (default: 5) | `--timeout` |
| `-j, --jobs <num>` | Max concurrent parallel jobs (default: 10) | `--jobs` |
| `-f, --format <format>` | Output format: `text`, `json`, `csv`, `xml` | `--format` |
| `-c, --combined` | Generate dated combined report | `--combined` |

---

## 🛡️ License

Distributed under the **GNU General Public License v3 (GPL-3.0)**. See `LICENSE` for details.
