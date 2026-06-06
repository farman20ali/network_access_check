#!/bin/bash
# Backward compatibility wrapper for NetCheck (Python-native implementation)
# Delegates all execution directly to the Python backend.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "${SCRIPT_DIR}/check_ip.py" ]; then
    python3 "${SCRIPT_DIR}/check_ip.py" "$@"
else
    if command -v netcheck &> /dev/null; then
        netcheck "$@"
    else
        echo "Error: Python netcheck implementation not found!" >&2
        exit 1
    fi
fi
