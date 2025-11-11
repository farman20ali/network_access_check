.PHONY: help install uninstall test clean

# Default target
help:
	@echo "Network Connectivity Checker (netcheck) - Installation"
	@echo ""
	@echo "Available targets:"
	@echo "  make install     - Install netcheck system-wide (requires sudo)"
	@echo "  make uninstall   - Uninstall netcheck (requires sudo)"
	@echo "  make test        - Run basic tests"
	@echo "  make clean       - Remove temporary files"
	@echo ""
	@echo "Quick usage:"
	@echo "  sudo make install"

install:
	@echo "Installing netcheck..."
	@sudo ./install.sh

uninstall:
	@echo "Uninstalling netcheck..."
	@sudo ./uninstall.sh

test:
	@echo "Running basic tests..."
	@echo ""
	@echo "Test 1: Help command"
	@./check_ip.sh --help | head -5
	@echo ""
	@echo "Test 2: Quick test localhost:80"
	@./check_ip.sh -q localhost 80 || true
	@echo ""
	@echo "Test 3: Stdin input"
	@echo "localhost 80" | ./check_ip.sh 2>&1 | grep -E "Check Complete|Total"
	@echo ""
	@echo "Tests completed!"

clean:
	@echo "Cleaning temporary files..."
	@rm -f result.txt fail-*.txt combined-*.txt
	@echo "Done!"
