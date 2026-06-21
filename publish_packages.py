#!/usr/bin/env python3
"""
publish_packages.py — netcheck publish orchestrator
====================================================
Mirrors the flag-based interface of build_packages.py but for *publishing*
already-built artefacts to public stores.

Usage examples
--------------
  python3 publish_packages.py --check                     # verify all publish tools
  python3 publish_packages.py --pypi                      # upload to PyPI (production)
  python3 publish_packages.py --pypi --test               # upload to TestPyPI first
  python3 publish_packages.py --snap                      # push to Snap Store (stable)
  python3 publish_packages.py --snap --channel edge       # push to edge/beta/candidate
  python3 publish_packages.py --chocolatey                # push nupkg to Chocolatey.org

Environment variables (optional, avoids interactive prompts)
------------------------------------------------------------
  TWINE_USERNAME / TWINE_PASSWORD   — PyPI credentials (or __token__ / API key)
  SNAPCRAFT_STORE_CREDENTIALS       — Snapcraft exported credentials
  CHOCO_API_KEY                     — Chocolatey.org API key
"""

import argparse
import os
import platform
import subprocess
import sys

# Force stdout and stderr to UTF-8 to prevent UnicodeEncodeError on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, TypeError):
    pass
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.resolve()
DIST_DIR  = REPO_ROOT / "dist"

# ── Python executable (platform-aware) ───────────────────────────────────────
PYTHON_CMD = "python" if platform.system().lower() == "windows" else "python3"

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.resolve()
DIST_DIR  = REPO_ROOT / "dist"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tool_ok(name: str) -> bool:
    """Return True if *name* is findable on PATH."""
    return subprocess.run(
        ["which", name] if os.name != "nt" else ["where", name],
        capture_output=True
    ).returncode == 0


def _run(cmd: list, label: str) -> None:
    """Run *cmd*, print output live, and abort on non-zero exit."""
    sep = "─" * 60
    print(f"\n{sep}\n▶ {label}\n$ {' '.join(cmd)}\n{sep}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        sys.exit(f"\n❌  {label} failed (exit {result.returncode})")
    print(f"✅  {label}")


def _glob_newest(pattern: str, sub: str = "") -> Path | None:
    """Return the newest file matching *pattern* inside dist/[sub]."""
    search_dir = DIST_DIR / sub if sub else DIST_DIR
    matches = sorted(search_dir.glob(pattern))
    return matches[-1] if matches else None


# ── --check ───────────────────────────────────────────────────────────────────

def run_check() -> None:
    """Print availability of all publish-time tools."""
    print("\n─── Publish tool diagnostic ───\n")
    tools = {
        "twine"      : "pip install twine",
        "snapcraft"  : "sudo snap install snapcraft --classic",
        "choco"      : "https://chocolatey.org/install  (Windows only)",
        "gh"         : "https://cli.github.com  (optional, for GitHub Releases)",
    }
    all_ok = True
    for tool, install_hint in tools.items():
        ok  = _tool_ok(tool)
        sym = "✅" if ok else "❌"
        hint = "" if ok else f"  →  {install_hint}"
        print(f"  {sym}  {tool:<14}{hint}")
        if not ok:
            all_ok = False
    print()
    if all_ok:
        print("✅  All publish tools are available.")
    else:
        print("⚠️   Install the missing tools before publishing.")


# ── --pypi ────────────────────────────────────────────────────────────────────

def publish_pypi(test: bool = False) -> None:
    """Upload wheel + sdist to PyPI (or TestPyPI when *test* is True)."""
    print(f"\n─── Publishing to {'TestPyPI' if test else 'PyPI'} ───")

    if not _tool_ok("twine"):
        sys.exit("❌  twine not found.\n  Install: pip install twine")

    # Collect artefacts
    artefacts = list(DIST_DIR.glob("netcheckx-*.whl")) + list(DIST_DIR.glob("netcheckx-*.tar.gz"))
    if not artefacts:
        sys.exit(
            "❌  No wheel / sdist found in dist/.\n"
            f"  Run first:  {PYTHON_CMD} build_packages.py --pypi"
        )

    print("  Artefacts to upload:")
    for a in sorted(artefacts):
        print(f"    {a.name}")

    cmd = ["twine", "upload"]
    if test:
        cmd += ["--repository", "testpypi"]
    cmd += [str(a) for a in sorted(artefacts)]

    _run(cmd, f"twine upload → {'TestPyPI' if test else 'PyPI'}")
    store_url = "https://test.pypi.org/project/netcheckx/" if test else "https://pypi.org/project/netcheckx/"
    print(f"\n🔗  View at: {store_url}")


# ── --snap ────────────────────────────────────────────────────────────────────

def publish_snap(channel: str = "stable") -> None:
    """Upload the newest .snap to the Snap Store and release to *channel*."""
    print(f"\n─── Publishing to Snap Store (channel: {channel}) ───")

    if not _tool_ok("snapcraft"):
        sys.exit("❌  snapcraft not found.\n  Install: sudo snap install snapcraft --classic")

    snap_file = _glob_newest("*.snap", sub="snap")
    if snap_file is None:
        # Also check root-level snaps (leftover from older builds)
        snap_file = _glob_newest("netcheck_*.snap")
    if snap_file is None:
        sys.exit(
            "❌  No .snap file found in dist/snap/ or repo root.\n"
            f"  Run first:  {PYTHON_CMD} build_packages.py --snap"
        )

    print(f"  Snap file: {snap_file.name}")

    # Upload — snapcraft upload returns the revision number
    print(f"\n  Uploading {snap_file.name} …")
    upload_result = subprocess.run(
        ["snapcraft", "upload", str(snap_file), "--release", channel],
        cwd=REPO_ROOT,
        capture_output=False,
    )
    if upload_result.returncode != 0:
        sys.exit("❌  snapcraft upload failed.")

    print(f"\n✅  Snap published to channel '{channel}'.")
    print("🔗  View at: https://snapcraft.io/netcheck")

    # Show current channel status
    print()
    subprocess.run(["snapcraft", "status", "netcheck"], cwd=REPO_ROOT)


# ── --chocolatey ──────────────────────────────────────────────────────────────

def publish_chocolatey() -> None:
    """Push the newest .nupkg to Chocolatey.org."""
    print("\n─── Publishing to Chocolatey ───")

    if not _tool_ok("choco"):
        sys.exit(
            "❌  choco not found. Chocolatey is Windows-only.\n"
            "  Install: https://chocolatey.org/install"
        )

    nupkg = _glob_newest("netcheck.*.nupkg", sub="choco")
    if nupkg is None:
        sys.exit(
            "❌  No .nupkg found in dist/choco/.\n"
            f"  Run first:  {PYTHON_CMD} build_packages.py --win"
        )

    print(f"  Package: {nupkg.name}")

    api_key = os.environ.get("CHOCO_API_KEY", "")
    cmd = ["choco", "push", str(nupkg), "--source", "https://push.chocolatey.org/"]
    if api_key:
        cmd += ["--api-key", api_key]
    else:
        print("  ℹ️   CHOCO_API_KEY not set — you will be prompted for it.")

    _run(cmd, "choco push → Chocolatey.org")
    print("🔗  View at: https://community.chocolatey.org/packages/netcheck")


# ── --github-release (optional helper) ───────────────────────────────────────

def publish_github_release(tag: str) -> None:
    """Create a GitHub release for *tag* and attach all dist artefacts."""
    print(f"\n─── Creating GitHub Release {tag} ───")

    if not _tool_ok("gh"):
        sys.exit(
            "❌  gh (GitHub CLI) not found.\n"
            "  Install: https://cli.github.com"
        )

    # Collect all dist artefacts (wheel, sdist, deb, snap, nupkg)
    artefacts: list[Path] = []
    artefacts += list(DIST_DIR.glob("*.whl"))
    artefacts += list(DIST_DIR.glob("*.tar.gz"))
    artefacts += list((DIST_DIR / "deb").glob("*.deb"))
    artefacts += list((DIST_DIR / "snap").glob("*.snap"))
    artefacts += list((DIST_DIR / "choco").glob("*.nupkg"))

    if not artefacts:
        sys.exit("❌  No artefacts found in dist/. Build them first.")

    notes_path = REPO_ROOT / "docs" / "releases" / f"RELEASE_NOTES_V{tag.lstrip('v').replace('.', '.')}.md"
    notes_flag = ["--notes-file", str(notes_path)] if notes_path.exists() else ["--generate-notes"]

    cmd = (
        ["gh", "release", "create", tag,
         "--title", f"netcheck {tag}",
         "--latest"]
        + notes_flag
        + [str(a) for a in sorted(artefacts)]
    )
    _run(cmd, f"gh release create {tag}")
    print(f"🔗  https://github.com/farman20ali/network_access_check/releases/tag/{tag}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="netcheck publish orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  {PYTHON_CMD} publish_packages.py --check\n"
            f"  {PYTHON_CMD} publish_packages.py --pypi --test\n"
            f"  {PYTHON_CMD} publish_packages.py --pypi\n"
            f"  {PYTHON_CMD} publish_packages.py --snap\n"
            f"  {PYTHON_CMD} publish_packages.py --snap --channel edge\n"
            f"  {PYTHON_CMD} publish_packages.py --chocolatey\n"
            f"  {PYTHON_CMD} publish_packages.py --github-release v2.1.0\n"
        )
    )

    p.add_argument("--check",            action="store_true",
                   help="Verify all publish tools are installed")
    p.add_argument("--pypi",             action="store_true",
                   help="Upload wheel + sdist to PyPI")
    p.add_argument("--test",             action="store_true",
                   help="(With --pypi) upload to TestPyPI instead of production")
    p.add_argument("--snap",             action="store_true",
                   help="Upload .snap to Snap Store")
    p.add_argument("--channel",          default="stable", metavar="CHANNEL",
                   help="Snap channel to release to: stable|candidate|beta|edge  (default: stable)")
    p.add_argument("--chocolatey",       action="store_true",
                   help="Push .nupkg to Chocolatey.org")
    p.add_argument("--github-release",   metavar="TAG",
                   help="Create a GitHub Release for TAG and attach all dist artefacts")

    args = p.parse_args()

    if args.check:
        run_check()
    elif args.pypi:
        publish_pypi(test=args.test)
    elif args.snap:
        publish_snap(channel=args.channel)
    elif args.chocolatey:
        publish_chocolatey()
    elif args.github_release:
        publish_github_release(tag=args.github_release)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
