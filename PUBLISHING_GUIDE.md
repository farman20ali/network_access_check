# Publishing Quick Reference

## 📦 What We Have

You now have **3 ways** to distribute your `netcheck` tool:

| Method | Command | Users Install With | Best For |
|--------|---------|-------------------|----------|
| **Manual** | `sudo ./install.sh` | Same | Development, local testing |
| **DEB Package** | `./build-deb.sh` | `sudo dpkg -i netcheck_1.0.0.deb` | Debian/Ubuntu users |
| **Snap Package** | `./build-snap.sh` | `sudo snap install netcheck` | All Linux distributions |

---

## 🎯 Makefile Purpose

### What is a Makefile?
A **build automation tool** that provides convenient shortcuts for common tasks.

### Why do we need it?
Instead of typing long commands, users can type simple ones:

```bash
# Without Makefile - Hard to remember
sudo bash install.sh
rm -f result.txt fail-*.txt combined-*.txt

# With Makefile - Easy to remember
make install
make clean
```

### Available Commands
```bash
make              # Show help
make install      # Install system-wide (sudo ./install.sh)
make uninstall    # Remove installation (sudo ./uninstall.sh)
make test         # Run basic tests
make clean        # Remove temporary files
```

### Professional Standard
Most open-source projects use Makefiles. Users expect these commands:
- ✅ `make install` - Universal installation command
- ✅ `make test` - Standard testing command
- ✅ `make clean` - Standard cleanup command

---

## 📥 DEB Package (Ubuntu/Debian)

### What is it?
A `.deb` file is the standard package format for Debian-based Linux (Ubuntu, Debian, Linux Mint, etc.)

### Build DEB Package
```bash
./build-deb.sh
# Creates: netcheck_1.0.0.deb
```

### Test Locally
```bash
# Install
sudo dpkg -i netcheck_1.0.0.deb

# Fix dependencies if needed
sudo apt-get install -f

# Test
netcheck --help
netcheck -q google.com 443

# Uninstall
sudo apt remove netcheck
```

### Publish Options

#### Option 1: Ubuntu PPA (Free, Easy)
```bash
# 1. Create account at https://launchpad.net/
# 2. Install tools
sudo apt install devscripts debhelper

# 3. Upload to PPA
dput ppa:yourusername/netcheck netcheck_1.0.0.deb

# 4. Users install with:
sudo add-apt-repository ppa:yourusername/netcheck
sudo apt update
sudo apt install netcheck
```

#### Option 2: GitHub Releases (Simple)
```bash
# 1. Create GitHub release
# 2. Upload netcheck_1.0.0.deb as asset
# 3. Users download and install:
wget https://github.com/user/netcheck/releases/download/v1.0.0/netcheck_1.0.0.deb
sudo dpkg -i netcheck_1.0.0.deb
```

#### Option 3: Custom Repository (Advanced)
```bash
# Host .deb on your own server
# See DEB_PACKAGING.md for full instructions
```

---

## 📦 Snap Package (Universal Linux)

### What is it?
A **universal package** that works on Ubuntu, Debian, Fedora, Arch, and other distributions. Auto-updates included!

### Prerequisites
```bash
# Install snapcraft
sudo snap install snapcraft --classic
```

### Build Snap Package
```bash
./build-snap.sh
# Creates: netcheck_1.0.0_amd64.snap
```

### Test Locally
```bash
# Install in devmode (for testing)
sudo snap install netcheck_1.0.0_amd64.snap --devmode --dangerous

# Test
netcheck --help
netcheck -q google.com 443

# Check logs if issues
snap logs netcheck

# Uninstall
sudo snap remove netcheck
```

### Publish to Snap Store (Recommended!)

#### Step 1: Create Account
- Go to https://snapcraft.io/
- Sign up with Ubuntu One account

#### Step 2: Login
```bash
snapcraft login
```

#### Step 3: Register Name (One-time)
```bash
snapcraft register netcheck
```

#### Step 4: Upload Package
```bash
snapcraft upload netcheck_1.0.0_amd64.snap
# Returns revision number (e.g., 1)
```

#### Step 5: Release to Channel
```bash
# Release to stable (production)
snapcraft release netcheck 1 stable

# Or test first with beta
snapcraft release netcheck 1 beta
```

#### Step 6: Check Status
```bash
snapcraft status netcheck
```

#### Users Install From Store
```bash
# One simple command - works on ALL Linux!
sudo snap install netcheck

# Auto-updates enabled by default! 🎉
```

---

## 🚀 Publishing Comparison

### DEB Package
**Pros:**
- ✅ Standard for Debian/Ubuntu
- ✅ No sandboxing restrictions
- ✅ Can use `apt` commands
- ✅ Familiar to sysadmins

**Cons:**
- ❌ Only works on Debian-based distros
- ❌ Manual updates required
- ❌ Dependency management needed

**Best for:** Traditional Linux users, enterprise environments

### Snap Package
**Pros:**
- ✅ Works on ALL Linux distributions
- ✅ Auto-updates automatically
- ✅ Sandboxed (more secure)
- ✅ Single Snap Store for all distros
- ✅ Easy CI/CD integration

**Cons:**
- ❌ Slightly larger package size
- ❌ Sandboxing can limit functionality
- ❌ Requires snapd installed

**Best for:** Cross-distribution support, auto-updates

### Recommendation
**Publish BOTH!**
- DEB for traditional Debian/Ubuntu users
- Snap for universal compatibility and auto-updates

---

## 📋 Publishing Checklist

### Before Publishing
- [ ] Test all features work correctly
- [ ] Update version number in all files
- [ ] Update README.md with installation instructions
- [ ] Create GitHub repository (if not exists)
- [ ] Add LICENSE file (e.g., MIT)
- [ ] Test installation on clean system

### DEB Package
- [ ] Build: `./build-deb.sh`
- [ ] Test: `sudo dpkg -i netcheck_1.0.0.deb`
- [ ] Verify: `netcheck --help`
- [ ] Create GitHub release
- [ ] Upload .deb as release asset
- [ ] Update README with download link

### Snap Package
- [ ] Build: `./build-snap.sh`
- [ ] Test: `sudo snap install netcheck_*.snap --devmode --dangerous`
- [ ] Verify: `netcheck --help`
- [ ] Create Snapcraft.io account
- [ ] Login: `snapcraft login`
- [ ] Register: `snapcraft register netcheck`
- [ ] Upload: `snapcraft upload netcheck_*.snap`
- [ ] Release: `snapcraft release netcheck <rev> stable`
- [ ] Update README with snap install command

---

## 📖 Files Summary

| File | Purpose |
|------|---------|
| `Makefile` | Build automation shortcuts |
| `MAKEFILE_GUIDE.md` | Explains Makefile purpose |
| `DEB_PACKAGING.md` | Full DEB packaging guide |
| `SNAP_PACKAGING.md` | Full Snap packaging guide |
| `build-deb.sh` | Automated DEB builder |
| `build-snap.sh` | Automated Snap builder |

---

## 🎓 Summary

### Makefile
- Provides **convenient shortcuts** (`make install`, `make test`)
- Industry **standard practice**
- Makes project **professional**

### DEB Package
- For **Debian/Ubuntu** users
- Traditional package format
- Can publish to **Ubuntu PPA** or GitHub releases

### Snap Package
- For **ALL Linux distributions**
- **Auto-updates** automatically
- Publish to **Snap Store** (recommended!)

### Quick Start
```bash
# Build both packages
./build-deb.sh    # Creates .deb
./build-snap.sh   # Creates .snap

# Test DEB
sudo dpkg -i netcheck_1.0.0.deb

# Test Snap
sudo snap install netcheck_1.0.0_amd64.snap --devmode --dangerous

# Publish Snap (easiest!)
snapcraft login
snapcraft register netcheck
snapcraft upload netcheck_1.0.0_amd64.snap
snapcraft release netcheck 1 stable
```

---

## 📚 Resources

- **Snap Store**: https://snapcraft.io/
- **Launchpad (PPA)**: https://launchpad.net/
- **Debian Packaging**: https://www.debian.org/doc/manuals/maint-guide/
- **Snapcraft Docs**: https://snapcraft.io/docs

---

**Recommendation:** Start with **Snap** - it's the easiest to publish and works everywhere!
