import json
import csv
import io
import sys
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

def strip_ansi(text: str) -> str:
    """Removes ANSI escape codes from a string for accurate length calculation."""
    return re.sub(r'\033\[[0-9;]*m', '', text)

def pad_right(text: str, width: int) -> str:
    """Pads a string to the right, ignoring any embedded ANSI escape sequences."""
    visible_len = len(strip_ansi(text))
    padding = max(0, width - visible_len)
    return text + (" " * padding)

def get_colors(use_color: bool) -> Dict[str, str]:
    """Returns ANSI escape sequences if colors are enabled, else empty strings."""
    if use_color:
        return {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "bold": "\033[1m",
            "reset": "\033[0m"
        }
    return {
        "green": "",
        "red": "",
        "yellow": "",
        "blue": "",
        "cyan": "",
        "bold": "",
        "reset": ""
    }

def format_json(results: List[Dict[str, Any]]) -> str:
    """Format results to structured JSON matching legacy keys."""
    all_success = all(r.get("success", False) for r in results) if results else True
    all_fail = all(not r.get("success", False) for r in results) if results else True
    
    formatted_results = []
    for r in results:
        host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
        try:
            port = int(r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1]))
        except ValueError:
            port = 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if r.get("success", False):
            # For TCP checks, default method is netcat if not defined
            method = r.get("metadata", {}).get("method", "netcat")
            formatted_results.append({
                "status": "success",
                "host": host,
                "port": port,
                "method": method,
                "timestamp": timestamp
            })
        else:
            reason = r.get("error", "timeout") or "timeout"
            formatted_results.append({
                "status": "failed",
                "host": host,
                "port": port,
                "reason": reason,
                "timestamp": timestamp
            })
            
    if all_success and results:
        data = {
            "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": formatted_results
        }
    elif all_fail and results:
        data = {
            "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "failures": formatted_results
        }
    else:
        data = {
            "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "all_results": formatted_results
        }
    return json.dumps(data, indent=2)

def format_csv(results: List[Dict[str, Any]]) -> str:
    """Format results to CSV format matching legacy columns."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    all_success = all(r.get("success", False) for r in results) if results else True
    all_fail = all(not r.get("success", False) for r in results) if results else True
    
    if all_success and results:
        writer.writerow(["Status", "Host", "Port", "Method", "Timestamp"])
        for r in results:
            host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
            port = r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1])
            method = r.get("metadata", {}).get("method", "netcat")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(["SUCCESS", host, port, method, timestamp])
    elif all_fail and results:
        writer.writerow(["Status", "Host", "Port", "Reason", "Timestamp"])
        for r in results:
            host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
            port = r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1])
            reason = r.get("error", "timeout") or "timeout"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(["FAILED", host, port, reason, timestamp])
    else:
        writer.writerow(["Status", "Host", "Port", "Method/Reason", "Timestamp"])
        for r in results:
            host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
            port = r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1])
            status = "SUCCESS" if r.get("success", False) else "FAILED"
            method_reason = r.get("metadata", {}).get("method", "netcat") if r.get("success", False) else (r.get("error", "timeout") or "timeout")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([status, host, port, method_reason, timestamp])
    return output.getvalue()

def format_xml(results: List[Dict[str, Any]]) -> str:
    """Format results to XML format matching legacy structure."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    root = ET.Element("connectivity_check", date=timestamp)
    
    all_success = all(r.get("success", False) for r in results) if results else True
    all_fail = all(not r.get("success", False) for r in results) if results else True
    
    if all_success and results:
        container = ET.SubElement(root, "successful_connections")
    elif all_fail and results:
        container = ET.SubElement(root, "failed_connections")
    else:
        container = ET.SubElement(root, "all_results")
        
    for r in results:
        host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
        port = str(r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1]))
        r_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if r.get("success", False):
            method = r.get("metadata", {}).get("method", "netcat")
            ET.SubElement(container, "connection", host=host, port=port, method=method, timestamp=r_time)
        else:
            reason = r.get("error", "timeout") or "timeout"
            ET.SubElement(container, "connection", host=host, port=port, reason=reason, timestamp=r_time)
            
    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


def format_text(results: List[Dict[str, Any]], verbose: bool = False, use_color: Optional[bool] = None) -> str:
    """Format results to a polished, human-readable terminal output."""
    if use_color is None:
        use_color = sys.stdout.isatty()
        
    c = get_colors(use_color)
    lines = []
    
    # Single-target custom formatters (restoring legacy prettiness)
    if len(results) == 1:
        r = results[0]
        target = r.get("target", "")
        status = r.get("status", "")
        success = r.get("success", False)
        error = r.get("error", "")
        latency = r.get("latency_ms")
        meta = r.get("metadata", {})
        
        # 1. Network Interfaces formatter
        if target == "interfaces" or "interfaces" in meta:
            lines.append("Network Interface Information")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")
            
            if not meta.get("all_interfaces_shown", False):
                lines.append(f"📡 {c['bold']}Active Network Interfaces (UP only):{c['reset']}")
                lines.append("   Use '--my-ip --all' to show all interfaces")
            else:
                lines.append(f"📡 {c['bold']}All Network Interfaces:{c['reset']}")
            lines.append("")
            
            interfaces = meta.get("interfaces", {})
            for name in sorted(interfaces.keys()):
                iface = interfaces[name]
                lines.append(f"Interface: {c['bold']}{name}{c['reset']}")
                if iface.get("ipv4"):
                    lines.append(f"  IPv4: {', '.join(iface['ipv4'])}")
                if iface.get("ipv6"):
                    lines.append(f"  IPv6: {', '.join(iface['ipv6'])}")
                
                state = iface.get("status", "DOWN")
                if state == "UP":
                    status_str = f"{c['green']}✅ UP{c['reset']}"
                else:
                    status_str = f"{c['yellow']}⚠️  {state}{c['reset']}"
                lines.append(f"  Status: {status_str}")
                lines.append("")
                
            gw_ip = meta.get("gateway_ip")
            gw_dev = meta.get("gateway_dev")
            if gw_ip:
                lines.append(f"🌐 {c['bold']}Default Gateway:{c['reset']} {gw_ip}")
                if gw_dev:
                    lines.append(f"   Via Interface: {gw_dev}")
                lines.append("")
                
            public_ip = meta.get("public_ip")
            lines.append(f"🌍 {c['bold']}Public IP Address:{c['reset']}")
            if public_ip and public_ip != "Unknown":
                lines.append(f"  {public_ip}")
            else:
                lines.append("  Unable to determine (no internet or curl/wget not available)")
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)
            
        # 2. DNS Lookup formatter
        elif "resolved_host" in meta:
            lines.append(f"DNS Lookup for: {meta.get('resolved_host')}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Hostname: {meta.get('resolved_host')}")
            lines.append("")
            lines.append("IP Addresses:")
            for ip in meta.get("ips", []):
                if ":" in ip:
                    lines.append(f"  {ip} (IPv6)")
                else:
                    lines.append(f"  {ip}")
            lines.append("")
            
            aliases = meta.get("aliases", [])
            if aliases:
                lines.append("Aliases:")
                for alias in aliases:
                    lines.append(f"  {alias}")
                lines.append("")
                
            rev = meta.get("reverse_dns")
            if rev:
                lines.append("Reverse DNS:")
                lines.append(f"  {rev}")
                lines.append("")
                
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)
            
        # 3. HTTP Status check formatter
        elif "status_code" in meta and not "valid_until" in meta:
            lines.append(f"HTTP Status Check for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("Sending HTTP request...")
            lines.append("")
            
            status_code = meta.get("status_code")
            size = meta.get("size_bytes", 0)
            redirect_url = meta.get("redirect_url")
            headers = meta.get("headers", {})
            
            if size > 1048576:
                size_human = f"{size / 1048576:.2f} MB"
            elif size > 1024:
                size_human = f"{size / 1024:.2f} KB"
            else:
                size_human = f"{size} bytes"
                
            status_descriptions = {
                200: "OK", 201: "Created", 202: "Accepted", 204: "No Content",
                301: "Moved Permanently", 302: "Found (Temporary Redirect)", 303: "See Other", 304: "Not Modified",
                307: "Temporary Redirect", 308: "Permanent Redirect",
                400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
                405: "Method Not Allowed", 408: "Request Timeout", 429: "Too Many Requests",
                500: "Internal Server Error", 501: "Not Implemented", 502: "Bad Gateway", 503: "Service Unavailable", 504: "Gateway Timeout"
            }
            code_desc = status_descriptions.get(status_code, "Unknown Status") if status_code else "Unknown"
            
            if status_code and 200 <= status_code < 300:
                status_icon = f"{c['green']}✅ SUCCESS{c['reset']}"
            elif status_code and 300 <= status_code < 400:
                status_icon = f"{c['yellow']}↪ REDIRECT{c['reset']}"
            else:
                status_icon = f"{c['red']}❌ FAILED{c['reset']}"
                
            lines.append("┌─────────────────────────────────────────────┐")
            lines.append(f"│ URL: {pad_right(target, 38)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Status: {pad_right(status_icon, 35)} │")
            lines.append(f"│ Code: {pad_right(f'{status_code} {code_desc}', 37)} │")
            lines.append(f"│ Response Time: {pad_right(f'{latency}ms' if latency is not None else 'N/A', 28)} │")
            lines.append(f"│ Content Size: {pad_right(size_human, 29)} │")
            if redirect_url:
                lines.append(f"│ Redirected To: {pad_right(redirect_url, 27)} │")
            lines.append("└─────────────────────────────────────────────┘")
            lines.append("")
            
            if verbose and headers:
                lines.append("Response Headers:")
                lines.append("─────────────────────────────────────────────")
                for k, v in sorted(headers.items()):
                    lines.append(f"{k.title()}: {v}")
                lines.append("─────────────────────────────────────────────")
                lines.append("")
                
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)
            
        # 4. SSL Certificate check formatter
        elif "valid_until" in meta:
            lines.append(f"SSL/TLS Certificate Check for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Connecting to {target}...")
            lines.append("")
            
            expired = meta.get("expired", False)
            days_until_expiry = meta.get("days_until_expiry")
            subject = meta.get("subject", {})
            issuer = meta.get("issuer", {})
            valid_from = meta.get("valid_from")
            valid_until = meta.get("valid_until")
            sans = meta.get("sans", [])
            verification_error = meta.get("verification_error") or error
            
            if verification_error:
                status_icon = f"{c['red']}❌ VERIFICATION FAILED{c['reset']}"
            elif expired:
                status_icon = f"{c['red']}❌ EXPIRED{c['reset']}"
            elif not success:
                status_icon = f"{c['red']}❌ FAILED{c['reset']}"
            elif days_until_expiry is not None and days_until_expiry < 30:
                status_icon = f"{c['yellow']}⚠️  EXPIRING SOON{c['reset']}"
            else:
                status_icon = f"{c['green']}✅ VALID{c['reset']}"
                
            subject_cn = subject.get("commonName", "")
            issuer_o = issuer.get("organizationName", "")
            
            lines.append("┌─────────────────────────────────────────────┐")
            lines.append(f"│ Host: {pad_right(target, 37)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Status: {pad_right(status_icon, 35)} │")
            if verification_error:
                err_to_show = str(verification_error)
                if len(err_to_show) > 36:
                    err_to_show = err_to_show[:33] + "..."
                lines.append(f"│ Error: {pad_right(err_to_show, 36)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append("│ Certificate Details:                        │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Subject: CN = {pad_right(subject_cn, 29)} │")
            lines.append(f"│ Issuer: O = {pad_right(issuer_o, 31)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Valid From: {pad_right(valid_from if valid_from else 'N/A', 31)} │")
            lines.append(f"│ Valid Until: {pad_right(valid_until if valid_until else 'N/A', 30)} │")
            lines.append(f"│ Days Until Expiry: {pad_right(str(days_until_expiry) if days_until_expiry is not None else 'N/A', 24)} │")
            lines.append("└─────────────────────────────────────────────┘")
            lines.append("")
            
            if verbose and sans:
                lines.append("Subject Alternative Names (SANs):")
                lines.append("─────────────────────────────────────────────")
                lines.append("\n".join(f"  {san}" for san in sans))
                lines.append("─────────────────────────────────────────────")
                lines.append("")
                
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)
            
        # 5. ICMP Ping formatter
        elif "packets_sent" in meta:
            lines.append(f"ICMP Ping Test for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Target: {meta.get('host', target)}")
            lines.append("")
            lines.append("Sending 4 ICMP packets...")
            lines.append("")
            
            ping_output = meta.get("ping_output", "")
            if ping_output:
                lines.append(ping_output)
            else:
                lines.append(f"No ping output captured. Success: {success}")
                
            lines.append("")
            if success:
                lines.append(f"{c['green']}✅ Ping successful{c['reset']}")
            else:
                lines.append(f"{c['red']}❌ Ping failed (host unreachable or no response){c['reset']}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)
            
        # 6. Fallback default single-target box
        else:
            status_icon = f"{c['green']}✅ SUCCESS{c['reset']}" if success else f"{c['red']}❌ FAILED{c['reset']}"
            if status == "REDIRECT":
                status_icon = f"{c['yellow']}↪ REDIRECT{c['reset']}"
                
            lines.append("┌─────────────────────────────────────────────┐")
            lines.append(f"│ Target: {pad_right(target, 35)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Status: {pad_right(status_icon, 35)} │")
            
            if latency is not None:
                lines.append(f"│ Latency: {pad_right(f'{latency}ms', 34)} │")
                
            if error:
                err_str = str(error)
                if len(err_str) > 35:
                    err_str = err_str[:32] + "..."
                lines.append(f"│ Reason: {pad_right(err_str, 35)} │")
                
            for k, v in meta.items():
                val_str = str(v)
                if len(val_str) > 32:
                    val_str = val_str[:29] + "..."
                lines.append(f"│ {k.capitalize()}: {pad_right(val_str, 45 - len(k) - 2)} │")
                
            lines.append("└─────────────────────────────────────────────┘")
            return "\n".join(lines)
            
    # Bulk targets check format (tabular)
    else:
        lines.append("="*80)
        lines.append(f"Network Check Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("="*80)
        lines.append(f"{'Status':12} {'Target':30} {'Latency':10} {'Details'}")
        lines.append("-"*80)
        
        successes = 0
        failures = 0
        
        for r in results:
            target = r.get("target", "")
            status = r.get("status", "")
            success = r.get("success", False)
            latency = f"{r.get('latency_ms', '')}ms" if r.get('latency_ms') is not None else "N/A"
            details = r.get("error", "") or ""
            
            if success:
                successes += 1
                status_str = f"{c['green']}SUCCESS{c['reset']}"
            else:
                failures += 1
                status_str = f"{c['red']}FAILED{c['reset']}"
                
            if status == "REDIRECT":
                status_str = f"{c['yellow']}REDIRECT{c['reset']}"
                
            meta = r.get("metadata", {})
            if "status_code" in meta:
                details = f"HTTP {meta['status_code']}" + (f" -> {meta['redirect_url']}" if meta.get("redirect_url") else "")
            elif "days_until_expiry" in meta:
                details = f"SSL expires in {meta['days_until_expiry']} days"
            elif "ips" in meta:
                details = f"IPs: {', '.join(meta['ips'][:3])}"
                
            lines.append(f"{pad_right(status_str, 12)} {pad_right(target, 30)} {pad_right(latency, 10)} {details}")
            
        lines.append("="*80)
        lines.append("Check Complete!")
        lines.append(f"Total: {len(results)}  |  Successful: {successes}  |  Failed: {failures}")
        lines.append("="*80)
        
    return "\n".join(lines)
