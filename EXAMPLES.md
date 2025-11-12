# Comprehensive Examples - All Features

## 1. Version & Help

### Check Version
```bash
netcheck -v
netcheck --version
```

Output:
```
Network Connectivity Checker (netcheck) version 1.0.0
Copyright (c) 2025
License: GNU GPL v3
```

### Get Help
```bash
netcheck -h
netcheck --help
```

---

## 2. DNS Lookup Examples

### Basic DNS Resolution
```bash
netcheck -d google.com
netcheck -d github.com
netcheck -d example.com
```

### DNS from URLs (NEW!)
```bash
# Automatically strips http://, https://, paths, and ports
netcheck -d https://api.example.com
netcheck -d http://services.company.com:8080/api/v1
netcheck -d https://github.com/user/repo

# All of these resolve just the hostname
```

Output:
```
DNS Lookup for: https://api.example.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Hostname: api.example.com

IP Addresses:
  93.184.216.34

Aliases:

Reverse DNS:
  example.com.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Check Before Testing
```bash
# First resolve DNS
netcheck -d myserver.com

# Then test connectivity
netcheck -q myserver.com 443
```

---

## 3. ICMP Ping Examples

### Basic Ping
```bash
# Ping IP address
netcheck -p 8.8.8.8
netcheck -p 192.168.1.1

# Ping hostname
netcheck -p google.com
netcheck -p github.com
```

### Ping from URLs (NEW!)
```bash
# Automatically strips http://, https://, paths, and ports
netcheck -p https://github.com
netcheck -p http://api.example.com:8080
netcheck -p https://services.company.com/api
```

Output:
```
ICMP Ping Test for: https://github.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target: github.com

Sending 4 ICMP packets...

PING github.com (20.207.73.82) 56(84) bytes of data.
64 bytes from 20.207.73.82: icmp_seq=1 ttl=51 time=45.2 ms
64 bytes from 20.207.73.82: icmp_seq=2 ttl=51 time=43.8 ms
64 bytes from 20.207.73.82: icmp_seq=3 ttl=51 time=44.1 ms
64 bytes from 20.207.73.82: icmp_seq=4 ttl=51 time=43.9 ms

--- github.com ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 43.823/44.250/45.234/0.556 ms

✅ Ping successful
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. Quick Mode Examples

### Single Port Check
```bash
netcheck -q google.com 443
netcheck -q 192.168.1.1 80
```

### Save Quick Mode Results (NEW!)
```bash
# Save to file with -o flag
netcheck -q 192.168.1.1-5 80 -o quick-results.txt
netcheck -q server.com 80,443 -o webcheck.txt

# Results include formatted output with summary
cat quick-results.txt
```

### Quick Mode Parallel Processing (NEW!)
```bash
# Automatic parallel processing for >5 tests
netcheck -q 192.168.1.1-20 80    # Runs in parallel (20 tests)
netcheck -q 10.0.0.1-3 80        # Sequential (3 tests)

# Control parallel jobs with -j flag
netcheck -q 192.168.1.1-50 80 -j 20    # 20 parallel jobs
```

### Multiple Ports
```bash
# Check web ports
netcheck -q server.com 80,443,8080

# Check database ports
netcheck -q db.local 3306,5432,6379
```

### Port Range Scanning
```bash
# Scan common ports
netcheck -q server.local 20-25

# Scan high ports
netcheck -q localhost 8000-8100
```

### IP Range with Quick Mode
```bash
# Test multiple hosts at once
netcheck -q 10.90.95.72-75 50000
netcheck -q 192.168.1.1-10 22
netcheck -q 172.16.0.1-5 80,443
```

---

## 4. CSV Input Examples

### Basic CSV File
```csv
host,port
google.com,443
github.com,443
localhost,80
```

**Usage:**
```bash
netcheck --csv hosts.csv
```

### CSV with Ranges
```csv
host,port
192.168.1.1-50,22
10.0.0.0/24,80
server.local,"80,443,8080"
web-app.com,8000-8010
```

**Usage:**
```bash
netcheck --csv servers.csv -j 50 -f json
```

### Generate CSV from Script
```bash
# Create CSV dynamically
cat << EOF | netcheck --csv -f csv
host,port
$(for i in {1..10}; do echo "192.168.1.$i,80"; done)
EOF
```

---

## 5. Space-Separated Format (Traditional)

### File Format
```
# comments supported
google.com 443
192.168.1.1-50 80
10.0.0.0/24 22
localhost 80,443,3306
server.com 8000-8100
```

**Usage:**
```bash
netcheck hosts.txt
cat hosts.txt | netcheck -V  # Verbose mode
```

---

## 6. Verbose Mode

### Enable Detailed Output
```bash
# Note: Use capital -V for verbose
netcheck -V hosts.txt
echo "google.com 443" | netcheck -V
netcheck --csv servers.csv -V
```

Shows detailed information:
- Start date/time
- Configuration settings
- Real-time progress
- Success/failure status
- Summary statistics

---

## 7. Real-World Scenarios

**Usage:**
```bash
netcheck hosts.txt
cat hosts.txt | netcheck -v
```

---

## 4. Real-World Scenarios

### Scenario 1: Data Center Health Check
```bash
# Create CSV of all servers
cat << EOF > datacenter.csv
host,port
web-01.prod,"80,443"
web-02.prod,"80,443"
db-master.prod,3306
db-slave.prod,3306
cache-01.prod,6379
cache-02.prod,6379
192.168.100.0/26,22
EOF

# Check with high parallelism
netcheck --csv datacenter.csv -j 50 -t 3 -f json
```

### Scenario 2: Quick Server Diagnostics
```bash
# Check all common services on a server
netcheck -q server.prod.com 22,80,443,3306,5432,6379,8080,9000
```

### Scenario 3: Network Subnet Discovery
```bash
# Find active hosts in multiple subnets
cat << EOF | netcheck -j 100 -f csv
192.168.1.0/24 22
192.168.2.0/24 22
192.168.3.0/24 22
10.0.0.0/24 22
EOF
```

### Scenario 4: Port Scanner
```bash
# Scan ports 1-1024 on target (use responsibly!)
echo "target.local 1-1024" | netcheck -j 200 -t 1

# Or quick scan common ports
netcheck -q target.local 20-25,80,443,3306,3389,5432,6379,8000-8100
```

### Scenario 5: Monitoring Script
```bash
#!/bin/bash
# monitor-services.sh

CRITICAL_SERVICES="critical-services.csv"

# Create service list
cat << EOF > $CRITICAL_SERVICES
host,port
api-gateway.prod,"80,443"
auth-service.prod,"8080,8443"
db-primary.prod,3306
redis-master.prod,6379
EOF

# Run check
if netcheck --csv $CRITICAL_SERVICES -t 5 -f json > status.json; then
    echo "All services healthy"
else
    echo "Some services are down! Check status.json"
    # Send alert
    mail -s "Service Alert" admin@example.com < status.json
fi
```

### Scenario 6: Load Balancer Pool Check
```bash
# Check all backend servers
cat << EOF | netcheck -j 20
backend-01.local 80,443
backend-02.local 80,443
backend-03.local 80,443
backend-04.local 80,443
backend-05.local 80,443
EOF
```

### Scenario 7: CSV Export for Reporting
```bash
# Check and generate CSV report
netcheck --csv infrastructure.csv -f csv -c

# Result can be opened in Excel/LibreOffice
libreoffice result.csv

# Or process with other tools
cat result.csv | grep SUCCESS | wc -l
```

---

## 5. Advanced Combinations

### CSV + JSON Output + Combined Report
```bash
netcheck --csv servers.csv -f json -c -j 50 -t 3
# Creates: result.txt, fail-*.txt, combined-*.txt (all in JSON)
```

### Mixed Input with Ranges
```bash
cat << EOF | netcheck -v
# Web servers
web-01.prod 80,443
web-02.prod 80,443

# Database cluster
192.168.10.1-5 3306

# Dev environment subnet
10.20.0.0/28 22,80

# Monitoring range
monitor.local 8000-8010
EOF
```

### Pipeline Processing
```bash
# Generate hosts, check them, process results
for subnet in 192.168.{1..5}; do
    echo "${subnet}.0/24 22"
done | netcheck -j 100 -f csv | grep SUCCESS | cut -d',' -f2
```

---

## 8. Format Comparison

| Format | Syntax | Use Case |
|--------|--------|----------|
| Space | `host 80` | Simple, traditional |
| CSV | `host,80` | Excel, databases |
| Quick | `-q host 80` | One-off tests |
| Multiple | `host 80,443` | Many ports |
| Range | `host 80-100` | Port scanning |
| IP Range | `192.168.1.1-50 80` | Subnet checks |
| CIDR | `10.0.0.0/24 80` | Network scans |
| DNS | `-d host` | Resolve to IP |
| Version | `-v` | Check tool version |

---

## 9. Performance Tips

```bash
# Slow: Sequential (default 10 parallel)
netcheck large-list.txt

# Fast: High parallelism
netcheck large-list.txt -j 100

# Very Fast: High parallelism + short timeout
netcheck large-list.txt -j 200 -t 1

# For large CIDR blocks
echo "10.0.0.0/16 22" | netcheck -j 256 -t 2
```

---

## 8. Output Format Examples

### Text (default)
```bash
netcheck hosts.txt
```

### JSON (for scripts)
```bash
netcheck --csv hosts.csv -f json | jq '.results[] | select(.status=="success")'
```

### CSV (for Excel)
```bash
netcheck hosts.txt -f csv
libreoffice result.csv
```

### XML (for systems)
```bash
netcheck hosts.txt -f xml
xmllint --format result.txt
```

---

## Summary

**Version & Help:**
- `-v` or `--version` - Show version
- `-h` or `--help` - Show help

**DNS Lookup:**
- `-d google.com` - Resolve DNS to IP
- Shows IPv4, IPv6, aliases, reverse DNS

**Quick Tests:**
- `-q host 80` - Single port
- `-q host 80,443` - Multiple ports  
- `-q host 80-100` - Port range
- `-q 10.0.0.1-10 80` - IP range (NEW!)

**CSV Input:**
- `--csv file.csv` - Read CSV file
- `--csv` with stdin - Pipe CSV data

**Ranges:**
- `192.168.1.1-50` - IP range
- `10.0.0.0/24` - CIDR notation
- `80,443,8080` - Multiple ports
- `8000-8100` - Port range

**Other Options:**
- `-V` - Verbose mode (capital V, not lowercase)
- `-f json|csv|xml` - Output formats
- `-j 100` - High parallelism
- `-t 3` - Custom timeout
- `-c` - Combined reports

**All features work together!**
