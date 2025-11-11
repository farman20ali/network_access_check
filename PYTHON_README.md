# Network Connectivity Checker (Python)

**Version:** 1.1.0

A portable Network Connectivity Checker implemented in Python 3. It is a full-featured port of the original Bash/PowerShell tool and supports parallel TCP connectivity checks, IP/port range expansion, CIDR expansion (limited to avoid accidental wide scans), DNS and ICMP helpers, CSV input, and multiple output formats (text/json/csv/xml).

---

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)

  * [Command-line options](#command-line-options)
  * [Input formats](#input-formats)
  * [Quick test mode](#quick-test-mode)
  * [DNS and Ping helpers](#dns-and-ping-helpers)
* [Examples](#examples)
* [Output files](#output-files)
* [Implementation notes & limitations](#implementation-notes--limitations)
* [Troubleshooting](#troubleshooting)
* [Extending the tool](#extending-the-tool)
* [License](#license)

---

## Features

* Expand IP ranges (e.g. `192.168.1.1-50`) and CIDR blocks (`192.168.1.0/24`) — CIDR expansion capped to the first 256 hosts by default.
* Expand port lists (`80,443`) and ranges (`8000-8100`) with validation and safe limits.
* CSV input support (`--csv`) with quoted fields and header detection.
* Quick test mode (`-q`) for ad-hoc checks.
* DNS resolution (`-d`) and ICMP ping (`-p`) helpers using system utilities where applicable.
* Parallel TCP connection checks using `ThreadPoolExecutor` with configurable concurrency.
* Multiple output formats: `text`, `json`, `csv`, `xml`.
* Progress bar printed to `stderr`, per-test response times recorded.
* Exit code `0` when all tests succeed, `1` when any failure occurs (suitable for CI).

---

## Requirements

This script is implemented using the **Python standard library**, so **no external packages are required** to run the default feature set.

Optional packages (use if you extend the script):

* `colorama` — cross-platform terminal coloring (if you want colored output on Windows)

A `requirements.txt` file is included with suggested optional packages and comments.

---

## Installation

1. Make sure you have Python 3.8+ installed.
2. Save the script as `check_ip.py` in a folder of your choice.
3. (Optional) Create a virtual environment and install optional packages from `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt
```

> Note: By default the script uses only the standard library — these steps are optional.

---

## Usage

```
python3 check_ip.py [OPTIONS] [input_file]
```

### Command-line options

* `-t, --timeout <seconds>` — connection timeout (default: `5`).
* `-j, --jobs <number>` — max parallel jobs (default: `10`).
* `-V, --verbose` — verbose output.
* `-f, --format <format>` — output format: `text`, `json`, `csv`, `xml` (default: `text`).
* `-c, --combined` — create combined report file with both successes and failures.
* `--csv` — input file is CSV format (`host,port`).
* `-q, --quick <HOST> <PORTS>` — quick test mode (e.g. `-q google.com 80` or `-q 10.0.0.1-5 22`).
* `-d, --dns <HOST>` — resolve DNS and print addresses.
* `-p, --ping <HOST>` — ping (ICMP) helper.
* `-v, --version` — show version.
* `input_file` — optional path to input file. If omitted and STDIN is piped, lines are read from STDIN.

### Input formats

Each line should contain two fields: `HOST PORTS`.

* `HOST` can be:

  * Single IP or hostname: `192.168.1.1`, `example.com`
  * IP range: `192.168.1.1-50`
  * CIDR: `192.168.1.0/24` (limited to first 256 hosts)

* `PORTS` can be:

  * Single port: `80`
  * Comma list: `80,443,8080`
  * Range: `8000-8100`

CSV input example (use `--csv`):

```
host,port
192.168.1.1,80
server.com,443
"10.0.0.1-5","22"
```

---

## Quick test mode

Quick mode allows immediate checks without an input file:

```bash
python3 check_ip.py -q google.com 80
python3 check_ip.py -q "10.0.0.1-5" 22
python3 check_ip.py -q localhost "8000-8010"
```

---

## DNS and Ping helpers

* `-d <host>` performs DNS resolution (strips URL scheme/path) and prints A/AAAA addresses.
* `-p <host>` calls the system `ping` command and prints output. Behavior varies by OS (Windows/macOS/Linux).

Examples:

```bash
python3 check_ip.py -d https://api.example.com/v1
python3 check_ip.py -p 8.8.8.8
```

---

## Examples

Basic file input:

```bash
python3 check_ip.py hosts.txt
```

JSON output with combined report:

```bash
python3 check_ip.py -f json -c hosts.txt
```

CSV input and increased concurrency:

```bash
python3 check_ip.py --csv -j 50 hosts.csv
```

Pipe input from another command:

```bash
cat hosts.txt | python3 check_ip.py -V
```

---

## Output files

By default the script creates files in the current working directory:

* `result-YYYY-MM-DD.txt` — successful checks (or JSON/CSV/XML depending on `-f`).
* `fail-YYYY-MM-DD.txt` — failed checks.
* `combined-YYYY-MM-DD.txt` — when `-c` is used.

The JSON format produces structured JSON files and the CSV/XML options produce appropriate files for downstream parsing.

---

## Implementation notes & limitations

* The script uses `ThreadPoolExecutor` for parallelism. For very large scans an `asyncio`-based or process-based approach may scale better.
* CIDR expansion is intentionally limited to 256 hosts to avoid accidental wide scans — change `MAX_CIDR_LIMIT` in the script only if you understand the network impact.
* ICMP ping uses the system `ping` utility which behaves differently across platforms and may require privileges.
* TCP checks use `socket.create_connection` which performs a basic TCP connect — it does not validate TLS or perform application-layer handshakes.

---

## Troubleshooting

* **No input provided**: If you run without `-q` and without an input file, you must pipe input via STDIN.
* **Permission/ping issues**: If `--ping` fails, try running with appropriate privileges or use TCP checks as they do not require raw ICMP sockets.
* **Slow scans**: Increase `-j` or reduce `-t` where appropriate.

---

## Extending the tool

Ideas for improvements:

* Add TLS/TCP handshake checks and SNI support.
* Add retries/backoff and jitter for unstable networks.
* Add rate-limiting, concurrency limits per-host, or per-network.
* Add output to SQLite/InfluxDB/Elasticsearch for long-term storage and dashboards.

---

## License

MIT-style: reuse, adapt, and redistribute. (Add your preferred license text.)

---

## Author / Contact

Ported to Python from an advanced Bash/PowerShell implementation. For modifications or custom features (asyncio-based engine, TLS checks, DB output), tell me which direction and I will update the code.