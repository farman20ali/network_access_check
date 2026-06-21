# Release Notes — NetCheck v2.1.0

**Release Date:** 2026-06-21
**Type:** Minor — Packaging & Tooling Modernisation

---

## Overview

v2.1.0 is a packaging and tooling modernisation release. No changes were made to the `netcheck` runtime engine or CLI behaviour. This release reorganises the entire distribution pipeline into a clean `packaging/` directory, introduces a unified version-sync tool, a new `publish_packages.py` publisher, and a full CI test matrix.

---

## What's New

### `packaging/` Directory Structure

All platform-specific packaging templates are now consolidated under one top-level directory:

```
packaging/
├── chocolatey/         ← Windows Chocolatey (.nupkg)
│   └── tools/
├── linux/              ← install.sh / uninstall.sh
├── macos/              ← placeholder for .pkg scripts
├── snap/               ← snapcraft.yaml (version placeholder)
└── windows/            ← NSIS installer (.nsi)
```

Templates use a `{version}` placeholder that `build_packages.py` substitutes at build time, keeping package config separate from the build script logic.

### `--sync-version` — Single-Command Version Bump

```bash
python3 build_packages.py --sync-version 2.2.0
```

Propagates the new version to every file that embeds the version string:
- `netcheck/__init__.py`
- `pyproject.toml`
- `netcheck/mcp/server.py`
- `packaging/snap/snapcraft.yaml`

### `publish_packages.py` — Unified Publisher

A new flag-based publisher mirrors the build script interface:

```bash
python3 publish_packages.py --snap                      # push to Snap Store (stable)
python3 publish_packages.py --snap --channel edge       # push to edge channel
python3 publish_packages.py --pypi                      # upload to PyPI (production)
python3 publish_packages.py --pypi --test               # upload to TestPyPI first
python3 publish_packages.py --chocolatey                # push to Chocolatey.org
python3 publish_packages.py --check                     # verify publish tools are available
```

### CI Workflow (`.github/workflows/ci.yml`)

New automated test matrix:
- **Python versions:** 3.8, 3.9, 3.10, 3.11, 3.12
- **Platforms:** Ubuntu, macOS, Windows
- Runs on every push and pull request

### `netcheck/__main__.py`

Standard Python module entrypoint — `python3 -m netcheck` now works alongside the `netcheck` command.

---

## Breaking Changes

None. All legacy CLI flags remain fully supported.

---

## Files Removed

| File | Reason |
|---|---|
| `build-deb.sh` | Superseded by `python3 build_packages.py --deb` |
| `build-snap.sh` | Superseded by `python3 build_packages.py --snap` |
| `check_ip.py` | Legacy wrapper — deleted |
| `check_ip.sh` | Legacy wrapper — deleted |
| `PYTHON_README.md` | Stub; `README.md` is the single source of truth |
| Root `install.sh` | Moved to `packaging/linux/install.sh` |
| Root `uninstall.sh` | Moved to `packaging/linux/uninstall.sh` |
| Root `snap/` | Moved to `packaging/snap/` |

---

## Files Added / Changed

| File | Change |
|---|---|
| `build_packages.py` | Reads templates from `packaging/`; adds `--sync-version` |
| `publish_packages.py` | **New** — flag-based publisher for Snap, PyPI, Chocolatey |
| `packaging/snap/snapcraft.yaml` | Canonical Snap template |
| `packaging/linux/install.sh` | Moved from root |
| `packaging/linux/uninstall.sh` | Moved from root |
| `packaging/windows/netcheck.nsi` | NSIS installer template |
| `packaging/chocolatey/netcheck.nuspec` | Chocolatey package template |
| `tests/test_cli.py` | New — 15 CLI tests covering all subcommands |
| `README.md` | Full rewrite with accurate installation options |
| `CHANGELOG.md` | v2.1.0 entry added |
| `pyproject.toml` | License field updated to SPDX string |

---

## Release Artefacts

| Artefact | Platform |
|---|---|
| `netcheck-2.1.0-py3-none-any.whl` | PyPI / all platforms |
| `netcheck-2.1.0.tar.gz` | Source distribution |
| `netcheck_2.1.0-1_all.deb` | Debian / Ubuntu |
| `netcheck_2.1.0_amd64.snap` | All Linux (Snap Store) |

---

## Upgrade Guide

### From v2.0.0 (pip install)
```bash
pip install --upgrade netcheck
```

### From v2.0.0 (snap)
```bash
sudo snap refresh netcheck
```

### From v2.0.0 (.deb)
```bash
sudo dpkg -i netcheck_2.1.0-1_all.deb
```

---

## Full Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for the complete history.
