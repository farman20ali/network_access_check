# Publishing Quick Reference (v2.3.0)

## 📦 Distribution Methods

You now have a unified, Python-based pipeline to package and publish the `netcheck` tool across multiple platforms.

| Method | Build Command | Publish Command / Store | Target Users |
|--------|---------------|-------------------------|--------------|
| **Manual** | — | `sudo make install` | Development, local testing |
| **PyPI (pip)** | `python build_packages.py --pypi` | `python publish_packages.py --pypi` | All Python developers (`pip install netcheckx`) |
| **DEB Package** | `python build_packages.py --deb` | GitHub Releases or APT repository | Debian / Ubuntu / Linux Mint |
| **RPM Package** | `python build_packages.py --rpm` | GitHub Releases or RPM repository | Fedora / RHEL / CentOS |
| **Snap Package** | `python build_packages.py --snap` | `python publish_packages.py --snap` | Universal Linux (Ubuntu, Arch, Fedora, etc.) |
| **Windows Installer** | `python build_packages.py --win` | GitHub Releases / Chocolatey | Windows Command Line / GUI Users |
| **macOS PKG** | `python build_packages.py --mac` | GitHub Releases | macOS Command Line Users |

---

## 🎯 Orchestrators Quick Start

Instead of scattered Bash scripts, `netcheck` utilizes two main orchestrators:

### 1. `build_packages.py` (Building)
Runs platform-aware package compilers to generate final installation assets in the `dist/` directory.

```bash
# Verify which packaging compilers are installed on your current host
python build_packages.py --check

# Bump/Synchronise version across pyproject.toml, __init__.py, and metadata config templates
python build_packages.py --sync-version 2.3.0

# Build PyPI distribution files (wheel + sdist)
python build_packages.py --pypi

# Build Snap packages
python build_packages.py --snap

# Build DEB packages
python build_packages.py --deb

# Build RPM packages
python build_packages.py --rpm

# Build Windows binaries (EXE + NSIS Installer + Chocolatey .nupkg)
python build_packages.py --win

# Build all packages supported by the current OS
python build_packages.py --all
```

### 2. `publish_packages.py` (Publishing)
Automates the secure upload of compiled packages from the `dist/` folder to public registries.

```bash
# Verify available credentials and publishing tools (twine, snapcraft, choco, gh)
python publish_packages.py --check

# Upload wheel + source distribution to TestPyPI
python publish_packages.py --pypi --test

# Upload to production PyPI (requires TWINE_USERNAME / TWINE_PASSWORD or API token)
python publish_packages.py --pypi

# Upload and release Snap package to the Snap Store stable channel
python publish_packages.py --snap

# Upload Snap to a custom testing channel (e.g. edge or beta)
python publish_packages.py --snap --channel edge

# Upload Windows Chocolatey package to Chocolatey.org (requires CHOCO_API_KEY)
python publish_packages.py --chocolatey

# Create a GitHub Release v2.3.0 and attach all compiled assets from dist/
python publish_packages.py --github-release v2.3.0
```

---

## 📥 Platform Publishing Details

### 1. PyPI / Pip
- **Distribution Name**: `netcheckx` (to avoid conflicts with existing packages).
- **Executable Aliases**: Both `netcheck` and `netcheckx` CLI commands are available post-installation.
- **Upload Tool**: Uses `twine`. Ensure you install twine: `pip install twine`.

### 2. Universal Linux (Snap Store)
- **Account Registration**: Sign up at https://snapcraft.io/ using an Ubuntu One account.
- **Classic confinement vs strict**: Netcheck uses strict confinement but plugs `network-observe` and `system-observe` to allow pinging and process mapping.
- **Command flow**:
  1. `snapcraft login`
  2. `python build_packages.py --snap`
  3. `python publish_packages.py --snap`
- **User Installation**:
  ```bash
  sudo snap install netcheck
  sudo snap connect netcheck:network-observe
  sudo snap connect netcheck:system-observe
  ```

### 3. Debian / Ubuntu (`.deb`)
- **Compilation**: Runs `dpkg-buildpackage` under the hood. Requires `build-essential devscripts debhelper fakeroot dh-python python3-all`.
- **Install locally**:
  ```bash
  sudo dpkg -i dist/deb/netcheck_2.3.0-1_all.deb
  ```

### 4. Windows (NSIS & Chocolatey)
- **EXE & NSIS**: Built via PyInstaller and NSIS. Outputs `netcheck-2.3.0-setup.exe` in `dist/win/`.
- **Chocolatey**: Outputs `netcheck.2.3.0.nupkg` in `dist/choco/`. Push using `python publish_packages.py --chocolatey`.

---

## 📋 Release Checklist

- [ ] Test code: `python -m pytest`
- [ ] Sync version to 2.3.0: `python build_packages.py --sync-version 2.3.0`
- [ ] Document changes in `CHANGELOG.md` and `docs/releases/RELEASE_NOTES_V2.3.0.md`
- [ ] Build all binaries: `python build_packages.py --all`
- [ ] Check publish tools: `python publish_packages.py --check`
- [ ] Publish to PyPI: `python publish_packages.py --pypi`
- [ ] Publish Snap: `python publish_packages.py --snap`
- [ ] Publish Chocolatey (if on Windows): `python publish_packages.py --chocolatey`
- [ ] Create GitHub Release with all assets: `python publish_packages.py --github-release v2.3.0`
