import socket
import time
from typing import Dict, Any, List
from netcheck.utils.cache import dns_cache
from netcheck.utils.normalize import normalize_host
from netcheck.utils.timeout import run_with_timeout

def dns_lookup(raw_target: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Resolves DNS for a given hostname or URL.
    Returns structured results with latency and A/AAAA IPs.
    """
    host = normalize_host(raw_target)
    if not host:
        return {
            "target": raw_target,
            "status": "FAILED",
            "latency_ms": 0.0,
            "success": False,
            "error": "Empty host target",
            "metadata": {}
        }
        
    result = {
        "target": raw_target,
        "status": "FAILED",
        "latency_ms": None,
        "success": False,
        "error": None,
        "metadata": {
            "resolved_host": host,
            "ips": [],
            "aliases": [],
            "reverse_dns": None
        }
    }
    
    # Check if target is already an IP address
    is_ip = False
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(family, host)
            is_ip = True
            break
        except OSError:
            pass
            
    if is_ip:
        result["status"] = "SUCCESS"
        result["success"] = True
        result["latency_ms"] = 0.0
        result["metadata"]["ips"] = [host]
        # Attempt a quick reverse lookup
        try:
            def _quick_rev():
                return socket.gethostbyaddr(host)[0]
            rev_name = run_with_timeout(2.0, _quick_rev)
            result["metadata"]["reverse_dns"] = rev_name
        except Exception:
            pass
        return result

    # Check the DNS cache
    cached = dns_cache.get(host)
    if cached:
        result.update(cached)
        result["target"] = raw_target
        return result

    start_time = time.perf_counter()
    try:
        def _resolve():
            return socket.getaddrinfo(host, None)
            
        addr_info = run_with_timeout(timeout, _resolve)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        
        ips = list(set(info[4][0] for info in addr_info))
        result["status"] = "SUCCESS"
        result["success"] = True
        result["latency_ms"] = round(duration_ms, 2)
        result["metadata"]["ips"] = ips
        
        if ips:
            try:
                def _reverse():
                    name, aliases, _ = socket.gethostbyaddr(ips[0])
                    return name, aliases
                rev_name, aliases = run_with_timeout(2.0, _reverse)
                result["metadata"]["reverse_dns"] = rev_name
                result["metadata"]["aliases"] = aliases
            except Exception:
                pass
                
        # Cache successful resolutions
        dns_cache.set(host, {
            "status": "SUCCESS",
            "success": True,
            "latency_ms": result["latency_ms"],
            "metadata": result["metadata"]
        })
        
    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        result["latency_ms"] = round(duration_ms, 2)
        result["error"] = str(e)
        result["status"] = "FAILED"
        result["success"] = False

    return result
