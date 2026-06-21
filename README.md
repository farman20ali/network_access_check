# Network Connectivity Checker (`netcheck`)

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)](#)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](#)

A premium, cross-platform, production-grade **Network Intelligence Engine & CLI** written in pure Python 3. Overhauled from a legacy Bash tool into a zero-dependency Python engine with high-concurrency diagnostics, lenient target input normalisation, structured output (JSON/CSV/XML), and an integrated **Model Context Protocol (MCP) Server** for AI assistants.

---

## 🚀 Key Features

- **Zero-Dependency Core** — Built on the Python standard library. No third-party packages required to run.
- **Cross-Platform** — Native support for Linux, macOS, and Windows with consistent terminal output.
- **Subcommand CLI** — Modular `tcp`, `dns`, `http`, `ssl`, `ping`, and `interfaces` subcommands.
- **Structured Output** — Every check returns `--format text|json|csv|xml`.
- **MCP Server** — Turns `netcheck` into a local tool-server for Claude, ChatGPT, and other AI agents.
- **Lenient Parsing** — Accepts CSVs, URLs, bracketed IPv6, IP ranges (`192.168.1.1-50`), CIDR (`10.0.0.0/24`), port lists (`80,443`), and port ranges (`8000-8100`).
- **Concurrent Batch Checks** — Configurable thread pools (`--jobs`) with real-time progress.

---

## 📦 Installation

### Option 1: `pip` (recommended)
```bash
pip install .
# or system-wide:
sudo pip install .
```

### Option 2: Snap Store (Linux)
```bash
sudo snap install netcheck
sudo snap connect netcheck:network-observe   # enables ping & interfaces
```

### Option 3: Debian package (`.deb`)
```bash
sudo dpkg -i netcheck_2.0.0_amd64.deb
```

### Option 4: Chocolatey (Windows)
```powershell
choco install netcheck
```

### Option 5: macOS `.pkg`
Double-click the downloaded `.pkg` file, or:
```bash
sudo installer -pkg netcheck-2.0.0.pkg -target /
```

### Option 6: Developer / local run (no install)
```bash
# 1. Clone the repo
git clone https://github.com/farman20ali/network_access_check.git
cd network_access_check

# 2. Install dev dependencies
pip install -r python-requirements.txt
# or
pip install -e ".[dev]"

# 3. Run directly
python3 -m netcheck --help
```

---

## 🛠️ CLI Reference

### Subcommands

| Subcommand | Description | Example |
|---|---|---|
| `tcp` | TCP port reachability | `netcheck tcp google.com 80,443` |
| `dns` | DNS hostname resolution | `netcheck dns github.com` |
| `http` | HTTP/HTTPS status + latency | `netcheck http https://google.com` |
| `ssl` | SSL certificate inspection | `netcheck ssl google.com` |
| `ping` | ICMP ping with RTT stats | `netcheck ping 8.8.8.8` |
| `interfaces` | Active network interfaces + public IP | `netcheck interfaces --all` |

### Global Flags

| Flag | Default | Description |
|---|---|---|
| `-t, --timeout` | `5` | Connection timeout in seconds |
| `-j, --jobs` | `10` | Concurrent thread pool size |
| `-f, --format` | `text` | Output format: `text`, `json`, `csv`, `xml` |
| `--retry` | `1` | Number of connection attempts |
| `--retry-delay` | `1` | Delay between retries (seconds) |
| `-v, --version` | — | Print version and exit |

### Legacy Flags (kept for backward compatibility)

| Legacy | Equivalent subcommand |
|---|---|
| `-q, --quick <host> <port>` | `netcheck tcp` |
| `-d, --dns <host>` | `netcheck dns` |
| `-p, --ping <host>` | `netcheck ping` |
| `-s, --status <url>` | `netcheck http` |
| `--cert <host>` | `netcheck ssl` |
| `--my-ip, -ip` | `netcheck interfaces` |

---

## 🤖 MCP Server

`netcheck` ships an integrated [Model Context Protocol](https://modelcontextprotocol.io/) server.

```bash
netcheck --mcp
# or
python3 -m netcheck.mcp.server
```

**Claude Desktop `claude_desktop_config.json`:**
```json
{
  "mcpServers": {
    "netcheck": {
      "command": "python3",
      "args": ["-m", "netcheck.mcp.server"],
      "env": { "PYTHONPATH": "/path/to/network_access_check" }
    }
  }
}
```

**Exposed MCP tools:** `dns_lookup`, `ping_host`, `check_tcp_port`, `check_http_status`, `check_ssl_certificate`, `list_interfaces`.

---

## 🏗️ Building Packages

All packaging is orchestrated by [`build_packages.py`](build_packages.py). Templates live in [`packaging/`](packaging/).

```
packaging/
├── chocolatey/        ← Windows Chocolatey (.nupkg)
│   └── tools/
├── linux/             ← install.sh / uninstall.sh
├── macos/             ← macOS .pkg scripts
├── snap/              ← snapcraft.yaml template
└── windows/           ← NSIS installer script (.nsi)
```

### Common build commands

```bash
# Check available tools on this machine
python3 build_packages.py --check

# Sync a new version across all config files
python3 build_packages.py --sync-version 2.1.0

# Build all packages for the current OS
python3 build_packages.py --all

# Individual targets
python3 build_packages.py --pypi      # wheel + sdist
python3 build_packages.py --deb       # Debian .deb
python3 build_packages.py --rpm       # RPM
python3 build_packages.py --snap      # Snap .snap
python3 build_packages.py --linux     # standalone binary (PyInstaller)
python3 build_packages.py --win       # Windows .exe + NSIS + Chocolatey
python3 build_packages.py --mac       # macOS binary + .pkg
```

All output lands in `dist/<target>/`.

---

## 🧪 Running Tests

```bash
# Using Make
make test

# Using pytest directly
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ --cov=netcheck --cov-report=term-missing
```

---

## 📁 Repository Structure

```
network_access_check/
├── netcheck/                  ← Python package
│   ├── __init__.py            ← version string
│   ├── __main__.py            ← python3 -m netcheck entry point
│   ├── cli.py                 ← CLI argument parsing & dispatch
│   ├── mcp/                   ← MCP server
│   ├── modules/               ← dns, tcp, http, ssl, ping, interfaces
│   └── utils/                 ← formatters, retry, concurrency helpers
├── packaging/                 ← Platform packaging templates
│   ├── chocolatey/
│   ├── linux/
│   ├── macos/
│   ├── snap/
│   └── windows/
├── tests/                     ← pytest test suite
├── docs/                      ← Guides and release notes
├── .github/workflows/         ← CI (ci.yml) + Release (release.yml)
├── build_packages.py          ← Build orchestration script
├── pyproject.toml             ← Package metadata & build config
├── python-requirements.txt    ← Local dev setup shortcut
└── Makefile                   ← make install / test / clean
```

---

## 🛡️ License

Distributed under the **GNU General Public License v3 (GPL-3.0)**. See [`LICENSE`](LICENSE) for details.
