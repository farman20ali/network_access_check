#!/usr/bin/env python3
"""
Network Connectivity Checker (Python)
Port of check_ip.sh / check_ip.ps1

Features:
 - Expand IP ranges (1-50), CIDR (limited to first 256 hosts)
 - Expand port lists and port ranges
 - CSV input support
 - Quick mode (-q host ports)
 - DNS lookup and ICMP ping helpers
 - Parallel TCP connect checks with response time
 - Output formats: text, json, csv, xml
"""

from __future__ import annotations
import argparse
import csv
import ipaddress
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict, Any, Iterable, Optional
import xml.etree.ElementTree as ET

__version__ = "1.1.0"
MAX_CIDR_LIMIT = 256  # cap expansion to avoid insane scans

# ------------------------
# Utility helpers
# ------------------------
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def normalize_host(raw: str) -> str:
    if "://" in raw:
        raw = raw.split("://", 1)[1]
    raw = raw.split("/", 1)[0]
    raw = raw.split(":", 1)[0]
    return raw.strip()

def expand_ip_range(pattern: str) -> List[str]:
    pattern = pattern.strip()
    if "-" in pattern and "/" not in pattern:
        # e.g., 192.168.1.1-50
        try:
            prefix, range_part = pattern.rsplit(".", 1)
            start_end = range_part.split("-", 1)
            if len(start_end) == 2:
                start = int(start_end[0])
                end = int(start_end[1])
                if 0 <= start <= 255 and 0 <= end <= 255 and start <= end:
                    return [f"{prefix}.{i}" for i in range(start, end + 1)]
        except Exception:
            pass
    # CIDR?
    if "/" in pattern:
        try:
            net = ipaddress.ip_network(pattern, strict=False)
            hosts = list(net.hosts())
            # if hosts too many limit to first MAX_CIDR_LIMIT
            if len(hosts) > MAX_CIDR_LIMIT:
                eprint(f"Warning: CIDR {pattern} generates {len(hosts)} IPs; limiting to first {MAX_CIDR_LIMIT}")
                hosts = hosts[:MAX_CIDR_LIMIT]
            return [str(h) for h in hosts]
        except Exception:
            return [pattern]
    # single host or invalid -> return as-is
    return [pattern]

def expand_port_range(pattern: str) -> List[int]:
    result: List[int] = []
    parts = [p.strip() for p in pattern.split(",") if p.strip() != ""]
    for part in parts:
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                s = int(start); e = int(end)
                if s > e:
                    eprint(f"Warning: Invalid port range {part} (start > end) - skipping")
                    continue
                if (e - s) > 1000:
                    eprint(f"Warning: Port range {part} too large (>1000), limiting to first 1000")
                    e = s + 1000
                for p in range(s, e + 1):
                    if 1 <= p <= 65535:
                        result.append(p)
            except Exception:
                eprint(f"Warning: Invalid port range {part} - skipping")
        else:
            try:
                p = int(part)
                if 1 <= p <= 65535:
                    result.append(p)
                else:
                    eprint(f"Warning: Invalid port {p} - ignoring")
            except Exception:
                eprint(f"Warning: Invalid port token '{part}' - ignoring")
    return result

def expand_line(line: str) -> List[Tuple[str,int]]:
    """Input line: HOST PORTSPEC -> returns list of (host,port) pairs"""
    line = line.strip()
    if not line or line.startswith("#"):
        return []
    parts = line.split(None, 1)
    if len(parts) < 2:
        eprint(f"Warning: Invalid line format: {line}")
        return []
    host_part, port_part = parts[0].strip(), parts[1].strip()
    ips = expand_ip_range(host_part)
    ports = expand_port_range(port_part)
    out: List[Tuple[str,int]] = []
    for ip in ips:
        for p in ports:
            out.append((ip, p))
    return out

# TCP check
def test_tcp_connect(host: str, port: int, timeout: float) -> Dict[str, Any]:
    ts = time.perf_counter()
    res = {
        "status": "FAILED",
        "host": host,
        "port": port,
        "method": "tcp",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": "",
        "response_ms": None
    }
    try:
        # socket.create_connection respects timeout
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        duration = (time.perf_counter() - ts) * 1000.0
        res.update({"status": "SUCCESS", "response_ms": int(duration), "message": "Connected"})
    except Exception as exc:
        duration = (time.perf_counter() - ts) * 1000.0
        res.update({"status": "FAILED", "response_ms": int(duration), "message": str(exc)})
    return res

# DNS lookup
def do_dns(raw: str) -> int:
    host = normalize_host(raw)
    eprint(f"DNS Lookup for: {host}")
    eprint("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = []
        for info in infos:
            addr = info[4][0]
            if addr not in addrs:
                addrs.append(addr)
        if not addrs:
            eprint(f"❌ Failed to resolve: {host}")
            return 1
        eprint(f"Hostname: {host}\n")
        eprint("IP Addresses:")
        for a in addrs:
            eprint("  " + a)
        # Try reverse for first
        try:
            rev = socket.gethostbyaddr(addrs[0])
            eprint("\nReverse DNS: " + rev[0])
        except Exception:
            eprint("\nReverse DNS: (none)")
        eprint("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return 0
    except Exception as exc:
        eprint(f"❌ Failed to resolve: {host} ({exc})")
        return 1

# Ping helper (cross-platform)
def do_ping(raw: str) -> int:
    host = normalize_host(raw)
    eprint(f"ICMP Ping Test for: {host}")
    eprint("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    eprint("Target: " + host + "\n")
    plat = platform.system().lower()
    try:
        if plat == "windows":
            # -n count, -w timeout in ms
            cmd = ["ping", "-n", "4", "-w", "2000", host]
        else:
            # mac/linux: -c count, -W timeout in seconds (Linux). macOS uses -W in ms? Use -c 4 -W 2 that works on many linux.
            if platform.system().lower() == "darwin":
                # macOS: -c count, -W timeout in ms (but behaviour varies). We'll keep -c 4
                cmd = ["ping", "-c", "4", host]
            else:
                cmd = ["ping", "-c", "4", "-W", "2", host]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(proc.stdout)
        if proc.returncode == 0:
            eprint("✅ Ping successful")
            return 0
        else:
            eprint("❌ Ping failed (no response or unreachable)")
            return 1
    except FileNotFoundError:
        eprint("❌ Error: 'ping' command not found")
        return 1
    except Exception as exc:
        eprint(f"❌ Ping failed: {exc}")
        return 1

# Terminal progress bar (simple)
_progress_lock = threading.Lock()
def show_progress(count: int, total: int, width: int = 50):
    with _progress_lock:
        if total == 0:
            pct = 100
            bar = "=" * width
        else:
            pct = int((count/ total) * 100)
            completed = int(width * count // total)
            bar = "=" * completed + ">" + " " * (width - completed - 1)
        sys.stderr.write(f"\rProgress: [{bar}] {pct:3d}% ({count}/{total})")
        sys.stderr.flush()
        if count == total:
            sys.stderr.write("\n")

# ------------------------
# Main program
# ------------------------
def parse_args():
    parser = argparse.ArgumentParser(prog="netcheck", description="Network Connectivity Checker - Python port")
    parser.add_argument("-t", "--timeout", type=float, default=5.0, help="Connection timeout (seconds)")
    parser.add_argument("-j", "--jobs", type=int, default=10, help="Max parallel jobs")
    parser.add_argument("-V", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-f", "--format", choices=["text","json","csv","xml"], default="text", help="Output format")
    parser.add_argument("-c", "--combined", action="store_true", help="Create combined report")
    parser.add_argument("--csv", dest="csv_input", action="store_true", help="Input file is CSV host,port")
    parser.add_argument("-q", "--quick", nargs=2, metavar=("HOST","PORTS"), help="Quick test: host ports (ports like 80,443 or 8000-8100)")
    parser.add_argument("-d", "--dns", metavar="HOST", help="Resolve DNS and show IP(s)")
    parser.add_argument("-p", "--ping", metavar="HOST", help="Ping host (ICMP)")
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    parser.add_argument("input_file", nargs="?", help="Input file (default: stdin)")
    return parser.parse_args()

def read_input_lines(input_file: Optional[str]) -> List[str]:
    if input_file:
        if not os.path.exists(input_file):
            eprint(f"Error: Input file not found: {input_file}")
            sys.exit(1)
        with open(input_file, "r", encoding="utf-8") as fh:
            return [ln.rstrip("\n") for ln in fh]
    else:
        # read from stdin if piped
        if not sys.stdin.isatty():
            data = sys.stdin.read().splitlines()
            return data
        else:
            return []

def parse_csv_lines(lines: List[str]) -> List[str]:
    out: List[str] = []
    header_skipped = False
    for line in lines:
        if not line:
            continue
        if not header_skipped:
            # peek if header-like
            if "," in line and any(h in line.lower() for h in ["host","hostname","ip","server","address"]):
                header_skipped = True
                continue
            header_skipped = True
        if line.strip().startswith("#"):
            continue
        # use CSV parsing to handle quotes
        try:
            reader = csv.reader([line])
            row = next(reader)
            if len(row) >= 2:
                host = row[0].strip()
                port = row[1].strip()
                out.append(f"{host} {port}")
            else:
                eprint(f"Warning: Invalid CSV line: {line}")
        except Exception:
            eprint(f"Warning: Invalid CSV line: {line}")
    return out

def init_output_files(fmt: str, combined: bool) -> Tuple[str,str,Optional[str]]:
    today = datetime.now().strftime("%Y-%m-%d")
    result_file = f"result-{today}.txt"
    fail_file = f"fail-{today}.txt"
    combined_file = f"combined-{today}.txt" if combined else None

    if fmt == "text":
        with open(result_file, "w", encoding="utf-8") as r:
            r.write("="*66 + "\n")
            r.write("Network Connectivity Check - Successful Connections\n")
            r.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            r.write("="*66 + "\n")
            r.write(f"{'Status':15} {'Host':20} {'Port':7} {'Method':10}\n")
            r.write("-"*66 + "\n")
        with open(fail_file, "w", encoding="utf-8") as f:
            f.write("="*66 + "\n")
            f.write("Network Connectivity Check - Failed Connections\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*66 + "\n")
            f.write(f"{'Status':15} {'Host':20} {'Port':7} {'Timestamp':20}\n")
            f.write("-"*66 + "\n")
        if combined_file:
            with open(combined_file, "w", encoding="utf-8") as c:
                c.write("="*80 + "\n")
                c.write("Network Connectivity Check - All Results\n")
                c.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                c.write("="*80 + "\n")
                c.write(f"{'Status':15} {'Host':20} {'Port':7} {'Method/Time':15} {'Notes':20}\n")
                c.write("-"*80 + "\n")
    elif fmt == "json":
        # we'll write at the end
        pass
    elif fmt == "csv":
        with open(result_file, "w", newline='', encoding="utf-8") as r:
            writer = csv.writer(r)
            writer.writerow(["Status","Host","Port","Method","Timestamp"])
        with open(fail_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Status","Host","Port","Reason","Timestamp"])
    elif fmt == "xml":
        # write headers
        with open(result_file, "w", encoding="utf-8") as r:
            r.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            r.write(f'<connectivity_check date="{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}">\n')
            r.write("  <successful_connections>\n")
        with open(fail_file, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(f'<connectivity_check date="{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}">\n')
            f.write("  <failed_connections>\n")
        if combined_file:
            with open(combined_file, "w", encoding="utf-8") as c:
                c.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                c.write(f'<connectivity_check date="{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}">\n')
                c.write("  <all_results>\n")
    return result_file, fail_file, combined_file

def write_result(fmt: str, status: str, host: str, port: int, method: str, timestamp: str,
                 message: str, result_file: str, fail_file: str, combined_file: Optional[str]):
    if fmt == "text":
        if status == "SUCCESS":
            with open(result_file, "a", encoding="utf-8") as r:
                r.write(f"{status:15} {host:20} {port:7} {method:10}\n")
        else:
            with open(fail_file, "a", encoding="utf-8") as f:
                f.write(f"{status:15} {host:20} {port:7} {timestamp:20}\n")
        if combined_file:
            with open(combined_file, "a", encoding="utf-8") as c:
                c.write(f"{status:15} {host:20} {port:7} {method}/{message:15} {message:20}\n")
    elif fmt == "json":
        # caller will assemble lists and dump at end
        pass
    elif fmt == "csv":
        if status == "SUCCESS":
            with open(result_file, "a", newline='', encoding="utf-8") as r:
                writer = csv.writer(r)
                writer.writerow([status, host, port, method, timestamp])
        else:
            with open(fail_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([status, host, port, message, timestamp])
        if combined_file:
            with open(combined_file, "a", newline='', encoding="utf-8") as c:
                writer = csv.writer(c)
                writer.writerow([status, host, port, f"{method}: {message}", timestamp])
    elif fmt == "xml":
        if status == "SUCCESS":
            with open(result_file, "a", encoding="utf-8") as r:
                r.write(f'    <connection host="{host}" port="{port}" method="{method}" timestamp="{timestamp}" />\n')
        else:
            with open(fail_file, "a", encoding="utf-8") as f:
                escaped = message.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                f.write(f'    <connection host="{host}" port="{port}" reason="{escaped}" timestamp="{timestamp}" />\n')
        if combined_file:
            with open(combined_file, "a", encoding="utf-8") as c:
                escaped = message.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                c.write(f'    <result status="{status}" host="{host}" port="{port}" method="{method}" message="{escaped}" timestamp="{timestamp}" />\n')

# ------------------------
# Runner
# ------------------------
def main():
    args = parse_args()
    if args.version:
        print(f"netcheck version {__version__}")
        sys.exit(0)
    if args.dns:
        rc = do_dns(args.dns)
        sys.exit(rc)
    if args.ping:
        rc = do_ping(args.ping)
        sys.exit(rc)

    # input lines
    lines = []
    if args.quick:
        host_raw, ports_raw = args.quick
        lines = [f"{host_raw} {ports_raw}"]
    else:
        lines = read_input_lines(args.input_file)
        if args.csv_input:
            lines = parse_csv_lines(lines)

    if not lines:
        eprint("Error: No input provided! Provide a file or pipe lines to stdin, or use -q for quick mode.")
        sys.exit(1)

    # expand lines into (host,port) pairs
    pairs: List[Tuple[str,int]] = []
    for ln in lines:
        ex = expand_line(ln)
        for h,p in ex:
            # validate port just in case
            if not (1 <= p <= 65535):
                eprint(f"Warning: Invalid port {p} - skipping")
                continue
            pairs.append((h,p))

    total = len(pairs)
    if total == 0:
        eprint("Error: No valid hosts to check")
        sys.exit(1)

    # Prepare output files
    result_file, fail_file, combined_file = init_output_files(args.format, args.combined)

    # For json we accumulate
    json_results: List[Dict[str,Any]] = []
    json_failures: List[Dict[str,Any]] = []

    eprint("="*42)
    eprint("Network Connectivity Check Starting...")
    eprint(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    eprint(f"Timeout: {args.timeout}s")
    eprint(f"Parallel Jobs: {args.jobs}")
    eprint(f"Output Format: {args.format}")
    eprint(f"Total Hosts: {total}")
    eprint("="*42)
    eprint("")

    # perform checks in thread pool
    successes = 0
    failures = 0
    completed = 0

    with ThreadPoolExecutor(max_workers=args.jobs) as exe:
        futures = { exe.submit(test_tcp_connect, host, port, args.timeout): (host,port) for host,port in pairs }
        for fut in as_completed(futures):
            host, port = futures[fut]
            try:
                res = fut.result()
            except Exception as exc:
                res = {
                    "status":"FAILED",
                    "host": host,
                    "port": port,
                    "method": "tcp",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "message": str(exc),
                    "response_ms": None
                }

            completed += 1
            show_progress(completed, total)

            if res["status"] == "SUCCESS":
                successes += 1
                if args.format == "json":
                    json_results.append({
                        "status":"success",
                        "host": res["host"],
                        "port": res["port"],
                        "method": res["method"],
                        "response_ms": res["response_ms"],
                        "timestamp": res["timestamp"]
                    })
                else:
                    write_result(args.format, "SUCCESS", res["host"], res["port"], res["method"], res["timestamp"], res["message"], result_file, fail_file, combined_file)
                if args.verbose:
                    eprint(f"✓ SUCCESS: {res['host']}:{res['port']} ({res.get('response_ms','?')}ms)")
            else:
                failures += 1
                if args.format == "json":
                    json_failures.append({
                        "status":"failed",
                        "host": res["host"],
                        "port": res["port"],
                        "reason": res["message"],
                        "timestamp": res["timestamp"]
                    })
                else:
                    write_result(args.format, "FAILED", res["host"], res["port"], res["method"], res["timestamp"], res["message"], result_file, fail_file, combined_file)
                if args.verbose:
                    eprint(f"✗ FAILED: {res['host']}:{res['port']} ({res['message']})")

    # finalize json/xml and write files
    if args.format == "json":
        main_obj = {"check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": json_results}
        with open(result_file, "w", encoding="utf-8") as rfh:
            json.dump(main_obj, rfh, indent=2)
        fail_obj = {"check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "failures": json_failures}
        with open(fail_file, "w", encoding="utf-8") as ffh:
            json.dump(fail_obj, ffh, indent=2)
        if combined_file:
            all_items = json_results + json_failures
            with open(combined_file, "w", encoding="utf-8") as cfh:
                json.dump({"check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "all_results": all_items}, cfh, indent=2)
    elif args.format == "xml":
        # close tags
        with open(result_file, "a", encoding="utf-8") as rfh:
            rfh.write("  </successful_connections>\n</connectivity_check>\n")
        with open(fail_file, "a", encoding="utf-8") as ffh:
            ffh.write("  </failed_connections>\n</connectivity_check>\n")
        if combined_file:
            with open(combined_file, "a", encoding="utf-8") as cfh:
                cfh.write("  </all_results>\n</connectivity_check>\n")

    # final summary
    eprint("="*42)
    eprint("Check Complete!")
    eprint("="*42)
    eprint(f"Total Checked: {total}")
    eprint(f"Successful:    {successes}")
    eprint(f"Failed:        {failures}")
    eprint("="*42)
    eprint(f"Results saved to: {result_file}")
    eprint(f"Failures saved to: {fail_file}")
    if combined_file:
        eprint(f"Combined report: {combined_file}")
    eprint("="*42)

    # exit code
    sys.exit(0 if failures == 0 else 1)

if __name__ == "__main__":
    main()
