import socket
import platform
import subprocess
import re
from typing import Dict, Any, List, Tuple, Optional

def get_active_local_ip() -> str:
    """
    Finds the primary outbound IP address using the UDP routing table query.
    Falls back to a local IP check or returns '127.0.0.1' if disconnected.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually transmit packets, just queries the OS routing table
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip
    except Exception:
        # Fallback to query local gateway subnet
        try:
            s.connect(('192.168.1.1', 80))
            ip = s.getsockname()[0]
            return ip
        except Exception:
            return "127.0.0.1"
    finally:
        s.close()

def get_public_ip(timeout: float = 3.0) -> str:
    """Retrieves public IP address from public APIs."""
    import urllib.request
    services = ["https://api.ipify.org", "https://ifconfig.me", "https://icanhazip.com"]
    for service in services:
        try:
            req = urllib.request.Request(service, headers={'User-Agent': 'NetCheck/2.0'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                ip = response.read().decode('utf-8').strip()
                if ip:
                    return ip
        except Exception:
            continue
    return "Unknown"

def get_default_gateway() -> Tuple[Optional[str], Optional[str]]:
    """Returns (gateway_ip, interface_name) for the default route."""
    plat = platform.system().lower()
    if plat == "linux":
        try:
            with open("/proc/net/route", "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3 and parts[1] == "00000000": # default route
                        gw_hex = parts[2]
                        dev = parts[0]
                        # Hex IP is little-endian in /proc/net/route (e.g. 010116AC for 172.22.1.1)
                        gw_ip = socket.inet_ntoa(int(gw_hex, 16).to_bytes(4, byteorder='little'))
                        return gw_ip, dev
        except Exception:
            pass
            
    # Cross-platform fallback using route commands
    try:
        if plat == "windows":
            proc = subprocess.run(["route", "print", "0.0.0.0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    if "0.0.0.0" in line:
                        parts = line.strip().split()
                        if len(parts) >= 4 and parts[0] == "0.0.0.0":
                            return parts[2], None
        else: # macOS / Unix fallback
            proc = subprocess.run(["netstat", "-rn"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    if line.strip().startswith("default") or line.strip().startswith("0.0.0.0"):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            gateway = parts[1]
                            dev = parts[-1] if len(parts) >= 4 else None
                            return gateway, dev
    except Exception:
        pass
        
    return None, None

def get_network_interfaces(all_interfaces: bool = False, timeout: float = 3.0) -> Dict[str, Any]:
    """
    Identifies local network interfaces, their status, IPv4/IPv6 addresses,
    and flags the primary active connection.
    """
    primary_ip = get_active_local_ip()
    plat = platform.system().lower()
    
    interfaces = {}
    
    if plat == "windows":
        interfaces = _parse_windows_ipconfig()
    elif plat == "darwin":
        interfaces = _parse_unix_ifconfig()
    else:
        interfaces = _parse_linux_ip_addr()
        
    # If no interfaces were parsed but we have a primary IP, insert a dummy entry
    if not interfaces and primary_ip != "127.0.0.1":
        interfaces["default"] = {
            "ipv4": [primary_ip],
            "ipv6": [],
            "status": "UP",
            "active": True
        }
    else:
        # Post-process interfaces to set "active" flags based on primary IP match
        has_active = False
        for name, iface in interfaces.items():
            iface["active"] = False
            # Check if primary_ip matches any IPv4 address on this interface
            if primary_ip in iface["ipv4"]:
                iface["active"] = True
                iface["status"] = "UP"  # Force status to UP if it holds the active IP
                has_active = True
                
        # If no interface matched the primary IP, set the first one with an IP as active
        if not has_active:
            for name, iface in interfaces.items():
                if iface["ipv4"] and primary_ip != "127.0.0.1":
                    iface["active"] = True
                    iface["status"] = "UP"
                    break

    # Get gateway details
    gateway_ip, gateway_dev = get_default_gateway()
    
    # Get public IP
    public_ip = get_public_ip(timeout=timeout)
    
    # Filter active only if all_interfaces is False
    if not all_interfaces:
        interfaces = {name: iface for name, iface in interfaces.items() if iface.get("status") == "UP"}

    return {
        "target": "interfaces",
        "status": "SUCCESS",
        "latency_ms": 0.0,
        "success": True,
        "error": None,
        "metadata": {
            "primary_ip": primary_ip,
            "interfaces": interfaces,
            "gateway_ip": gateway_ip,
            "gateway_dev": gateway_dev,
            "public_ip": public_ip,
            "all_interfaces_shown": all_interfaces
        }
    }

def _parse_linux_ip_addr() -> Dict[str, Any]:
    interfaces = {}
    try:
        proc = subprocess.run(["ip", "addr", "show"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            current_iface = None
            for line in proc.stdout.splitlines():
                iface_match = re.match(r"^\d+:\s+([^:]+):", line)
                if iface_match:
                    current_iface = iface_match.group(1).strip()
                    if current_iface == "lo" or current_iface.startswith("veth"):
                        current_iface = None
                        continue
                    
                    state = "DOWN"
                    if "state UP" in line:
                        state = "UP"
                    elif "state UNKNOWN" in line:
                        state = "UNKNOWN"
                    elif "state DORMANT" in line:
                        state = "DORMANT"
                    
                    interfaces[current_iface] = {
                        "ipv4": [],
                        "ipv6": [],
                        "status": state
                    }
                elif current_iface and line.strip().startswith("inet "):
                    inet_match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", line)
                    if inet_match:
                        interfaces[current_iface]["ipv4"].append(inet_match.group(1))
                        # If interface has an IP, ensure it's considered UP
                        if interfaces[current_iface]["status"] in ("DOWN", "DORMANT"):
                            interfaces[current_iface]["status"] = "UP"
                elif current_iface and line.strip().startswith("inet6 "):
                    inet6_match = re.search(r"inet6\s+([0-9a-fA-F:]+)", line)
                    if inet6_match:
                        ip6 = inet6_match.group(1)
                        if not ip6.lower().startswith("fe80"):
                            interfaces[current_iface]["ipv6"].append(ip6)
    except Exception:
        # Fallback to ifconfig
        return _parse_unix_ifconfig()
    return interfaces

def _parse_unix_ifconfig() -> Dict[str, Any]:
    interfaces = {}
    try:
        proc = subprocess.run(["ifconfig"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            current_iface = None
            for line in proc.stdout.splitlines():
                if line and not line.startswith("\t") and not line.startswith(" "):
                    parts = line.split(":")
                    if len(parts) > 0:
                        current_iface = parts[0].strip()
                        if current_iface.startswith("lo") or current_iface.startswith("veth"):
                            current_iface = None
                            continue
                        state = "DOWN"
                        if "UP" in line or "RUNNING" in line:
                            state = "UP"
                        interfaces[current_iface] = {
                            "ipv4": [],
                            "ipv6": [],
                            "status": state
                        }
                elif current_iface and line.strip().startswith("inet "):
                    inet_match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", line)
                    if inet_match:
                        interfaces[current_iface]["ipv4"].append(inet_match.group(1))
                        interfaces[current_iface]["status"] = "UP"
                elif current_iface and line.strip().startswith("inet6 "):
                    inet6_match = re.search(r"inet6\s+([0-9a-fA-F:]+)", line)
                    if inet6_match:
                        ip6 = inet6_match.group(1)
                        if not ip6.lower().startswith("fe80"):
                            interfaces[current_iface]["ipv6"].append(ip6)
    except Exception:
        pass
    return interfaces

def _parse_windows_ipconfig() -> Dict[str, Any]:
    interfaces = {}
    try:
        proc = subprocess.run(["ipconfig"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode == 0:
            current_iface = None
            for line in proc.stdout.splitlines():
                if line.strip() and not line.startswith("   "):
                    if "adapter" in line:
                        current_iface = line.split(":", 1)[0].replace("adapter", "").strip()
                        current_iface = current_iface.replace("Wireless LAN", "WLAN").replace("Ethernet adapter", "Ethernet")
                        interfaces[current_iface] = {
                            "ipv4": [],
                            "ipv6": [],
                            "status": "DOWN"
                        }
                elif current_iface and "IPv4 Address" in line:
                    ip_match = re.search(r":\s*(\d+\.\d+\.\d+\.\d+)", line)
                    if ip_match:
                        interfaces[current_iface]["ipv4"].append(ip_match.group(1))
                        interfaces[current_iface]["status"] = "UP"
                elif current_iface and "IPv6 Address" in line:
                    ip6_match = re.search(r":\s*([0-9a-fA-F:]+)", line)
                    if ip6_match:
                        ip6 = ip6_match.group(1)
                        if not ip6.lower().startswith("fe80"):
                            interfaces[current_iface]["ipv6"].append(ip6)
                            interfaces[current_iface]["status"] = "UP"
    except Exception:
        pass
    return interfaces
