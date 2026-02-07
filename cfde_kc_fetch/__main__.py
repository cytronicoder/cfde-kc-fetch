"""
Main entry point for the cfde_kc_fetch package.

Allows running the CLI via: python -m cfde_kc_fetch
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
