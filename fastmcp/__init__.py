"""Compatibility shim for the installed FastMCP package.

This workspace contains a folder named fastmcp, which shadows the real package
when the current directory is in sys.path. We redirect the import to the actual
site-packages installation so the app can use the real FastMCP SDK.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_CURRENT_DIR = Path(__file__).resolve().parent


def _load_real_fastmcp():
    for entry in sys.path:
        if not entry:
            continue
        abs_entry = os.path.abspath(entry)
        if abs_entry == str(_CURRENT_DIR):
            continue
        candidate = Path(abs_entry) / "fastmcp" / "__init__.py"
        if candidate.exists() and candidate.resolve() != Path(__file__).resolve():
            real_package_dir = candidate.parent
            spec = importlib.util.spec_from_file_location(
                "fastmcp",
                str(candidate),
                submodule_search_locations=[str(real_package_dir)],
            )
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules["fastmcp"] = module
            spec.loader.exec_module(module)
            return module
    raise ImportError("Could not locate the installed FastMCP package outside this workspace shadow folder.")


_real_fastmcp = _load_real_fastmcp()

# Re-export the real package so existing imports keep working.
for name in [
    "Client",
    "Context",
    "FastMCP",
    "settings",
    "__version__",
]:
    if hasattr(_real_fastmcp, name):
        globals()[name] = getattr(_real_fastmcp, name)

# Make sure the package object used by Python is the real one from site-packages.
sys.modules[__name__] = _real_fastmcp
__all__ = list(getattr(_real_fastmcp, "__all__", ["FastMCP"]))
