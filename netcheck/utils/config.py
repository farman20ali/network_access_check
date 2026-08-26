"""
netcheck.utils.config
~~~~~~~~~~~~~~~~~~~~~

Cross-platform configuration management for netcheck.

Config file locations:
  Linux/macOS: ~/.config/netcheck/config.yaml
  Windows:     %APPDATA%\\netcheck\\config.yaml

Priority (highest to lowest):
  1. Environment variables (NETCHECK_*)
  2. Config file (~/.config/netcheck/config.yaml)
  3. Built-in defaults

Passwords are NEVER stored in the config file.
They are always retrieved from the OS keychain via keyring.
"""

from __future__ import annotations

import json
import os
import platform
import stat
import sys
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Default configuration schema
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    "timeout": 5,
    "max_workers": 10,
    "retry": {
        "max_attempts": 3,
        "delay": 1.0,
        "backoff": 2.0,
    },
    "smtp": {
        "host": "",
        "port": 587,
        "user": "",
        "to": "",
        "use_tls": True,
    },
    "slack": {
        "webhook_url": "",
    },
    "webhook": {
        "url": "",
        "token": "",
    },
    "prometheus": {
        "enabled": False,
        "port": 9090,
        "host": "0.0.0.0",
    },
    "alert": {
        "flap_threshold": 2,
        "cooldown_seconds": 300,
    },
}

# ---------------------------------------------------------------------------
# Environment variable → config key mappings
# ---------------------------------------------------------------------------

_ENV_MAP: dict[str, tuple[str, ...]] = {
    "NETCHECK_TIMEOUT": ("timeout",),
    "NETCHECK_MAX_WORKERS": ("max_workers",),
    "NETCHECK_SMTP_HOST": ("smtp", "host"),
    "NETCHECK_SMTP_PORT": ("smtp", "port"),
    "NETCHECK_SMTP_USER": ("smtp", "user"),
    "NETCHECK_SMTP_TO": ("smtp", "to"),
    "NETCHECK_SLACK_WEBHOOK": ("slack", "webhook_url"),
    "NETCHECK_WEBHOOK_URL": ("webhook", "url"),
    "NETCHECK_WEBHOOK_TOKEN": ("webhook", "token"),
    "NETCHECK_PROMETHEUS_PORT": ("prometheus", "port"),
}

# ---------------------------------------------------------------------------
# Keychain service name
# ---------------------------------------------------------------------------

_KEYCHAIN_SERVICE = "netcheck"


# ---------------------------------------------------------------------------
# NetCheckConfig
# ---------------------------------------------------------------------------

class NetCheckConfig:
    """Loads, validates, and saves the netcheck config file."""

    # ── Paths ──────────────────────────────────────────────────────────────

    @staticmethod
    def path() -> Path:
        """Return the OS-appropriate config file path."""
        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            return Path(appdata) / "netcheck" / "config.yaml"
        # Linux / macOS
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "netcheck" / "config.yaml"

    # ── Load ───────────────────────────────────────────────────────────────

    @staticmethod
    def load() -> dict[str, Any]:
        """Load config with env-var overrides merged on top."""
        import copy

        cfg = copy.deepcopy(_DEFAULTS)
        config_path = NetCheckConfig.path()

        if config_path.exists():
            try:
                raw = _yaml_load(config_path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    _deep_merge(cfg, raw)
            except Exception as exc:
                # Malformed config — warn but continue with defaults
                print(
                    f"[netcheck] Warning: could not parse config at {config_path}: {exc}",
                    file=sys.stderr,
                )

        # Apply environment variable overrides
        for env_key, path in _ENV_MAP.items():
            val = os.environ.get(env_key)
            if val is not None:
                _set_nested(cfg, path, _coerce(val))

        return cfg

    # ── Save ───────────────────────────────────────────────────────────────

    @staticmethod
    def save(data: dict[str, Any]) -> None:
        """Write config YAML. Sets chmod 600 on POSIX platforms."""
        config_path = NetCheckConfig.path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(_yaml_dump(data), encoding="utf-8")
        if platform.system() != "Windows":
            os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)

    # ── Show ───────────────────────────────────────────────────────────────

    @staticmethod
    def show() -> str:
        """Return config as YAML string with sensitive fields masked."""
        import copy

        cfg = NetCheckConfig.load()
        masked = copy.deepcopy(cfg)
        _mask_sensitive(masked)
        return _yaml_dump(masked)

    # ── Init wizard ────────────────────────────────────────────────────────

    @staticmethod
    def init_wizard() -> None:
        """Interactive prompt-based setup wizard."""
        print("NetCheck Configuration Wizard")
        print("=" * 40)
        cfg: dict[str, Any] = {}

        timeout = _prompt("Default timeout (seconds)", default="5")
        cfg["timeout"] = int(timeout)

        workers = _prompt("Max concurrent workers", default="10")
        cfg["max_workers"] = int(workers)

        use_smtp = _prompt("Configure SMTP alerts? [y/N]", default="n").lower()
        if use_smtp == "y":
            cfg["smtp"] = {
                "host": _prompt("SMTP host"),
                "port": int(_prompt("SMTP port", default="587")),
                "user": _prompt("SMTP username"),
                "to": _prompt("Alert recipient email"),
                "use_tls": True,
            }

        use_slack = _prompt("Configure Slack alerts? [y/N]", default="n").lower()
        if use_slack == "y":
            cfg["slack"] = {"webhook_url": _prompt("Slack webhook URL")}

        NetCheckConfig.save(cfg)
        print(f"\n✅ Configuration saved to: {NetCheckConfig.path()}")

    # ── Keychain ───────────────────────────────────────────────────────────

    @staticmethod
    def set_password(service: str) -> None:
        """Prompt for password securely and store in OS keychain."""
        import getpass

        password = getpass.getpass(f"Password for {service}: ")
        _keyring_set(_KEYCHAIN_SERVICE, service, password)
        print(f"✅ Password stored in keychain for service '{service}'.")

    @staticmethod
    def clear_password(service: str) -> None:
        """Remove password from OS keychain."""
        _keyring_delete(_KEYCHAIN_SERVICE, service)
        print(f"✅ Password removed from keychain for service '{service}'.")

    @staticmethod
    def get_password(service: str) -> Optional[str]:
        """Retrieve password from OS keychain (never from config file)."""
        return _keyring_get(_KEYCHAIN_SERVICE, service)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override into base in-place."""
    for key, val in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deep_merge(base[key], val)
        else:
            base[key] = val


def _set_nested(cfg: dict, path: tuple, value: Any) -> None:
    """Set a nested dict key from a tuple path."""
    for key in path[:-1]:
        cfg = cfg.setdefault(key, {})
    cfg[path[-1]] = value


def _coerce(value: str) -> Any:
    """Try to coerce a string value to int or float."""
    for converter in (int, float):
        try:
            return converter(value)
        except ValueError:
            pass
    return value


def _mask_sensitive(cfg: dict, _mask: str = "***") -> None:
    """Mask known sensitive keys in-place."""
    sensitive_keys = {"password", "token", "webhook_url", "secret", "api_key"}
    for key in list(cfg.keys()):
        if key in sensitive_keys:
            cfg[key] = _mask
        elif isinstance(cfg[key], dict):
            _mask_sensitive(cfg[key], _mask)


def _prompt(label: str, default: str = "") -> str:
    """Simple interactive prompt with optional default."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"{label}{suffix}: ").strip()
    return answer if answer else default


# ---------------------------------------------------------------------------
# Minimal YAML helpers (stdlib only — no PyYAML dependency)
# ---------------------------------------------------------------------------

def _yaml_load(text: str) -> Any:
    """
    Minimal YAML-compatible loader.
    Supports nested key: value and simple lists.
    Falls back to JSON if the text looks like JSON.
    """
    text = text.strip()
    if text.startswith("{") or text.startswith("["):
        return json.loads(text)
    return _parse_yaml_block(text.splitlines())


def _parse_yaml_block(lines: list[str], indent: int = 0) -> dict[str, Any]:
    """Recursive minimal YAML block parser."""
    result: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        if current_indent < indent:
            break
        if current_indent > indent:
            i += 1
            continue

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if ":" in stripped:
            raw_key, _, raw_val = stripped.partition(":")
            key = raw_key.strip()
            val = raw_val.strip()

            if not val:
                # Nested block: collect child lines
                child_lines: list[str] = []
                j = i + 1
                while j < len(lines):
                    cl = lines[j]
                    cs = cl.lstrip()
                    ci = len(cl) - len(cs)
                    if ci <= indent and cs and not cs.startswith("#"):
                        break
                    child_lines.append(cl)
                    j += 1
                result[key] = _parse_yaml_block(child_lines, indent + 2)
                i = j
                continue

            # Scalar value
            result[key] = _coerce_yaml_scalar(val)

        i += 1
    return result


def _coerce_yaml_scalar(val: str) -> Any:
    """Convert a YAML scalar string to a Python type."""
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    if val.lower() in ("null", "~", ""):
        return None
    # Strip quotes
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        return val[1:-1]
    for converter in (int, float):
        try:
            return converter(val)
        except ValueError:
            pass
    return val


def _yaml_dump(data: Any, indent: int = 0) -> str:
    """Minimal YAML dumper (no PyYAML dependency)."""
    lines: list[str] = []
    pad = "  " * indent

    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                lines.append(f"{pad}{key}:")
                lines.append(_yaml_dump(val, indent + 1))
            elif isinstance(val, list):
                lines.append(f"{pad}{key}:")
                for item in val:
                    lines.append(f"{pad}  - {item}")
            elif isinstance(val, bool):
                lines.append(f"{pad}{key}: {'true' if val else 'false'}")
            elif val is None:
                lines.append(f"{pad}{key}: ~")
            elif isinstance(val, str) and (":" in val or "#" in val or not val):
                lines.append(f'{pad}{key}: "{val}"')
            else:
                lines.append(f"{pad}{key}: {val}")
    else:
        lines.append(f"{pad}{data}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Keychain wrappers (optional dependency: keyring)
# ---------------------------------------------------------------------------

def _keyring_available() -> bool:
    try:
        import keyring  # noqa: F401
        return True
    except ImportError:
        return False


def _keyring_set(service: str, username: str, password: str) -> None:
    if _keyring_available():
        import keyring
        keyring.set_password(service, username, password)
    else:
        raise RuntimeError(
            "keyring package not installed. Run: pip install keyring"
        )


def _keyring_get(service: str, username: str) -> Optional[str]:
    if _keyring_available():
        import keyring
        return keyring.get_password(service, username)
    return None


def _keyring_delete(service: str, username: str) -> None:
    if _keyring_available():
        import keyring
        try:
            keyring.delete_password(service, username)
        except keyring.errors.PasswordDeleteError:
            pass
    else:
        raise RuntimeError(
            "keyring package not installed. Run: pip install keyring"
        )
