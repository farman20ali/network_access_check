#!/bin/bash

# Network Connectivity Checker
# Advanced version with parallel processing, progress bar, and multiple output formats
# Usage: ./check_ip.sh [OPTIONS] [input_file]
# Input format: Each line should contain IP/hostname and port separated by space
# Example: 192.168.1.1 80

set -u

# Default configuration
TIMEOUT=5
MAX_JOBS=10
VERBOSE=0
OUTPUT_FORMAT="text"
INPUT_FILE=""
COMBINED_REPORT=0
QUICK_TEST=0
CSV_INPUT=0

# Show help
show_help() {
    cat << EOF
Network Connectivity Checker - Advanced Version

Usage: $0 [OPTIONS] [input_file]

OPTIONS:
    -t, --timeout <seconds>     Connection timeout (default: 5)
    -j, --jobs <number>         Max parallel jobs (default: 10)
    -v, --verbose               Verbose output
    -f, --format <format>       Output format: text, json, csv, xml (default: text)
    -c, --combined              Create combined report with all results
    -q, --quick <host> <port>   Quick test mode (supports ranges: 80,443 or 8000-8100)
    --csv                       Input file is in CSV format (host,port)
    -h, --help                  Show this help message

INPUT:
    input_file                  File containing IP:port pairs (one per line)
                               If not specified, reads from stdin
                               Use --csv flag for CSV format files

EXAMPLES:
    $0 ip-text.txt                          # Basic usage
    $0 --csv hosts.csv                      # Read from CSV file
    $0 -t 10 -j 20 ip-text.txt             # Custom timeout and parallel jobs
    $0 -f json -c ip-text.txt              # JSON output with combined report
    cat ip-text.txt | $0 -v                 # Verbose mode from stdin
    $0 -q 192.168.1.1 80                    # Quick test single port
    $0 -q google.com 80,443                 # Quick test multiple ports
    $0 -q localhost 8000-8100               # Quick test port range
    echo "192.168.1.1-50 80" | $0          # Check IP range
    echo "192.168.1.0/24 22" | $0          # Check CIDR subnet
    echo "host.com 80,443,8080" | $0       # Check multiple ports
    echo "host.com 8000-8100" | $0         # Check port range

INPUT FORMAT:
    Each line should contain: HOST PORT(S)
    
    Basic:      192.168.1.1 80
    IP Range:   192.168.1.1-50 80        (checks .1 through .50)
    CIDR:       192.168.1.0/24 80        (checks entire subnet)
    Multi-port: 192.168.1.1 80,443,8080  (checks multiple ports)
    Port Range: 192.168.1.1 8000-8100    (checks port range)
    Combined:   192.168.1.1-10 80,443    (IP range with multiple ports)
    
    CSV FORMAT (with --csv flag):
    host,port
    192.168.1.1,80
    server.com,443
    10.0.0.1-5,22           (ranges supported)
    host.local,"80,443"     (multiple ports in quotes)

EOF
    exit 0
}

# Parse command-line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            -j|--jobs)
                MAX_JOBS="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=1
                shift
                ;;
            -f|--format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            -c|--combined)
                COMBINED_REPORT=1
                shift
                ;;
            --csv)
                CSV_INPUT=1
                shift
                ;;
            -q|--quick)
                QUICK_TEST=1
                QUICK_HOST="$2"
                QUICK_PORT="$3"
                shift 3
                ;;
            -h|--help)
                show_help
                ;;
            -*)
                echo "Error: Unknown option: $1" >&2
                echo "Use -h or --help for usage information" >&2
                exit 1
                ;;
            *)
                INPUT_FILE="$1"
                shift
                ;;
        esac
    done
}

parse_args "$@"

# Function to expand IP range (192.168.1.1-50)
expand_ip_range() {
    local ip_pattern=$1
    local ips=()
    
    # Check if it's a range (contains -)
    if [[ $ip_pattern =~ ^([0-9]+\.[0-9]+\.[0-9]+\.)([0-9]+)-([0-9]+)$ ]]; then
        local prefix="${BASH_REMATCH[1]}"
        local start="${BASH_REMATCH[2]}"
        local end="${BASH_REMATCH[3]}"
        
        for ((i=start; i<=end; i++)); do
            ips+=("${prefix}${i}")
        done
    # Check if it's CIDR notation
    elif [[ $ip_pattern =~ ^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/([0-9]+)$ ]]; then
        local base_ip="${BASH_REMATCH[1]}"
        local cidr="${BASH_REMATCH[2]}"
        
        # Convert CIDR to IP range
        IFS='.' read -r i1 i2 i3 i4 <<< "$base_ip"
        local ip_num=$((i1 * 256**3 + i2 * 256**2 + i3 * 256 + i4))
        local hosts=$((2**(32-cidr)))
        
        # Calculate network address
        local mask=$((0xFFFFFFFF << (32 - cidr) & 0xFFFFFFFF))
        local network=$((ip_num & mask))
        
        # Skip network address and broadcast for /24 or smaller
        local start_offset=0
        local end_offset=$hosts
        
        if [[ $cidr -ge 24 ]]; then
            start_offset=1
            end_offset=$((hosts - 1))
        fi
        
        # Generate IPs (limit to reasonable number)
        if [[ $hosts -gt 256 ]]; then
            echo "Warning: CIDR /$cidr generates $hosts IPs, limiting to first 256" >&2
            end_offset=256
        fi
        
        for ((i=start_offset; i<end_offset; i++)); do
            local curr=$((network + i))
            local ip="$((curr >> 24 & 255)).$((curr >> 16 & 255)).$((curr >> 8 & 255)).$((curr & 255))"
            ips+=("$ip")
        done
    else
        # Single IP or hostname
        ips+=("$ip_pattern")
    fi
    
    printf '%s\n' "${ips[@]}"
}

# Function to expand port range (80,443,8080 or 8000-8100)
expand_port_range() {
    local port_pattern=$1
    local ports=()
    
    # Split by comma for multiple ports
    IFS=',' read -ra port_parts <<< "$port_pattern"
    
    for part in "${port_parts[@]}"; do
        # Check if it's a range (contains -)
        if [[ $part =~ ^([0-9]+)-([0-9]+)$ ]]; then
            local start="${BASH_REMATCH[1]}"
            local end="${BASH_REMATCH[2]}"
            
            # Validate range
            if [[ $start -gt $end ]]; then
                echo "Warning: Invalid port range $part (start > end)" >&2
                continue
            fi
            
            if [[ $((end - start)) -gt 1000 ]]; then
                echo "Warning: Port range $part too large (>1000 ports), limiting to first 1000" >&2
                end=$((start + 1000))
            fi
            
            for ((i=start; i<=end; i++)); do
                ports+=("$i")
            done
        else
            # Single port
            ports+=("$part")
        fi
    done
    
    printf '%s\n' "${ports[@]}"
}

# Function to expand a line with IP and port ranges
expand_line() {
    local line=$1
    local expanded_lines=()
    
    # Parse line into IP and port parts
    IFS=' ' read -ra parts <<< "$line"
    
    if [[ ${#parts[@]} -lt 2 ]]; then
        echo "Warning: Invalid line format: $line" >&2
        return
    fi
    
    local ip_pattern="${parts[0]}"
    local port_pattern="${parts[1]}"
    
    # Expand IPs
    local ips=()
    while IFS= read -r ip; do
        ips+=("$ip")
    done < <(expand_ip_range "$ip_pattern")
    
    # Expand ports
    local ports=()
    while IFS= read -r port; do
        ports+=("$port")
    done < <(expand_port_range "$port_pattern")
    
    # Create combinations
    for ip in "${ips[@]}"; do
        for port in "${ports[@]}"; do
            echo "$ip $port"
        done
    done
}

parse_args "$@"

# Quick test mode - check without creating files (supports port ranges)
if [[ $QUICK_TEST -eq 1 ]]; then
    echo "Quick Test Mode"
    echo "Host: $QUICK_HOST"
    echo "Port(s): $QUICK_PORT"
    echo "Timeout: ${TIMEOUT}s"
    echo ""
    
    # Expand ports if it's a range or multiple ports
    test_ports=()
    while IFS= read -r port; do
        test_ports+=("$port")
    done < <(expand_port_range "$QUICK_PORT")
    
    # Validate expanded ports
    for port in "${test_ports[@]}"; do
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [[ "$port" -lt 1 ]] || [[ "$port" -gt 65535 ]]; then
            echo "Error: Invalid port number: $port" >&2
            exit 1
        fi
    done
    
    total_ports=${#test_ports[@]}
    success_count=0
    fail_count=0
    
    echo "Testing ${total_ports} port(s)..."
    echo ""
    
    # Test each port
    for test_port in "${test_ports[@]}"; do
        # Try telnet first
        TELNET_EXIT_CODE=1
        NC_EXIT_CODE=1
        
        start_time=$(date +%s%N)
        (echo '^]'; echo quit) | timeout --signal=9 "$TIMEOUT" telnet "$QUICK_HOST" "$test_port" > /dev/null 2>&1 < /dev/null
        TELNET_EXIT_CODE=$?
        end_time=$(date +%s%N)
        
        # If telnet fails, try netcat
        if [[ $TELNET_EXIT_CODE -ne 0 ]]; then
            start_time=$(date +%s%N)
            nc -w "$TIMEOUT" -z "$QUICK_HOST" "$test_port" > /dev/null 2>&1
            NC_EXIT_CODE=$?
            end_time=$(date +%s%N)
        fi
        
        # Calculate response time in milliseconds
        response_time=$(( (end_time - start_time) / 1000000 ))
        
        # Display result
        echo "┌─────────────────────────────────────────────┐"
        printf "│ %-43s │\n" "Host: $QUICK_HOST"
        printf "│ %-43s │\n" "Port: $test_port"
        echo "├─────────────────────────────────────────────┤"
        
        if [[ $TELNET_EXIT_CODE -eq 0 ]] || [[ $NC_EXIT_CODE -eq 0 ]]; then
            method="telnet"
            [[ $NC_EXIT_CODE -eq 0 ]] && method="netcat"
            
            printf "│ Status: \033[0;32m%-34s\033[0m │\n" "✓ CONNECTED"
            printf "│ %-43s │\n" "Method: $method"
            printf "│ %-43s │\n" "Response Time: ${response_time}ms"
            echo "└─────────────────────────────────────────────┘"
            ((success_count++))
        else
            printf "│ Status: \033[0;31m%-34s\033[0m │\n" "✗ FAILED"
            printf "│ %-43s │\n" "Reason: Connection timeout or refused"
            printf "│ %-43s │\n" "Attempted Time: ${response_time}ms"
            echo "└─────────────────────────────────────────────┘"
            ((fail_count++))
        fi
        echo ""
    done
    
    # Summary for multiple ports
    if [[ $total_ports -gt 1 ]]; then
        echo "════════════════════════════════════════════"
        echo "Quick Test Summary"
        echo "════════════════════════════════════════════"
        echo "Total Ports: $total_ports"
        echo -e "Successful:  \033[0;32m$success_count\033[0m"
        echo -e "Failed:      \033[0;31m$fail_count\033[0m"
        echo "════════════════════════════════════════════"
    fi
    
    # Exit with proper code
    if [[ $fail_count -eq 0 ]]; then
        exit 0
    else
        exit 1
    fi
fi

# Validate output format
if [[ ! "$OUTPUT_FORMAT" =~ ^(text|json|csv|xml)$ ]]; then
    echo "Error: Invalid output format '$OUTPUT_FORMAT'. Must be: text, json, csv, or xml" >&2
    exit 1
fi

# Create temporary directory for parallel processing
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Initialize output files
name=$(date +"%Y-%m-%d")
timestamp=$(date +"%Y-%m-%d %H:%M:%S")

result_file="result.txt"
fail_file="fail-${name}.txt"
combined_file="combined-${name}.txt"

# Function to initialize output files based on format
init_output_files() {
    case $OUTPUT_FORMAT in
        text)
            init_text_format
            ;;
        json)
            init_json_format
            ;;
        csv)
            init_csv_format
            ;;
        xml)
            init_xml_format
            ;;
    esac
}

init_text_format() {
    echo "==================================================================" > "$result_file"
    echo "Network Connectivity Check - Successful Connections" >> "$result_file"
    echo "Date: $timestamp" >> "$result_file"
    echo "==================================================================" >> "$result_file"
    printf "%-15s %-20s %-10s %-20s\n" "Status" "Host" "Port" "Method" >> "$result_file"
    echo "------------------------------------------------------------------" >> "$result_file"

    echo "==================================================================" > "$fail_file"
    echo "Network Connectivity Check - Failed Connections" >> "$fail_file"
    echo "Date: $timestamp" >> "$fail_file"
    echo "==================================================================" >> "$fail_file"
    printf "%-15s %-20s %-10s %-20s\n" "Status" "Host" "Port" "Timestamp" >> "$fail_file"
    echo "------------------------------------------------------------------" >> "$fail_file"
    
    if [[ $COMBINED_REPORT -eq 1 ]]; then
        echo "==================================================================" > "$combined_file"
        echo "Network Connectivity Check - All Results" >> "$combined_file"
        echo "Date: $timestamp" >> "$combined_file"
        echo "==================================================================" >> "$combined_file"
        printf "%-15s %-20s %-10s %-20s %-20s\n" "Status" "Host" "Port" "Method/Time" "Notes" >> "$combined_file"
        echo "------------------------------------------------------------------" >> "$combined_file"
    fi
}

init_json_format() {
    echo "{\"check_date\":\"$timestamp\",\"results\":[" > "$result_file"
    echo "{\"check_date\":\"$timestamp\",\"failures\":[" > "$fail_file"
    
    if [[ $COMBINED_REPORT -eq 1 ]]; then
        echo "{\"check_date\":\"$timestamp\",\"all_results\":[" > "$combined_file"
    fi
}

init_csv_format() {
    echo "Status,Host,Port,Method,Timestamp" > "$result_file"
    echo "Status,Host,Port,Reason,Timestamp" > "$fail_file"
    
    if [[ $COMBINED_REPORT -eq 1 ]]; then
        echo "Status,Host,Port,Method/Reason,Timestamp" > "$combined_file"
    fi
}

init_xml_format() {
    echo '<?xml version="1.0" encoding="UTF-8"?>' > "$result_file"
    echo "<connectivity_check date=\"$timestamp\">" >> "$result_file"
    echo "  <successful_connections>" >> "$result_file"
    
    echo '<?xml version="1.0" encoding="UTF-8"?>' > "$fail_file"
    echo "<connectivity_check date=\"$timestamp\">" >> "$fail_file"
    echo "  <failed_connections>" >> "$fail_file"
    
    if [[ $COMBINED_REPORT -eq 1 ]]; then
        echo '<?xml version="1.0" encoding="UTF-8"?>' > "$combined_file"
        echo "<connectivity_check date=\"$timestamp\">" >> "$combined_file"
        echo "  <all_results>" >> "$combined_file"
    fi
}

init_output_files

init_output_files

# Function to write results in appropriate format
write_result() {
    local status=$1
    local host=$2
    local port=$3
    local method=$4
    local check_time=$5
    local file=$6
    
    case $OUTPUT_FORMAT in
        text)
            if [[ $status == "SUCCESS" ]]; then
                printf "%-15s %-20s %-10s %-20s\n" "$status" "$host" "$port" "$method" >> "$file"
            else
                printf "%-15s %-20s %-10s %-20s\n" "$status" "$host" "$port" "$check_time" >> "$file"
            fi
            ;;
        json)
            local comma=""
            [[ -s "$file" ]] && [[ $(tail -c 2 "$file") == "[" ]] && comma="" || comma=","
            if [[ $status == "SUCCESS" ]]; then
                echo "${comma}{\"status\":\"success\",\"host\":\"$host\",\"port\":$port,\"method\":\"$method\",\"timestamp\":\"$check_time\"}" >> "$file"
            else
                echo "${comma}{\"status\":\"failed\",\"host\":\"$host\",\"port\":$port,\"reason\":\"$method\",\"timestamp\":\"$check_time\"}" >> "$file"
            fi
            ;;
        csv)
            echo "\"$status\",\"$host\",$port,\"$method\",\"$check_time\"" >> "$file"
            ;;
        xml)
            if [[ $status == "SUCCESS" ]]; then
                echo "    <connection host=\"$host\" port=\"$port\" method=\"$method\" timestamp=\"$check_time\" />" >> "$file"
            else
                echo "    <connection host=\"$host\" port=\"$port\" reason=\"$method\" timestamp=\"$check_time\" />" >> "$file"
            fi
            ;;
    esac
}

# Function to finalize output files
finalize_output_files() {
    case $OUTPUT_FORMAT in
        json)
            echo "]}" >> "$result_file"
            echo "]}" >> "$fail_file"
            [[ $COMBINED_REPORT -eq 1 ]] && echo "]}" >> "$combined_file"
            ;;
        xml)
            echo "  </successful_connections>" >> "$result_file"
            echo "</connectivity_check>" >> "$result_file"
            echo "  </failed_connections>" >> "$fail_file"
            echo "</connectivity_check>" >> "$fail_file"
            if [[ $COMBINED_REPORT -eq 1 ]]; then
                echo "  </all_results>" >> "$combined_file"
                echo "</connectivity_check>" >> "$combined_file"
            fi
            ;;
    esac
}

# Progress bar function
show_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))
    
    printf "\rProgress: [" >&2
    printf "%${completed}s" | tr ' ' '=' >&2
    printf ">" >&2
    printf "%${remaining}s" | tr ' ' ' ' >&2
    printf "] %3d%% (%d/%d)" "$percentage" "$current" "$total" >&2
}

# Function to check a single host
check_host() {
    local line=$1
    local index=$2
    
    # Parse line into array
    IFS=' ' read -ra arr <<< "$line"
    
    local REMOTEHOST="${arr[0]}"
    local REMOTEPORT="${arr[1]}"
    local result_data="$TEMP_DIR/result_${index}"
    
    # Initialize exit codes
    local TELNET_EXIT_CODE=1
    local NC_EXIT_CODE=1
    
    [[ $VERBOSE -eq 1 ]] && echo "Checking: $REMOTEHOST:$REMOTEPORT" >&2
    
    # Try telnet first
    (echo '^]'; echo quit) | timeout --signal=9 "$TIMEOUT" telnet "$REMOTEHOST" "$REMOTEPORT" > /dev/null 2>&1 < /dev/null
    TELNET_EXIT_CODE=$?
    
    # If telnet fails, try netcat
    if [[ $TELNET_EXIT_CODE -ne 0 ]]; then
        nc -w "$TIMEOUT" -z "$REMOTEHOST" "$REMOTEPORT" > /dev/null 2>&1
        NC_EXIT_CODE=$?
    fi
    
    # Save results
    local check_time=$(date +"%Y-%m-%d %H:%M:%S")
    if [[ $TELNET_EXIT_CODE -eq 0 ]] || [[ $NC_EXIT_CODE -eq 0 ]]; then
        local method="telnet"
        [[ $NC_EXIT_CODE -eq 0 ]] && method="netcat"
        echo "SUCCESS|$REMOTEHOST|$REMOTEPORT|$method|$check_time" > "$result_data"
    else
        echo "FAILED|$REMOTEHOST|$REMOTEPORT|timeout/refused|$check_time" > "$result_data"
    fi
}

# Read input and store in array
readarray -t lines < "${INPUT_FILE:-/dev/stdin}"

# Parse CSV if --csv flag is set
if [[ $CSV_INPUT -eq 1 ]]; then
    parsed_lines=()
    skip_header=1
    
    for line in "${lines[@]}"; do
        [[ -z "$line" ]] && continue
        
        # Skip header line if it looks like a header
        if [[ $skip_header -eq 1 ]]; then
            if [[ $line =~ ^[[:space:]]*(host|hostname|ip|server|address)[[:space:]]*,.*port ]]; then
                skip_header=0
                continue
            fi
            skip_header=0
        fi
        
        # Skip comments
        [[ $line =~ ^[[:space:]]*# ]] && continue
        
        # Parse CSV: split by comma, handle quoted fields
        if [[ $line =~ ^\"([^\"]+)\",\"?([^\"]+)\"?$ ]]; then
            # Quoted format: "host","port"
            host="${BASH_REMATCH[1]}"
            port="${BASH_REMATCH[2]}"
        elif [[ $line =~ ^([^,]+),\"([^\"]+)\"$ ]]; then
            # Mixed: host,"port"
            host="${BASH_REMATCH[1]}"
            port="${BASH_REMATCH[2]}"
        elif [[ $line =~ ^([^,]+),([^,]+)$ ]]; then
            # Simple: host,port
            host="${BASH_REMATCH[1]}"
            port="${BASH_REMATCH[2]}"
        else
            echo "Warning: Invalid CSV format: $line" >&2
            continue
        fi
        
        # Trim whitespace
        host=$(echo "$host" | xargs)
        port=$(echo "$port" | xargs)
        
        # Convert to space-separated format
        parsed_lines+=("$host $port")
    done
    
    # Replace lines with parsed CSV data
    lines=("${parsed_lines[@]}")
fi

# Filter out empty lines, expand ranges, and validate
valid_lines=()
for line in "${lines[@]}"; do
    [[ -z "$line" ]] && continue
    
    # Skip comments
    [[ $line =~ ^[[:space:]]*# ]] && continue
    
    # Expand IP and port ranges
    while IFS= read -r expanded_line; do
        IFS=' ' read -ra arr <<< "$expanded_line"
        
        # Validate expanded line
        if [[ ${#arr[@]} -lt 2 ]]; then
            continue
        fi
        
        check_port="${arr[1]}"
        
        # Validate port number (should be single port after expansion)
        if ! [[ "$check_port" =~ ^[0-9]+$ ]] || [[ "$check_port" -lt 1 ]] || [[ "$check_port" -gt 65535 ]]; then
            echo "Warning: Invalid port number after expansion: $expanded_line" >&2
            continue
        fi
        
        valid_lines+=("$expanded_line")
    done < <(expand_line "$line")
done

TOTAL_HOSTS=${#valid_lines[@]}

if [[ $TOTAL_HOSTS -eq 0 ]]; then
    echo "Error: No valid hosts to check" >&2
    exit 1
fi

# Configuration
SUCCESS_COUNT=0
FAIL_COUNT=0
CURRENT_COUNT=0

echo "==========================================" >&2
echo "Network Connectivity Check Starting..." >&2
echo "Date: $timestamp" >&2
echo "Timeout: ${TIMEOUT}s" >&2
echo "Parallel Jobs: $MAX_JOBS" >&2
echo "Output Format: $OUTPUT_FORMAT" >&2
echo "Total Hosts: $TOTAL_HOSTS" >&2
echo "==========================================" >&2
echo "" >&2
echo "==========================================" >&2
echo "" >&2

# Process hosts in parallel
index=0
for line in "${valid_lines[@]}"; do
    # Wait if we've reached max parallel jobs
    while [[ $(jobs -r | wc -l) -ge $MAX_JOBS ]]; do
        sleep 0.1
    done
    
    # Start check in background
    check_host "$line" "$index" &
    ((index++))
    ((CURRENT_COUNT++))
    
    # Update progress bar
    show_progress "$CURRENT_COUNT" "$TOTAL_HOSTS"
done

# Wait for all background jobs to complete
wait

# Clear progress bar
echo "" >&2
echo "" >&2

# Process results
for i in $(seq 0 $((TOTAL_HOSTS - 1))); do
    result_file_temp="$TEMP_DIR/result_${i}"
    
    if [[ -f "$result_file_temp" ]]; then
        IFS='|' read -r status host port method check_time < "$result_file_temp"
        
        if [[ $status == "SUCCESS" ]]; then
            ((SUCCESS_COUNT++))
            write_result "$status" "$host" "$port" "$method" "$check_time" "$result_file"
            [[ $COMBINED_REPORT -eq 1 ]] && write_result "$status" "$host" "$port" "$method" "$check_time" "$combined_file"
            [[ $VERBOSE -eq 1 ]] && echo "✓ SUCCESS: $host:$port (via $method)" >&2
        else
            ((FAIL_COUNT++))
            write_result "FAILED" "$host" "$port" "$method" "$check_time" "$fail_file"
            [[ $COMBINED_REPORT -eq 1 ]] && write_result "FAILED" "$host" "$port" "$method" "$check_time" "$combined_file"
            [[ $VERBOSE -eq 1 ]] && echo "✗ FAILED: $host:$port ($method)" >&2
        fi
    fi
done

# Finalize output files
finalize_output_files

# Print summary
echo "==========================================" >&2
echo "Check Complete!" >&2
echo "==========================================" >&2
echo "Total Checked: $TOTAL_HOSTS" >&2
echo -e "Successful:    \033[0;32m$SUCCESS_COUNT\033[0m" >&2
echo -e "Failed:        \033[0;31m$FAIL_COUNT\033[0m" >&2
echo "==========================================" >&2
echo "Results saved to: $result_file" >&2
echo "Failures saved to: $fail_file" >&2
[[ $COMBINED_REPORT -eq 1 ]] && echo "Combined report: $combined_file" >&2
echo "==========================================" >&2


