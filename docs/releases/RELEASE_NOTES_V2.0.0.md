# Release Notes - NetCheck v2.0.0

NetCheck v2.0.0 is a major modernization release, transitioning the engine from a Bash-based tool into a cross-platform, zero-dependency Python 3 engine.

## New Features
- **Pure Python 3 Engine**: Zero external python library dependencies required. Works natively on Linux, macOS, and Windows.
- **Advanced Diagnostic Outputs**: Complete overhaul of formatting engines (JSON, CSV, XML) for non-TCP diagnostic checks (DNS, HTTP, SSL, Ping, Interfaces).
- **Subcommand Routing**: Supports direct subcommand usage (e.g., `netcheck tcp google.com 80`, `netcheck dns google.com`, `netcheck http https://github.com`, `netcheck ssl github.com`, `netcheck ping 8.8.8.8`, `netcheck interfaces`).
- **Model Context Protocol (MCP)**: Native MCP JSON-RPC stdio server integrated for seamless integration with AI editors (e.g., Cline, Roo Code, Cursor).
- **Multi-IP SSL Verification**: Loops sequentially over all resolved IPv4 & IPv6 records with fallback to direct cryptography certificate metadata parsing when verification fails.
- **Lenient Target Parsing**: Regex-based target extraction to parse hosts and ports from arbitrary format strings, URLs, brackets, and octet/CIDR ranges.
- **Orchestrated Packaging**: Platform-independent packaging utility `build_packages.py` to compile native binaries and construct DEB, Snap, and RPM targets.

## Upgrade Guide
Standard usage remains backwards-compatible with legacy flags (e.g., `-q`, `-d`, `-p`, `-s`, `--cert`, `-ip`). Output formats for downstream scripts match legacy fields.
