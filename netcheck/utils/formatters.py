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
    """Format results to structured JSON matching legacy or specialized formats."""
    if results and len(results) == 1:
        res = results[0]
        meta = res.get("metadata", {})
        # 1. Interfaces
        if res.get("target") == "interfaces":
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "interfaces",
                **meta
            }, indent=2)
        # 2. DNS
        elif "resolved_host" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "dns",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "latency_ms": res.get("latency_ms"),
                **meta
            }, indent=2)
        # 3. HTTP
        elif "status_code" in meta and "headers" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "http",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "latency_ms": res.get("latency_ms"),
                **meta
            }, indent=2)
        # 4. SSL
        elif "valid_until" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "ssl",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "latency_ms": res.get("latency_ms"),
                **meta
            }, indent=2)
        # 5. Ping
        elif "packets_sent" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "ping",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "latency_ms": res.get("latency_ms"),
                **meta
            }, indent=2)
        # 6. Local Listening Ports
        elif res.get("target") == "ports" or "listening_ports" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "ports",
                "success": res.get("success", False),
                "error": res.get("error"),
                "listening_ports": meta.get("listening_ports", [])
            }, indent=2)
        # 7. Port Scanner
        elif "open_ports" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "scan",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "ips": meta.get("ips", []),
                "open_ports": meta.get("open_ports", []),
                "closed_ports": meta.get("closed_ports", [])
            }, indent=2)
        # 8. Traceroute
        elif "hops" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "traceroute",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "hops": meta.get("hops", [])
            }, indent=2)
        # 9. WHOIS / RDAP
        elif "rdap_source" in meta:
            return json.dumps({
                "check_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "check_type": "whois",
                "target": res.get("target"),
                "success": res.get("success", False),
                "error": res.get("error"),
                "rdap_type": meta.get("type", ""),
                "rdap_source": meta.get("rdap_source", ""),
                "registrar": meta.get("registrar", ""),
                "creation_date": meta.get("creation_date", "")
            }, indent=2)

    # Default legacy TCP connect check format
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
            method = r.get("metadata", {}).get("method", "socket")
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
    """Format results to CSV format matching legacy or specialized headers."""
    if results and len(results) == 1:
        res = results[0]
        meta = res.get("metadata", {})
        # 1. Interfaces
        if res.get("target") == "interfaces":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Interface", "IPv4", "IPv6", "Status", "Default_Gateway", "Public_IP"])
            interfaces = meta.get("interfaces", {})
            gw = meta.get("gateway_ip", "")
            pub = meta.get("public_ip", "")
            for name, iface in sorted(interfaces.items()):
                writer.writerow([
                    name,
                    ", ".join(iface.get("ipv4", [])),
                    ", ".join(iface.get("ipv6", [])),
                    iface.get("status", ""),
                    gw,
                    pub
                ])
            return output.getvalue()
        # 2. DNS
        elif "resolved_host" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Resolved_Host", "IP", "Reverse_DNS", "Success", "Latency_MS", "Error"])
            ips = meta.get("ips", [])
            rev = meta.get("reverse_dns", "") or ""
            success = "SUCCESS" if res.get("success", False) else "FAILED"
            lat = res.get("latency_ms") if res.get("latency_ms") is not None else "N/A"
            err = res.get("error", "") or ""
            if ips:
                for ip in ips:
                    writer.writerow([res.get("target"), meta.get("resolved_host"), ip, rev, success, lat, err])
            else:
                writer.writerow([res.get("target"), meta.get("resolved_host"), "", rev, success, lat, err])
            return output.getvalue()
        # 3. HTTP
        elif "status_code" in meta and "headers" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Status_Code", "Redirect_URL", "Size_Bytes", "Success", "Latency_MS", "Error"])
            writer.writerow([
                res.get("target"),
                meta.get("status_code") if meta.get("status_code") is not None else "N/A",
                meta.get("redirect_url") or "",
                meta.get("size_bytes", 0),
                "SUCCESS" if res.get("success", False) else "FAILED",
                res.get("latency_ms") if res.get("latency_ms") is not None else "N/A",
                res.get("error") or ""
            ])
            return output.getvalue()
        # 4. SSL
        elif "valid_until" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Subject_CN", "Issuer_O", "Valid_From", "Valid_Until", "Days_Until_Expiry", "Expired", "Success", "Latency_MS", "Error"])
            writer.writerow([
                res.get("target"),
                meta.get("subject", {}).get("commonName", ""),
                meta.get("issuer", {}).get("organizationName", ""),
                meta.get("valid_from") or "",
                meta.get("valid_until") or "",
                meta.get("days_until_expiry") if meta.get("days_until_expiry") is not None else "N/A",
                "True" if meta.get("expired", False) else "False",
                "SUCCESS" if res.get("success", False) else "FAILED",
                res.get("latency_ms") if res.get("latency_ms") is not None else "N/A",
                res.get("error") or ""
            ])
            return output.getvalue()
        # 5. Ping
        elif "packets_sent" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Host", "Packets_Sent", "Packets_Received", "Packet_Loss_Pct", "Min_RTT_MS", "Avg_RTT_MS", "Max_RTT_MS", "Success", "Latency_MS", "Error"])
            writer.writerow([
                res.get("target"),
                meta.get("host", ""),
                meta.get("packets_sent", 0),
                meta.get("packets_received", 0),
                meta.get("packet_loss_pct", 0.0),
                meta.get("min_rtt_ms") if meta.get("min_rtt_ms") is not None else "N/A",
                meta.get("avg_rtt_ms") if meta.get("avg_rtt_ms") is not None else "N/A",
                meta.get("max_rtt_ms") if meta.get("max_rtt_ms") is not None else "N/A",
                "SUCCESS" if res.get("success", False) else "FAILED",
                res.get("latency_ms") if res.get("latency_ms") is not None else "N/A",
                res.get("error") or ""
            ])
            return output.getvalue()
        # 6. Local Listening Ports
        elif res.get("target") == "ports" or "listening_ports" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Proto", "Address", "Port", "Process", "PID"])
            for p in meta.get("listening_ports", []):
                writer.writerow([
                    p.get("proto", "TCP"),
                    p.get("address", "*"),
                    p.get("port", ""),
                    p.get("process", ""),
                    p.get("pid", "")
                ])
            return output.getvalue()
        # 7. Port Scanner
        elif "open_ports" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Port", "Status", "Service", "Latency_MS"])
            for p in meta.get("open_ports", []):
                writer.writerow([
                    res.get("target"),
                    p.get("port", ""),
                    "OPEN",
                    p.get("service", ""),
                    p.get("latency_ms") if p.get("latency_ms") is not None else "N/A"
                ])
            for p in meta.get("closed_ports", []):
                writer.writerow([
                    res.get("target"),
                    p.get("port", ""),
                    "CLOSED",
                    p.get("service", ""),
                    "N/A"
                ])
            return output.getvalue()
        # 8. Traceroute
        elif "hops" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Hop", "IP", "Hostname", "Latency_MS"])
            for h in meta.get("hops", []):
                writer.writerow([
                    res.get("target"),
                    h.get("hop", ""),
                    h.get("ip", "*"),
                    h.get("name", "*"),
                    h.get("latency_ms") if h.get("latency_ms") is not None else "*"
                ])
            return output.getvalue()
        # 9. WHOIS / RDAP
        elif "rdap_source" in meta:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Target", "Type", "Source", "Registrar", "Creation_Date", "Success", "Error"])
            writer.writerow([
                res.get("target"),
                meta.get("type", ""),
                meta.get("rdap_source", ""),
                meta.get("registrar", ""),
                meta.get("creation_date", ""),
                "SUCCESS" if res.get("success", False) else "FAILED",
                res.get("error") or ""
            ])
            return output.getvalue()

    # Default legacy TCP connect check format
    output = io.StringIO()
    writer = csv.writer(output)
    
    all_success = all(r.get("success", False) for r in results) if results else True
    all_fail = all(not r.get("success", False) for r in results) if results else True
    
    if all_success and results:
        writer.writerow(["Status", "Host", "Port", "Method", "Timestamp"])
        for r in results:
            host = r.get("metadata", {}).get("host", r.get("target", "").split(":")[0])
            port = r.get("metadata", {}).get("port", r.get("target", "").split(":")[-1])
            method = r.get("metadata", {}).get("method", "socket")
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
            method_reason = r.get("metadata", {}).get("method", "socket") if r.get("success", False) else (r.get("error", "timeout") or "timeout")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([status, host, port, method_reason, timestamp])
    return output.getvalue()

def format_xml(results: List[Dict[str, Any]]) -> str:
    """Format results to XML format matching legacy or specialized structures."""
    if results and len(results) == 1:
        res = results[0]
        meta = res.get("metadata", {})
        # 1. Interfaces
        if res.get("target") == "interfaces":
            root = ET.Element("network_interfaces", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ET.SubElement(root, "primary_ip").text = meta.get("primary_ip", "")
            ET.SubElement(root, "gateway_ip").text = meta.get("gateway_ip", "")
            ET.SubElement(root, "gateway_dev").text = meta.get("gateway_dev", "")
            ET.SubElement(root, "public_ip").text = meta.get("public_ip", "")
            
            ifaces_elem = ET.SubElement(root, "interfaces")
            for name, iface in sorted(meta.get("interfaces", {}).items()):
                iface_elem = ET.SubElement(ifaces_elem, "interface", name=name, status=iface.get("status", ""))
                ipv4_elem = ET.SubElement(iface_elem, "ipv4_addresses")
                for ip in iface.get("ipv4", []):
                    ET.SubElement(ipv4_elem, "ip").text = ip
                ipv6_elem = ET.SubElement(iface_elem, "ipv6_addresses")
                for ip in iface.get("ipv6", []):
                    ET.SubElement(ipv6_elem, "ip").text = ip
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 2. DNS
        elif "resolved_host" in meta:
            root = ET.Element("dns_lookup", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target=res.get("target"), success=str(res.get("success", False)).lower())
            ET.SubElement(root, "resolved_host").text = meta.get("resolved_host", "")
            ips_elem = ET.SubElement(root, "ip_addresses")
            for ip in meta.get("ips", []):
                ET.SubElement(ips_elem, "ip").text = ip
            aliases_elem = ET.SubElement(root, "aliases")
            for alias in meta.get("aliases", []):
                ET.SubElement(aliases_elem, "alias").text = alias
            ET.SubElement(root, "reverse_dns").text = meta.get("reverse_dns", "") or ""
            if res.get("latency_ms") is not None:
                ET.SubElement(root, "latency_ms").text = str(res.get("latency_ms"))
            if res.get("error"):
                ET.SubElement(root, "error").text = res.get("error")
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 3. HTTP
        elif "status_code" in meta and "headers" in meta:
            root = ET.Element("http_check", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target=res.get("target"), success=str(res.get("success", False)).lower())
            ET.SubElement(root, "status_code").text = str(meta.get("status_code") if meta.get("status_code") is not None else "")
            ET.SubElement(root, "redirect_url").text = meta.get("redirect_url") or ""
            ET.SubElement(root, "size_bytes").text = str(meta.get("size_bytes", 0))
            if res.get("latency_ms") is not None:
                ET.SubElement(root, "latency_ms").text = str(res.get("latency_ms"))
            if res.get("error"):
                ET.SubElement(root, "error").text = res.get("error")
                
            headers_elem = ET.SubElement(root, "headers")
            for k, v in sorted(meta.get("headers", {}).items()):
                ET.SubElement(headers_elem, "header", name=k).text = str(v)
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 4. SSL
        elif "valid_until" in meta:
            root = ET.Element("ssl_check", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target=res.get("target"), success=str(res.get("success", False)).lower())
            ET.SubElement(root, "subject_cn").text = meta.get("subject", {}).get("commonName", "")
            ET.SubElement(root, "issuer_o").text = meta.get("issuer", {}).get("organizationName", "")
            ET.SubElement(root, "valid_from").text = meta.get("valid_from") or ""
            ET.SubElement(root, "valid_until").text = meta.get("valid_until") or ""
            ET.SubElement(root, "days_until_expiry").text = str(meta.get("days_until_expiry") if meta.get("days_until_expiry") is not None else "")
            ET.SubElement(root, "expired").text = str(meta.get("expired", False)).lower()
            if res.get("latency_ms") is not None:
                ET.SubElement(root, "latency_ms").text = str(res.get("latency_ms"))
            if res.get("error"):
                ET.SubElement(root, "error").text = res.get("error")
                
            sans_elem = ET.SubElement(root, "sans")
            for san in meta.get("sans", []):
                ET.SubElement(sans_elem, "san").text = san
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 5. Ping
        elif "packets_sent" in meta:
            root = ET.Element("ping_check", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target=res.get("target"), success=str(res.get("success", False)).lower())
            ET.SubElement(root, "host").text = meta.get("host", "")
            ET.SubElement(root, "packets_sent").text = str(meta.get("packets_sent", 0))
            ET.SubElement(root, "packets_received").text = str(meta.get("packets_received", 0))
            ET.SubElement(root, "packet_loss_pct").text = str(meta.get("packet_loss_pct", 0.0))
            ET.SubElement(root, "min_rtt_ms").text = str(meta.get("min_rtt_ms") if meta.get("min_rtt_ms") is not None else "")
            ET.SubElement(root, "avg_rtt_ms").text = str(meta.get("avg_rtt_ms") if meta.get("avg_rtt_ms") is not None else "")
            ET.SubElement(root, "max_rtt_ms").text = str(meta.get("max_rtt_ms") if meta.get("max_rtt_ms") is not None else "")
            if res.get("latency_ms") is not None:
                ET.SubElement(root, "latency_ms").text = str(res.get("latency_ms"))
            if res.get("error"):
                ET.SubElement(root, "error").text = res.get("error")
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 6. Local Listening Ports
        elif res.get("target") == "ports" or "listening_ports" in meta:
            root = ET.Element("listening_ports", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              success=str(res.get("success", False)).lower())
            for p in meta.get("listening_ports", []):
                ET.SubElement(root, "port",
                              proto=str(p.get("proto", "TCP")),
                              address=str(p.get("address", "*")),
                              port=str(p.get("port", "")),
                              process=str(p.get("process", "")),
                              pid=str(p.get("pid", "")))
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 7. Port Scanner
        elif "open_ports" in meta:
            root = ET.Element("port_scan", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              target=str(res.get("target", "")),
                              success=str(res.get("success", False)).lower())
            ips_elem = ET.SubElement(root, "resolved_ips")
            for ip in meta.get("ips", []):
                ET.SubElement(ips_elem, "ip").text = ip
            open_elem = ET.SubElement(root, "open_ports")
            for p in meta.get("open_ports", []):
                ET.SubElement(open_elem, "port",
                              number=str(p.get("port", "")),
                              service=str(p.get("service", "")),
                              latency_ms=str(p.get("latency_ms", "")))
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 8. Traceroute
        elif "hops" in meta:
            root = ET.Element("traceroute", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              target=str(res.get("target", "")),
                              success=str(res.get("success", False)).lower())
            for h in meta.get("hops", []):
                ET.SubElement(root, "hop",
                              number=str(h.get("hop", "")),
                              ip=str(h.get("ip", "*")),
                              name=str(h.get("name", "*")),
                              latency_ms=str(h.get("latency_ms", "")))
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        # 9. WHOIS / RDAP
        elif "rdap_source" in meta:
            root = ET.Element("whois_lookup", date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                              target=str(res.get("target", "")),
                              success=str(res.get("success", False)).lower())
            ET.SubElement(root, "type").text = meta.get("type", "")
            ET.SubElement(root, "rdap_source").text = meta.get("rdap_source", "")
            ET.SubElement(root, "registrar").text = meta.get("registrar", "") or ""
            ET.SubElement(root, "creation_date").text = meta.get("creation_date", "") or ""
            if res.get("error"):
                ET.SubElement(root, "error").text = res.get("error")
            xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
            return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str

    # Default legacy TCP connect check format
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
            method = r.get("metadata", {}).get("method", "socket")
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

        # 1.5. Local Listening Ports formatter
        elif target == "ports" or "listening_ports" in meta:
            lines.append("Local Listening Ports & Services")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")

            listening_ports = meta.get("listening_ports", [])
            if listening_ports:
                lines.append(f"🔓 {c['bold']}Active Listening Sockets:{c['reset']}")
                lines.append("  Proto  Local Address                  Port   Process/Service (PID)")
                lines.append("  ──────────────────────────────────────────────────────────────────")
                for p in sorted(listening_ports, key=lambda x: x.get("port", 0)):
                    proto = p.get("proto", "TCP")
                    addr = p.get("address", "*")
                    port = p.get("port", 0)
                    proc = p.get("process", "Unknown")
                    pid = p.get("pid", "")
                    
                    pid_str = f" ({pid})" if pid else ""
                    proc_details = f"{proc}{pid_str}"
                    
                    lines.append(f"  {proto:<5}  {pad_right(addr, 30)} {port:<6} {proc_details}")
                lines.append("")
            else:
                lines.append("No active listening ports found or failed to retrieve.")
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
            cipher = meta.get("cipher")
            tls_version = meta.get("tls_version")
            fingerprint = meta.get("fingerprint")
            if tls_version or cipher or fingerprint:
                lines.append("├─────────────────────────────────────────────┤")
                lines.append("│ Connection Security Details:                 │")
                lines.append("├─────────────────────────────────────────────┤")
                if tls_version:
                    lines.append(f"│ TLS Version: {pad_right(tls_version, 30)} │")
                if cipher:
                    lines.append(f"│ Cipher Suite: {pad_right(cipher, 29)} │")
                if fingerprint:
                    fp_short = f"{fingerprint[:16]}...{fingerprint[-16:]}"
                    lines.append(f"│ SHA-256 FP: {pad_right(fp_short, 31)} │")
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
            
        # 6. TCP Connection Check Formatter
        elif "port" in meta and not "valid_until" in meta and not "status_code" in meta:
            lines.append(f"TCP Connection Test for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Connecting to {target}...")
            lines.append("")
            
            status_icon = f"{c['green']}✅ SUCCESS{c['reset']}" if success else f"{c['red']}❌ FAILED{c['reset']}"
            service_name = meta.get("service", "")
            ip_addr = meta.get("ip") or "Unknown"
            
            lines.append("┌─────────────────────────────────────────────┐")
            lines.append(f"│ Host: {pad_right(target, 37)} │")
            lines.append(f"│ Port: {pad_right(str(meta.get('port', '')), 37)} │")
            if service_name:
                lines.append(f"│ Service: {pad_right(service_name, 34)} │")
            lines.append("├─────────────────────────────────────────────┤")
            lines.append(f"│ Status: {pad_right(status_icon, 35)} │")
            lines.append(f"│ IP Address: {pad_right(ip_addr, 31)} │")
            lines.append(f"│ Latency: {pad_right(f'{latency}ms' if latency is not None else 'N/A', 34)} │")
            if error:
                err_str = str(error)
                if len(err_str) > 35:
                    err_str = err_str[:32] + "..."
                lines.append(f"│ Reason: {pad_right(err_str, 35)} │")
            lines.append("└─────────────────────────────────────────────┘")
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        # 7. Traceroute Formatter
        elif "hops" in meta:
            lines.append(f"Traceroute to: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"{'Hop':3} {'IP Address':15} {'Hostname/Details':30} {'Latency'}")
            lines.append("────────────────────────────────────────")
            for h in meta.get("hops", []):
                hop_num = h.get("hop")
                ip = h.get("ip", "*")
                name = h.get("name", "*")
                latency = f"{h.get('latency_ms')} ms" if h.get('latency_ms') is not None else "*"
                
                name_str = name
                if name_str == ip:
                    name_str = ""
                lines.append(f"{hop_num:<3} {pad_right(ip, 15)} {pad_right(name_str, 30)} {latency}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        # 8. Port Scanner Formatter
        elif "open_ports" in meta:
            lines.append(f"Port Scan for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Scan complete. Resolved IPs: {', '.join(meta.get('ips', []))}")
            lines.append("")
            lines.append(f"📡 {c['bold']}Open Ports:{c['reset']}")
            lines.append("────────────────────────────────────────")
            open_ports = meta.get("open_ports", [])
            if not open_ports:
                lines.append("  No open ports found.")
            else:
                for p in open_ports:
                    service = p.get("service")
                    service_str = f"({service})" if service else ""
                    latency = f"{p.get('latency_ms')} ms" if p.get('latency_ms') is not None else ""
                    lines.append(f"  Port {p.get('port'):<5} - OPEN {service_str:<15} {latency}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        # 9. Whois/RDAP Formatter
        elif "rdap_source" in meta:
            lines.append(f"Registration/WHOIS Lookup for: {target}")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"Type: {meta.get('type', 'UNKNOWN')}")
            lines.append(f"Source: {meta.get('rdap_source', 'N/A')}")
            if meta.get("registrar"):
                lines.append(f"Registrar/Owner: {meta.get('registrar')}")
            if meta.get("creation_date"):
                lines.append(f"Creation Date: {meta.get('creation_date')}")
            if meta.get("raw_whois"):
                lines.append("")
                lines.append("Raw WHOIS Data (Snippet):")
                lines.append("────────────────────────────────────────")
                snippet = "\n".join(meta.get("raw_whois", "").splitlines()[:20])
                lines.append(snippet)
                if len(meta.get("raw_whois", "").splitlines()) > 20:
                    lines.append("...")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            return "\n".join(lines)

        # 10. Fallback default single-target box
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
            elif "port" in meta and not "valid_until" in meta:
                service_str = f" ({meta['service']})" if meta.get("service") else ""
                details = f"TCP port {meta['port']}{service_str}" + (f" - IP: {meta['ip']}" if meta.get("ip") else "")
            elif "ips" in meta:
                details = f"IPs: {', '.join(meta['ips'][:3])}"
                
            lines.append(f"{pad_right(status_str, 12)} {pad_right(target, 30)} {pad_right(latency, 10)} {details}")
            
        lines.append("="*80)
        lines.append("Check Complete!")
        latencies = [r["latency_ms"] for r in results if r.get("success", False) and r.get("latency_ms") is not None]
        avg_latency = f"{sum(latencies)/len(latencies):.2f}ms" if latencies else "N/A"
        lines.append(f"Total: {len(results)}  |  Successful: {successes}  |  Failed: {failures}  |  Avg Latency: {avg_latency}")
        lines.append("="*80)
        
    return "\n".join(lines)
