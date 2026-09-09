# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Dev-only import shim for the sibling-repository layout.

When this package is pip-installed (CI, a release, an end user) this file does
nothing. It exists so a fresh local checkout can run ``pytest`` without an
install step: the package's own ``src`` is prepended to ``sys.path`` only if the
import would otherwise fail. loomground-factual is a leaf — it has no Loomground
siblings at runtime — so only the self-src shim is needed.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]  # repo root; this file lives in tests/

if importlib.util.find_spec("loomground_factual") is None:
    _self_src = _HERE / "src"
    if _self_src.is_dir() and str(_self_src) not in sys.path:
        sys.path.insert(0, str(_self_src))
