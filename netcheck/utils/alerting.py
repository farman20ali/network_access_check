"""
netcheck.utils.alerting
~~~~~~~~~~~~~~~~~~~~~~~

Alert dispatchers for netcheck.

Supported channels:
  - SMTP email (stdlib smtplib)
  - Slack incoming webhook
  - Generic HTTP webhook
  - Desktop notification (plyer, optional)

All dispatchers accept an AlertEvent and return a boolean success flag.
They NEVER raise — errors are caught and printed to stderr.

Usage::

    from netcheck.utils.alerting import AlertDispatcher
    from netcheck.utils.alert_state import AlertEvent
    from netcheck.utils.config import NetCheckConfig

    cfg = NetCheckConfig.load()
    dispatcher = AlertDispatcher(cfg)
    dispatcher.dispatch(event)
"""

from __future__ import annotations

import json
import smtplib
import ssl
import sys
import traceback
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

from netcheck.utils.alert_state import AlertEvent


# ---------------------------------------------------------------------------
# Alert message formatting
# ---------------------------------------------------------------------------

def _format_subject(event: AlertEvent) -> str:
    icon = "✅" if event.new_state == "UP" else "❌"
    return f"{icon} NetCheck ALERT: {event.target} is {event.new_state}"


def _format_body_plain(event: AlertEvent) -> str:
    lines = [
        f"NetCheck Alert",
        f"=============",
        f"Target  : {event.target}",
        f"Status  : {event.old_state} → {event.new_state}",
        f"Time    : {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Checks  : {event.consecutive} consecutive",
    ]
    if event.last_error:
        lines.append(f"Error   : {event.last_error}")
    return "\n".join(lines)


def _format_slack_payload(event: AlertEvent) -> dict[str, Any]:
    color = "good" if event.new_state == "UP" else "danger"
    icon = "✅" if event.new_state == "UP" else "❌"
    return {
        "text": f"{icon} *{event.target}* is *{event.new_state}*",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {"title": "Target", "value": event.target, "short": True},
                    {
                        "title": "State Change",
                        "value": f"{event.old_state} → {event.new_state}",
                        "short": True,
                    },
                    {
                        "title": "Time",
                        "value": event.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "short": True,
                    },
                    {
                        "title": "Consecutive Checks",
                        "value": str(event.consecutive),
                        "short": True,
                    },
                ]
                + (
                    [{"title": "Error", "value": event.last_error, "short": False}]
                    if event.last_error
                    else []
                ),
            }
        ],
    }


# ---------------------------------------------------------------------------
# Individual dispatchers
# ---------------------------------------------------------------------------

def send_email_alert(event: AlertEvent, smtp_cfg: dict) -> bool:
    """Send an SMTP email alert. Returns True on success."""
    host = smtp_cfg.get("host", "")
    port = int(smtp_cfg.get("port", 587))
    user = smtp_cfg.get("user", "")
    to_addr = smtp_cfg.get("to", "")
    use_tls = smtp_cfg.get("use_tls", True)

    if not all([host, user, to_addr]):
        return False

    # Retrieve password from keychain
    from netcheck.utils.config import NetCheckConfig
    password = NetCheckConfig.get_password("email") or ""

    subject = _format_subject(event)
    body = _format_body_plain(event)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        if use_tls:
            with smtplib.SMTP(host, port) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.login(user, password)
                smtp.sendmail(user, to_addr, msg.as_string())
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.login(user, password)
                smtp.sendmail(user, to_addr, msg.as_string())
        return True
    except Exception:
        print("[netcheck] Email alert failed:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False


def send_slack_alert(event: AlertEvent, webhook_url: str) -> bool:
    """Send a Slack incoming webhook alert. Returns True on success."""
    if not webhook_url:
        return False
    payload = _format_slack_payload(event)
    return _post_json(webhook_url, payload)


def send_webhook_alert(
    event: AlertEvent,
    url: str,
    token: Optional[str] = None,
) -> bool:
    """Send a generic JSON webhook alert. Returns True on success."""
    if not url:
        return False
    payload = {
        "target": event.target,
        "old_state": event.old_state,
        "new_state": event.new_state,
        "timestamp": event.timestamp.isoformat(),
        "consecutive": event.consecutive,
        "error": event.last_error,
    }
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _post_json(url, payload, headers=headers)


def send_desktop_notification(event: AlertEvent) -> bool:
    """Send a desktop notification via plyer (optional dep)."""
    try:
        from plyer import notification  # type: ignore

        title = _format_subject(event)
        message = f"{event.old_state} → {event.new_state}"
        notification.notify(title=title, message=message, app_name="NetCheck", timeout=10)
        return True
    except ImportError:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# AlertDispatcher
# ---------------------------------------------------------------------------

class AlertDispatcher:
    """
    Unified alert dispatcher. Reads channel config from the netcheck
    config dict and fires all configured channels.

    Usage::

        dispatcher = AlertDispatcher(cfg)
        dispatcher.dispatch(event)
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg = cfg

    def dispatch(self, event: AlertEvent) -> dict[str, bool]:
        """
        Fire all configured alert channels.

        Returns a dict of channel → success flag.
        """
        results: dict[str, bool] = {}

        smtp_cfg = self._cfg.get("smtp", {})
        if smtp_cfg.get("host") and smtp_cfg.get("to"):
            results["email"] = send_email_alert(event, smtp_cfg)

        slack_url = self._cfg.get("slack", {}).get("webhook_url", "")
        if slack_url:
            results["slack"] = send_slack_alert(event, slack_url)

        webhook = self._cfg.get("webhook", {})
        if webhook.get("url"):
            results["webhook"] = send_webhook_alert(
                event, webhook["url"], webhook.get("token")
            )

        results["desktop"] = send_desktop_notification(event)

        return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _post_json(
    url: str,
    payload: dict,
    headers: Optional[dict] = None,
    timeout: int = 10,
) -> bool:
    """HTTP POST JSON payload to *url*. Returns True on 2xx response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            **(headers or {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception:
        print(f"[netcheck] Webhook POST to {url!r} failed:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False
