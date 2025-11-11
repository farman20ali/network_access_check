# Comprehensive Examples - All Features

## 1. Quick Mode Examples

### Single Port Check
```bash
netcheck -q google.com 443
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

---

## 2. CSV Input Examples

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

## 3. Space-Separated Format (Traditional)

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

## 6. Format Comparison

| Format | Syntax | Use Case |
|--------|--------|----------|
| Space | `host 80` | Simple, traditional |
| CSV | `host,80` | Excel, databases |
| Quick | `-q host 80` | One-off tests |
| Multiple | `host 80,443` | Many ports |
| Range | `host 80-100` | Port scanning |
| IP Range | `192.168.1.1-50 80` | Subnet checks |
| CIDR | `10.0.0.0/24 80` | Network scans |

---

## 7. Performance Tips

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

**Quick Tests:**
- `-q host 80` - Single port
- `-q host 80,443` - Multiple ports  
- `-q host 80-100` - Port range

**CSV Input:**
- `--csv file.csv` - Read CSV file
- `--csv` with stdin - Pipe CSV data

**Ranges:**
- `192.168.1.1-50` - IP range
- `10.0.0.0/24` - CIDR notation
- `80,443,8080` - Multiple ports
- `8000-8100` - Port range

**All features work together!**
