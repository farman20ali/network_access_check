# Release Notes — NetCheck v2.3.0

**Release Date:** 2026-07-30
**Type:** Feature — Refactor, Public IP, Output Filtering & Concurrent Ping

---

## Overview

v2.3.0 is a focused feature and robustness release built on top of the v2.2.0 Tier 3 diagnostics engine. It introduces concurrent public IP resolution, output filtering for batch TCP checks, a `--json` shorthand flag, full IP-range concurrency for `ping`, and a deep module refactor that adds typed result envelopes across every diagnostic module. The formatter layer is rebuilt around a unified type-detection helper, making JSON/CSV/XML output more reliable and consistent in all code paths.

---

## What's New

### 1. Public IP Resolution (`--public`)

```bash
netcheck interfaces --public          # Show public IP alongside local interfaces
netcheck --my-ip --public            # Legacy flag also supported
```

- Added `--public` flag to the `interfaces` subcommand and the legacy `--my-ip` flag.
- Queries **multiple public IP APIs concurrently** (race strategy — returns the first valid response) with a configurable timeout.
- APIs queried: `https://api.ipify.org`, `https://checkip.amazonaws.com`, `https://icanhazip.com`, and `https://ifconfig.me/ip`.
- Falls back gracefully to `"Unknown"` if all queries fail or time out.
- New `public_ip_checked` key is emitted in the JSON output when using `-f json`.

### 2. Output Filtering for Batch TCP / Quick Checks (`--show`)

```bash
netcheck tcp 192.168.1.1-50 22 --show success    # Print only successful connections
netcheck tcp 10.0.0.0/24 443 --show fail         # Print only failures
netcheck -q 192.168.1.1 80,443 --show success    # Legacy quick-mode filtering
```

- New `--show` flag accepts `all` (default), `success`, or `fail`.
- Works with both the `tcp` subcommand and the legacy `-q`/`--quick` mode.
- In text mode, only the matching result lines are printed; in JSON/CSV/XML modes, only matching records are included in the output.

### 3. `--json` Flag Alias

```bash
netcheck -q 192.168.1.1 22 --json                # Equivalent to -f json
netcheck tcp 10.0.0.1 80 --json                  # Cleaner CI syntax
```

- `--json` is now a first-class CLI flag (alias for `-f json`) in legacy mode.
- Eliminates the need to type `-f json` when piping output to `jq` or other JSON tools.

### 4. Concurrent Ping for IP Ranges

```bash
netcheck -p 192.168.1.1-20             # Pings 20 hosts concurrently
netcheck ping 10.0.0.1-50 -f json      # JSON batch envelope with typed results
```

- The `-p` / `--ping` legacy flag now expands IP ranges (`192.168.1.1-20`, `10.0.0.0/24`) and executes all pings **concurrently** using a thread pool.
- Results are sorted by target IP for deterministic output.
- Single-host pings continue to use the simple retry path.
- **New typed JSON envelope** for multi-ping results:
  ```json
  {
    "check_date": "2026-07-30 10:00:00",
    "type": "ping",
    "count": 20,
    "results": [
      { "target": "192.168.1.1", "success": true, "latency_ms": 1.2, ... },
      ...
    ]
  }
  ```

### 5. Typed Result Envelopes Across All Modules

Every diagnostic module (`dns`, `http`, `ssl`, `ping`, `tcp`, `interfaces`, `traceroute`, `port_scanner`, `whois`) now includes a `"type"` key in the result dictionary it returns. This enables downstream code (formatters, MCP tools, CI scripts) to reliably identify the result kind without heuristic metadata inspection.

| Module | `type` value |
|---|---|
| `dns.py` | `"dns"` |
| `http.py` | `"http"` |
| `ssl.py` | `"ssl"` |
| `ping.py` | `"ping"` |
| `tcp.py` | `"tcp"` |
| `interfaces.py` | `"interfaces"` / `"ports"` |
| `traceroute.py` | `"traceroute"` |
| `port_scanner.py` | `"scan"` |
| `whois.py` | `"whois"` |

### 6. Unified Result-Type Detection in Formatters

- New internal `_detect_result_type(res)` helper in `formatters.py` provides a single, authoritative dispatch path for all JSON, CSV, and XML formatting.
- Reads the `"type"` key first; falls back to heuristic metadata inspection for backward compatibility with pre-v2.3.0 result dicts.
- Eliminates duplicated type-sniffing logic that was previously scattered across `format_json`, `format_csv`, and `format_xml`.

---

## Breaking Changes

None. All CLI flags, subcommands, and output formats remain fully backward-compatible.

---

## Files Added / Changed

| File | Change |
|---|---|
| `netcheck/cli.py` | Added `--public`, `--json`, `--show` flags; concurrent ping range dispatch; IP range handling in `-p` legacy mode |
| `netcheck/modules/interfaces.py` | Added `get_public_ip()` (concurrent multi-API fetch); `get_network_interfaces` emits `type` and `public_ip_checked` |
| `netcheck/modules/ping.py` | Result dict now includes `"type": "ping"` |
| `netcheck/modules/dns.py` | Result dict now includes `"type": "dns"` |
| `netcheck/modules/http.py` | Result dict now includes `"type": "http"` |
| `netcheck/modules/ssl.py` | Result dict now includes `"type": "ssl"` |
| `netcheck/modules/tcp.py` | Result dict now includes `"type": "tcp"` |
| `netcheck/modules/traceroute.py` | Result dict now includes `"type": "traceroute"` |
| `netcheck/modules/port_scanner.py` | Result dict now includes `"type": "scan"` |
| `netcheck/modules/whois.py` | Result dict now includes `"type": "whois"` |
| `netcheck/utils/formatters.py` | Added `_detect_result_type()`; multi-ping JSON batch envelope; unified type dispatch in `format_json`, `format_csv`, `format_xml` |
| `netcheck/utils/cache.py` | Minor utility improvements |
| `netcheck/utils/normalize.py` | Minor input-normalisation improvements |
| `netcheck/utils/timeout.py` | Minor utility improvements |
| `tests/test_cli.py` | Added tests for `--public`, `--show`, `--quick` argument validation, `interfaces --public`, concurrent ping range, multi-ping JSON envelope |
| `tests/test_netcheck.py` | Updated formatter tests to cover typed result detection |
| `docs/releases/RELEASE_NOTES_V2.3.0.md` | **New** — this file |
| `CHANGELOG.md` | v2.3.0 entry added |

---

## Release Artefacts

| Artefact | Platform |
|---|---|
| `netcheckx-2.3.0-py3-none-any.whl` | PyPI / All platforms |
| `netcheckx-2.3.0.tar.gz` | Source distribution (PyPI) |
| `netcheck_2.3.0_amd64.deb` | Debian / Ubuntu |
| `netcheck_2.3.0_amd64.snap` | All Linux (Snap Store) |
| `netcheck-2.3.0-setup.exe` | Windows NSIS Installer |
| `netcheck-2.3.0.nupkg` | Windows Chocolatey |

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
sudo dpkg -i netcheck_2.3.0_amd64.deb
```

---

## Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for the complete history.
