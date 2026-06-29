import sys
import os
import time
import argparse
import csv
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional

from netcheck.modules.tcp import check_tcp_connect
from netcheck.modules.dns import dns_lookup
from netcheck.modules.http import check_http_status
from netcheck.modules.ssl import check_ssl_certificate
from netcheck.modules.ping import ping_host
from netcheck.modules.interfaces import get_network_interfaces
from netcheck.utils.formatters import format_text, format_json, format_csv, format_xml, get_colors
from netcheck.utils.range_expanders import expand_ip_range, expand_port_range
from netcheck.utils.normalize import parse_line_to_raw_host_port

def run_check_with_retry(check_fn, args=(), kwargs=None, retries=1, delay=1.0) -> Dict[str, Any]:
    """Runs a check function and retries it if it fails or returns success=False."""
    if kwargs is None:
        kwargs = {}
        
    attempt = 1
    result = None
    while attempt <= retries:
        try:
            result = check_fn(*args, **kwargs)
            if result.get("success", False):
                return result
        except Exception as e:
            result = {
                "target": str(args[0]) if args else "unknown",
                "status": "FAILED",
                "latency_ms": 0.0,
                "success": False,
                "error": str(e),
                "metadata": {}
            }
            
        if attempt < retries:
            time.sleep(delay)
        attempt += 1
        
    return result or {"success": False, "status": "FAILED", "target": "unknown", "error": "No attempts made"}

def parse_csv_content(content: str) -> List[Tuple[str, str]]:
    """Parses CSV content of hosts and ports."""
    targets = []
    try:
        reader = csv.reader(io.StringIO(content))
        # Skip header if it exists
        first_row = next(reader, None)
        if first_row:
            # Check if first row is header
            if len(first_row) >= 2 and (first_row[0].lower() in ("host", "target", "hostname") or first_row[1].lower() in ("port", "ports")):
                pass
            else:
                targets.append((first_row[0].strip(), first_row[1].strip()))
                
            for row in reader:
                if len(row) >= 2:
                    targets.append((row[0].strip(), row[1].strip()))
    except Exception as e:
        print(f"Error parsing CSV content: {e}", file=sys.stderr)
    return targets

def parse_csv_file(filepath: str) -> List[Tuple[str, str]]:
    """Parses a CSV file of hosts and ports."""
    try:
        with open(filepath, "r", newline="") as f:
            return parse_csv_content(f.read())
    except Exception as e:
        print(f"Error reading CSV file {filepath}: {e}", file=sys.stderr)
        return []

def parse_batch_content(content: str) -> List[Tuple[str, str]]:
    """Parses a lenient batch content containing targets (using parse_line_to_raw_host_port)."""
    targets = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        h, p = parse_line_to_raw_host_port(line)
        if h and p:
            targets.append((h, p))
        else:
            print(f"⚠️  Warning: skipping malformed line: '{stripped}'", file=sys.stderr)
    return targets

def parse_batch_file(filepath: str) -> List[Tuple[str, str]]:
    """Parses a lenient batch file of targets."""
    try:
        with open(filepath, "r") as f:
            return parse_batch_content(f.read())
    except Exception as e:
        print(f"Error reading batch file {filepath}: {e}", file=sys.stderr)
        return []

def print_help():
    cmd_name = "netcheck"
    if len(sys.argv) > 0:
        prog = sys.argv[0]
        if "netcheck" not in prog and ("__main__.py" in prog or "cli.py" in prog):
            cmd_name = "python3 -m netcheck"
            
    help_text = f"""Network Connectivity Checker - Advanced Version

Usage: {cmd_name} [OPTIONS] [input_file]
       {cmd_name} SUBCOMMAND [sub_args]

OPTIONS:
    -t, --timeout <seconds>     Connection timeout (default: 5)
    -j, --jobs <number>         Max parallel jobs (default: 10)
    -V, --verbose               Verbose output
    -f, --format <format>       Output format: text, json, csv, xml (default: text)
    -c, --combined              Create combined report with all results
    -q, --quick <host> <port>   Quick test mode (supports ranges: 80,443 or 8000-8100)
    -o, --output <file>         Save quick mode results to file
    -d, --dns <host>            Resolve DNS and show IP address (accepts URLs)
    -p, --ping <host>           Ping host using ICMP (accepts URLs/IPs)
    -s, --status <url>          Check HTTP/HTTPS status code and response time
    --cert <host>               Check SSL/TLS certificate validity and expiration
    --my-ip, -ip                Show all network interfaces and IP addresses (UP only)
    --my-ip --all               Show all interfaces including inactive ones
    --retry <number>            Retry failed connections N times (default: 1, no retry)
    --retry-delay <seconds>     Delay between retries in seconds (default: 1)
    --csv                       Input file is in CSV format (host,port)
    -h, --help                  Show this help message
    -v, --version               Show version information

SUBCOMMANDS (v2.2.0):
    tcp <host> <port>           Check TCP connectivity (accepts ranges)
    dns <host>                  Perform DNS lookup and show nameservers
    http <url>                  Validate HTTP response and size
    ssl <host> [port]           Validate SSL/TLS certificate validity
    ping <host>                 Ping host via native ICMP
    interfaces                  List local network interfaces
    ports                       List local listening ports and services (including Docker)
    traceroute <host>           Trace route to destination host
    scan <host>                 Perform quick concurrent port scan
    whois <target>              Lookup domain/IP registrar and registration details

WATCH MODE:
    Any subcommand can be looped/watched with:
      -w, --watch               Enable watch mode (clear screen and refresh)
      -i, --interval <seconds>  Refresh interval in seconds (default: 2.0)

INPUT:
    input_file                  File containing IP:port pairs (one per line)
                               If not specified, reads from stdin
                               Use --csv flag for CSV format files

EXAMPLES:
    {cmd_name} ip-text.txt                          # Basic usage
    {cmd_name} --csv hosts.csv                      # Read from CSV file
    {cmd_name} -t 10 -j 20 ip-text.txt             # Custom timeout and parallel jobs
    {cmd_name} -f json -c ip-text.txt              # JSON output with combined report
    cat ip-text.txt | {cmd_name} -V                 # Verbose mode from stdin
    {cmd_name} tcp google.com 80,443                # Subcommand TCP check
    {cmd_name} dns google.com                       # Subcommand DNS check
    {cmd_name} http https://google.com              # Subcommand HTTP check
    {cmd_name} ssl google.com                       # Subcommand SSL check
    {cmd_name} traceroute google.com                # Subcommand Traceroute
    {cmd_name} scan google.com                      # Subcommand Port Scan
    {cmd_name} whois google.com                     # Subcommand WHOIS/RDAP lookup
    {cmd_name} ports                                # Subcommand ports/services mapping
    {cmd_name} tcp google.com 443 -w -i 1           # Watch TCP connection every 1s
    {cmd_name} -q 10.0.0.1-50 22                    # Quick test IP range
    {cmd_name} -d google.com                        # Resolve DNS to IP
    {cmd_name} -p 8.8.8.8                           # Ping Google DNS
    {cmd_name} --my-ip                              # Show all network interfaces and IPs

INPUT FORMAT:
    Each line should contain: HOST PORT(S)
    
    Basic:      192.168.1.1 80
    IP Range:   192.168.1.1-50 80        (checks .1 through .50)
    CIDR:       192.168.1.0/24 80        (checks entire subnet)
    Multi-port: 192.168.1.1 80,443,8080  (checks multiple ports)
    Port Range: 192.168.1.1 8000-8100    (checks port range)
    Combined:   192.168.1.1-10 80,443    (IP range with multiple ports)
    
    CSV FORMAT (with --csv flag):
    host,port
    192.168.1.1,80
    server.com,443
    host.local,"80,443"     (multiple ports in quotes)"""
    print(help_text)

class NetCheckArgumentParser(argparse.ArgumentParser):
    """Custom parser to output advanced example-rich help on syntax or argument errors."""
    def error(self, message):
        print(f"Error: {message}\n", file=sys.stderr)
        print_help()
        sys.exit(2)

def main():
    # Force stdout and stderr to UTF-8 to prevent UnicodeEncodeError on Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, TypeError):
        pass

    import os
    env_timeout = 5.0
    if "NETCHECK_TIMEOUT" in os.environ:
        try:
            env_timeout = float(os.environ["NETCHECK_TIMEOUT"])
        except ValueError:
            pass
            
    env_jobs = 10
    if "NETCHECK_MAX_WORKERS" in os.environ:
        try:
            env_jobs = int(os.environ["NETCHECK_MAX_WORKERS"])
        except ValueError:
            pass

    # NO_COLOR env var (https://no-color.org/) or explicit flag detection
    env_no_color = ("NO_COLOR" in os.environ or "NETCHECK_NO_COLOR" in os.environ)

    if len(sys.argv) < 2:
        # Check if stdin has data
        if not sys.stdin.isatty():
            lines = sys.stdin.read().splitlines()
            run_batch_lines(lines, timeout=env_timeout, max_jobs=env_jobs, format_name="text", combined=False, retries=1, retry_delay=1.0, verbose=False)
            return
        print_help()
        sys.exit(1)
        
    first_arg = sys.argv[1]
    
    # 1. Redesigned Subcommand Route
    if first_arg in ("tcp", "dns", "http", "ssl", "ping", "interfaces", "traceroute", "scan", "whois", "ports"):
        handle_subcommands(first_arg, sys.argv[2:], env_timeout=env_timeout, env_jobs=env_jobs, env_no_color=env_no_color)
        return
        
    # 2. Legacy Parsing Route
    parser = NetCheckArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-q", "--quick", nargs=2)
    parser.add_argument("-d", "--dns")
    parser.add_argument("-p", "--ping")
    parser.add_argument("-s", "--status")
    parser.add_argument("--cert")
    parser.add_argument("-ip", "--my-ip", action="store_true")
    parser.add_argument("--mcp", action="store_true")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("-t", "--timeout", type=float, default=env_timeout)
    parser.add_argument("-j", "--jobs", type=int, default=env_jobs)
    parser.add_argument("-f", "--format", default="text", choices=["text", "json", "csv", "xml"])
    parser.add_argument("-c", "--combined", action="store_true")
    parser.add_argument("-o", "--output")
    parser.add_argument("--retry", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=1.0)
    parser.add_argument("-V", "--verbose", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--no-color", action="store_true", default=env_no_color, help="Disable ANSI color output")
    parser.add_argument("input_file", nargs="?")
    
    args, unknown = parser.parse_known_args()
    
    if args.help:
        print_help()
        sys.exit(0)
        
    if args.version:
        from netcheck import __version__
        print(f"netcheck version {__version__}")
        sys.exit(0)
        
    if args.mcp:
        from netcheck.mcp.server import start_mcp_server
        start_mcp_server()
        return
        
    # Apply format and parameters
    fmt = args.format
    timeout = args.timeout
    retries = args.retry
    retry_delay = args.retry_delay
    verbose = args.verbose
    
    if args.my_ip:
        res = get_network_interfaces(all_interfaces=args.all)
        print(format_output([res], fmt, verbose=verbose))
        sys.exit(0 if res["success"] else 1)
        
    if args.dns:
        res = run_check_with_retry(dns_lookup, (args.dns, timeout), retries=retries, delay=retry_delay)
        print(format_output([res], fmt, verbose=verbose))
        sys.exit(0 if res["success"] else 1)
        
    if args.ping:
        res = run_check_with_retry(ping_host, (args.ping, 4, timeout), retries=retries, delay=retry_delay)
        print(format_output([res], fmt, verbose=verbose))
        sys.exit(0 if res["success"] else 1)
        
    if args.status:
        res = run_check_with_retry(check_http_status, (args.status, timeout), retries=retries, delay=retry_delay)
        print(format_output([res], fmt, verbose=verbose))
        sys.exit(0 if res["success"] else 1)
        
    if args.cert:
        res = run_check_with_retry(check_ssl_certificate, (args.cert, 443, timeout), retries=retries, delay=retry_delay)
        print(format_output([res], fmt, verbose=verbose))
        sys.exit(0 if res["success"] else 1)
        
    if args.quick:
        host, port_str = args.quick
        run_quick_test(host, port_str, timeout, args.jobs, fmt, args.output, retries, retry_delay, verbose=verbose)
        return
        
    # Stdin or File Batch checks
    targets = []
    if args.csv:
        if args.input_file:
            targets = parse_csv_file(args.input_file)
        elif not sys.stdin.isatty():
            targets = parse_csv_content(sys.stdin.read())
        else:
            print("Error: No CSV input file or stdin stream provided", file=sys.stderr)
            sys.exit(1)
        run_batch_targets(targets, timeout, args.jobs, fmt, args.combined, retries, retry_delay, verbose=verbose)
        return
        
    if args.input_file:
        targets = parse_batch_file(args.input_file)
        run_batch_targets(targets, timeout, args.jobs, fmt, args.combined, retries, retry_delay, verbose=verbose)
        return
        
    # Stdin fallback if no args are matched
    if not sys.stdin.isatty():
        targets = parse_batch_content(sys.stdin.read())
        run_batch_targets(targets, timeout, args.jobs, fmt, args.combined, retries, retry_delay, verbose=verbose)
        return
        
    print_help()
    sys.exit(1)

def handle_subcommands(subcommand: str, sub_args: List[str], env_timeout: float = 5.0, env_jobs: int = 10, env_no_color: bool = False):
    parser = argparse.ArgumentParser(prog=f"netcheck {subcommand}")
    parser.add_argument("-t", "--timeout", type=float, default=env_timeout)
    parser.add_argument("-f", "--format", default="text", choices=["text", "json", "csv", "xml"])
    parser.add_argument("--retry", type=int, default=1)
    parser.add_argument("--retry-delay", type=float, default=1.0)
    parser.add_argument("-V", "--verbose", action="store_true")
    parser.add_argument("-w", "--watch", action="store_true", help="Watch/loop mode")
    parser.add_argument("-i", "--interval", type=float, default=2.0, help="Interval for watch mode in seconds")
    parser.add_argument("--no-color", action="store_true", default=env_no_color, help="Disable ANSI color output")
    
    if subcommand == "tcp":
        parser.add_argument("host")
        parser.add_argument("port")
        parser.add_argument("-j", "--jobs", type=int, default=env_jobs)
        parser.add_argument("-o", "--output")
        args = parser.parse_args(sub_args)
        
    elif subcommand == "dns":
        parser.add_argument("host")
        args = parser.parse_args(sub_args)
        
    elif subcommand == "http":
        parser.add_argument("url")
        parser.add_argument("--method", "-X", default="GET", choices=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"],
                            help="HTTP method (default: GET)")
        parser.add_argument("--header", "-H", action="append", dest="headers",
                            help="Custom header in 'Key: Value' format (repeatable)")
        parser.add_argument("--auth", help="Basic auth in 'user:pass' format")
        args = parser.parse_args(sub_args)
        
    elif subcommand == "ssl":
        parser.add_argument("host")
        parser.add_argument("port", type=int, nargs="?", default=443)
        args = parser.parse_args(sub_args)
        
    elif subcommand == "ping":
        parser.add_argument("host")
        parser.add_argument("-c", "--count", type=int, default=4)
        args = parser.parse_args(sub_args)
        
    elif subcommand == "interfaces":
        parser.add_argument("--all", action="store_true")
        args = parser.parse_args(sub_args)
        
    elif subcommand == "ports":
        args = parser.parse_args(sub_args)
        
    elif subcommand == "traceroute":
        parser.add_argument("host")
        parser.add_argument("-m", "--max-hops", type=int, default=30)
        args = parser.parse_args(sub_args)
        
    elif subcommand == "scan":
        parser.add_argument("host")
        parser.add_argument("-p", "--ports", help="Comma-separated list of ports to scan, or range e.g. 80-100")
        parser.add_argument("-j", "--jobs", type=int, default=env_jobs)
        args = parser.parse_args(sub_args)
        
    elif subcommand == "whois":
        parser.add_argument("target")
        args = parser.parse_args(sub_args)
        
    else:
        parser.print_help()
        sys.exit(1)

    def execute_once() -> bool:
        use_color = None if not args.no_color else False
        if subcommand == "tcp":
            return run_quick_test(
                args.host, args.port, args.timeout, args.jobs, 
                args.format, args.output, args.retry, args.retry_delay, 
                verbose=args.verbose, exit_on_complete=False
            )
        elif subcommand == "dns":
            res = run_check_with_retry(dns_lookup, (args.host, args.timeout), retries=args.retry, delay=args.retry_delay)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "http":
            # Parse custom headers from -H 'Key: Value' args
            custom_headers = {}
            if args.headers:
                for hdr in args.headers:
                    if ":" in hdr:
                        k, v = hdr.split(":", 1)
                        custom_headers[k.strip()] = v.strip()
            # Parse --auth user:pass
            auth_tuple = None
            if args.auth and ":" in args.auth:
                user, pw = args.auth.split(":", 1)
                auth_tuple = (user, pw)
            res = run_check_with_retry(
                check_http_status,
                (args.url, args.timeout),
                kwargs={"method": args.method, "headers": custom_headers or None, "auth": auth_tuple},
                retries=args.retry, delay=args.retry_delay
            )
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "ssl":
            res = run_check_with_retry(check_ssl_certificate, (args.host, args.port, args.timeout), retries=args.retry, delay=args.retry_delay)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "ping":
            res = run_check_with_retry(ping_host, (args.host, args.count, args.timeout), retries=args.retry, delay=args.retry_delay)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "interfaces":
            res = get_network_interfaces(all_interfaces=args.all)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "ports":
            from netcheck.modules.interfaces import check_listening_ports
            res = check_listening_ports()
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "traceroute":
            from netcheck.modules.traceroute import traceroute as run_traceroute
            res = run_traceroute(args.host, max_hops=args.max_hops, timeout=args.timeout)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "scan":
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
                    sys.exit(1)
            res = scan_ports(args.host, ports=port_list, timeout=args.timeout, max_workers=args.jobs)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        elif subcommand == "whois":
            from netcheck.modules.whois import lookup_registration
            res = lookup_registration(args.target)
            print(format_output([res], args.format, verbose=args.verbose, use_color=use_color))
            return res["success"]
        return False

    if args.watch:
        import platform
        import os
        import time
        from datetime import datetime
        
        def clear_screen():
            if platform.system().lower() == "windows":
                os.system("cls")
            else:
                os.system("clear")
                
        try:
            while True:
                clear_screen()
                print(f"NetCheck Watch Mode - Interval: {args.interval}s - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                execute_once()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nWatch mode stopped.")
            sys.exit(0)
    else:
        success = execute_once()
        sys.exit(0 if success else 1)

def run_quick_test(host: str, port_str: str, timeout: float, max_jobs: int, fmt: str, output_file: str, retries: int, retry_delay: float, verbose: bool = False, exit_on_complete: bool = True) -> bool:
    hosts = expand_ip_range(host)
    ports = expand_port_range(port_str)
    
    targets = []
    for h in hosts:
        for p in ports:
            targets.append((h, p))
            
    if not targets:
        print("Error: No valid host or port specified", file=sys.stderr)
        if exit_on_complete:
            sys.exit(1)
        return False
        
    results = execute_concurrent_checks(targets, timeout, max_jobs, retries, retry_delay, verbose=verbose)
    
    output_str = format_output(results, fmt, verbose=verbose)
    print(output_str)
    
    if output_file:
        try:
            with open(output_file, "w") as f:
                f.write(format_output(results, fmt, verbose=verbose, use_color=False))
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Error saving results to file {output_file}: {e}", file=sys.stderr)
            
    all_success = all(r["success"] for r in results)
    if exit_on_complete:
        sys.exit(0 if all_success else 1)
    return all_success

def run_batch_targets(targets: List[Tuple[str, str]], timeout: float, max_jobs: int, fmt: str, combined: bool, retries: int, retry_delay: float, verbose: bool = False):
    expanded_targets = []
    for host, p_str in targets:
        ports = expand_port_range(p_str)
        hosts = expand_ip_range(host)
        for h in hosts:
            for p in ports:
                expanded_targets.append((h, p))
            
    if not expanded_targets:
        print("Error: No targets found to test", file=sys.stderr)
        sys.exit(1)
        
    results = execute_concurrent_checks(expanded_targets, timeout, max_jobs, retries, retry_delay, verbose=verbose)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    ext = "json" if fmt == "json" else "csv" if fmt == "csv" else "xml" if fmt == "xml" else "txt"
    
    success_results = [r for r in results if r["success"]]
    fail_results = [r for r in results if not r["success"]]
    
    res_filename = f"result-{date_str}.{ext}"
    fail_filename = f"fail-{date_str}.{ext}"
    comb_filename = f"combined-{date_str}.{ext}"
    
    try:
        if success_results:
            with open(res_filename, "w") as f:
                f.write(format_output(success_results, fmt, verbose=verbose, use_color=False))
        if fail_results:
            with open(fail_filename, "w") as f:
                f.write(format_output(fail_results, fmt, verbose=verbose, use_color=False))
        if combined:
            with open(comb_filename, "w") as f:
                f.write(format_output(results, fmt, verbose=verbose, use_color=False))
                
        print(f"Check Complete! Results written to output files.")
        print(f"Successful checks written to: {res_filename} ({len(success_results)} items)")
        print(f"Failed checks written to: {fail_filename} ({len(fail_results)} items)")
        if combined:
            print(f"Combined report written to: {comb_filename}")
            
    except Exception as e:
        print(f"Error saving batch output files: {e}", file=sys.stderr)
        
    print(format_output(results, fmt, verbose=verbose))
    sys.exit(0 if len(fail_results) == 0 else 1)

def run_batch_lines(lines: List[str], timeout: float, max_jobs: int, format_name: str, combined: bool, retries: int, retry_delay: float, verbose: bool = False):
    content = "\n".join(lines)
    targets = parse_batch_content(content)
    run_batch_targets(targets, timeout, max_jobs, format_name, combined, retries, retry_delay, verbose=verbose)

def execute_concurrent_checks(targets: List[Tuple[str, int]], timeout: float, max_jobs: int, retries: int, retry_delay: float, verbose: bool = False) -> List[Dict[str, Any]]:
    results = []
    
    with ThreadPoolExecutor(max_workers=max_jobs) as executor:
        futures = {}
        for host, port in targets:
            fut = executor.submit(
                run_check_with_retry,
                check_tcp_connect,
                args=(host, int(port), timeout),
                retries=retries,
                delay=retry_delay
            )
            futures[fut] = (host, port)
            
        completed = 0
        total = len(targets)
        
        for fut in as_completed(futures):
            host, port = futures[fut]
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                res = {
                    "target": f"{host}:{port}",
                    "status": "FAILED",
                    "latency_ms": 0.0,
                    "success": False,
                    "error": str(e),
                    "metadata": {"host": host, "port": port}
                }
                results.append(res)
                
            completed += 1
            
            # Print real-time connection status if verbose is enabled
            if verbose:
                use_color = sys.stdout.isatty()
                c_ansi = get_colors(use_color)
                if res.get("success", False):
                    sys.stderr.write(f"{c_ansi['green']}✓ SUCCESS:{c_ansi['reset']} {host}:{port} ({res.get('latency_ms', '?')}ms)\n")
                else:
                    sys.stderr.write(f"{c_ansi['red']}✗ FAILED:{c_ansi['reset']} {host}:{port} ({res.get('error', 'unknown error')})\n")
                sys.stderr.flush()
            elif total > 5 and sys.stdout.isatty():
                sys.stdout.write(f"\rProgress: {completed}/{total} completed ({int(completed/total * 100)}%)...")
                sys.stdout.flush()
                
        if total > 5 and sys.stdout.isatty() and not verbose:
            print("")
            
    return results

def format_output(results: List[Dict[str, Any]], format_name: str, verbose: bool = False, use_color: Optional[bool] = None) -> str:
    if format_name == "json":
        return format_json(results)
    elif format_name == "csv":
        return format_csv(results)
    elif format_name == "xml":
        return format_xml(results)
    else:
        return format_text(results, verbose=verbose, use_color=use_color)
