"""
Subcommand dispatcher for NetCheck CLI.

Each subcommand (tcp, dns, http, ssl, ping, interfaces, ports,
traceroute, scan, whois, mcp) is handled by a dedicated private
helper, keeping routing logic clean.
"""
import sys
import argparse
from typing import List

from netcheck.cli.args import make_base_parser
from netcheck.cli.executor import run_check_with_retry
from netcheck.cli.exitcodes import EXIT_OK, EXIT_FAIL, EXIT_BAD_ARGS, EXIT_ERROR

# Module-level imports for the check functions used most frequently
from netcheck.modules.tcp import check_tcp_connect
from netcheck.modules.dns import dns_lookup
from netcheck.modules.http import check_http_status
from netcheck.modules.ssl import check_ssl_certificate
from netcheck.modules.ping import ping_host
from netcheck.modules.interfaces import get_network_interfaces
from netcheck.utils.formatters import format_text, format_json, format_csv, format_xml
from netcheck.utils.range_expanders import expand_ip_range, expand_port_range
from concurrent.futures import ThreadPoolExecutor, as_completed


# ---------------------------------------------------------------------------
# Output helper
# ---------------------------------------------------------------------------

def _fmt_output(results, fmt: str, verbose: bool = False, use_color=None) -> str:
    if fmt == "json":
        return format_json(results)
    elif fmt == "csv":
        return format_csv(results)
    elif fmt == "xml":
        return format_xml(results)
    return format_text(results, verbose=verbose, use_color=use_color)


# ---------------------------------------------------------------------------
# Per-subcommand argument builders
# ---------------------------------------------------------------------------

def _build_tcp_parser(base: argparse.ArgumentParser, env_jobs: int) -> None:
    base.add_argument("host")
    base.add_argument("port")
    base.add_argument("-j", "--jobs", type=int, default=env_jobs)
    base.add_argument("-o", "--output")
    base.add_argument("--show", default="all", choices=["all", "success", "fail"])


def _build_dns_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("host")


def _build_http_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("url")
    base.add_argument("--method", "-X", default="GET",
                      choices=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"])
    base.add_argument("--header", "-H", action="append", dest="headers")
    base.add_argument("--auth")


def _build_ssl_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("host")
    base.add_argument("port", type=int, nargs="?", default=443)


def _build_ping_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("host")
    base.add_argument("-c", "--count", type=int, default=4)


def _build_interfaces_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("--all", action="store_true")
    base.add_argument("--public", action="store_true")


def _build_traceroute_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("host")
    base.add_argument("-m", "--max-hops", type=int, default=30)


def _build_scan_parser(base: argparse.ArgumentParser, env_jobs: int) -> None:
    base.add_argument("host")
    base.add_argument("-p", "--ports",
                      help="Comma-separated ports or range, e.g. 80-100")
    base.add_argument("-j", "--jobs", type=int, default=env_jobs)


def _build_whois_parser(base: argparse.ArgumentParser) -> None:
    base.add_argument("target")


# ---------------------------------------------------------------------------
# Per-subcommand execution helpers
# ---------------------------------------------------------------------------

def _run_tcp(args, env_jobs: int) -> bool:
    """Run TCP check with optional range expansion and output filtering."""
    from netcheck.cli.batch import _format_output
    hosts = expand_ip_range(args.host)
    ports = expand_port_range(args.port)
    targets = [(h, p) for h in hosts for p in ports]

    if not targets:
        print("Error: No valid host or port specified", file=sys.stderr)
        return False

    from netcheck.cli.executor import execute_concurrent_checks
    results = execute_concurrent_checks(
        targets, args.timeout, getattr(args, "jobs", env_jobs),
        args.retry, args.retry_delay, verbose=args.verbose,
    )

    show_filter = getattr(args, "show", "all")
    if show_filter == "success":
        display = [r for r in results if r["success"]]
    elif show_filter == "fail":
        display = [r for r in results if not r["success"]]
    else:
        display = results

    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format

    if display:
        print(_fmt_output(display, fmt, verbose=args.verbose, use_color=use_color))
    else:
        label = "successful" if show_filter == "success" else "failed"
        print(f"No {label} results to display.")

    output_file = getattr(args, "output", None)
    if output_file:
        try:
            with open(output_file, "w") as fh:
                fh.write(_fmt_output(display, fmt, verbose=args.verbose, use_color=False))
            print(f"Results saved to: {output_file} ({len(display)} items)")
        except Exception as exc:
            print(f"Error saving results: {exc}", file=sys.stderr)

    return all(r["success"] for r in results)


def _run_dns(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    res = run_check_with_retry(dns_lookup, (args.host, args.timeout),
                               retries=args.retry, delay=args.retry_delay)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_http(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    custom_headers = {}
    if args.headers:
        for hdr in args.headers:
            if ":" in hdr:
                k, v = hdr.split(":", 1)
                custom_headers[k.strip()] = v.strip()
    auth_tuple = None
    if args.auth and ":" in args.auth:
        user, pw = args.auth.split(":", 1)
        auth_tuple = (user, pw)
    res = run_check_with_retry(
        check_http_status,
        (args.url, args.timeout),
        kwargs={"method": args.method, "headers": custom_headers or None, "auth": auth_tuple},
        retries=args.retry,
        delay=args.retry_delay,
    )
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_ssl(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    res = run_check_with_retry(check_ssl_certificate, (args.host, args.port, args.timeout),
                               retries=args.retry, delay=args.retry_delay)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_ping(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    res = run_check_with_retry(ping_host, (args.host, args.count, args.timeout),
                               retries=args.retry, delay=args.retry_delay)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_interfaces(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    res = get_network_interfaces(all_interfaces=args.all, include_public=args.public)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_ports(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    from netcheck.modules.interfaces import check_listening_ports
    res = check_listening_ports()
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_traceroute(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    from netcheck.modules.traceroute import traceroute as run_traceroute
    res = run_traceroute(args.host, max_hops=args.max_hops, timeout=args.timeout)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_scan(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    from netcheck.modules.port_scanner import scan_ports
    port_list = None
    if args.ports:
        try:
            if "-" in args.ports:
                start_p, end_p = map(int, args.ports.split("-"))
                port_list = list(range(start_p, end_p + 1))
            else:
                port_list = [int(p.strip()) for p in args.ports.split(",")]
        except ValueError:
            print("Error: Invalid ports format. Use e.g. 80,443 or 80-100", file=sys.stderr)
            sys.exit(EXIT_BAD_ARGS)
    res = scan_ports(args.host, ports=port_list, timeout=args.timeout,
                     max_workers=getattr(args, "jobs", 20))
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_whois(args) -> bool:
    use_color = None if not args.no_color else False
    fmt = "json" if args.json else args.format
    from netcheck.modules.whois import lookup_registration
    res = lookup_registration(args.target)
    print(_fmt_output([res], fmt, verbose=args.verbose, use_color=use_color))
    return res["success"]


def _run_mcp(sub_args: List[str]) -> None:
    """Handle: netcheck mcp [install|status]"""
    if not sub_args or sub_args[0] == "start":
        from netcheck.mcp.server import start_mcp_server
        start_mcp_server()
    elif sub_args[0] == "install":
        from netcheck.mcp.commands import cmd_mcp_install
        cmd_mcp_install()
    elif sub_args[0] == "status":
        from netcheck.mcp.commands import cmd_mcp_status
        cmd_mcp_status()
    else:
        print(f"Unknown mcp subcommand: {sub_args[0]}", file=sys.stderr)
        print("Usage: netcheck mcp [install|status]", file=sys.stderr)
        sys.exit(EXIT_BAD_ARGS)


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

SUBCOMMANDS = frozenset({
    "tcp", "dns", "http", "ssl", "ping",
    "interfaces", "ports", "traceroute", "scan", "whois", "mcp",
})


def handle_subcommands(
    subcommand: str,
    sub_args: List[str],
    env_timeout: float = 5.0,
    env_jobs: int = 10,
    env_no_color: bool = False,
) -> None:
    """
    Parse sub_args for the given subcommand, execute once or in watch loop.
    Calls sys.exit() with the correct exit code.
    """
    # MCP doesn't follow the watch/format pattern
    if subcommand == "mcp":
        _run_mcp(sub_args)
        return

    base = make_base_parser(
        f"netcheck {subcommand}",
        env_timeout=env_timeout,
        env_jobs=env_jobs,
        env_no_color=env_no_color,
    )

    # Attach subcommand-specific positional/optional args
    if subcommand == "tcp":
        _build_tcp_parser(base, env_jobs)
    elif subcommand == "dns":
        _build_dns_parser(base)
    elif subcommand == "http":
        _build_http_parser(base)
    elif subcommand == "ssl":
        _build_ssl_parser(base)
    elif subcommand == "ping":
        _build_ping_parser(base)
    elif subcommand == "interfaces":
        _build_interfaces_parser(base)
    elif subcommand == "ports":
        pass  # no extra args
    elif subcommand == "traceroute":
        _build_traceroute_parser(base)
    elif subcommand == "scan":
        _build_scan_parser(base, env_jobs)
    elif subcommand == "whois":
        _build_whois_parser(base)
    else:
        base.print_help()
        sys.exit(EXIT_BAD_ARGS)

    args = base.parse_args(sub_args)

    # Map subcommand name → execute_fn
    _dispatch = {
        "tcp":        lambda: _run_tcp(args, env_jobs),
        "dns":        lambda: _run_dns(args),
        "http":       lambda: _run_http(args),
        "ssl":        lambda: _run_ssl(args),
        "ping":       lambda: _run_ping(args),
        "interfaces": lambda: _run_interfaces(args),
        "ports":      lambda: _run_ports(args),
        "traceroute": lambda: _run_traceroute(args),
        "scan":       lambda: _run_scan(args),
        "whois":      lambda: _run_whois(args),
    }
    execute_fn = _dispatch[subcommand]

    if args.watch:
        from netcheck.cli.watch import run_watch_loop
        run_watch_loop(execute_fn, args.interval)
    else:
        try:
            success = execute_fn()
            sys.exit(EXIT_OK if success else EXIT_FAIL)
        except Exception as exc:
            print(f"Unexpected error: {exc}", file=sys.stderr)
            sys.exit(EXIT_ERROR)
