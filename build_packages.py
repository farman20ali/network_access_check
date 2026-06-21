#!/usr/bin/env python3
"""
build_packages.py — Cross-platform package build orchestration for netcheck.

Commands:
  --check   Diagnose available packaging tools
  --deb     Build Debian package  (Linux, uses dpkg-buildpackage)
  --rpm     Build RPM package     (Linux, uses rpmbuild — no alien needed)
  --snap    Build Snap package    (Linux, uses snapcraft --destructive-mode)
  --win     Build Windows .exe    (any OS with PyInstaller)
  --mac     Build macOS binary    (any OS with PyInstaller)
  --all     Build all formats supported on the current host OS
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys

# Force stdout and stderr to UTF-8 to prevent UnicodeEncodeError on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, TypeError):
    pass
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR  = REPO_ROOT / "dist"

# ── python executable (platform-aware) ────────────────────────────────────────
# On Windows 'python3' is not on PATH; use 'python'. On Unix prefer 'python3'.
PYTHON_CMD = "python" if platform.system().lower() == "windows" else "python3"


# ── helpers ────────────────────────────────────────────────────────────────────

def get_version() -> str:
    init = REPO_ROOT / "netcheck" / "__init__.py"
    m = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]', init.read_text())
    if not m:
        sys.exit("Error: cannot parse __version__ from netcheck/__init__.py")
    return m.group(1)


def tool_ok(name: str) -> bool:
    return shutil.which(name) is not None


def pyinstaller_ok() -> bool:
    if tool_ok("pyinstaller"):
        return True
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        return False


def run(cmd: list[str], description: str, cwd: Path | None = None) -> None:
    print(f"\n{'─'*60}\n▶ {description}\n$ {' '.join(cmd)}\n{'─'*60}")
    r = subprocess.run(cmd, cwd=str(cwd or REPO_ROOT))
    if r.returncode != 0:
        sys.exit(f"❌  Failed: {description} (exit {r.returncode})")
    print(f"✅  {description}")


def _rfc2822() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")


# ── --check ────────────────────────────────────────────────────────────────────

def run_check() -> None:
    plat = platform.system().lower()
    print(f"\n{'='*60}\nPackaging Tools Diagnostics\n{'='*60}")
    print(f"Host OS : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Version : {get_version()}\n")

    tools = {
        "dpkg-buildpackage": ("DEB build tool",        ["linux"]),
        "rpmbuild":          ("RPM build tool",        ["linux"]),
        "snapcraft":         ("Snap build tool",       ["linux"]),
        "pyinstaller":       ("PyInstaller (binary)",  ["linux","windows","darwin"]),
        "fakeroot":          ("fakeroot",              ["linux"]),
    }
    missing_host = []
    for tool, (desc, platforms) in tools.items():
        ok = pyinstaller_ok() if tool == "pyinstaller" else tool_ok(tool)
        rel = plat in platforms
        tag = "✅" if ok else ("❌" if rel else "➖")
        note = " ← needed" if (not ok and rel) else (" (other OS)" if not rel else "")
        print(f"  {tag}  {desc:<30} {tool}{note}")
        if not ok and rel:
            missing_host.append(tool)

    print()
    if missing_host:
        print(f"⚠️   Missing for this OS: {', '.join(missing_host)}")
        hints = {
            "dpkg-buildpackage": "sudo apt install dpkg-dev build-essential devscripts debhelper",
            "rpmbuild":          "sudo apt install rpm   OR   sudo dnf install rpm-build",
            "snapcraft":         "sudo snap install snapcraft --classic",
            "pyinstaller":       "pip install pyinstaller",
            "fakeroot":          "sudo apt install fakeroot",
        }
        for t in missing_host:
            print(f"    Install {t}: {hints.get(t,'')}")
    else:
        print("✅  All tools for this host are available.")


# ── --deb ──────────────────────────────────────────────────────────────────────

def _debian_skeleton(work: Path, version: str) -> None:
    """Write a minimal debian/ directory into *work* (temp copy of repo)."""
    debian = work / "debian"
    debian.mkdir(parents=True, exist_ok=True)
    (debian / "source").mkdir(exist_ok=True)

    maint_name  = os.environ.get("DEBFULLNAME") or "netcheck builder"
    maint_email = os.environ.get("DEBEMAIL")    or "netcheck@example.com"
    deb_ver     = f"{version}-1"

    # ── control ──
    (debian / "control").write_text(textwrap.dedent(f"""\
        Source: netcheck
        Section: utils
        Priority: optional
        Maintainer: {maint_name} <{maint_email}>
        Build-Depends: debhelper-compat (= 12)
        Standards-Version: 4.6.2
        Homepage: https://github.com/farman20ali/network_access_check
        Rules-Requires-Root: no

        Package: netcheck
        Architecture: all
        Depends: ${{misc:Depends}}, python3, python3-cryptography, iproute2 | net-tools, iputils-ping
        Description: Network connectivity checker (DNS, ping, HTTP, TCP, SSL)
         A cross-platform Python 3 engine for network diagnostics.
         Supports JSON/CSV/XML output, MCP server, and batch target testing.
    """))

    # ── rules ──
    rules = (
        "#!/usr/bin/make -f\n\n"
        "%:\n\tdh $@\n\n"
        "override_dh_auto_install:\n"
        "\tinstall -d debian/netcheck/usr/bin\n"
        "\tinstall -d debian/netcheck/usr/lib/python3/dist-packages\n"
        "\tcp -r netcheck debian/netcheck/usr/lib/python3/dist-packages/\n"
        "\tfind debian/netcheck/usr/lib/python3/dist-packages/netcheck "
        "-name '__pycache__' -exec rm -rf {} + 2>/dev/null || true\n"
        "\tprintf '#!/usr/bin/env python3\\nimport sys\\n"
        "from netcheck.cli import main\\nsys.exit(main())\\n' "
        "> debian/netcheck/usr/bin/netcheck\n"
        "\tchmod 755 debian/netcheck/usr/bin/netcheck\n\n"
        "override_dh_auto_test:\n\ttrue\n"
    )
    rfile = debian / "rules"
    rfile.write_text(rules)
    rfile.chmod(0o755)

    # ── copyright (required by Lintian) ──
    (debian / "copyright").write_text(textwrap.dedent("""\
        Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
        Upstream-Name: netcheck
        Upstream-Contact: https://github.com/farman20ali/network_access_check
        Source: https://github.com/farman20ali/network_access_check

        Files: *
        Copyright: 2024-2026 Network Tools <netcheck@example.com>
        License: GPL-3

        License: GPL-3
         On Debian systems, the full text of the GNU General Public
         License version 3 can be found in the file
         '/usr/share/common-licenses/GPL-3'.
    """))

    # ── changelog ──
    (debian / "changelog").write_text(textwrap.dedent(f"""\
        netcheck ({deb_ver}) stable; urgency=medium

          * Release {version} — cross-platform Python 3 engine.

         -- {maint_name} <{maint_email}>  {_rfc2822()}
    """))

    # ── source/format ──
    (debian / "source" / "format").write_text("3.0 (native)\n")


def _ignore_deb(dirpath: str, names: list) -> set:
    skip = {".git","__pycache__",".pytest_cache",".venv","venv",
            "dist","build","parts","prime","stage"}
    out = {n for n in names if n in skip or n.endswith(".egg-info")}
    return out


def build_deb() -> None:
    print("\n─── Building Debian Package (.deb) ───")
    for t in ("dpkg-buildpackage", "fakeroot"):
        if not tool_ok(t):
            sys.exit(f"Error: '{t}' not found.\n  Install: sudo apt install build-essential devscripts debhelper fakeroot dh-python python3-all")

    version = get_version()
    out_dir = DIST_DIR / "deb"
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="netcheck-deb-") as td:
        tmp   = Path(td)
        work  = tmp / "netcheck"
        shutil.copytree(REPO_ROOT, work, dirs_exist_ok=True, ignore=_ignore_deb)
        _debian_skeleton(work, version)

        before = {p.name for p in tmp.glob("*.deb")}
        run(["dpkg-buildpackage", "-us", "-uc", "-rfakeroot"],
            "dpkg-buildpackage", cwd=work)

        new_debs = [p for p in tmp.glob("*.deb") if p.name not in before]
        if not new_debs:
            sys.exit("Error: dpkg-buildpackage ran but no .deb was found.")

        new_debs.sort(key=lambda p: ("dbgsym" in p.name, p.name))
        dest = out_dir / new_debs[0].name
        shutil.copy2(new_debs[0], dest)
        print(f"\n✅  DEB package: {dest}")
        print(f"    Install with: sudo dpkg -i {dest}")


# ── --rpm ──────────────────────────────────────────────────────────────────────

def _rpm_spec(version: str) -> str:
    return textwrap.dedent(f"""\
        Name:           netcheck
        Version:        {version}
        Release:        1%{{?dist}}
        Summary:        Network connectivity checker (DNS, ping, HTTP, TCP, SSL)
        License:        GPL-3.0+
        URL:            https://github.com/farman20ali/network_access_check
        BuildArch:      noarch
        Requires:       python3

        %description
        A cross-platform Python 3 engine for network diagnostics.
        Supports JSON/CSV/XML output, MCP server, and batch target testing.

        %install
        # Copy Python package
        mkdir -p %{{buildroot}}/usr/lib/python3/site-packages
        cp -r %{{_sourcedir}}/netcheck %{{buildroot}}/usr/lib/python3/site-packages/
        find %{{buildroot}}/usr/lib/python3/site-packages/netcheck \\
            -name '__pycache__' -exec rm -rf {{}} + 2>/dev/null || true

        # Write entrypoint
        mkdir -p %{{buildroot}}/usr/bin
        cat > %{{buildroot}}/usr/bin/netcheck << 'EOF'
        #!/usr/bin/env python3
        import sys
        from netcheck.cli import main
        sys.exit(main())
        EOF
        chmod 755 %{{buildroot}}/usr/bin/netcheck

        %files
        /usr/bin/netcheck
        /usr/lib/python3/site-packages/netcheck

        %changelog
        * {datetime.now().strftime('%a %b %d %Y')} netcheck builder <builder@localhost> - {version}-1
        - Release {version}
    """)


def build_rpm() -> None:
    print("\n─── Building RPM Package (.rpm) ───")
    if not tool_ok("rpmbuild"):
        sys.exit(
            "Error: 'rpmbuild' not found.\n"
            "  On Ubuntu/Debian : sudo apt install rpm\n"
            "  On Fedora/RHEL   : sudo dnf install rpm-build"
        )

    version  = get_version()
    rpm_home = Path.home() / "rpmbuild"
    for d in ("BUILD","RPMS","SOURCES","SPECS","SRPMS"):
        (rpm_home / d).mkdir(parents=True, exist_ok=True)

    # Write spec file
    spec_path = rpm_home / "SPECS" / "netcheck.spec"
    spec_path.write_text(_rpm_spec(version))

    # Copy source tree into SOURCES so the spec can reference it
    src_dest = rpm_home / "SOURCES" / "netcheck"
    if src_dest.exists():
        shutil.rmtree(src_dest)
    shutil.copytree(REPO_ROOT / "netcheck", src_dest)

    run(["rpmbuild", "-bb",
         "--define", f"_sourcedir {rpm_home / 'SOURCES'}",
         str(spec_path)],
        "rpmbuild")

    # Find and copy output RPM
    out_dir = DIST_DIR / "rpm"
    out_dir.mkdir(parents=True, exist_ok=True)
    rpms = list((rpm_home / "RPMS").rglob("netcheck-*.rpm"))
    if not rpms:
        print("⚠️   rpmbuild succeeded but no .rpm was found in ~/rpmbuild/RPMS/")
        return
    for r in rpms:
        dest = out_dir / r.name
        shutil.copy2(r, dest)
        print(f"\n✅  RPM package: {dest}")
        print(f"    Install with: sudo rpm -i {dest}  OR  sudo dnf install {dest}")


# ── --snap ─────────────────────────────────────────────────────────────────────

def build_snap() -> None:
    print("\n─── Building Snap Package (.snap) ───")
    if not tool_ok("snapcraft"):
        sys.exit("Error: 'snapcraft' not found.\n  Install: sudo snap install snapcraft --classic")

    version = get_version()
    snap_dir  = REPO_ROOT / "snap"
    snap_dir.mkdir(parents=True, exist_ok=True)

    # ── render snapcraft.yaml template ──────────────────────────────────────
    src_yaml  = REPO_ROOT / "packaging" / "snap" / "snapcraft.yaml"
    dest_yaml = snap_dir / "snapcraft.yaml"
    if src_yaml.exists():
        txt = src_yaml.read_text()
        txt = txt.replace("{version}", version)
        dest_yaml.write_text(txt)
        print(f"Prepared snap/snapcraft.yaml with version {version}")
    else:
        print(f"⚠️   Template not found: {src_yaml}. Using existing snap/snapcraft.yaml if present.")

    # ── copy packaging/snap/gui/ → snap/gui/ (icon for Snap Store) ──────────
    src_gui = REPO_ROOT / "packaging" / "snap" / "gui"
    if src_gui.exists():
        dest_gui = snap_dir / "gui"
        if dest_gui.exists():
            shutil.rmtree(dest_gui)
        shutil.copytree(src_gui, dest_gui)
        print(f"Copied snap GUI assets ({', '.join(p.name for p in src_gui.iterdir())}) → snap/gui/")
    else:
        print("⚠️   No packaging/snap/gui/ found — snap will have no store icon.")

    try:
        # --destructive-mode: build on the host directly — no LXD/container needed
        run(["snapcraft", "pack", "--destructive-mode", "--verbose"], "snapcraft pack")
    finally:
        # Remove the temporary snap/ dir generated for the build
        if snap_dir.exists():
            shutil.rmtree(snap_dir)
            print("Cleaned up temporary snap/ directory.")
        # Remove snapcraft artefact folders from repo root
        for _folder in ("stage", "prime", "parts"):
            _p = REPO_ROOT / _folder
            if _p.exists():
                shutil.rmtree(_p)
                print(f"Cleaned up {_folder}/ from repo root.")

    snaps = list(REPO_ROOT.glob("netcheck_*.snap"))
    if snaps:
        out_dir = DIST_DIR / "snap"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / snaps[-1].name
        shutil.copy2(snaps[-1], dest)
        snaps[-1].unlink()  # remove from root
        print(f"\n✅  Snap package: {dest}")


# ── --win / --mac ──────────────────────────────────────────────────────────────

def _pyinstaller_build(name: str, out_subdir: str, exe_name: str,
                       icon: Path | None = None) -> None:
    """Run PyInstaller for *name* platform. Pass *icon* (Path) for Windows."""
    if not pyinstaller_ok():
        sys.exit("Error: PyInstaller not found.\n  Install: pip install pyinstaller")

    entry = REPO_ROOT / "netcheck" / "__main__.py"
    cmd = ["pyinstaller", "--onefile", "--name", "netcheck", "--clean"]
    if icon and icon.exists():
        cmd += ["--icon", str(icon)]
        print(f"Using icon: {icon}")
    elif icon:
        print(f"⚠️   Icon not found at {icon} — building without icon.")
    cmd.append(str(entry))
    run(cmd, f"PyInstaller ({name})")

    out_dir = DIST_DIR / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "dist" / exe_name
    if src.exists():
        dest = out_dir / exe_name
        shutil.copy2(src, dest)
        print(f"\n✅  {name} binary: {dest}")
    else:
        print(f"⚠️   PyInstaller finished but {exe_name} not found in dist/")


def build_win_installer(version: str) -> None:
    print("\n─── Building Windows NSIS Setup Installer ───")

    # Configure UTF-8 encoding for standard streams on Windows to avoid UnicodeEncodeError
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except Exception:
                    pass

        # Dynamic path enhancement for Windows build tools
        extra_paths = [
            r"C:\Program Files (x86)\NSIS",
            r"C:\Program Files\NSIS",
            r"C:\ProgramData\chocolatey\bin",
        ]
        path_env = os.environ.get("PATH", "")
        paths = [p.strip() for p in path_env.split(os.pathsep) if p.strip()]
        added = False
        for p in extra_paths:
            if os.path.exists(p) and p not in paths:
                paths.append(p)
                added = True
        if added:
            os.environ["PATH"] = os.pathsep.join(paths)

    if not tool_ok("makensis"):
        print("⚠️   makensis not found. Skipping Windows Installer build.")
        return

    nsi_template = REPO_ROOT / "packaging" / "windows" / "netcheck.nsi"
    if not nsi_template.exists():
        print(f"⚠️   NSIS template not found at {nsi_template}. Skipping.")
        return

    nsi_content = (
        nsi_template.read_text(encoding="utf-8")
        .replace("{version}", version)
        .replace("{repo_root}", str(REPO_ROOT.resolve()))
    )
    nsi_path = REPO_ROOT / "dist" / "netcheck.nsi"
    nsi_path.write_text(nsi_content, encoding="utf-8")
    run(["makensis", str(nsi_path)], "NSIS Compiler")
    print(f"✅  Windows NSIS Installer built at dist/win/netcheck-{version}-setup.exe")


def _build_win_installer_legacy(version: str) -> None:
    """Kept for reference – inline NSIS script used before packaging/ templates."""
    nsi_content = f"""
!define PRODUCT_NAME "netcheck"
!define PRODUCT_VERSION "{version}"
!define PRODUCT_PUBLISHER "Network Tools Team"
!define PRODUCT_WEB_SITE "https://github.com/farman20ali/network_access_check"

SetCompressor lzma

Name "${{PRODUCT_NAME}}"
OutFile "dist\\win\\netcheck-${{PRODUCT_VERSION}}-setup.exe"
InstallDir "$PROGRAMFILES64\\${{PRODUCT_NAME}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\win\\netcheck.exe"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "DisplayName" "${{PRODUCT_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}" "URLInfoAbout" "${{PRODUCT_WEB_SITE}}"

    # Add to system PATH (using registry)
    ReadRegStr $0 HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path"
    WriteRegExpandStr HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path" "$0;$INSTDIR"
    
    # Broadcast environment change (WM_SETTINGCHANGE)
    SendMessage 0x001A 0 0 /TIMEOUT=5000
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\netcheck.exe"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}"
SectionEnd
"""
    nsi_path = REPO_ROOT / "dist" / "netcheck.nsi"
    nsi_path.write_text(nsi_content, encoding="utf-8")
    
    run(["makensis", str(nsi_path)], "NSIS Compiler")
    print(f"✅  Windows NSIS Installer built at dist/win/netcheck-{version}-setup.exe")


def build_choco_package(version: str) -> None:
    print("\n─── Building Chocolatey Package ───")
    if not tool_ok("choco"):
        print("⚠️   choco not found. Skipping Chocolatey package build.")
        return

    choco_dir = REPO_ROOT / "dist" / "choco"
    choco_dir.mkdir(parents=True, exist_ok=True)
    tools_dir = choco_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)

    # Read .nuspec template from packaging/
    nuspec_template = REPO_ROOT / "packaging" / "chocolatey" / "netcheck.nuspec"
    install_template = REPO_ROOT / "packaging" / "chocolatey" / "tools" / "chocolateyInstall.ps1"
    uninstall_template = REPO_ROOT / "packaging" / "chocolatey" / "tools" / "chocolateyUninstall.ps1"

    if not nuspec_template.exists():
        print(f"⚠️   Chocolatey nuspec template not found at {nuspec_template}. Skipping.")
        return

    nuspec_content = nuspec_template.read_text(encoding="utf-8").replace("{version}", version)
    nuspec_path = choco_dir / "netcheck.nuspec"
    nuspec_path.write_text(nuspec_content, encoding="utf-8")

    # Copy install and uninstall scripts (NOT the .exe binary)
    if install_template.exists():
        install_content = install_template.read_text(encoding="utf-8").replace("{version}", version)
        (tools_dir / "chocolateyInstall.ps1").write_text(install_content, encoding="utf-8")
    
    if uninstall_template.exists():
        shutil.copy2(uninstall_template, tools_dir / "chocolateyUninstall.ps1")
    run(["choco", "pack", str(nuspec_path), "--outputdirectory", "."],"Chocolatey Packager", cwd=choco_dir)
    print(f"✅  Chocolatey package built at dist/choco/netcheck.{version}.nupkg")


def _build_choco_package_legacy(version: str) -> None:
    """Kept for reference – inline nuspec generation before packaging/ templates."""
    nuspec_content = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>netcheck</id>
    <version>{version}</version>
    <title>NetCheck</title>
    <authors>Network Tools Team</authors>
    <owners>Network Tools Team</owners>
    <projectUrl>https://github.com/farman20ali/network_access_check</projectUrl>
    <licenseUrl>https://github.com/farman20ali/network_access_check/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <description>Network connectivity checker with DNS, ping, HTTP, and SSL validation</description>
    <summary>A premium, cross-platform network diagnostic engine</summary>
    <tags>netcheck network ping dns ssl http diagnostic cli tool</tags>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>
"""
    nuspec_path = choco_dir / "netcheck.nuspec"
    nuspec_path.write_text(nuspec_content, encoding="utf-8")

    # Generate chocolateyInstall.ps1 (optional but recommended for completeness)
    install_ps1 = """$ErrorActionPreference = 'Stop';
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
# Embedded package automatically shims netcheck.exe
"""
    (tools_dir / "chocolateyInstall.ps1").write_text(install_ps1, encoding="utf-8")

    # Run choco pack
    run(["choco", "pack", str(nuspec_path), "--outputdirectory", "dist/choco"], "Chocolatey Packager", cwd=choco_dir)
    print(f"✅  Chocolatey package built at dist/choco/netcheck.{version}.nupkg")


def build_mac_pkg(version: str) -> None:
    print("\n─── Building macOS Installer Package (.pkg) ───")
    if not tool_ok("pkgbuild"):
        print("⚠️   pkgbuild not found. Skipping macOS .pkg build.")
        return

    pkg_dir = REPO_ROOT / "dist" / "mac_pkg"
    bin_dir = pkg_dir / "usr" / "local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    # Copy netcheck binary to usr/local/bin
    shutil.copy2(REPO_ROOT / "dist" / "mac" / "netcheck", bin_dir / "netcheck")

    pkg_out = REPO_ROOT / "dist" / "mac" / f"netcheck-{version}.pkg"
    
    run([
        "pkgbuild",
        "--root", str(pkg_dir),
        "--identifier", "com.netcheck.cli",
        "--version", version,
        "--install-location", "/",
        str(pkg_out)
    ], "pkgbuild")
    print(f"✅  macOS .pkg built at {pkg_out}")


def build_win() -> None:
    print("\n─── Building Windows Executable (.exe) ───")
    icon = REPO_ROOT / "assets" / "icons" / "icon.ico"
    _pyinstaller_build("Windows", "win", "netcheck.exe", icon=icon)
    version = get_version()
    build_win_installer(version)
    build_choco_package(version)


def build_mac() -> None:
    print("\n─── Building macOS Binary ───")
    _pyinstaller_build("macOS", "mac", "netcheck")
    version = get_version()
    build_mac_pkg(version)


def build_linux_bin() -> None:
    print("\n─── Building Linux Executable ───")
    _pyinstaller_build("Linux", "linux", "netcheck")


def build_pypi() -> None:
    print("\n─── Building PyPI Packages (Wheel + sdist) ───")
    if not tool_ok(PYTHON_CMD) and not tool_ok("python"):
        sys.exit("Error: python is not available")
    run([PYTHON_CMD, "-m", "build"], "PyPI Package Builder (wheel + sdist)")


# ── --all ──────────────────────────────────────────────────────────────────────

def build_all() -> None:
    plat    = platform.system().lower()
    version = get_version()
    print(f"\nBuilding all packages for {platform.system()} (netcheck v{version})…")
    results: dict[str, str] = {}

    if plat == "linux":
        try:
            build_pypi()
            results["PyPI (wheel/sdist)"] = "✅  Success"
        except SystemExit as e:
            results["PyPI (wheel/sdist)"] = f"❌  Failed — {e}"

        try:
            build_linux_bin()
            results["Linux Binary"] = "✅  Success"
        except SystemExit as e:
            results["Linux Binary"] = f"❌  Failed — {e}"

        for label, fn in [("DEB", build_deb), ("Snap", build_snap), ("RPM", build_rpm)]:
            try:
                fn()
                results[label] = "✅  Success"
            except SystemExit as e:
                results[label] = f"⚠️   Skipped — {e}"
    elif plat == "windows":
        try:
            build_win()
            results["Windows EXE"] = "✅  Success"
            results["Windows Installer"] = "✅  Success" if tool_ok("makensis") else "⚠️   Skipped (no makensis)"
            results["Chocolatey Package"] = "✅  Success" if tool_ok("choco") else "⚠️   Skipped (no choco)"
        except SystemExit as e:
            results["Windows builds"] = f"❌  Failed — {e}"
    elif plat == "darwin":
        try:
            build_mac()
            results["macOS Binary"] = "✅  Success"
            results["macOS PKG"] = "✅  Success" if tool_ok("pkgbuild") else "⚠️   Skipped (no pkgbuild)"
        except SystemExit as e:
            results["macOS builds"] = f"❌  Failed — {e}"
    else:
        sys.exit(f"Unsupported host OS: {plat}")

    print(f"\n{'='*50}\nBuild Summary\n{'='*50}")
    for pkg, status in results.items():
        print(f"  {pkg:<20}: {status}")
    print("="*50)


# ── CLI ────────────────────────────────────────────────────────────────────────

def sync_version(new_version: str) -> None:
    """Propagate *new_version* to every file that embeds the version string."""
    print(f"\nSynchronising version → {new_version}")

    _subs = [
        # (path_relative_to_REPO_ROOT, regex_pattern, replacement_template)
        ("netcheck/__init__.py",
         r'__version__\s*=\s*[\'"][^\'"]+[\'"]',
         f'__version__ = "{new_version}"'),
        ("pyproject.toml",
         r'(?m)^version\s*=\s*[\'"][^\'"]+[\'"]',
         f'version = "{new_version}"'),
        ("netcheck/mcp/server.py",
         r'"version":\s*[\'"][^\'"]+[\'"]',
         f'"version": "{new_version}"'),
        # packaging templates use literal {version} placeholders – skip regex here
    ]

    for rel, pattern, repl in _subs:
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"  ⚠️   {rel} not found – skipped")
            continue
        original = path.read_text(encoding="utf-8")
        updated  = re.sub(pattern, repl, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print(f"  ✓ {rel}")
        else:
            print(f"  – {rel}  (no change)")

    # packaging/snap/snapcraft.yaml keeps a literal '{version}' placeholder
    snap_yaml = REPO_ROOT / "packaging" / "snap" / "snapcraft.yaml"
    if snap_yaml.exists():
        txt = snap_yaml.read_text()
        txt = re.sub(r"version:\s*['\"][^'\"]+['\"]", f"version: '{new_version}'", txt)
        snap_yaml.write_text(txt)
        print(f"  ✓ packaging/snap/snapcraft.yaml")

    print("Version synchronisation complete!\n")


def main() -> None:
    p = argparse.ArgumentParser(
        description="netcheck package builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python build_packages.py --sync-version 2.1.0\n"
            "  python build_packages.py --check\n"
            "  python build_packages.py --deb\n"
            "  python build_packages.py --snap\n"
            "  python build_packages.py --all\n"
        )
    )
    p.add_argument("--check",        action="store_true",  help="Diagnose available packaging tools")
    p.add_argument("--sync-version", metavar="VERSION",    help="Sync VERSION to all config files (pyproject.toml, __init__.py, etc.)")
    p.add_argument("--pypi",         action="store_true",  help="Build PyPI wheel + sdist")
    p.add_argument("--linux",        action="store_true",  help="Build Linux binary (PyInstaller)")
    p.add_argument("--deb",          action="store_true",  help="Build Debian .deb")
    p.add_argument("--rpm",          action="store_true",  help="Build RPM")
    p.add_argument("--snap",         action="store_true",  help="Build Snap .snap")
    p.add_argument("--win",          action="store_true",  help="Build Windows exe + NSIS + Choco")
    p.add_argument("--mac",          action="store_true",  help="Build macOS binary + PKG")
    p.add_argument("--all",          action="store_true",  help="Build all for current OS")
    args = p.parse_args()

    if   args.sync_version: sync_version(args.sync_version)
    elif args.check:        run_check()
    elif args.pypi:         build_pypi()
    elif args.linux:        build_linux_bin()
    elif args.deb:          build_deb()
    elif args.rpm:          build_rpm()
    elif args.snap:         build_snap()
    elif args.win:          build_win()
    elif args.mac:          build_mac()
    elif args.all:          build_all()
    else:                   p.print_help()


if __name__ == "__main__":
    main()
