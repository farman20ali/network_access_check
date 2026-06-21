from typing import Tuple

def normalize_host(raw: str) -> str:
    """Strips scheme, path, query, and port to return a clean hostname/IP."""
    if not raw:
        return ""
    if "://" in raw:
        raw = raw.split("://", 1)[1]
    raw = raw.split("/", 1)[0]
    raw = raw.split("?", 1)[0]
    raw = raw.split("#", 1)[0]
    raw = raw.split(":", 1)[0]
    return raw.strip()

def parse_line_to_raw_host_port(line: str, default_port: str = "80") -> Tuple[str, str]:
    """
    Robustly parses an input line to extract raw host (could be range/CIDR)
    and raw port (could be list/range).
    Supports:
      - host port
      - host,port
      - host:port
      - http://host:port/path
      - [ipv6]:port
      - Handles trailing comments (#) and paths/queries.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return "", ""
        
    # Remove trailing comments starting with #
    if "#" in line:
        line = line.split("#", 1)[0].strip()
        
    # Is it a URL?
    if "://" in line:
        try:
            proto, rest = line.split("://", 1)
            # Strip path, query, fragment
            rest_host = rest.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip()
            default_p = "443" if proto.lower() == "https" else default_port
            
            if ":" in rest_host:
                if rest_host.startswith("["):
                    if "]:" in rest_host:
                        h, p = rest_host.split("]:", 1)
                        return h[1:], p
                    elif rest_host.endswith("]"):
                        return rest_host[1:-1], default_p
                h, p = rest_host.rsplit(":", 1)
                if p.isdigit():
                    return h, p
                return rest_host, default_p
            return rest_host, default_p
        except Exception:
            pass

    # Does it have whitespace? E.g. "192.168.1.1 80" or "google.com 80,443"
    parts = line.split(None, 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
        
    # Does it have a comma? E.g. "google.com,80" or "google.com,80,443"
    if "," in line and not line.startswith(",") and not line.endswith(","):
        parts = line.split(",", 1)
        h_part, p_part = parts[0].strip(), parts[1].strip()
        clean_p = p_part.replace("-", "").replace(",", "").replace(" ", "")
        if clean_p.isdigit():
            return h_part, p_part
            
    # Does it have a colon? E.g. "google.com:80" or "[2a00::]:80"
    if ":" in line:
        if line.startswith("["):
            if "]:" in line:
                h, p = line.split("]:", 1)
                p = p.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip()
                return h[1:], p
            elif line.endswith("]"):
                return line[1:-1], default_port
        h, p = line.rsplit(":", 1)
        p_clean = p.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip()
        if p_clean.isdigit():
            return h, p_clean
            
    # Fallback: strip trailing paths/slashes if present (e.g. google.com/path)
    host_clean = line.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0].strip()
    return host_clean, default_port
