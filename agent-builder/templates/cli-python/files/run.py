"""Entry script for PyInstaller (it needs a plain script, not a package module)."""

import sys

from __PKG_NAME__.cli import main

sys.exit(main())
