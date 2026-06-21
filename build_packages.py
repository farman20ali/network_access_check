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
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR  = REPO_ROOT / "dist"


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
    yaml    = REPO_ROOT / "snap" / "snapcraft.yaml"
    if yaml.exists():
        txt = yaml.read_text()
        txt = re.sub(r"version:\s*['\"].*?['\"]", f"version: '{version}'", txt)
        yaml.write_text(txt)
        print(f"Updated snap/snapcraft.yaml version → {version}")

    # --destructive-mode: build on the host directly — no LXD/container needed
    run(["snapcraft", "pack", "--destructive-mode", "--verbose"], "snapcraft pack")

    snaps = list(REPO_ROOT.glob("netcheck_*.snap"))
    if snaps:
        out_dir = DIST_DIR / "snap"
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / snaps[-1].name
        shutil.copy2(snaps[-1], dest)
        print(f"\n✅  Snap package: {dest}")


# ── --win / --mac ──────────────────────────────────────────────────────────────

def _pyinstaller_build(name: str, out_subdir: str, exe_name: str) -> None:
    if not pyinstaller_ok():
        sys.exit("Error: PyInstaller not found.\n  Install: pip install pyinstaller")

    entry = REPO_ROOT / "netcheck" / "cli.py"
    run(["pyinstaller", "--onefile", "--name", "netcheck", "--clean", str(entry)],
        f"PyInstaller ({name})")

    out_dir = DIST_DIR / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    src = REPO_ROOT / "dist" / exe_name
    if src.exists():
        dest = out_dir / exe_name
        shutil.copy2(src, dest)
        print(f"\n✅  {name} binary: {dest}")
    else:
        print(f"⚠️   PyInstaller finished but {exe_name} not found in dist/")


def build_win() -> None:
    print("\n─── Building Windows Executable (.exe) ───")
    _pyinstaller_build("Windows", "win", "netcheck.exe")


def build_mac() -> None:
    print("\n─── Building macOS Binary ───")
    _pyinstaller_build("macOS", "mac", "netcheck")


# ── --all ──────────────────────────────────────────────────────────────────────

def build_all() -> None:
    plat    = platform.system().lower()
    version = get_version()
    print(f"\nBuilding all packages for {platform.system()} (netcheck v{version})…")
    results: dict[str, str] = {}

    if plat == "linux":
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
        except SystemExit as e:
            results["Windows EXE"] = f"❌  Failed — {e}"
    elif plat == "darwin":
        try:
            build_mac()
            results["macOS Binary"] = "✅  Success"
        except SystemExit as e:
            results["macOS Binary"] = f"❌  Failed — {e}"
    else:
        sys.exit(f"Unsupported host OS: {plat}")

    print(f"\n{'='*50}\nBuild Summary\n{'='*50}")
    for pkg, status in results.items():
        print(f"  {pkg:<20}: {status}")
    print("="*50)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(description="netcheck package builder")
    p.add_argument("--check", action="store_true", help="Diagnose packaging tools")
    p.add_argument("--deb",   action="store_true", help="Build Debian .deb")
    p.add_argument("--rpm",   action="store_true", help="Build RPM (no alien needed)")
    p.add_argument("--snap",  action="store_true", help="Build Snap .snap")
    p.add_argument("--win",   action="store_true", help="Build Windows .exe (PyInstaller)")
    p.add_argument("--mac",   action="store_true", help="Build macOS binary (PyInstaller)")
    p.add_argument("--all",   action="store_true", help="Build all for current OS")
    args = p.parse_args()

    if   args.check: run_check()
    elif args.deb:   build_deb()
    elif args.rpm:   build_rpm()
    elif args.snap:  build_snap()
    elif args.win:   build_win()
    elif args.mac:   build_mac()
    elif args.all:   build_all()
    else:            p.print_help()


if __name__ == "__main__":
    main()
