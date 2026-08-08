# NetCheck — Full Product Roadmap & Feature Plan
**Based on v2.3.0 | Updated: August 2026**

---

## 1. Market Context

### The Gap NetCheck Fills

| Heavy Tools | NetCheck's Lane | Light Tools |
|---|---|---|
| nmap, Nessus, Zabbix — powerful but complex, slow to install | Rapid, human-readable, multi-host audits. Portable, pip-installable, cross-platform, AI-ready | ping, curl, nc — single-purpose, no output formatting, no parallelism |

### Competitor Gap Table

| Feature | NetCheck v2.3.0 | nmap | fping | mtr | UptimeRobot |
|---|---|---|---|---|---|
| Cross-platform | ✅ | ✅ | ❌ Linux | ❌ | ✅ cloud |
| Human + machine output | ✅ JSON/CSV/XML | partial | minimal | minimal | web only |
| Watch/continuous mode | ✅ | ❌ | ✅ | ✅ | ✅ |
| UDP scanning | ❌ | ✅ | ❌ | ❌ | ❌ |
| Alerting | ❌ | ❌ | ❌ | ❌ | ✅ |
| MCP integration | partial | ❌ | ❌ | ❌ | ❌ |
| VSCode extension | ❌ | ❌ | ❌ | ❌ | ❌ |
| Prometheus metrics | ❌ | ❌ | ❌ | ❌ | ❌ |
| Homebrew | ❌ → v2.4 | ✅ | ✅ | ✅ | N/A |
| AUR (Arch) | ❌ → v2.4 | ✅ | ✅ | ❌ | N/A |
| winget | ❌ → v2.4 | ❌ | ❌ | ❌ | N/A |

---

## 2. What's Already Implemented (v2.3.0)

### Subcommands
`tcp`, `dns`, `http`, `ssl`, `ping`, `interfaces`, `ports`, `traceroute`, `scan`, `whois`

### Cross-cutting
- Watch mode (`-w`, `-i`)
- Output: text, JSON, CSV, XML; `--json`; `--show` filter
- Retry logic, parallel jobs, timeout
- Typed result envelopes + unified formatter
- CI/GitHub Actions release automation

### Current Packaging
| Package | Platform | Status |
|---|---|---|
| `netcheckx` PyPI wheel | All | ✅ |
| `.tar.gz` source dist | All | ✅ |
| `.deb` | Debian/Ubuntu | ✅ |
| `.snap` | All Linux | ✅ |
| `.exe` NSIS installer | Windows | ✅ |
| `.nupkg` Chocolatey | Windows | ✅ |

### Not Yet Done (your notes)
- MCP wiring of remaining subcommands
- VSCode extension (MCP server in `packaging/vscode/`)
- Build/package Makefile commands for VSCode ext
- CI pipeline for VSCode ext
- Homebrew, AUR, winget, macOS `.pkg`, Linux tarball

---

## 3. Packaging Folder Structure

Match your other tool exactly:

```
packaging/
  aur/
    PKGBUILD
    .SRCINFO
    README.md
  chocolatey/
    netcheck.nuspec          ← already have, extend
    tools/
      chocolateyInstall.ps1
      chocolateyUninstall.ps1
    README.md
  homebrew/
    netcheck.rb              ← Homebrew formula
    README.md
  linux/
    netcheck.spec            ← RPM spec (Fedora/RHEL/CentOS)
    netcheck.deb/            ← already have, keep
    README.md
  macos/
    netcheck.pkgbuild        ← macOS .pkg via pkgbuild
    entitlements.plist
    README.md
  snap/
    snapcraft.yaml           ← already have, keep
    README.md
  vscode/                    ← NEW — extension as MCP server
    package.json
    extension.ts
    mcp/
    panels/
    commands/
    README.md
  windows/
    installer.iss            ← Inno Setup (or NSIS, whichever you use)
    README.md
  winget/
    manifests/
      farman20ali.netcheck.yaml
      farman20ali.netcheck.installer.yaml
      farman20ali.netcheck.locale.en-US.yaml
    README.md
```

---

## 4. Packaging Guides

---

### 4.1 Homebrew (`packaging/homebrew/`)

**Formula file: `packaging/homebrew/netcheck.rb`**

```ruby
class Netcheck < Formula
  include Language::Python::Virtualenv

  desc "Lightweight network connectivity checker — TCP, DNS, HTTP, SSL, ping, traceroute, WHOIS"
  homepage "https://github.com/farman20ali/network_access_check"
  url "https://files.pythonhosted.org/packages/.../netcheckx-2.3.0.tar.gz"
  sha256 "REPLACE_WITH_SHA256"
  license "GPL-3.0-only"
  head "https://github.com/farman20ali/network_access_check.git", branch: "main"

  bottle do
    sha256 cellar: :any_skip_relocation, arm64_sonoma: "..."
    sha256 cellar: :any_skip_relocation, ventura:      "..."
    sha256 cellar: :any_skip_relocation, x86_64_linux: "..."
  end

  depends_on "python@3.12"

  # List your pip dependencies here — get them from python-requirements.txt
  resource "requests" do
    url "https://files.pythonhosted.org/packages/.../requests-2.32.3.tar.gz"
    sha256 "REPLACE"
  end

  # Add remaining deps from requirements.txt the same way

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/netcheck", "--version"
    system "#{bin}/netcheck", "dns", "google.com"
  end
end
```

**Two distribution options:**

Option A — Custom Tap (faster, no review needed):
```bash
# User installs via:
brew tap farman20ali/netcheck
brew install netcheck

# You maintain: github.com/farman20ali/homebrew-netcheck
# That repo contains only the .rb formula file
```

Option B — homebrew-core (more visibility, slow review process):
- Submit PR to `Homebrew/homebrew-core`
- Requires 75+ GitHub stars and stable releases
- Takes weeks to get merged

**Recommendation: Start with Option A (custom tap), migrate to core later.**

**Create the tap repo:**
```bash
# Create github.com/farman20ali/homebrew-netcheck
# Put netcheck.rb in the root of that repo
# Done — users can now brew tap farman20ali/netcheck
```

**Auto-update formula on release (CI):**
```yaml
# .github/workflows/release.yml — add this step
- name: Update Homebrew Formula
  if: startsWith(github.ref, 'refs/tags/')
  run: |
    VERSION=${GITHUB_REF#refs/tags/v}
    TARBALL_URL="https://files.pythonhosted.org/packages/source/n/netcheckx/netcheckx-${VERSION}.tar.gz"
    SHA256=$(curl -sL "$TARBALL_URL" | sha256sum | cut -d' ' -f1)
    
    # Clone tap repo
    git clone https://x-access-token:${{ secrets.TAP_GITHUB_TOKEN }}@github.com/farman20ali/homebrew-netcheck.git
    cd homebrew-netcheck
    
    # Update version and sha256
    sed -i "s|url \".*\"|url \"$TARBALL_URL\"|" netcheck.rb
    sed -i "s|sha256 \".*\"|sha256 \"$SHA256\"|" netcheck.rb
    
    git config user.email "ci@github.com"
    git config user.name "GitHub Actions"
    git commit -am "Update netcheck to v${VERSION}"
    git push
```

**`packaging/homebrew/README.md`:**
```markdown
# Homebrew Packaging

## Install
```bash
brew tap farman20ali/netcheck
brew install netcheck
```

## Update
```bash
brew upgrade netcheck
```

## Uninstall
```bash
brew uninstall netcheck
brew untap farman20ali/netcheck
```

## For Maintainers
Formula is at: https://github.com/farman20ali/homebrew-netcheck/blob/main/netcheck.rb

To update manually:
1. Update `url` to new PyPI tarball URL
2. Update `sha256` (run: `curl -sL <url> | sha256sum`)
3. Update version string
4. Test: `brew install --build-from-source ./netcheck.rb`
5. Push to homebrew-netcheck repo
```

---

### 4.2 AUR — Arch Linux (`packaging/aur/`)

AUR = Arch User Repository. This covers Arch, Manjaro, EndeavourOS, and any Arch-based distro.

**`packaging/aur/PKGBUILD`:**
```bash
# Maintainer: Farman Ali <your-email>
pkgname=netcheck
pkgver=2.3.0
pkgrel=1
pkgdesc="Lightweight network connectivity checker — TCP, DNS, HTTP, SSL, ping, traceroute, WHOIS"
arch=('any')
url="https://github.com/farman20ali/network_access_check"
license=('GPL3')
depends=('python>=3.10' 'python-pip')
makedepends=('python-build' 'python-installer' 'python-wheel')
provides=('netcheck')
conflicts=()
source=("https://files.pythonhosted.org/packages/.../netcheckx-${pkgver}.tar.gz")
sha256sums=('REPLACE_WITH_SHA256')

build() {
    cd "netcheckx-${pkgver}"
    python -m build --wheel --no-isolation
}

package() {
    cd "netcheckx-${pkgver}"
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install man page if present
    install -Dm644 "man/netcheck.1" "$pkgdir/usr/share/man/man1/netcheck.1" 2>/dev/null || true
    
    # Install bash completion
    install -Dm644 "completion/netcheck.bash" \
        "$pkgdir/usr/share/bash-completion/completions/netcheck" 2>/dev/null || true
    install -Dm644 "completion/netcheck.zsh" \
        "$pkgdir/usr/share/zsh/site-functions/_netcheck" 2>/dev/null || true
}
```

**`packaging/aur/README.md`:**
```markdown
# AUR Packaging (Arch Linux)

## Install (users)
```bash
# Using yay
yay -S netcheck

# Using paru
paru -S netcheck

# Manual
git clone https://aur.archlinux.org/netcheck.git
cd netcheck
makepkg -si
```

## Uninstall
```bash
yay -R netcheck
```

## For Maintainers

The AUR package lives at: https://aur.archlinux.org/packages/netcheck

To update after a new release:
1. Update `pkgver` in PKGBUILD
2. Update `sha256sums` (run: `updpkgsums`)
3. Update `.SRCINFO`: `makepkg --printsrcinfo > .SRCINFO`
4. Push to AUR:
   ```bash
   git clone ssh://aur@aur.archlinux.org/netcheck.git
   # copy PKGBUILD and .SRCINFO
   git add PKGBUILD .SRCINFO
   git commit -m "Update to v2.x.x"
   git push
   ```

Requirements: You need an AUR account at https://aur.archlinux.org/register
```

---

### 4.3 winget (`packaging/winget/`)

winget is Microsoft's official package manager, built into Windows 10/11.

**Manifest files** (3 files required):

**`packaging/winget/manifests/farman20ali.netcheck.yaml`** (version manifest):
```yaml
PackageIdentifier: farman20ali.netcheck
PackageVersion: 2.3.0
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.6.0
```

**`packaging/winget/manifests/farman20ali.netcheck.installer.yaml`**:
```yaml
PackageIdentifier: farman20ali.netcheck
PackageVersion: 2.3.0
Platform:
  - Windows.Desktop
MinimumOSVersion: 10.0.17763.0
InstallerType: exe
Scope: machine
InstallModes:
  - interactive
  - silent
Installers:
  - Architecture: x64
    InstallerUrl: https://github.com/farman20ali/network_access_check/releases/download/v2.3.0/netcheck-2.3.0-setup.exe
    InstallerSha256: REPLACE_WITH_SHA256
    InstallerSwitches:
      Silent: /S
      SilentWithProgress: /S
      Log: /LOG=$TEMP\netcheck_install.log
    ProductCode: "{REPLACE-WITH-PRODUCT-GUID}"
UpgradeBehavior: install
Commands:
  - netcheck
ManifestType: installer
ManifestVersion: 1.6.0
```

**`packaging/winget/manifests/farman20ali.netcheck.locale.en-US.yaml`**:
```yaml
PackageIdentifier: farman20ali.netcheck
PackageVersion: 2.3.0
PackageLocale: en-US
Publisher: Farman Ali
PublisherUrl: https://github.com/farman20ali
PublisherSupportUrl: https://github.com/farman20ali/network_access_check/issues
Author: Farman Ali
PackageName: NetCheck
PackageUrl: https://github.com/farman20ali/network_access_check
License: GPL-3.0
LicenseUrl: https://github.com/farman20ali/network_access_check/blob/main/LICENSE
ShortDescription: Lightweight network connectivity checker with cross-platform support
Description: >-
  NetCheck is a powerful CLI tool for testing network connectivity to multiple 
  hosts and ports. Supports TCP, DNS, HTTP, SSL, ping, traceroute, port scanning, 
  WHOIS, and more. Outputs JSON, CSV, XML. Cross-platform: Windows, Linux, macOS.
Moniker: netcheck
Tags:
  - network
  - connectivity
  - cli
  - tcp
  - dns
  - ssl
  - ping
  - devops
ReleaseNotes: See https://github.com/farman20ali/network_access_check/releases/tag/v2.3.0
ReleaseNotesUrl: https://github.com/farman20ali/network_access_check/releases/tag/v2.3.0
ManifestType: defaultLocale
ManifestVersion: 1.6.0
```

**`packaging/winget/README.md`:**
```markdown
# winget Packaging (Windows)

## Install (users)
```powershell
winget install farman20ali.netcheck
```

## Update
```powershell
winget upgrade farman20ali.netcheck
```

## Uninstall
```powershell
winget uninstall farman20ali.netcheck
```

## For Maintainers

winget packages live in the winget-pkgs repo:
https://github.com/microsoft/winget-pkgs/tree/master/manifests/f/farman20ali/netcheck

To submit a new version:
1. Fork https://github.com/microsoft/winget-pkgs
2. Copy manifests/ to manifests/f/farman20ali/netcheck/2.x.x/
3. Update PackageVersion, InstallerUrl, InstallerSha256, ProductCode
4. Validate: `winget validate --manifest manifests/`
5. Submit PR to winget-pkgs

CI Auto-submit (add to release.yml):
Use the wingetcreate tool:
```powershell
wingetcreate update farman20ali.netcheck \
  --version $VERSION \
  --urls "https://github.com/.../netcheck-$VERSION-setup.exe" \
  --submit \
  --token $WINGET_GITHUB_TOKEN
```
```

---

### 4.4 macOS `.pkg` (`packaging/macos/`)

For users who want a double-click installer, not Homebrew.

**`packaging/macos/README.md`:**
```markdown
# macOS Packaging

## Install Options

### Option 1 — Homebrew (Recommended)
```bash
brew tap farman20ali/netcheck
brew install netcheck
```

### Option 2 — pip
```bash
pip install netcheckx
netcheck --version
```

### Option 3 — macOS .pkg Installer
Download `netcheck-2.3.0.pkg` from GitHub Releases.
Double-click to install. NetCheck is placed in `/usr/local/bin/netcheck`.

## For Maintainers

Build the .pkg:
```bash
# Install dependencies into a staging dir
pip install netcheckx --target packaging/macos/stage/lib/python3.12/site-packages

# Create the pkg
pkgbuild \
  --root packaging/macos/stage \
  --identifier com.farman20ali.netcheck \
  --version 2.3.0 \
  --install-location /usr/local \
  netcheck-2.3.0.pkg

# Optionally sign (requires Apple Developer cert):
productsign --sign "Developer ID Installer: YOUR NAME" \
  netcheck-2.3.0.pkg netcheck-2.3.0-signed.pkg
```

Alternatively, use `py2app` to create a standalone .app bundle 
or `briefcase` (BeeWare) for a proper macOS app package.
```

---

### 4.5 Linux Tarball (`packaging/linux/`)

For distros without a package manager supported above (Alpine, RHEL, Amazon Linux, etc.).

**`packaging/linux/README.md`:**
```markdown
# Linux Packaging

## Install Options

### Option 1 — pip (All distros)
```bash
pip install netcheckx
netcheck --version
```

### Option 2 — Snap (All Linux)
```bash
sudo snap install netcheck
sudo snap connect netcheck:network-observe  # required for ping and --my-ip
```

### Option 3 — .deb (Debian / Ubuntu / Mint)
```bash
wget https://github.com/farman20ali/network_access_check/releases/download/v2.3.0/netcheck_2.3.0_amd64.deb
sudo dpkg -i netcheck_2.3.0_amd64.deb
```

### Option 4 — RPM (Fedora / RHEL / CentOS / Amazon Linux)
```bash
# RPM not yet available — use pip:
pip install netcheckx
```
*RPM packaging is on the roadmap for v2.5.0.*

### Option 5 — AUR (Arch / Manjaro)
```bash
yay -S netcheck
```

### Option 6 — Binary Tarball (Any Linux, no pip needed)
```bash
wget https://github.com/farman20ali/network_access_check/releases/download/v2.3.0/netcheck-2.3.0-linux-x86_64.tar.gz
tar xzf netcheck-2.3.0-linux-x86_64.tar.gz
sudo mv netcheck /usr/local/bin/
netcheck --version
```

## Uninstall

| Method | Command |
|---|---|
| pip | `pip uninstall netcheckx` |
| snap | `sudo snap remove netcheck` |
| deb | `sudo apt remove netcheck` |
| tarball | `sudo rm /usr/local/bin/netcheck` |
| AUR | `yay -R netcheck` |

## For Maintainers — Building the Binary Tarball

Uses PyInstaller to create a single-file binary with no Python dependency:

```bash
pip install pyinstaller
pyinstaller --onefile --name netcheck netcheck/__main__.py
# Output: dist/netcheck
tar czf netcheck-2.3.0-linux-x86_64.tar.gz -C dist netcheck
```

Add to CI (release.yml):
```yaml
- name: Build Linux binary
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: pip install pyinstaller netcheckx
    - run: pyinstaller --onefile --name netcheck netcheck/__main__.py
    - run: tar czf netcheck-${{ env.VERSION }}-linux-x86_64.tar.gz -C dist netcheck
    - uses: actions/upload-artifact@v4
      with:
        name: linux-binary
        path: netcheck-*.tar.gz
```
```

---

### 4.6 Windows (`packaging/windows/`)

**`packaging/windows/README.md`:**
```markdown
# Windows Packaging

## Install Options

### Option 1 — winget (Recommended for Windows 10/11)
```powershell
winget install farman20ali.netcheck
```

### Option 2 — Chocolatey
```powershell
choco install netcheck
```

### Option 3 — NSIS Installer (.exe)
Download `netcheck-2.3.0-setup.exe` from GitHub Releases.
Run as Administrator. NetCheck is added to PATH automatically.

### Option 4 — pip
```powershell
pip install netcheckx
netcheck --version
```

### Option 5 — Scoop (no admin needed)
```powershell
# Add the bucket (once you create it):
scoop bucket add farman20ali https://github.com/farman20ali/scoop-netcheck
scoop install netcheck
```

## Notes

- ICMP ping (`-p / --ping`) requires **Administrator** on Windows
  (Windows restricts raw socket access to admin)
- All other features (TCP, DNS, HTTP, SSL, traceroute, WHOIS, scan) work without admin
- Tested on Windows 10 21H2+ and Windows 11

## Uninstall

| Method | Command |
|---|---|
| winget | `winget uninstall farman20ali.netcheck` |
| Chocolatey | `choco uninstall netcheck` |
| .exe installer | Control Panel → Add/Remove Programs → NetCheck |
| pip | `pip uninstall netcheckx` |
| Scoop | `scoop uninstall netcheck` |

## For Maintainers — Building the .exe

Uses NSIS (Nullsoft Scriptable Install System):

```bash
# Install NSIS on Windows, then:
makensis packaging/windows/installer.nsi

# Or via GitHub Actions (Windows runner):
- name: Build Windows installer
  runs-on: windows-latest
  steps:
    - run: pip install pyinstaller
    - run: pyinstaller --onefile --name netcheck netcheck/__main__.py
    - run: makensis packaging/windows/installer.iss
```
```

---

## 5. Alerting Design — Credential Storage

You asked the right question: **how does a user securely provide SMTP credentials?**

The answer is: **never store credentials in a flag or a command**. Three layered approaches, in order of preference:

### 5.1 Config File (Primary Method)

```bash
netcheck config init          # Interactive wizard — asks questions, writes file
netcheck config edit          # Opens config in $EDITOR
netcheck config show          # Print current config (masks passwords)
netcheck config path          # Print path to config file
```

Config stored at OS-appropriate path:
- Linux/macOS: `~/.config/netcheck/config.yaml`
- Windows: `%APPDATA%\netcheck\config.yaml`
- File permissions set to `600` (owner-read-only) automatically

**`~/.config/netcheck/config.yaml`:**
```yaml
# NetCheck Configuration
# Created by: netcheck config init

defaults:
  timeout: 5
  jobs: 10
  format: text
  retry: 1

alerts:
  # Alert only on state CHANGE (up→down or down→up)
  # Not on every failure — prevents alert storms
  on_state_change: true
  cooldown_seconds: 300      # minimum gap between repeat alerts

  email:
    enabled: false
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_tls: true           # STARTTLS
    smtp_ssl: false          # SSL/TLS on connect (port 465)
    username: you@gmail.com
    # password: stored in system keychain — see below
    from: you@gmail.com
    to:
      - ops@company.com
      - you@gmail.com
    subject_prefix: "[NetCheck Alert]"

  slack:
    enabled: false
    webhook_url: https://hooks.slack.com/services/T.../B.../xxx
    channel: "#alerts"       # optional override
    mention: "@oncall"       # optional mention on alert

  webhook:
    enabled: false
    url: https://your-pagerduty-or-custom-url.com/event
    method: POST
    headers:
      Authorization: "Bearer YOUR_TOKEN"
      Content-Type: "application/json"
    # payload template — {host}, {port}, {status}, {timestamp} are substituted
    payload_template: |
      {
        "event": "netcheck_alert",
        "host": "{host}",
        "port": "{port}",
        "status": "{status}",
        "timestamp": "{timestamp}"
      }

  desktop:
    enabled: false           # OS native notification (plyer)
```

### 5.2 SMTP Password → System Keychain (Best Practice)

Never store plain passwords in the config file. Use OS keychain:

```bash
netcheck config set-password email    # Prompts securely, stores in keychain
netcheck config clear-password email  # Removes from keychain
```

**Implementation using `keyring` library:**
```python
import keyring

# Store
keyring.set_password("netcheck-email", config["alerts"]["email"]["username"], password)

# Retrieve (at runtime, never written to disk)
password = keyring.get_password("netcheck-email", username)
```

Keychain backends:
- macOS: Keychain Access (automatic)
- Windows: Windows Credential Manager (automatic)
- Linux: GNOME Keyring or KWallet (via `secretstorage`)
- Linux (headless/server): falls back to encrypted file via `keyrings.alt`

### 5.3 Environment Variables (CI/Server Use)

For CI pipelines and servers where interactive keychain isn't available:

```bash
# Environment variables — always override config file
export NETCHECK_SMTP_HOST=smtp.gmail.com
export NETCHECK_SMTP_PORT=587
export NETCHECK_SMTP_USER=you@gmail.com
export NETCHECK_SMTP_PASSWORD=your-app-password
export NETCHECK_SMTP_TO=ops@company.com
export NETCHECK_SLACK_WEBHOOK=https://hooks.slack.com/...
export NETCHECK_WEBHOOK_URL=https://pagerduty.com/...
export NETCHECK_WEBHOOK_TOKEN=Bearer xyz123

# Then just use --alert without any credentials inline
netcheck tcp api.example.com 443 -w --alert email
netcheck tcp api.example.com 443 -w --alert slack
```

Priority order: **env vars > config file > defaults**

### 5.4 Gmail-Specific Note

Gmail requires App Passwords (not your account password) when 2FA is on:
1. Go to myaccount.google.com → Security → App Passwords
2. Generate a password for "Mail" + "Other device"
3. Use that 16-character password, NOT your Gmail password

Add this to `packaging/*/README.md` under the alerts section.

### 5.5 Alert CLI Usage

```bash
# One-time setup (run once per machine)
netcheck config init

# Then use alerts naturally
netcheck tcp api.example.com 443 -w --alert email
netcheck tcp db.prod.com 3306 -w --alert slack
netcheck tcp host.com 443 -w --alert email,slack      # multiple
netcheck tcp host.com 443 -w --alert webhook
netcheck tcp host.com 443 -w --alert desktop          # pop-up notification

# Works with batch mode too
netcheck hosts.txt -w --alert slack --interval 60

# Custom alert thresholds
netcheck tcp api.example.com 443 -w --alert slack \
  --alert-cooldown 600                               # max 1 alert per 10 min
```

### 5.6 Alert State Logic

```
State Machine per host:port:
  UNKNOWN → (first check) → UP or DOWN
  UP → (failure) → DOWN → send alert "host:port is DOWN"
  DOWN → (success) → UP → send alert "host:port is back UP"
  DOWN → (failure) → DOWN → no alert (cooldown applies)
  UP → (success) → UP → no alert
```

This prevents alert storms on transient failures.

---

## 6. Phase Plan (Updated)

### 🔴 Phase 1 — MCP + Packaging Completeness (v2.4.0) [3–4 weeks]

**MCP:**
- [ ] `netcheck/mcp_server.py` — stdio MCP server
- [ ] Wire all 10 subcommands as MCP tools
- [ ] `netcheck mcp install` / `netcheck mcp status`
- [ ] `tests/test_mcp.py`
- [ ] README: MCP section

**Packaging (new):**
- [ ] `packaging/homebrew/netcheck.rb` + tap repo
- [ ] `packaging/aur/PKGBUILD` + `.SRCINFO`
- [ ] `packaging/winget/manifests/` (3 yaml files)
- [ ] `packaging/linux/` README + binary tarball CI step
- [ ] `packaging/macos/` README + `.pkg` build script
- [ ] `packaging/windows/` README (NSIS already exists)
- [ ] CI: auto-update Homebrew formula on release tag
- [ ] CI: wingetcreate auto-submit on release tag

**Exit Codes (blocking for CI):**
- [ ] `exit 0` all pass, `exit 1` any fail, `exit 2` bad args, `exit 3` runtime error

---

### 🟠 Phase 2 — VSCode Extension (v2.5.0) [3–4 weeks]

- [ ] `packaging/vscode/` scaffold
- [ ] MCP server in TypeScript (spawns Python netcheck)
- [ ] Webview side panel with result cards
- [ ] Right-click context for hostname/IP/URL detection
- [ ] Status bar watch mode indicator
- [ ] Makefile: `vscode-build`, `vscode-publish`, `vscode-dev`
- [ ] CI: build + upload `.vsix` on release tag
- [ ] Publish to VS Code Marketplace

---

### 🟡 Phase 3 — Alerting + Prometheus + Config (v2.6.0) [4–6 weeks]

- [ ] `netcheck config init` interactive wizard
- [ ] `~/.config/netcheck/config.yaml` with masked display
- [ ] `netcheck config set-password email` → keychain
- [ ] `netcheck/utils/alerting.py` — email, Slack, webhook, desktop
- [ ] Alert state machine (UP/DOWN change detection)
- [ ] `--alert-cooldown` flag
- [ ] `netcheck serve --metrics --port 9090` Prometheus exporter
- [ ] ENV variable support for all credentials
- [ ] Gmail App Password note in docs

---

### 🟢 Phase 4 — Polish (v3.0.0)

- [ ] Rich color output (✅ green / ❌ red / ⚠️ yellow)
- [ ] Homebrew submission to homebrew-core (when 75+ stars)
- [ ] Docker image: `docker run --rm farman20ali/netcheck tcp google.com 443`
- [ ] UDP support: `netcheck udp 8.8.8.8 53`
- [ ] MTR-style combined ping+traceroute: `netcheck mtr google.com`
- [ ] Preset host lists: `netcheck preset aws / gcp / k8s`
- [ ] RPM packaging for Fedora/RHEL
- [ ] Scoop bucket for Windows (no-admin install)

---

## 7. Full Packaging Support Matrix (Target: v2.4.0)

| Platform | Method | Command |
|---|---|---|
| All | pip | `pip install netcheckx` |
| macOS | Homebrew tap | `brew tap farman20ali/netcheck && brew install netcheck` |
| Linux (Debian/Ubuntu) | apt / dpkg | `sudo dpkg -i netcheck_*.deb` |
| Linux (All) | Snap | `sudo snap install netcheck` |
| Linux (Arch) | AUR | `yay -S netcheck` |
| Linux (any) | Binary tarball | `tar xzf netcheck-*.tar.gz && sudo mv netcheck /usr/local/bin/` |
| Windows | winget | `winget install farman20ali.netcheck` |
| Windows | Chocolatey | `choco install netcheck` |
| Windows | NSIS .exe | Download + run installer |
| VSCode | Marketplace | `ext install farman20ali.netcheck` |

---

## 8. Competitive Differentiation (When v2.5.0 Ships)

NetCheck will be the only open-source network diagnostics tool that:

1. **Cross-platform** — pip/brew/winget/choco/deb/snap/AUR/tarball
2. **MCP-native** — every diagnostic exposed as a Claude tool
3. **VSCode extension** with side panel UI + MCP server bundled
4. **CI-first** — proper exit codes, JSON output, `--show` filtering
5. **10 diagnostics in one tool** — TCP, DNS, HTTP, SSL, ping, traceroute, WHOIS, port scan, interfaces, ports

No competitor has all five. That's the real moat.
