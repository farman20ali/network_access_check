import ipaddress
from typing import List

def expand_ip_range(ip_str: str) -> List[str]:
    """
    Expands an IP string representing a single IP, a CIDR block (e.g. 192.168.1.0/24),
    or a dash-range (e.g. 192.168.1.1-50).
    """
    ip_str = ip_str.strip()
    if not ip_str:
        return []
        
    if "/" in ip_str:
        try:
            network = ipaddress.ip_network(ip_str, strict=False)
            return [str(ip) for ip in network.hosts()]
        except Exception:
            return [ip_str]
            
    elif "-" in ip_str:
        try:
            parts = ip_str.split("-")
            start_ip = parts[0].strip()
            end_val = parts[1].strip()
            
            # If the second part is just a single octet (e.g. 192.168.1.1-50)
            if "." not in end_val:
                base_parts = start_ip.split(".")
                base_parts[-1] = end_val
                end_ip = ".".join(base_parts)
            else:
                end_ip = end_val
                
            start = ipaddress.ip_address(start_ip)
            end = ipaddress.ip_address(end_ip)
            
            ips = []
            curr = start
            while curr <= end:
                ips.append(str(curr))
                curr += 1
            return ips
        except Exception:
            return [ip_str]
    else:
        return [ip_str]

def expand_port_range(port_str: str) -> List[int]:
    """
    Expands a port range string which can be a single port (80), a list (80,443),
    or a dash-range (8000-8100).
    """
    port_str = str(port_str).strip()
    ports = []
    if "," in port_str:
        for p in port_str.split(","):
            ports.extend(expand_port_range(p))
    elif "-" in port_str:
        try:
            parts = port_str.split("-")
            start = int(parts[0])
            end = int(parts[1])
            if 1 <= start <= 65535 and 1 <= end <= 65535:
                ports.extend(range(start, end + 1))
        except Exception:
            pass
    else:
        try:
            p_val = int(port_str)
            if 1 <= p_val <= 65535:
                ports.append(p_val)
        except ValueError:
            pass
            
    # Remove duplicates and preserve order
    seen = set()
    return [p for p in ports if not (p in seen or seen.add(p))]
