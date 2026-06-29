import socket

# Curated dictionary of well-known port mapping to service names
_CURATED_SERVICES = {
    20: "ftp-data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    67: "dhcp-server",
    68: "dhcp-client",
    69: "tftp",
    80: "http",
    88: "kerberos",
    110: "pop3",
    115: "sftp",
    119: "nntp",
    123: "ntp",
    135: "msrpc",
    137: "netbios-ns",
    138: "netbios-dgm",
    139: "netbios-ssn",
    143: "imap",
    161: "snmp",
    162: "snmp-trap",
    179: "bgp",
    389: "ldap",
    443: "https",
    445: "microsoft-ds",
    465: "smtps",
    500: "isakmp",
    514: "syslog",
    587: "submission",
    636: "ldaps",
    873: "rsync",
    993: "imaps",
    995: "pop3s",
    1080: "socks",
    1433: "mssql",
    1521: "oracle",
    2049: "nfs",
    3000: "gitea/react",
    3306: "mysql",
    3389: "rdp",
    5060: "sip",
    5432: "postgresql",
    5672: "rabbitmq",
    5900: "vnc",
    6379: "redis",
    8000: "http-alt",
    8080: "http-proxy",
    8443: "https-alt",
    9000: "portainer",
    9092: "kafka",
    9200: "elasticsearch",
    11211: "memcached",
    27017: "mongodb"
}

def get_service_name(port: int) -> str:
    """
    Returns a service name string for a given port.
    Tries standard library socket.getservbyport first,
    falling back to a curated internal dictionary.
    """
    try:
        return socket.getservbyport(port, "tcp")
    except Exception:
        pass
    try:
        return socket.getservbyport(port, "udp")
    except Exception:
        pass
    return _CURATED_SERVICES.get(port, "")
