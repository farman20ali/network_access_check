import os
import sys

# Ensure parent directory is in sys.path when run directly as `python3 netcheck`
if __name__ == "__main__" and not __package__:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    __package__ = "netcheck"

from netcheck.cli import main

if __name__ == "__main__":
    main()
