.PHONY: help install uninstall test clean

# Default target
help:
	@echo "Network Connectivity Checker (netcheck) - Make Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make install     - Install netcheck system-wide (requires sudo)"
	@echo "  make uninstall   - Uninstall netcheck (requires sudo)"
	@echo "  make test        - Run unit tests using pytest"
	@echo "  make clean       - Clean temporary results and build artifacts"
	@echo ""
	@echo "Quick usage:"
	@echo "  sudo make install"

install:
	@./packaging/linux/install.sh

uninstall:
	@./packaging/linux/uninstall.sh

test:
	@if command -v pytest > /dev/null; then \
		PYTHONPATH=. pytest tests/ -v; \
	else \
		PYTHONPATH=. python3 -m pytest tests/ -v; \
	fi

clean:
	@echo "Cleaning temporary files and build caches..."
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .benchmarks/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -f result-* fail-* combined-*
	@echo "Done!"
